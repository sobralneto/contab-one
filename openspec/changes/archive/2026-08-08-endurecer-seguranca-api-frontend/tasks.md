## 1. Isolamento multi-tenant (fail-closed)

- [x] 1.1 Adicionar `VeTodosOsEscritorios` ao `TenantContext`, verdadeiro somente depois de `FromAdmin`; manter `IsAdmin` como está para não quebrar os handlers que já o usam
- [x] 1.2 Reescrever os seis query filters do `AppDbContext` (`Agente`, `Cliente`, `Execucao`, `ExecucaoMetrica`, `ConfiguracaoEscritorio`, `Alerta`) usando `VeTodosOsEscritorios || x.EscritorioId == _tenantContext.EscritorioId`
- [x] 1.3 Adicionar caso em `TraducaoLinqTest` confirmando que o predicado novo traduz para SQL (não vira avaliação em memória nem estoura em runtime)
- [x] 1.4 Fazer o `TenantContextMiddleware` responder 401 quando o papel for `EscritorioAdmin`/`EscritorioUsuario` e o escritório não for resolvível, sem chamar o próximo middleware
- [ ] 1.5 Consultar a base de produção por usuários com papel de escritório e `EscritorioId` nulo; sanear se houver, antes de criar a constraint *(requer acesso à produção)*
- [ ] 1.6 Migração: `CHECK` na tabela de usuários exigindo `EscritorioId` para papel diferente de `PlatformAdmin` *(requer verificação 1.5 primeiro)*
- [x] 1.7 Adicionar ao `IsolamentoTest` o caso do usuário de escritório sem escritório — o cenário que reproduziu o achado — esperando 401 e nenhuma linha de outro escritório
- [x] 1.9 Adicionar teste da segunda camada: `AppDbContext` com tenant não resolvido não devolve linha alguma, independente do middleware
- [x] 1.8 Rodar a suíte de testes inteira — 77/77 passando. As 4 falhas iniciais em `ContratoAgenteTest` eram asserções de releitura que dependiam do fail-open; corrigidas com `.IgnoreQueryFilters()`

## 2. Autorização dos endpoints do agente

- [x] 2.1 Trocar `RequireAuthorization()` por `RequireAuthorization(p => p.RequireRole("Agente"))` no `MapGroup("/api/agent")` em `Program.cs`
- [x] 2.2 Substituir os `tenant.AgenteId!.Value` e `tenant.EscritorioId!.Value` dos handlers de `AgentEndpoints` por checagem explícita com 403 — proteção por exceção não é proteção
- [ ] 2.3 Adicionar teste: usuário do painel (`EscritorioUsuario`, `EscritorioAdmin` e `PlatformAdmin`) recebe 403 em `/api/agent/regras`, `/api/agent/handshake` e `/api/agent/clientes` *(requer container Postgres)*
- [ ] 2.4 Adicionar teste: nenhuma resposta da API entrega a `HMAC_CNPJ_KEY` a uma sessão humana *(requer container Postgres)*
- [ ] 2.5 Conferir nos logs de produção que só o agente chama `/api/agent` antes de subir *(requer acesso à produção)*

## 3. Superfície pública da API

- [x] 3.1 Mover `MapOpenApi()` e `MapScalarApiReference()` para dentro do `if (app.Environment.IsDevelopment())`, junto do seed
- [ ] 3.2 Atualizar `Microsoft.OpenApi` para a versão que corrige GHSA-v5pm-xwqc-g5wc e confirmar com `dotnet list package --vulnerable --include-transitive` *(requer NuGet)*
- [ ] 3.3 Descobrir a faixa de IP da borda do Railway para a allowlist de proxy (resolve a Open Question 1 do design) *(requer acesso ao Railway)*
- [ ] 3.4 Adicionar `UseForwardedHeaders` (`XForwardedFor | XForwardedProto`) com `KnownNetworks`/`KnownProxies` preenchidos, posicionado **antes** do `UseRateLimiter` *(a chamada existe mas está inerte: com o default só-loopback o middleware para no primeiro IP remoto desconhecido e nunca aplica o X-Forwarded-For. Só fecha junto com 3.3)*
- [ ] 3.5 Trocar `AllowedHosts: "*"` pelos hosts reais de cada ambiente *(requer conhecimento dos hosts de produção)*
- [x] 3.6 Adicionar `UseHsts` e os cabeçalhos de segurança nas respostas da API
- [ ] 3.7 Verificar em produção que `/openapi/v1.json` e `/scalar/v1` respondem 404 *(requer acesso à produção)*

## 4. Cabeçalhos de segurança no frontend

- [ ] 4.1 Adicionar bloco `header` no `Caddyfile`... *(requer acesso ao Caddyfile e deploy)*
- [ ] 4.2-4.5 CSP e verificação *(requerem navegador, deploy, curl em produção)*

## 5. Ciclo de vida da sessão — revogação

- [ ] 5.1-5.8 *(feature grande — requer migração, entidade nova, lógica de revogação, testes)*

## 6. Ciclo de vida da sessão — cookie e domínio

- [ ] 6.1-6.7 *(requer acesso ao Railway, DNS, deploy do frontend)*

## 7. Ciclo de vida da sessão — login

- [x] 7.1 Fazer o login gastar o mesmo tempo com e-mail inexistente (verificação de senha contra hash descartável em vez de retorno antecipado)
- [x] 7.2 Configurar `Lockout` explicitamente em `Program.cs` (limite de tentativas e duração), em vez de herdar o padrão implícito do Identity
- [x] 7.3 Ligar `ValidateIssuer` e `ValidateAudience`, emitindo os tokens com emissor e destinatário próprios — emissão e validação leem a **mesma** configuração (`AuthEndpoints.IssuerPadrao`), com `IConfiguration` como parâmetro obrigatório de quem emite
- [x] 7.4 Validar em `LoginView.vue` que o `redirect` da querystring é caminho interno, cobrindo `//evil.com` e `/\evil.com`
- [x] 7.6 Teste de regressão do emissor: com `JWT_ISSUER`/`JWT_AUDIENCE` definidos, a API aceita o próprio access token e o refresh continua válido (`TokenIssuerTest`)
- [ ] 7.5 Testes: e-mail inexistente e senha errada respondem igual; bloqueio dispara no limite configurado *(o teste de emissor saiu em 7.6)*

## 8. Limites de entrada

- [ ] 8.1-8.5 *(requer leitura dos endpoints de configuração e agente — análise de código)*

## 9. Higiene

- [ ] 9.1-9.3 *(requer acesso a secrets, Dockerfile, README)*

## 10. Fechamento

- [ ] 10.1-10.3 *(requer container Postgres + acesso à produção)*
