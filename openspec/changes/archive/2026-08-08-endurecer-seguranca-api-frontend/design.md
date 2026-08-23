## Context

Ver `proposal.md` — Why para a motivação e os achados. O que importa aqui é o
estado atual que condiciona a solução:

- **Isolamento** vive inteiramente em query filters globais do `AppDbContext`,
  parametrizados por um `TenantContext` scoped que o `TenantContextMiddleware`
  preenche a partir dos claims do JWT (ou o `ApiKeyAuthenticationHandler`, para
  agentes). Não há filtro por linha no banco (nem RLS do Postgres).
- **Verificado durante o scan**: `DbSet.FindAsync` **respeita** os query filters
  quando vai ao banco. Os caminhos de escrita que usam `FindAsync` sem checagem
  explícita de tenant (`PUT`/`DELETE /api/clientes/{id}`,
  `DELETE /api/agentes/{id}`, `POST /api/alertas/{id}/resolver`) já estão
  protegidos. **Não mexer neles achando que são IDOR** — testados: 404 com o
  dado intacto.
- `Usuario` é a única entidade sem query filter, por necessidade: o
  `UserManager` precisa achar o usuário no login, antes de existir tenant.
  `UsuariosEndpoints` já aplica o escopo à mão em todos os handlers.
- **Deploy**: API e frontend são serviços Railway separados, em containers
  distintos, atrás de proxy de borda (Railway + Cloudflare no frontend). O
  frontend é Caddy servindo estático; a API é ASP.NET Core sem terminação TLS
  própria.
- **Domínios distintos hoje**: `contab-one.syslogic.com.br` (frontend) e
  `contab-one-production.up.railway.app` (API). `up.railway.app` está na
  Public Suffix List, então são *sites* diferentes para efeito de cookie.
- **Testes**: `ContabOne.Api.Tests` sobe a API real contra Postgres efêmero
  (Testcontainers). `IsolamentoTest` já cobre leitura entre escritórios pelos
  três caminhos. É onde as regressões deste trabalho devem ser fixadas.

## Goals / Non-Goals

**Goals:**

- Que a falha de isolamento seja *impossível por construção*, não evitada por
  validação: contexto de tenant ausente não pode significar acesso total, em
  nenhuma camada.
- Que a separação entre canal do agente e canal humano seja declarada na
  autorização, não emergente de um `NullReferenceException`.
- Que revogar acesso (logout, troca de senha, desativação) tenha efeito em
  segundos, não em dias.
- Manter compatibilidade do protocolo com os agentes instalados: nenhuma
  mudança neste trabalho pode exigir agente novo.

**Non-Goals:**

- Row-Level Security do Postgres. É a defesa mais forte para multi-tenant, mas
  exige repensar a conexão (usuário de banco por tenant ou `SET LOCAL`) e não
  cabe junto do resto. Fica registrado como caminho futuro.
- Rotação da `HMAC_CNPJ_KEY`. Ela é permanente por design — trocá-la invalida
  todo `CnpjHash` e duplica clientes. Este trabalho impede o vazamento; não
  trata resposta a um vazamento já ocorrido.
- Auditoria/trilha de acesso. Vale a pena, é outro trabalho.
- Revisão do `Nfse.Agent` (fora do escopo pedido no scan).

## Decisions

### 1. Filtro fail-closed com predicado explícito de admin

Trocar o `_tenantContext.EscritorioId == null || x.EscritorioId == _tenantContext.EscritorioId`
por um predicado em que a permissão total vem de um sinal próprio, não da
ausência de escopo:

```
x => _tenantContext.VeTodosOsEscritorios || x.EscritorioId == _tenantContext.EscritorioId
```

`VeTodosOsEscritorios` é uma propriedade do `TenantContext` que só fica
verdadeira quando `FromAdmin` foi chamado. O estado inicial do objeto — que é
exatamente o estado do bug — passa a filtrar por `EscritorioId == null`, e
nenhuma linha tem `EscritorioId` nulo. Falha fechada sem `if` extra.

*Alternativa descartada:* manter o `== null` e garantir no middleware que nunca
acontece. É o que existe hoje, e é justamente a estrutura frágil que o scan
encontrou — a correção não pode ser mais uma validação a montante.

