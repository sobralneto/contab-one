## Context

Ver [proposal.md](proposal.md) para a motivação. O que importa aqui são as restrições que moldam a abordagem:

- **O agente é distribuído como `.exe` PyInstaller** na máquina de cada escritório. Não há como corrigi-lo remotamente — qualquer coisa que dependa de atualizar o agente leva semanas ou meses para chegar a todos. Por isso a correção precisa ser resiliente a agente antigo falando com API nova.
- **As duas validações de bundle vivem em linguagens diferentes.** `regras.validar_bundle()` (Python) é a autoridade final: um bundle que ela rejeita não é adotado, aconteça o que acontecer no servidor. A validação que esta mudança adiciona na API é um portão de usabilidade para o admin, não uma fronteira de segurança.
- **`ConfiguracaoEscritorio` é chave/valor livre** (`string` → `string`), sem schema no banco. O front hoje grava quatro chaves: `tipos` (`"recebidas,emitidas"`), `primeira_busca_desde` (`"AAAA-MM-DD"`), `pasta_saida` e `gerar_pdf` (`"true"`/`"false"`).
- **`carregar_config()` no agente usa `erro_fatal()`** para valor inválido — o processo morre. Isso é correto para um `config.toml` que o próprio operador editou, e inaceitável para um valor que chegou pela rede.
- **Ordem em `main()`**: `carregar_config` → `--tipos` da CLI → `resolver_periodo` → handshake → `resolver_bundle`/`aplicar_regras` → `listar_empresas` → loop de coleta. A configuração remota chega depois da local e da CLI, mas antes de qualquer certificado ser tocado.

## Goals / Non-Goals

**Goals:**

- Eliminar os dois caminhos que hoje lançam exceção em runtime, com teste que os cubra sem precisar de banco de pé.
- Fazer a tela `admin/regras` sair do estado "campo vazio" de forma que ambiente novo já nasça correto.
- Fechar o laço da tela `Configuração`: o que é salvo chega e é aplicado.
- Manter agente antigo funcionando contra API nova, e agente novo funcionando contra API antiga.

**Non-Goals:**

- Reescrever a validação do bundle como schema único compartilhado entre C# e Python. Avaliado e descartado abaixo.
- Rollback de versão de regra pela tela. A tela continua só publicando adiante; rollback segue sendo republicar. Fica registrado como dívida.
- Aplicar `permiteEmitidas` no lado servidor (rejeitar métricas de emitidas na ingestão). Nesta mudança o limite é aplicado só no agente.
- Corrigir os itens cosméticos levantados na revisão (`CnpjHasher` morto, `Results.Forbid()` inalcançável, `AgenteVersaoMinima` hardcoded, aviso NU1903 do `Microsoft.OpenApi`).

## Decisions

### 1. `a.Aberto` → `a.ResolvidoEm == null`, e a propriedade computada fica

`Alerta.Aberto` e `Agente.Ativo` são propriedades somente-leitura sem coluna; o EF não as traduz dentro de `Where`/`Any`. Confirmado rodando `ToQueryString()` contra os trechos reais: os dois predicados lançam `InvalidOperationException`, enquanto a projeção final em `AlertasEndpoints` funciona (avaliação no cliente é permitida só ali).

Alternativas consideradas:

- **Mapear `Aberto` como coluna computada no Postgres.** Descartado: cria uma coluna redundante com `ResolvidoEm`, e uma migration por um problema que é de escrita de query.
- **Remover a propriedade computada.** Descartado: ela é legítima e correta em código que já materializou a entidade — `ApiKeyAuthenticationHandler` usa `agente.Ativo` assim.

Escolha: trocar só os dois predicados. O risco de reintrodução é real (é um erro natural de escrever), então o teste de tradução entra na suíte em vez de ficar como verificação manual.

### 2. Teste de tradução LINQ sem banco, via `ToQueryString()`

