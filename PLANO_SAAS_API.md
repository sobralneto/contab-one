# Plano — API .NET 10 + PostgreSQL (Railway)

Status: **plano, nada implementado**. Escrito para ser executado numa sessão
futura. Se algo aqui conflitar com o código real quando a implementação
começar, o código manda.

Documentos irmãos: [PLANO_SAAS_FRONTEND.md](PLANO_SAAS_FRONTEND.md) ·
[PLANO_SAAS_AGENTE.md](PLANO_SAAS_AGENTE.md) ·
[HANDOFF.md](HANDOFF.md) (a ferramenta local de hoje)

---

## 1. Contexto e modelo do produto

A ferramenta local (`nfse.exe`) deixa de ser um utilitário customizado para uma
empresa e vira o **agente** de um micro-SaaS. A API é o cérebro e o cofre de
licenciamento; o agente é o braço que roda na máquina do escritório contábil,
onde os certificados digitais ficam.

**Três níveis — vocabulário fixo, usado igual nos três documentos:**

| Termo | Quem é | Exemplo |
|---|---|---|
| **Plataforma** | você, dono do SaaS | admin único |
| **Escritório** (tenant) | seu cliente pagante | "Contabilidade Silva ME" |
| **Cliente** | empresa dona do certificado, cliente do escritório | "Solution Farma LTDA" |
| **Agente** | o `nfse.exe` rodando na máquina do escritório | 1..N por escritório |

**A regra que sustenta o modelo inteiro:** o certificado `.pfx` **nunca sai da
máquina do escritório**, e o conteúdo fiscal (XML/PDF das notas) **nunca é
enviado para a API**. Sobe só contagem, metadado e status. Isso é o que
permite vender sem virar custodiante da identidade digital de centenas de
empresas de terceiros — e é uma promessa que precisa ser mantida em toda
decisão futura de escopo.

---

## 2. Stack

| Camada | Escolha | Por quê |
|---|---|---|
| Runtime | **.NET 10** (LTS, nov/2025) | pedido; LTS dá 3 anos de suporte |
| API | ASP.NET Core **Minimal APIs** com endpoint groups | menos cerimônia que Controllers; agrupa bem por área (`/agent`, `/admin`) |
| ORM | **EF Core 10** + Npgsql | migrations versionadas + *global query filters* (crítico p/ multi-tenant) |
| Banco | **PostgreSQL** (Railway managed) | pedido; backups gerenciados |
| Auth (humano) | ASP.NET Core Identity + **JWT** (access curto + refresh) | padrão, integra com o front |
| Auth (agente) | **API key** por agente, hash no banco | máquina não usa login/senha de gente |
| Validação | FluentValidation | regras de entrada fora do endpoint |
| Logs | Serilog (JSON no stdout) | Railway coleta stdout automaticamente |
| Docs | `Microsoft.AspNetCore.OpenApi` + Scalar | OpenAPI nativo no .NET 9+ |
| Rate limit | `Microsoft.AspNetCore.RateLimiting` (nativo) | protege `/agent/*` e `/auth/login` |
| Testes | xUnit + **Testcontainers** (Postgres real) | testar isolamento multi-tenant exige banco de verdade |

Deliberadamente **fora** por enquanto: MediatR/CQRS, Clean Architecture em 5
camadas, cache distribuído. Para o tamanho do problema (dezenas de escritórios,
milhares de linhas de métrica) isso só adiciona custo de manutenção. Vertical
slices por feature resolvem melhor.

---

## 3. Estrutura do projeto

```
ContabOne.Api/
├── Program.cs                    composition root, pipeline, DI
├── Dockerfile
├── Features/                     vertical slice por área
│   ├── Auth/                     login, refresh, logout
│   ├── Dashboard/                KPIs e séries
│   ├── Clientes/                 CRUD dos clientes do escritório
│   ├── Agent/                    handshake, regras, ingestão de métricas
│   └── Admin/                    escritórios, planos, regras globais
├── Domain/                       entidades + enums, sem dependência de infra
├── Infra/
│   ├── AppDbContext.cs           inclui os global query filters
│   ├── Migrations/
│   └── TenantContext.cs          resolve o escritório da requisição
├── Security/                     hashing de API key, CNPJ, políticas
└── Jobs/                         alertas de vencimento (cron)

ContabOne.Tests/
```