*Cuidado de tradução:* a propriedade tem que ser avaliável como parâmetro pelo
EF Core, igual ao acesso a `EscritorioId` hoje. `TraducaoLinqTest` existe para
pegar exatamente esse tipo de regressão; incluir um caso lá.

### 2. Rejeição no middleware, e não só filtro

O filtro fail-closed faz um usuário sem escritório ver zero linhas — melhor que
ver tudo, mas confuso (tela vazia sem explicação) e ainda permite escrita em
caminhos que derivam o escritório de outro lugar. O `TenantContextMiddleware`
passa a responder 401 quando o principal tem papel de escritório e não dá para
resolver o escritório.

Duas camadas de propósito: o middleware dá a resposta correta ao caso conhecido,
o filtro cobre qualquer caminho que escape do middleware no futuro.

### 3. Constraint no banco, não só validação no handler

`CHECK ("Papel" = <PlatformAdmin> OR "EscritorioId" IS NOT NULL)` na tabela de
usuários. É a única camada que também vale para INSERT manual, seed e migração
de dados — as origens que o `ResolverEscopo` não cobre e que reabrem o buraco.

*Ordem importa na migração:* se a base já tiver alguma linha nesse estado, a
constraint falha ao subir. Verificar e corrigir os dados antes.

### 4. Policy `Agente` no grupo, e handshake que erra explícito

`RequireAuthorization(p => p.RequireRole("Agente"))` no `MapGroup("/api/agent")`.
Resolve regras, upsert, métricas e handshake de uma vez.

Junto: trocar os `tenant.AgenteId!.Value` / `tenant.EscritorioId!.Value` dos
handlers por checagem explícita com resposta 403. Hoje eles produzem 500 — o que
por acaso protegeu a `HMAC_CNPJ_KEY`, mas proteção por exceção não é proteção.

`PlatformAdmin` **não** ganha acesso ao grupo. Para inspecionar regras existe
`/api/admin/regras`, que já devolve o conteúdo.

### 5. Refresh token com identidade no banco

Tabela `RefreshToken` (`Id`, `UsuarioId`, `TokenHash`, `ExpiraEm`, `RevogadoEm`,
`CriadoEm`). O JWT de refresh passa a carregar o id da linha; validar significa
achar a linha, conferir que não está revogada nem vencida e conferir o hash.

- **Logout** revoga a linha da sessão atual (só ela — sair num navegador não
  derruba o outro).
- **Troca de senha / reset por admin / desativação** revogam todas as linhas do
  usuário. Na troca feita pelo próprio usuário, a sessão que trocou é reemitida
  logo em seguida, então na prática ela sobrevive.
- **Rotação**: `/refresh` revoga a linha usada e cria outra. Reuso de uma linha
  já revogada é sinal de token roubado → revogar toda a família daquele usuário.

*Alternativa descartada:* usar o `SecurityStamp` do Identity nos claims. Resolve
troca de senha e desativação sem tabela nova, mas não resolve logout de uma
sessão só, e não detecta reuso. A tabela custa uma migração e entrega os três.

*Custo aceito:* uma consulta ao banco por refresh. É uma vez a cada 15 minutos
por usuário.

### 6. Cookie de refresh: mover a API para o mesmo domínio

**Decidido:** publicar a API em `api.syslogic.com.br` e usar
`SameSite=Lax; Domain=.syslogic.com.br`. Frontend e API passam a ser o mesmo
site, o cookie viaja, e não é preciso token CSRF — `Lax` já barra requisição
forjada de terceiro nas rotas que mudam estado.

*Alternativa descartada:* manter domínios separados com `SameSite=None; Secure`.
Funciona, mas exige defesa contra CSRF em toda rota que muda estado (o CORS
restringe a origem, mas não protege o que não é preflightado) — uma peça a mais
para manter pelo resto da vida do produto, pelo mesmo resultado.

*Verificar antes de mudar:* o sintoma esperado hoje é o usuário ser levado à
tela de login a cada ~15 minutos (validade do token de acesso), porque o cookie
nunca chega ao `/refresh`. Não está confirmado em produção — a primeira task do
grupo é reproduzir isso, para não mexer em domínio com base em premissa. Se o
refresh estiver funcionando, o entendimento sobre o caminho do cookie está
errado em algum ponto e o grupo inteiro precisa ser reavaliado antes de seguir.

