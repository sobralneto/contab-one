## Why

A revisão das três camadas (frontend Vue, API .NET, agente Python) encontrou dois defeitos que quebram fluxos em produção — a finalização de execuções com status `Falha` e o job diário de alertas ambos lançam exceção de tradução LINQ, confirmado empiricamente — e um conjunto de promessas não cumpridas entre camadas: a tela `admin/regras` nunca teve conteúdo publicado, a tela `Configuração` salva dados que nenhum agente lê, e o `hmacCnpjKey` pode chegar nulo ao agente sem que nada alerte, desligando silenciosamente todo o envio de métricas.

O ponto comum é que a API não entrega ao agente parte do que as telas dizem que entrega. Enquanto isso, cada execução falha do agente cria uma execução órfã nova no dashboard a cada retentativa, por até 30 dias.

## What Changes

**Correções de defeito**

- Substituir `a.Aberto` (propriedade computada sem coluna) por `a.ResolvidoEm == null` nos dois predicados EF que hoje lançam `InvalidOperationException`: finalização de execução com falha e job diário de alertas.
- Validar `HMAC_CNPJ_KEY` na inicialização da API, como já é feito com `JWT_SIGNING_KEY` — ausência da variável passa a impedir o boot em vez de degradar em silêncio.
- Calcular a próxima versão de regra sobre todas as versões existentes, não só sobre as ativas, eliminando a violação de índice único após um rollback fora do endpoint.

**Regras de coleta deixam de ser um campo vazio**

- Migration semeia a `RegraColeta` v1 com o bundle de fábrica, para que todo ambiente nasça com regra ativa.
- `POST /api/admin/regras` passa a validar o schema do bundle antes de aceitar, espelhando a validação que o agente já faz — hoje qualquer JSON bem-formado é publicado e silenciosamente rejeitado por todos os agentes.
- O editor da tela `admin/regras` abre pré-preenchido com o bundle ativo e valida o schema no cliente antes de habilitar a publicação.

**A configuração do escritório passa a chegar ao agente**

- `HandshakeResponse` ganha um bloco `configuracao` com os valores do escritório.
- O agente aplica esses valores sobre o `config.toml` local, mantendo o arquivo como fallback quando a API não responde.
- O agente passa a respeitar `plano.permiteEmitidas`, descartando a coleta de emitidas com aviso em log quando o plano não cobre — hoje o campo trafega e ninguém lê.

## Capabilities

### New Capabilities

- `regras-coleta-remotas`: publicação, validação de schema e versionamento do bundle de regras pela plataforma, e sua entrega ao agente via `GET /api/agent/regras`.
- `handshake-agente`: o contrato do que a API entrega ao agente no handshake — chave HMAC garantida, versão de regras, limites do plano e configuração do escritório.
- `registro-execucoes-agente`: abertura, envio de métricas e finalização de uma execução reportada pelo agente, incluindo os alertas derivados do caminho de falha.

### Modified Capabilities

- `configuracao-persistencia`: além de persistir sem erro, a configuração salva pelo escritório passa a ser entregue ao agente e aplicada na execução seguinte.

## Impact

**API (`ContabOne.Api`)**

- `Features/Agent/AgentEndpoints.cs` — predicado do alerta, bloco `configuracao` no handshake
- `Jobs/AlertaJob.cs` — predicado do alerta
- `Program.cs` — validação de `HMAC_CNPJ_KEY` no boot
- `Features/Admin/AdminEndpoints.cs` — validação de schema do bundle, cálculo de versão
- Nova migration com o seed da `RegraColeta` v1
- Novo validador de bundle (espelho de `regras.validar_bundle`)

**Frontend (`ContabOne.Frontend/src`)**

- `views/admin/RegrasView.vue` — pré-preenchimento e validação de schema
- `views/ConfiguracaoView.vue` — texto do aviso passa a ser verdadeiro
- `api/endpoints/admin.ts`, `api/types.ts` — endpoint para ler o conteúdo da regra ativa

**Agente (`Nfse.Agent`)**

- `api_client.py` — `DecisaoLicenca` carrega a configuração do escritório
- `nfse.py` — aplica configuração remota sobre o `config.toml` e respeita `permiteEmitidas`
- `testes/` — cobertura offline para configuração remota e bloqueio de emitidas

**Operacional**

- `HMAC_CNPJ_KEY` passa a ser obrigatória no Railway. **BREAKING** para qualquer deploy que hoje sobe sem ela — hoje sobe e funciona pela metade; depois desta mudança não sobe.
