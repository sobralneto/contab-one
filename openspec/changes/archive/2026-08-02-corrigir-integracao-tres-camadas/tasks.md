## 1. Correções de defeito na API

Grupo autocontido — pode ser mergeado e deployado sozinho, sem depender de nenhum outro grupo.

- [x] 1.1 Em `ContabOne.Api/Features/Agent/AgentEndpoints.cs`, trocar `a.Aberto` por `a.ResolvidoEm == null` no predicado de `FinalizarExecucaoAsync`
- [x] 1.2 Em `ContabOne.Api/Jobs/AlertaJob.cs`, trocar `a.Aberto` por `a.ResolvidoEm == null` no predicado de `CriarAlertaSeNaoExiste`
- [x] 1.3 Em `ContabOne.Api/Program.cs`, validar `HMAC_CNPJ_KEY` na inicialização com `throw new InvalidOperationException`, no mesmo bloco e no mesmo estilo da validação de `JWT_SIGNING_KEY`
- [x] 1.4 Em `ContabOne.Api/Features/Admin/AdminEndpoints.cs`, calcular `novaVersao` sobre todas as regras (`MaxAsync(r => (int?)r.Versao) ?? 0`), não só sobre as ativas
- [x] 1.5 Registrar no README/`.env.example` que `HMAC_CNPJ_KEY` é obrigatória e permanente — trocá-la duplica todos os clientes já cadastrados

## 2. Projeto de testes .NET

Não existe projeto de teste no repositório hoje. Ele é criado aqui porque o grupo 1 introduz correções que precisam de rede de proteção contra reintrodução.

- [x] 2.1 Criar `ContabOne.Api.Tests` (xunit) com referência a `ContabOne.Api`, e uma solution na raiz reunindo os dois projetos
- [x] 2.2 Escrever teste de tradução LINQ usando `ToQueryString()` que cobre os dois predicados corrigidos em 1.1 e 1.2 — falha se alguém reintroduzir uma propriedade computada não-mapeada num `Where`/`Any`
- [x] 2.3 Confirmar que o teste falha ao reverter 1.1 ou 1.2 (verificação do próprio teste, não só do código)
- [x] 2.4 Rodar `dotnet test` e confirmar suíte verde

## 3. Validação do bundle de regras no servidor

- [x] 3.1 Criar o corpus compartilhado em `Nfse.Agent/testes/fixtures/bundles/`: arquivos JSON de bundle válidos e inválidos, cada um acompanhado do veredito esperado (válido, ou lista de campos com problema)
- [x] 3.2 Incluir no corpus os casos que `regras.validar_bundle()` já cobre: URL sem `https`, `maxDiasFiltro` fora de 1–366 e booleano no lugar de inteiro, `paramPagina` vazio, listagem faltando, `colunas` vazia ou com não-string, regex que não compila
- [x] 3.3 Adicionar `Nfse.Agent/testes/teste_corpus_bundles.py` que roda `validar_bundle()` contra o corpus e confere cada veredito
- [x] 3.4 Implementar o validador de bundle em C# espelhando `regras.validar_bundle()`, devolvendo a lista de campos problemáticos
- [x] 3.5 Adicionar teste .NET que roda o validador C# contra o mesmo corpus de 3.1 e confere os mesmos vereditos
- [x] 3.6 Ligar o validador ao `POST /api/admin/regras`, respondendo `ValidationProblem` com a lista de campos quando o bundle for inválido
- [x] 3.7 Adicionar `GET /api/admin/regras/{id}` (ou equivalente) que devolve o `Conteudo` de uma versão, necessário para o editor pré-preenchido do grupo 5 — **já existia** do change `visualizar-editar-regras` (`ObterRegraAsync` + `RegraDetalheDto`); apenas verificado

## 4. Seed da regra v1

- [x] 4.1 Criar migration com `INSERT ... WHERE NOT EXISTS` inserindo a `RegraColeta` v1 ativa, com conteúdo idêntico ao `BUNDLE_FABRICA` de `Nfse.Agent/regras.py`
- [x] 4.2 Adicionar teste que roda o conteúdo semeado pelo validador C# de 3.4 e confirma que ele é válido
- [x] 4.3 Verificar em banco limpo (`docker-compose up` + migrate) que a v1 nasce ativa e que o handshake passa a devolver `regrasVersaoAtual: 1`
- [x] 4.4 Verificar em banco que já tem dados que a migration é idempotente e não duplica linha

## 5. Editor de regras no frontend