---

## 4. Modelo de dados

### 4.1 Entidades

```
Escritorio (tenant)
  Id (guid), Nome, CnpjMascarado, CnpjHash
  PlanoId, Status: Ativo | Inadimplente | Suspenso | Cancelado
  CriadoEm, AtualizadoEm

Plano
  Id, Nome, MaxClientes, MaxAgentes, PermiteEmitidas (bool), PrecoMensal

Usuario  (ASP.NET Identity)
  Id, EscritorioId (NULL = admin da plataforma), Email, SenhaHash
  Papel: PlatformAdmin | EscritorioAdmin | EscritorioUsuario
  UltimoLoginEm, Ativo

Agente
  Id, EscritorioId, Nome ("PC da sala 2"), ApiKeyHash, ApiKeyPrefixo
  VersaoAgente, UltimoContatoEm, CriadoEm, RevogadoEm (NULL = ativo)

Cliente               ← empresa dona do certificado
  Id, EscritorioId, Codigo ("0001"), Nome
  CnpjMascarado ("54.283.***/**26"), CnpjHash
  CertificadoValidade (date?), CertificadoNomeArquivo
  PrimeiraVezVistoEm, AtualizadoEm, Origem: Manual | Agente

Execucao              ← uma rodada do agente
  Id, EscritorioId, AgenteId
  IniciadoEm, FinalizadoEm, Status: Sucesso | Parcial | Falha
  VersaoAgente, MensagemErro (nullable)

ExecucaoMetrica       ← detalhe por cliente/tipo/competência
  Id, ExecucaoId, ClienteId
  Tipo: Recebidas | Emitidas, Competencia ("2026-06")
  QtdBaixadas, QtdPuladas, QtdFalhas, DuracaoMs

RegraColeta           ← o "bundle" que o agente busca (ver §6)
  Id, Versao (int, incremental), Conteudo (jsonb), PublicadaEm, Ativa

ConfiguracaoEscritorio
  EscritorioId, Chave, Valor          ← tipos, primeira_busca_desde, etc.

Alerta
  Id, EscritorioId, ClienteId (nullable)
  Tipo: CertificadoVencendo | CertificadoVencido | ExecucaoFalhou | AgenteSilencioso
  Severidade, Mensagem, CriadoEm, ResolvidoEm (nullable)
```

### 4.2 Índices que importam desde o dia 1

```sql
CREATE INDEX ix_execucao_escritorio_iniciado ON "Execucao" ("EscritorioId", "IniciadoEm" DESC);
CREATE INDEX ix_metrica_execucao             ON "ExecucaoMetrica" ("ExecucaoId");
CREATE INDEX ix_metrica_cliente_competencia  ON "ExecucaoMetrica" ("ClienteId", "Competencia");
CREATE UNIQUE INDEX ux_cliente_escritorio_codigo ON "Cliente" ("EscritorioId", "Codigo");
CREATE INDEX ix_agente_apikeyhash            ON "Agente" ("ApiKeyHash");
CREATE INDEX ix_alerta_aberto                ON "Alerta" ("EscritorioId") WHERE "ResolvidoEm" IS NULL;
```

O dashboard vai fazer agregação por competência com frequência. Se o volume
crescer, o passo seguinte é uma *materialized view* de resumo mensal — mas
**não** comece por aí; meça primeiro.

### 4.3 CNPJ ofuscado — como fazer sem perder a capacidade de casar registros

O agente envia CNPJ ofuscado (decisão do produto). Isso cria um problema real:
sem o valor cheio, como identificar que "aquele cliente" é o mesmo entre duas
execuções? Solução em dois campos:

- **`CnpjHash`** — `HMAC-SHA256(cnpj_limpo, chave_secreta_do_servidor)`, guardado
  como `bytea`/texto. Serve para igualdade e deduplicação, é estável, e não é
  reversível sem a chave (que fica só em variável de ambiente da API, nunca no
  agente e nunca no banco).
- **`CnpjMascarado`** — `54.283.***/**26`, só para exibir na tela.