`ToQueryString()` força a compilação da query e a tradução para SQL sem abrir conexão. Isso permite cobrir os dois predicados corrigidos em um teste que roda no CI sem Postgres, e que falha no dia em que alguém escrever `a.Aberto` num `Where` de novo.

Alternativa: teste de integração com banco real via `docker-compose`. Descartado como porta de entrada — mais lento, mais frágil, e não pega nada a mais para esta classe de defeito.

### 3. Validador de bundle em C#, mantido honesto por corpus compartilhado

O servidor precisa de uma validação em C# porque o Python não roda lá. Duplicar regra dá divergência com o tempo.

Alternativas consideradas:

- **JSON Schema como fonte única**, validado nos dois lados. Descartado: exigiria uma biblioteca de JSON Schema no agente. O agente hoje depende de `requests`, `requests-pkcs12` e `reportlab`, é empacotado com PyInstaller, e cada dependência nova é peso no `.exe` e risco de `--hidden-import` faltando. O ganho não paga.
- **Endpoint na API que chama o Python.** Descartado, obviamente — acopla runtime.

Escolha: validador C# escrito à mão espelhando `regras.validar_bundle()`, mais um **corpus de fixtures em `testes/fixtures/bundles/`** — arquivos JSON válidos e inválidos, cada um com o veredito esperado. O teste .NET e o teste Python leem o mesmo corpus. Divergência entre os dois validadores vira falha de teste em vez de descoberta em produção.

A validação do servidor rejeita a publicação com a lista de campos problemáticos (`ValidationProblem`), não com um 500.

### 4. Seed da regra v1 por migration idempotente, não por `HasData`

Alternativas consideradas:

- **`HasData` no `OnModelCreating`.** Descartado: EF passa a considerar aquela linha parte permanente do modelo. Publicar a v2 e desativar a v1 faz o EF querer "restaurar" o estado semeado na migration seguinte, e o `Guid` fixo vira um valor mágico no código do modelo para sempre.
- **Seed no startup da API.** Descartado: roda a cada boot, precisa de guarda própria, e mistura configuração de dados com ciclo de vida do processo.

Escolha: migration explícita com `INSERT ... WHERE NOT EXISTS` sobre `RegraColeta`. É um estado inicial, aplicado uma vez, e some do caminho depois. O conteúdo semeado é exatamente o `BUNDLE_FABRICA` do agente — assim o seed não muda comportamento nenhum de quem já está rodando, só sincroniza a numeração e destrava a publicação de v2 em diante.

### 5. `configuracao` no handshake vai como dicionário cru

A alternativa é um DTO tipado (`ConfiguracaoInfo { Tipos, PrimeiraBuscaDesde, PastaSaida, GerarPdf }`).

Escolha: dicionário `{ chave: valor }`, espelhando o `valores` que `GET /api/configuracao` já devolve.

Razão: cada chave nova num DTO tipado obriga a mexer nas três camadas em conjunto e a versionar o contrato. Com dicionário, uma chave nova é aditiva — agente antigo ignora o que não conhece, exatamente como já faz com campos desconhecidos do bundle de regras. O custo é perder tipagem no trânsito; a mitigação é que o agente valida e coage cada chave conhecida na entrada, e o front continua sendo o único a decidir o formato de escrita.

### 6. Precedência de configuração, e configuração remota nunca mata a execução

Precedência, do mais forte para o mais fraco:

1. **Limite do plano** (`permiteEmitidas`) — teto comercial, corta acima de tudo
2. **Flag de CLI** (`--tipos`) — quem digitou está depurando; o servidor não sobrescreve
3. **Configuração remota** do handshake
4. **`config.toml` local**
5. **Padrão embutido**

`pasta_certificados`, `senhas` e `senha_padrao` **nunca** entram nesse fluxo: são segredo e caminho de máquina, não configuração de plataforma.