- [x] 5.1 Adicionar em `ContabOne.Frontend/src/api/endpoints/admin.ts` e `types.ts` a chamada que lê o conteúdo da versão ativa (endpoint de 3.7)
- [x] 5.2 Em `ContabOne.Frontend/src/views/admin/RegrasView.vue`, pré-preencher o editor com o conteúdo da versão ativa, formatado
- [x] 5.3 Adicionar validação de schema no cliente além do `JSON.parse` atual, exibindo os campos problemáticos e mantendo o botão de publicar desabilitado enquanto houver erro
- [x] 5.4 Tratar e exibir o `ValidationProblem` que o servidor pode devolver em 3.6, para o caso de o cliente e o servidor discordarem
- [x] 5.5 Rodar `npm run build` (inclui `vue-tsc`) e confirmar zero erros

## 6. Configuração do escritório no handshake (API)

- [x] 6.1 Adicionar `Configuracao` (dicionário `chave` → `valor`) a `HandshakeResponse` em `ContabOne.Api/Features/Agent/AgentEndpoints.cs`
- [x] 6.2 Preencher o dicionário a partir de `ConfiguracoesEscritorio` do escritório do agente, devolvendo objeto vazio quando não houver configuração salva
- [x] 6.3 Adicionar teste confirmando que o handshake de um escritório devolve apenas a configuração dele, e nada de outro escritório

## 7. Configuração remota e limite de plano no agente

- [x] 7.1 Em `Nfse.Agent/api_client.py`, expor a `configuracao` recebida no handshake através de `DecisaoLicenca`, e persistí-la no cache de licença junto com o restante do payload (para o modo offline)
- [x] 7.2 Em `Nfse.Agent/nfse.py`, criar a função que aplica a configuração remota sobre a local, coagindo cada chave conhecida (`tipos`, `primeira_busca_desde`, `pasta_saida`, `gerar_pdf`) e **descartando com aviso em log** qualquer valor inválido, nunca chamando `erro_fatal()`
- [x] 7.3 Implementar a precedência definida em design.md: plano > flag de CLI > configuração remota > `config.toml` > padrão
- [x] 7.4 Garantir que `pasta_certificados`, `senhas` e `senha_padrao` não sejam afetados por configuração remota
- [x] 7.5 Aplicar `plano.permiteEmitidas`: descartar `emitidas` dos tipos com aviso em log quando o plano não cobrir; nenhuma restrição quando o handshake não informar plano
- [x] 7.6 Chamar a aplicação da configuração remota em `main()` logo após o handshake e antes de `listar_empresas()`
- [x] 7.7 Subir `VERSAO_AGENTE` para `2.1.0` em `api_client.py`

## 8. Testes offline do agente

- [x] 8.1 Estender `Nfse.Agent/testes/_fake_api.py` para que `handshake_padrao()` aceite o bloco `configuracao`
- [x] 8.2 Teste: configuração remota sobrescreve a local para as chaves informadas, e a local supre as demais
- [x] 8.3 Teste: valor remoto inválido (data malformada, tipo desconhecido) é descartado com aviso e a execução continua com o valor anterior — nunca aborta
- [x] 8.4 Teste: `--tipos` na CLI vence sobre a configuração remota
- [x] 8.5 Teste: `permiteEmitidas: false` remove emitidas mesmo quando configuração remota, local e CLI pedem emitidas
- [x] 8.6 Teste: handshake sem `configuracao` mantém exatamente o comportamento atual (compatibilidade com API antiga)
- [x] 8.7 Teste: em carência offline, a configuração usada é a do cache de licença
- [x] 8.8 Rodar `python testes/executar_tudo.py` e confirmar suíte verde

## 9. Frontend — tela de Configuração

- [x] 9.1 Em `ContabOne.Frontend/src/views/ConfiguracaoView.vue`, ajustar o aviso para descrever com precisão quando as alterações passam a valer, agora que a entrega pelo handshake existe de fato
- [x] 9.2 Rodar `npm run build` e confirmar zero erros

## 10. Verificação de ponta a ponta

- [x] 10.1 Subir Postgres (`docker-compose up`) e a API com `HMAC_CNPJ_KEY` setada; confirmar boot e migration aplicada
- [x] 10.2 Confirmar que a API não sobe sem `HMAC_CNPJ_KEY`, com mensagem nomeando a variável
- [x] 10.3 Rodada real do agente contra a API local: handshake → configuração aplicada → regras v1 baixadas e cacheadas → upsert de clientes → métricas → finalizar com sucesso
- [x] 10.4 Rodada com falha forçada: confirmar que `finalizar` com status `Falha` responde com sucesso, grava o status e abre o alerta — o caminho que hoje devolve 500
- [x] 10.5 Rodar o job de alertas (`--job=alertas`) contra o banco populado e confirmar que percorre todos os escritórios sem exceção
- [x] 10.6 Publicar uma v2 pela tela `admin/regras` e confirmar que o agente a adota na execução seguinte
- [x] 10.7 Tentar publicar um bundle fora do schema e confirmar a rejeição com os campos apontados
- [x] 10.8 Rodar `dotnet build`, `dotnet test`, `npm run build` e `python testes/executar_tudo.py` — tudo verde