### 7. Forwarded headers restritos aos proxies conhecidos

`UseForwardedHeaders` com `ForwardedHeaders.XForwardedFor | XForwardedProto`,
**antes** do rate limiter. `KnownNetworks`/`KnownProxies` configurados; sem isso
qualquer um forja `X-Forwarded-For` e a partição por IP vira ficção — troca um
problema por outro pior.

Se a faixa do Railway não for estável o suficiente para uma allowlist, usar
`ForwardLimit` com o número real de saltos e documentar o motivo.

### 8. Cabeçalhos de segurança no Caddy e na API

No `Caddyfile`, bloco `header` com HSTS, `X-Frame-Options: DENY`,
`X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`,
`Permissions-Policy` restritiva e CSP.

CSP: o SPA é Vue compilado, sem `eval` e sem script inline — deve passar com
`default-src 'self'` sem `unsafe-inline` para script. `style-src` provavelmente
precisa de `'unsafe-inline'` (Vue injeta estilo de componente em runtime);
confirmar no navegador antes de fechar. `connect-src` precisa liberar o host da
API — e muda se a decisão 6 mudar o domínio.

Ordem: aplicar CSP em `Content-Security-Policy-Report-Only` primeiro, ver o
console limpo, então promover. Uma CSP errada quebra a aplicação inteira e o
sintoma é tela branca.

### 9. Allowlist de configuração vinda do que o frontend já usa

As chaves reconhecidas são as que a tela de Configuração salva e o handshake
entrega (ver `configuracao-persistencia` e `handshake-agente`). Definir a lista
como constante no backend e validar contra ela, com teto por valor.

*Compatibilidade:* se houver chave gravada hoje fora da lista, a leitura não
pode quebrar — filtrar na leitura, recusar só na escrita.

## Risks / Trade-offs

- **Constraint falha ao migrar por dado sujo** → Rodar antes uma consulta de
  verificação e corrigir; a migração inclui o `UPDATE` de saneamento se algo
  aparecer.
- **Filtro novo não traduz para SQL e vira avaliação em memória** (ou explode em
  runtime) → Caso em `TraducaoLinqTest` cobrindo o predicado novo, além do
  `IsolamentoTest`.
- **Revogação derruba todas as sessões ativas no deploy** → Esperado e aceitável
  (todo mundo faz login de novo uma vez). Avisar antes.
- **CSP quebra o frontend** → `Report-Only` primeiro, promoção depois de
  verificar.
- **Forwarded headers mal configurados fazem o rate limiter confiar em cabeçalho
  forjável** → Allowlist de proxy obrigatória; sem ela, não fazer a mudança.
- **Policy `Agente` derruba integração não prevista** → O grupo `/api/agent` só é
  chamado pelo agente; confirmar nos logs antes de subir.
- **Mudar o domínio da API exige atualizar `CORS_ORIGINS`, `.env.production` e
  reconstruir o frontend** (a URL é embutida no build, não lida em runtime) →
  Sequência explícita nas tasks.

## Migration Plan

1. Migração de banco: constraint de `EscritorioId` + tabela `RefreshToken`
   (aditiva, aplicada no boot como as demais).
2. Subir a API com filtro fail-closed, rejeição no middleware, policy do grupo
   agente, gate de OpenAPI, forwarded headers, `AllowedHosts` e lockout
   explícito. Nada aqui exige mudança no frontend nem no agente.
3. Subir o frontend com os cabeçalhos (CSP em `Report-Only`).
4. Revogação de refresh + cookie: junto da eventual mudança de domínio da API.
   Este é o passo que derruba sessões.
5. Promover a CSP depois de um período com o relatório limpo.

**Rollback:** cada passo é revertível pelo deploy anterior. A migração é
aditiva; a constraint pode ser derrubada isoladamente se bloquear operação.

## Open Questions

- Qual faixa de IP o Railway usa na borda, para a allowlist de proxy? Descobrir
  na implementação da decisão 7 — não muda a abordagem, só o valor configurado.
- `style-src` precisa mesmo de `'unsafe-inline'`? Verificar no navegador ao
  montar a CSP; se não precisar, fechar mais.