O CNPJ completo **nunca** é persistido. Consequência aceita conscientemente:
você não consegue, por exemplo, consultar a Receita por CNPJ a partir do banco.
Se um dia isso for requisito, é uma mudança deliberada de escopo — não um
detalhe de implementação.

> CNPJ é dado público no Brasil (diferente de CPF), então isso é mais rigoroso
> que o mínimo legal. Mantive porque foi pedido e porque reduz o impacto de um
> eventual vazamento do banco. Já o **nome do cliente** é dado pessoal de
> pessoa jurídica identificável e entra no escopo de LGPD do produto — vale
> ter contrato de tratamento com os escritórios antes de vender.

---

## 5. Isolamento multi-tenant — o maior risco do projeto

Um bug aqui mostra dados do cliente A para o cliente B. É a falha mais grave
possível num produto que guarda dado fiscal, e é fácil de introduzir sem
perceber (basta uma query nova esquecer o `WHERE EscritorioId = ...`).

**Defesa em três camadas, todas obrigatórias:**

1. **Global query filter no EF Core** — o filtro é o padrão, não a exceção:
   ```csharp
   modelBuilder.Entity<Cliente>().HasQueryFilter(
       c => c.EscritorioId == _tenantContext.EscritorioId);
   ```
   Aplicar em toda entidade com `EscritorioId`. Só um `IgnoreQueryFilters()`
   explícito (endpoints de admin) escapa — e cada uso desses deve ter comentário
   justificando.

2. **`TenantContext` resolvido no middleware**, a partir do claim do JWT ou da
   API key do agente. Nunca de um parâmetro de rota ou query string — senão
   basta trocar o id na URL para ver dados alheios (IDOR).

3. **Teste automatizado de vazamento**, rodando contra Postgres real
   (Testcontainers): cria dois escritórios com dados, autentica como o A, e
   afirma que *nenhum* endpoint devolve id do B. Esse teste é o guarda-corpo
   que sobrevive a refatorações.

---

## 6. Endpoints

### 6.1 Agente (`/api/agent/*`) — auth por API key

Header: `X-Api-Key: nfse_<prefixo>_<segredo>`

| Método | Rota | O que faz |
|---|---|---|
| POST | `/agent/handshake` | valida a key, devolve status do escritório, plano e a versão atual das regras. **É o ponto de checagem de adimplência.** |
| GET | `/agent/regras?versao=N` | devolve o bundle se houver versão mais nova; `304` se `N` já é a atual |
| POST | `/agent/execucoes` | abre uma execução, devolve `execucaoId` |
| POST | `/agent/execucoes/{id}/metricas` | envia o lote de métricas da rodada |
| POST | `/agent/execucoes/{id}/finalizar` | fecha com status + erro opcional |
| POST | `/agent/clientes` | *upsert* dos donos de certificado (nome, CNPJ ofuscado, validade) |

Resposta do handshake:
```jsonc
{
  "escritorio": { "id": "...", "nome": "Contabilidade Silva ME" },
  "status": "Ativo",              // Ativo | Inadimplente | Suspenso | Cancelado
  "podeExecutar": true,
  "mensagem": null,               // texto exibido pelo agente quando bloqueado
  "plano": { "maxClientes": 50, "permiteEmitidas": true },
  "regrasVersaoAtual": 7,
  "agenteVersaoMinima": "2.0.0"   // agente mais antigo avisa que precisa atualizar
}
```

### 6.2 Aplicação web — auth por JWT

```
POST   /api/auth/login            → access token + refresh (cookie httpOnly)
POST   /api/auth/refresh
POST   /api/auth/logout

GET    /api/dashboard/kpis        → cards do topo
GET    /api/dashboard/series      → notas por mês (?de=&ate=&clienteId=)
GET    /api/dashboard/ranking     → clientes por volume

GET    /api/clientes              → lista (paginada, filtro por nome/código)
POST   /api/clientes              → cadastro manual
PUT    /api/clientes/{id}
DELETE /api/clientes/{id}         → soft delete

GET    /api/execucoes             → histórico, com status e falhas
GET    /api/execucoes/{id}

GET    /api/alertas               → abertos primeiro
POST   /api/alertas/{id}/resolver

GET    /api/configuracao          → config da ferramenta do escritório
PUT    /api/configuracao

GET    /api/agentes               → agentes do escritório
POST   /api/agentes               → cria e devolve a API key (única exibição!)
DELETE /api/agentes/{id}          → revoga
```

