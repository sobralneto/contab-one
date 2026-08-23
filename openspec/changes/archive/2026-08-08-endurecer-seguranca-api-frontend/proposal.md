## Why

Um scan de segurança do backend (`ContabOne.Api`) e do frontend, com verificação
executada contra os endpoints reais em container Postgres, encontrou 16 achados.
Cinco foram confirmados por teste, e o mais grave é estrutural: **o filtro de
isolamento multi-tenant falha aberto**.

Todos os query filters do `AppDbContext` são escritos como
`_tenantContext.EscritorioId == null || <entidade>.EscritorioId == _tenantContext.EscritorioId`.
Tenant indefinido significa "vê tudo", não "vê nada". Um usuário com papel de
escritório e `EscritorioId` nulo não recebe o claim `escritorio_id` no login, o
`TenantContextMiddleware` nunca chama `FromUsuario`, e o filtro vira
sempre-verdadeiro. O teste confirmou: esse usuário leu clientes de **todos** os
escritórios (`viuClienteDeA=True viuClienteDeB=True`), e o mesmo vale para
execuções, alertas, agentes e configurações.

Hoje não existe caminho pela API para criar esse usuário — `ResolverEscopo`
barra a criação e o rebaixamento de PlatformAdmin. É exatamente esse o problema:
a única coisa entre o produto e um vazamento entre escritórios é uma validação
dentro de um handler. Um INSERT manual, um seed, uma migração de dados ou um
caminho novo de cadastro reabre. Num SaaS multi-tenant essa é a falha de maior
consequência possível.

Junto vêm dois achados de autorização e superfície:

1. O grupo `/api/agent` usa `RequireAuthorization()` sem policy de papel — só
   exige *estar autenticado*. Um `EscritorioUsuario` comum baixa o bundle
   completo de regras de coleta (`GET /api/agent/regras` → 200) e grava clientes
   por fora de `/api/clientes` (`POST /api/agent/clientes` → 200). O handshake
   só não entrega a `HMAC_CNPJ_KEY` do servidor porque quebra antes, em
   `tenant.AgenteId!.Value` — a chave está protegida por acidente, não por
   design. Com ela, todo `CnpjHash` é reversível por força bruta.
2. `/openapi/v1.json` e `/scalar/v1` respondem 200 em produção, e nenhum dos
   dois hosts publicados envia cabeçalho de segurança algum (sem HSTS, CSP,
   `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`).

Descartados por teste, para não virar retrabalho: `FindAsync` **respeita** os
query filters (`PUT`/`DELETE /api/clientes/{id}` e `DELETE /api/agentes/{id}`
devolvem 404 com o dado intacto — não são IDOR); o CORS de produção rejeita
origem forjada corretamente; os endpoints de seed estão ausentes em produção; o
frontend não tem sinks de XSS e o `npm audit` está limpo.

## What Changes

**Isolamento e autorização**

- Os query filters do `AppDbContext` passam a falhar **fechados**: sem tenant
  resolvido e sem ser PlatformAdmin, nenhuma linha é visível.
- O `TenantContextMiddleware` rejeita com 401 um principal de papel de
  escritório que chegue sem `escritorio_id` resolvível, em vez de deixá-lo
  seguir com contexto vazio.
- **BREAKING** (dados): `Usuario.EscritorioId` ganha constraint de banco
  exigindo valor para papéis não-`PlatformAdmin`.
- O grupo `/api/agent` passa a exigir o papel `Agente`.

**Sessão e tokens**

- Refresh token deixa de ser um JWT stateless irrevogável: logout, troca de
  senha e desativação de usuário passam a invalidar as sessões existentes.
- O cookie de refresh passa a ser efetivamente enviado pelo navegador — hoje
  `SameSite=Strict` com frontend e API em domínios distintos
  (`contab-one.syslogic.com.br` vs `contab-one-production.up.railway.app`)
  faz o navegador nunca mandá-lo, o que deve estar derrubando a sessão a cada
  15 minutos.
- Login passa a gastar o mesmo tempo com e-mail inexistente (fim da enumeração
  por timing), e a política de bloqueio de conta passa a ser explícita.