A regra que mais importa: **valor remoto inválido é descartado com aviso em log, nunca `erro_fatal()`**. Um `primeira_busca_desde` digitado errado na tela hoje derrubaria todos os agentes daquele escritório na próxima execução. A coerção remota reaproveita a mesma lógica da local, mas com tratamento de erro invertido — a local morre, a remota degrada para o valor anterior. Mesmo princípio que `validar_bundle` já aplica: dado vindo da rede não é confiável o bastante para matar o processo.

### 7. Ordem de deploy: API primeiro, agente depois

O campo `configuracao` é aditivo na resposta do handshake — agente antigo simplesmente não o lê. E o agente novo trata `configuracao` ausente como "sem configuração remota", que é o comportamento de hoje. Isso torna as duas pontas independentes: dá para subir a API e só depois distribuir o `.exe`, sem janela de incompatibilidade.

A exceção é `HMAC_CNPJ_KEY`, que passa a barrar o boot. Ver Migration Plan.

## Risks / Trade-offs

- **`HMAC_CNPJ_KEY` ausente derruba o deploy da API** → É deliberado: hoje ela sobe e o pipeline de métricas fica morto em silêncio, o que é pior. Mitigação: conferir a variável no Railway **antes** de fazer o merge, e a mensagem de erro nomeia a variável faltante.
- **Trocar a chave HMAC invalida todos os `CnpjHash` já gravados** → Fora do escopo desta mudança, mas a validação no boot torna a variável visível pela primeira vez, e alguém pode "arrumar" gerando uma nova. Mitigação: documentar no `.env.example`/README que a chave é permanente, e que trocá-la duplica todos os clientes.
- **Os dois validadores de bundle divergirem mesmo assim** → O corpus compartilhado cobre os casos que existirem nele, não os que ninguém pensou. Mitigação real: o agente continua sendo a autoridade — um bundle que passe indevidamente no servidor ainda é rejeitado localmente e a versão anterior é preservada. O pior caso continua sendo o de hoje, não pior que ele.
- **`pasta_saida` vinda do servidor pode não existir na máquina do cliente** → Um caminho válido para um escritório pode ser inválido para outro. Mitigação: tratar como qualquer valor remoto inválido — se o caminho não puder ser criado/resolvido, avisa e mantém o local.
- **Aplicar `permiteEmitidas` só no agente é contornável** → Quem edita o `.exe` ou bloqueia o handshake escapa. Aceito conscientemente: o modelo de licenciamento inteiro já assume isso (ver o comentário longo em `api_client._assinar_payload`). Aplicar no servidor entra quando houver motivo comercial, e está listado em Non-Goals.
- **Seed cria uma v1 em bancos que já rodam sem regra nenhuma** → Instalações existentes passam de `regrasVersaoAtual: 0` para `1`, e todo agente vai baixar o bundle no próximo handshake. Como o conteúdo é idêntico ao de fábrica, o efeito prático é só popular `_regras_cache.json`. Mitigação: nenhuma necessária, mas vale acompanhar o primeiro dia de logs.

## Migration Plan

1. **Antes do merge**: confirmar `HMAC_CNPJ_KEY` setada no ambiente Railway. Sem isso o deploy falha no boot.
2. **Deploy da API**: a migration roda no startup (`db.Database.MigrateAsync()`), semeando a regra v1. Agentes em campo continuam funcionando sem alteração — o handshake ganha um campo que eles ignoram.
3. **Deploy do frontend**: editor de regras pré-preenchido e aviso da tela de Configuração corrigido.
4. **Distribuição do agente**: `VERSAO_AGENTE` sobe para `2.1.0`; `AgenteVersaoMinima` na API permanece em `2.0.0` para não gerar aviso desnecessário em quem ainda não atualizou.

**Rollback**: reverter API e frontend é seguro — a linha semeada de `RegraColeta` é inofensiva para a versão anterior do código, que simplesmente passa a ter uma regra ativa onde antes não tinha. O agente novo contra API antiga também funciona (sem `configuracao` na resposta, cai no comportamento atual). Não há passo de rollback de dados.