### 6.3 Admin da plataforma (`/api/admin/*`) — papel `PlatformAdmin`

```
GET/POST/PUT  /api/admin/escritorios      inclui mudar Status (a alavanca de inadimplência)
GET/POST/PUT  /api/admin/planos
GET/POST      /api/admin/regras           publica nova versão do bundle
GET           /api/admin/visao-geral      execuções e saúde de todos os escritórios
```

---

## 7. Segurança

**API key do agente.** Formato `nfse_<prefixo8>_<segredo32>`. Guarda-se
`SHA-256(segredo)` e o prefixo em claro (para exibir "nfse_a1b2c3d4_…" na tela
e para achar o registro sem varrer a tabela). A chave completa é exibida
**uma única vez**, na criação. Como o segredo é aleatório de alta entropia,
SHA-256 basta — não precisa de bcrypt/Argon2 aqui (que existem para senhas
humanas, de baixa entropia).

**Rate limiting.** `/auth/login` por IP (evita força bruta) e `/agent/*` por
escritório (evita que um agente com bug em loop derrube a API).

**Outros pontos:**
- HTTPS obrigatório (Railway já entrega TLS no domínio público)
- CORS restrito ao domínio do front
- Refresh token em cookie `httpOnly` + `Secure` + `SameSite=Strict`
- Segredos (`HMAC_CNPJ_KEY`, `JWT_SIGNING_KEY`) só em variável de ambiente
- Auditoria: gravar quem mudou `Status` de escritório e quem revogou agente

---

## 8. O bundle de regras (`RegraColeta.Conteudo`)

É o que move a "inteligência" para o servidor — a decisão tomada na conversa
anterior. Formato sugerido:

```jsonc
{
  "versao": 7,
  "publicadaEm": "2026-07-26T12:00:00Z",
  "portal": {
    "urlLogin": "https://certificado.nfse.gov.br/EmissorNacional/Certificado",
    "urlNotas": "https://www.nfse.gov.br/EmissorNacional/Notas",
    "urlApiXml": "https://sefin.nfse.gov.br/sefinnacional/nfse",
    "maxDiasFiltro": 31,
    "paramPagina": "pg",
    "pausaEntreChamadasMs": 250,
    "listagens": {
      "recebidas": { "rota": "Recebidas", "executar": true,  "colunas": ["geracao","emitida_por","competencia","preco_servico","situacao"] },
      "emitidas":  { "rota": "Emitidas",  "executar": false, "colunas": ["geracao","emitida_para","competencia","municipio_emissor","preco_servico","situacao"] }
    }
  },
  "parsing": {
    "regexChave": "/Notas/Download/NFSe/(\\d{40,60})",
    "regexLinha": "<tr[^>]*>(.*?)</tr>",
    "regexTotalRegistros": "Total de\\s*(\\d+)\\s*registros?"
  }
}
```

**Não entra aqui:** o layout do DANFSe. A NT 008 é documento público do gov.br
— mover coordenadas e fontes para a API não esconde nada, geraria um payload
enorme, e o código que interpreta isso continua tendo que existir local de
qualquer jeito. O valor do `danfse.py` é a implementação validada campo a
campo, não as regras.

**Versionamento:** `Versao` incremental. O agente manda a que tem em cache; a
API responde `304` se já é a atual. Publicar uma versão nova é `INSERT` +
marcar a anterior como inativa — nunca `UPDATE` destrutivo, para permitir
rollback quando uma regra nova quebrar em produção.

---

## 9. Job de alertas (Railway Cron)

Serviço separado (ou o mesmo binário com um argumento), rodando 1×/dia:

- Certificado vencendo em ≤30 dias → `CertificadoVencendo`
- Certificado com validade passada → `CertificadoVencido`
- Escritório sem nenhuma execução há >3 dias → `AgenteSilencioso`
- Última execução com status `Falha` → `ExecucaoFalhou`

Alertas são idempotentes: não criar um novo se já existe um aberto do mesmo
tipo para o mesmo cliente. Sem isso, 30 dias de aviso viram 30 alertas.