- Validação de `issuer`/`audience` do JWT ligada.

**Superfície pública**

- `MapOpenApi()` e `MapScalarApiReference()` passam a existir só fora de
  produção, junto do seed.
- A API passa a ler o IP real do cliente via `X-Forwarded-For`: hoje o rate
  limiter particiona por `Connection.RemoteIpAddress`, que atrás do proxy do
  Railway/Cloudflare é sempre o mesmo — 10 logins/min para a plataforma inteira,
  e um atacante nega login a todos os clientes.
- `AllowedHosts` deixa de ser `*`.
- Frontend (Caddy) e API passam a enviar HSTS, CSP, `X-Frame-Options`,
  `X-Content-Type-Options`, `Referrer-Policy` e `Permissions-Policy`.

**Limites de entrada**

- `PUT /api/configuracao` passa a aceitar apenas chaves conhecidas, com teto de
  tamanho — hoje é um `Dictionary<string,string>` livre repassado ao agente no
  handshake.
- Os endpoints de lista do agente (`/clientes`, `/execucoes/{id}/metricas`)
  ganham teto de itens e deixam de fazer uma query por item.

**Sem impacto em spec** (tratados só em tasks): atualizar `Microsoft.OpenApi`
2.0.0 (GHSA-v5pm-xwqc-g5wc, severidade High); tirar os segredos de dev de
`appsettings.Development.json`; rodar o container da API como não-root; validar
o `redirect` da querystring no login.

## Capabilities

### New Capabilities

- `isolamento-multi-tenant`: como o escopo de tenant é resolvido e aplicado —
  falha fechada, sessão sem escritório rejeitada, e a garantia de que todo
  usuário de escritório tem escritório.
- `autorizacao-endpoints-agente`: quem pode alcançar `/api/agent` — só
  portadores de API key de agente ativo, nunca sessão humana.
- `ciclo-de-vida-da-sessao`: emissão, renovação e **revogação** de sessão;
  comportamento do cookie de refresh entre domínios; bloqueio de conta e
  resposta uniforme no login.
- `exposicao-publica-da-api`: o que a API expõe sem autenticação em produção —
  documentação, cabeçalhos de segurança, hosts aceitos e identificação do
  cliente real atrás do proxy para fins de rate limiting.
- `limites-de-entrada-da-api`: tetos e allowlists nas entradas que hoje chegam
  sem limite (configuração do escritório, listas do agente).

### Modified Capabilities

- `handshake-agente`: o requisito "A chave de ofuscação de CNPJ é sempre
  entregue" precisa dizer **a quem** — hoje o texto autoriza a leitura de que
  qualquer handshake bem-sucedido recebe a chave, e o grupo sem policy tornou
  isso quase verdade.

## Impact

**Backend** — `Infra/AppDbContext.cs` (filtros), `Infra/TenantContext.cs` e
`Infra/TenantContextMiddleware.cs` (resolução e rejeição), `Program.cs` (policy
do grupo agente, gate de OpenAPI, forwarded headers, HSTS, `AllowedHosts`,
lockout, JWT), `Features/Auth/AuthEndpoints.cs` (revogação, cookie, timing),
`Features/Dashboard/ConfiguracaoEndpoints.cs` (allowlist),
`Features/Agent/AgentEndpoints.cs` (tetos e escrita em lote), nova migração
(constraint de `EscritorioId` + tabela de refresh tokens), `Dockerfile` (usuário
não-root), `ContabOne.Api.csproj` (`Microsoft.OpenApi`).

**Frontend** — `Caddyfile` (cabeçalhos), `src/views/LoginView.vue` (validação do
`redirect`). Se o cookie de refresh for resolvido movendo a API para
`api.syslogic.com.br`, muda também `.env.production`.

**Testes** — `ContabOne.Api.Tests/IsolamentoTest.cs` ganha o caso do usuário sem
escritório (o cenário que reproduziu o achado) e o caso do usuário humano
tentando `/api/agent`.

**Operação** — as sessões ativas caem quando a revogação entrar; a mudança de
domínio da API (se adotada) exige atualizar `CORS_ORIGINS`.