Notificação por e-mail fica para depois do MVP (ver §12).

---

## 10. Fases

**Fase 1 — Fundação.** Projeto, Docker, EF Core, migrations, Postgres no
Railway, healthcheck, deploy vazio funcionando. *Entregável: `/health` responde
em produção.*

**Fase 2 — Auth e tenancy.** Identity, JWT, `TenantContext`, global query
filters, **e o teste de vazamento** (§5). Sem isso pronto, nada de features.

**Fase 3 — Ingestão do agente.** `Agente`, API key, handshake, `/agent/*`,
bundle de regras. Casa com a Fase 2 do plano do agente.

**Fase 4 — Leitura.** Dashboard, clientes, execuções, alertas. Casa com o front.

**Fase 5 — Admin.** Escritórios, planos, publicação de regras, visão geral.

**Fase 6 — Operação.** Job de alertas, rate limiting fino, auditoria, backup
testado (restaurar de verdade uma vez — backup não testado não é backup).

---

## 11. Deploy no Railway

**Serviços:** `api` (Dockerfile), `postgres` (managed), `cron-alertas`,
`frontend` (ver plano do front).

**Dockerfile** — multi-stage, imagens .NET 10:
```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY *.csproj ./
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o /app/out

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /app/out ./
ENTRYPOINT ["dotnet", "ContabOne.Api.dll"]
```

**Três armadilhas específicas do Railway** (as que custam uma tarde se
descobertas na hora do deploy):

1. **`PORT`** — o Railway injeta a porta; a app precisa escutar nela, não na
   8080 fixa. `ASPNETCORE_URLS=http://0.0.0.0:${PORT}`.

2. **`DATABASE_URL` não é connection string do Npgsql.** O Railway entrega
   `postgresql://user:senha@host:porta/db`; o Npgsql espera
   `Host=...;Port=...;Username=...;Password=...;Database=...`. Converter no
   startup — não perca tempo procurando erro de credencial que não existe.

3. **A rede privada do Railway é IPv6.** Ao usar
   `${{Postgres.RAILWAY_PRIVATE_DOMAIN}}` (recomendado: não passa pela internet
   e não gasta egress), garanta que o socket não está preso a IPv4.

**Migrations:** rodar como passo explícito no start, não como `EnsureCreated()`.
Enquanto for um escritório só, `dotnet ef database update` no boot resolve; com
múltiplas réplicas, migrar vira um job separado — senão duas instâncias migram
ao mesmo tempo.

**Variáveis:** `DATABASE_URL`, `JWT_SIGNING_KEY`, `HMAC_CNPJ_KEY`,
`ASPNETCORE_ENVIRONMENT`, `CORS_ORIGINS`.

---

## 12. Fora do MVP (registrado para não virar escopo por acidente)

- Cobrança automática (Stripe/Pagar.me) — no início, marcar `Status` na mão
  resolve e evita construir billing antes de ter o primeiro cliente pagante
- E-mail de alerta (Resend/SendGrid)
- Multi-usuário por escritório com permissão fina
- Webhook para o escritório integrar no ERP dele
- Suporte a portais municipais além do Nacional

## 13. Perguntas em aberto

1. **"Tela de configuração das métricas da ferramenta"** — é (a) configurar os
   parâmetros de operação (tipos, `primeira_busca_desde`, gerar PDF), ou (b)
   escolher quais métricas o agente coleta? Assumi **(a)** no modelo
   (`ConfiguracaoEscritorio`); se for (b), o desenho muda.
2. Um escritório pode ter **vários agentes** (várias máquinas)? Modelei que
   sim. Isso levanta: dois agentes rodando o mesmo cliente geram métrica
   duplicada — resolver por `(ClienteId, Competencia, Tipo)` com *upsert* em
   vez de *insert*?
3. O escritório cadastra o cliente na web **antes** do agente ver o
   certificado, ou o agente é sempre a fonte? Modelei os dois (`Origem`), mas
   isso precisa de regra de reconciliação quando os dois caminhos criarem o
   mesmo cliente.
4. Retenção de `ExecucaoMetrica`: guardar para sempre ou agregar depois de N
   meses? Afeta o custo de banco no Railway.
