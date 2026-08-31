# -*- coding: utf-8 -*-
"""
Gera o relatorio de auditoria de seguranca do ContabOne em PDF.
Uso: venv/Scripts/python.exe gerar_relatorio.py
Regenera docs/security-audit/relatorio-auditoria-seguranca.pdf a partir dos
achados coletados na auditoria manual (ver texto abaixo) -- editar os dados
em FINDINGS / STRENGTHS / RECOMMENDATIONS / ISSUES para atualizar o relatorio.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak, KeepTogether, HRFlowable, ListFlowable, ListItem
)
from reportlab.pdfgen import canvas as canvas_mod

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PDF = os.path.join(HERE, "relatorio-auditoria-seguranca.pdf")
ASSETS = os.path.join(HERE, "_assets")
os.makedirs(ASSETS, exist_ok=True)

# ── Paleta ──────────────────────────────────────────────────────────────
COLOR_CRITICA = "#B91C1C"
COLOR_ALTA = "#EA580C"
COLOR_MEDIA = "#D97706"
COLOR_BAIXA = "#2563EB"
COLOR_FORTE = "#059669"
COLOR_INFO = "#64748B"
COLOR_HEADER = "#0F172A"
COLOR_SUBHEADER = "#1E3A5F"
COLOR_TEXT = "#1E293B"
COLOR_MUTED = "#475569"
COLOR_BORDER = "#CBD5E1"
COLOR_BG_LIGHT = "#F1F5F9"

SEV_COLOR = {
    "Critica": COLOR_CRITICA,
    "Alta": COLOR_ALTA,
    "Media": COLOR_MEDIA,
    "Baixa": COLOR_BAIXA,
    "Informativa": COLOR_INFO,
}
SEV_LABEL = {
    "Critica": "CRÍTICA",
    "Alta": "ALTA",
    "Media": "MÉDIA",
    "Baixa": "BAIXA",
    "Informativa": "INFORMATIVA",
}

PROJECT_NAME = "ContabOne (monorepo contab-one)"
REPORT_TITLE = "Relatório de Auditoria de Segurança"
REPORT_DATE = "28 de agosto de 2026"

# ── Dados da auditoria ──────────────────────────────────────────────────

CATEGORIES = {
    1: "Isolamento de tenant",
    2: "Permissão no navegador",
    3: "IDOR",
    4: "Chaves expostas",
    5: "XSS / entradas sem tratamento",
}

FINDINGS = [
    {
        "id": "F1",
        "categoria": 4,
        "severidade": "Media",
        "arquivo": "DadosAcesso.txt",
        "linhas": "1-15",
        "titulo": "Credenciais de ambiente de dev versionadas em texto claro na raiz do repositório",
        "trecho": (
            "Login admin: admin@nfse.local / Admin123!\n"
            "Login escritório: escritorio@nfse.local / Admin123!\n"
            "Login usuario: usuario@nfse.local / Admin123!"
        ),
        "por_que": (
            "O arquivo está commitado no git (commit f16576b, \"login e senha do ambiente dev\") na raiz "
            "do repositório. As credenciais correspondem exatamente às contas criadas por "
            "POST /api/seed/dev (ContabOne.Api/Features/Seed/SeedEndpoints.cs:137-164). Credenciais reais "
            "(mesmo que de um ambiente de desenvolvimento) permanecem no histórico do git indefinidamente, "
            "são capturadas por scanners de segredo (GitHub secret scanning, gitleaks) e, se qualquer "
            "ambiente compartilhado subir com ASPNETCORE_ENVIRONMENT=Development por engano, dão acesso "
            "administrativo (PlatformAdmin) completo e imediato."
        ),
        "condicao": (
            "Exige que /api/seed/dev tenha sido executado contra o banco alvo, o que só é possível quando "
            "IsDevelopment() é verdadeiro (gate duplo em SeedEndpoints.cs)."
        ),
    },
    {
        "id": "F2",
        "categoria": 4,
        "severidade": "Baixa",
        "arquivo": "ContabOne.Api/appsettings.Development.json",
        "linhas": "7-9",
        "titulo": "Segredos de desenvolvimento hardcoded sem validação de ambiente na inicialização",
        "trecho": (
            '"ConnectionStrings": { "Default": "...;Password=contabone;..." }\n'
            '"JWT_SIGNING_KEY": "dev-key-change-in-production-min-32-chars!!"\n'
            '"HMAC_CNPJ_KEY": "dev-hmac-cnpj-key-change-in-production!!"'
        ),
        "por_que": (
            "Program.cs (linhas 85-94) exige que JWT_SIGNING_KEY e HMAC_CNPJ_KEY estejam definidos, mas não "
            "valida que NÃO sejam estes valores de exemplo conhecidos publicamente no repositório. O arquivo "
            "só é carregado quando ASPNETCORE_ENVIRONMENT=Development, mas nada no código impede a API de "
            "subir normalmente em produção assinando tokens JWT com esta chave pública caso essa variável "
            "seja erroneamente definida como \"Development\" — permitindo forjar tokens de qualquer papel, "
            "inclusive PlatformAdmin."
        ),
        "condicao": (
            "Requer erro de configuração do ambiente de deploy — não é o comportamento padrão (.NET assume "
            "\"Production\" quando a variável não é definida)."
        ),
    },
    {
        "id": "F3",
        "categoria": 4,
        "severidade": "Baixa",
        "arquivo": "docker-compose.yml",
        "linhas": "8-9, 11-12",
        "titulo": "Senha trivial hardcoded para Postgres local, exposta na porta padrão do host",
        "trecho": (
            "POSTGRES_USER: contabone\nPOSTGRES_PASSWORD: contabone\nports:\n  - \"5432:5432\""
        ),
        "por_que": (
            "O bind \"5432:5432\" expõe a porta em todas as interfaces do host Docker (0.0.0.0), não apenas "
            "em loopback. Em uma workstation local atrás de firewall isso é baixo risco; em uma VM de nuvem "
            "compartilhada ou ambiente com portas abertas, é uma instância Postgres com credenciais triviais "
            "(usuário = senha) acessível pela rede."
        ),
        "condicao": (
            "Aplica-se apenas ao ambiente local via docker-compose. O deploy real usa DATABASE_URL "
            "gerenciado pela plataforma (Railway), não este compose."
        ),
    },
    {
        "id": "F4",
        "categoria": 4,
        "severidade": "Informativa",
        "arquivo": "ContabOne.Api/Infra/AppDbContextFactory.cs",
        "linhas": "17-21",
        "titulo": "Connection string de fallback hardcoded no factory de design-time do EF Core",
        "trecho": (
            'rawConnString = Environment.GetEnvironmentVariable("DATABASE_URL");\n'
            'if (string.IsNullOrEmpty(rawConnString))\n'
            '    rawConnString = "Host=localhost;...;Password=contabone;...";'
        ),
        "por_que": (
            "Mesmas credenciais triviais do docker-compose, porém este código só executa durante "
            "\"dotnet ef migrations\" (ferramenta de design-time), nunca no processo da API publicado — "
            "Program.cs exige DATABASE_URL/ConnectionStrings:Default explicitamente e lança exceção se "
            "ausente. Risco teórico, não é um vetor de ataque em produção."
        ),
        "condicao": "Só é executado localmente por um desenvolvedor rodando o CLI do EF Core.",
    },
    {
        "id": "F5",
        "categoria": 4,
        "severidade": "Baixa",
        "arquivo": "ContabOne.Api/Features/Seed/SeedEndpoints.cs",
        "linhas": "17-79",
        "titulo": "Endpoints de seed sem segundo fator além do gate de ambiente (IsDevelopment)",
        "trecho": (
            'app.MapPost("/api/seed/admin", async (SeedAdminRequest req, ...) => {\n'
            '    if (!env.IsDevelopment()) return Results.NotFound();\n'
            '    ... Papel = PapelUsuario.PlatformAdmin ...\n'
            '}).AllowAnonymous();'
        ),
        "por_que": (
            "Gate duplo — não mapeado fora de Development (Program.cs:266-271) e cada handler reconfirma "
            "env.IsDevelopment() — mas o único controle é a variável ASPNETCORE_ENVIRONMENT. Não há um "
            "segundo fator (ex.: token comparado a um header) que sobreviva a uma configuração incorreta "
            "dessa variável. Se ela for setada como \"Development\" em qualquer ambiente real, qualquer "
            "visitante anônimo cria uma conta PlatformAdmin com senha arbitrária via /api/seed/admin, e "
            "/api/seed/status despeja e-mail/papel/escritório de todos os usuários via SQL bruto."
        ),
        "condicao": "Requer erro de configuração de ambiente; não reproduzido em produção.",
    },
    {
        "id": "F6",
        "categoria": 1,
        "severidade": "Media",
        "arquivo": "ContabOne.Api/Features/Agent/AgentEndpoints.cs",
        "linhas": "94-124",
        "titulo": "Segredo HMAC_CNPJ_KEY global compartilhado devolvido a todo agente de campo autenticado",
        "trecho": (
            'return Results.Ok(new HandshakeResponse {\n'
            '    ...\n'
            '    HmacCnpjKey = config["HMAC_CNPJ_KEY"]!, // same for all agents of this escritorio\n'
            '    ...\n'
            '});'
        ),
        "por_que": (
            "O mecanismo de isolamento do ContabOne é por-tenant via Global Query Filters do EF Core "
            "(AppDbContext.cs), mas este segredo criptográfico é ÚNICO PARA TODA A PLATAFORMA, não escopado "
            "por escritório. A cada handshake bem-sucedido, a API devolve o HMAC_CNPJ_KEY em texto claro a "
            "qualquer agente autenticado — um executável Python rodando na máquina de um escritório "
            "contábil, com a própria chave de API guardada em config.toml local em texto claro (ver "
            "Nfse.Agent/CLAUDE.md, seção \"Sensitive local data\"). Esse é o mesmo segredo usado para gerar "
            "Escritorio.CnpjHash (índice único) e Cliente.CnpjHash de TODOS os escritórios da plataforma. "
            "Comprometer um único agente de campo — o elo mais exposto do sistema, por rodar fora do "
            "perímetro do servidor — expõe o segredo que permite calcular o hash determinístico de qualquer "
            "CNPJ, quebrando a garantia de isolamento por tenant no nível criptográfico mesmo que os filtros "
            "de banco continuem corretos."
        ),
        "condicao": (
            "Mitigante: não foi encontrado, na superfície de API revisada, um endpoint que devolva CnpjHash "
            "bruto para comparação entre tenants — a exploração prática além da simples posse do segredo "
            "exigiria outro vetor (acesso direto ao banco, por exemplo). Por isso a severidade é MÉDIA, não "
            "ALTA."
        ),
    },
]

STRENGTHS = [
    (
        "Isolamento multi-tenant fail-closed via Global Query Filters do EF Core",
        "ContabOne.Api/Infra/AppDbContext.cs:45-69",
        "Todas as entidades sensíveis (Agente, Cliente, Execucao, ExecucaoMetrica, ConfiguracaoEscritorio, "
        "Alerta, EscritorioProduto) têm o filtro `VeTodosOsEscritorios || x.EscritorioId == tenant.EscritorioId`. "
        "Quando nem admin nem escritório estão resolvidos, o filtro vira `EscritorioId == null`, que nunca "
        "combina (a coluna é Guid não-nulo) — resultando em zero linhas. O padrão é fail-closed, não fail-open.",
    ),
    (
        "Middleware rejeita sessão sem escritório identificável em vez de abrir o filtro",
        "ContabOne.Api/Infra/TenantContextMiddleware.cs:37-56",
        "Um usuário com papel de escritório mas sem escritorio_id resolvível no token recebe 401 explícito, "
        "em vez de seguir com TenantContext vazio (o que abriria a condição `EscritorioId == null`).",
    ),
    (
        "Todos os usos de IgnoreQueryFilters() auditados e legítimos",
        "27 ocorrências em 8 arquivos (ApiKeyAuthenticationHandler, AdminEndpoints, AgentEndpoints, "
        "AgentesManagementEndpoints, ProdutosEndpoints, UsuariosEndpoints, SeedEndpoints, Jobs/AlertaJob)",
        "Cada ocorrência foi verificada individualmente: lookups pré-autenticação (antes do TenantContext "
        "existir), endpoints exclusivos de PlatformAdmin, ou o cron job iterando explicitamente por escritório. "
        "Nenhum uso encontrado que vaze dados entre tenants para um usuário comum.",
    ),
    (
        "Escalação de privilégio bloqueada na gestão de usuários",
        "ContabOne.Api/Features/Usuarios/UsuariosEndpoints.cs:239-258 (ResolverEscopo)",
        "O escritório de um usuário criado/editado por um EscritorioAdmin vem sempre de tenant.EscritorioId "
        "(token), nunca do corpo da requisição. Só PlatformAdmin pode conceder o papel PlatformAdmin ou mover "
        "um usuário para outro escritório. Um usuário não pode alterar o próprio papel nem desativar a si mesmo.",
    ),
    (
        "IDOR mitigado por busca escopada ao tenant, com 404 em vez de 403",
        "UsuariosEndpoints.cs:220-232 (BuscarNoEscopoAsync), TourEndpoints.cs:22-33 (UsuarioId sempre do "
        "token), ProdutosEndpoints.cs:34-38 (comentário cita explicitamente \"seria IDOR (§5)\")",
        "Objeto de outro tenant não é distinguível de objeto inexistente (404 em ambos os casos), evitando "
        "confirmar a existência de recursos de terceiros.",
    ),
    (
        "Paridade completa entre papéis exigidos no frontend e políticas de autorização no backend",
        "ContabOne.Frontend/src/router/index.ts (meta.papeis) × ContabOne.Api/Program.cs (RequireAuthorization)",
        "Cada uma das 11 rotas protegidas do frontend foi cruzada manualmente com a policy do grupo de "
        "endpoints correspondente no backend. Nenhuma divergência encontrada — toda operação que o frontend "
        "esconde por papel é também rejeitada pelo servidor caso chamada diretamente.",
    ),
    (
        "JWT com validação completa dos dois lados e cookies de sessão bem configurados",
        "ContabOne.Api/Program.cs:102-119, Features/Auth/AuthEndpoints.cs:84-91",
        "Issuer, audience, tempo de vida e assinatura validados; emissão e validação leem a mesma "
        "configuração (evita rejeitar os próprios tokens). Refresh token em cookie HttpOnly+Secure+"
        "SameSite=Strict; access token de vida curta (15 min) fica em sessionStorage do frontend, não em "
        "localStorage.",
    ),
    (
        "Login resistente a enumeração de usuários por tempo de resposta",
        "ContabOne.Api/Features/Auth/AuthEndpoints.cs:28-53",
        "Um hash \"descartável\" é verificado quando o e-mail não existe, gastando o mesmo tempo de "
        "derivação de chave (~90ms) de uma verificação real — a resposta não denuncia por timing quais "
        "e-mails existem na base.",
    ),
    (
        "Único uso de v-html do frontend é seguro por construção",
        "ContabOne.Frontend/src/components/comum/IconeCatalogo.vue:12,26-36",
        "Renderiza sempre um de três SVGs fixos definidos no próprio componente, selecionados por chave. O "
        "valor vindo do banco (Produto.Icone) é usado só como CHAVE de lookup, nunca interpretado como HTML "
        "— um valor desconhecido cai no ícone genérico. Documentado explicitamente no próprio código.",
    ),
    (
        "Nenhuma outra superfície de XSS encontrada no frontend",
        "Busca em todo ContabOne.Frontend/src (70 arquivos .vue/.ts)",
        "Nenhum innerHTML, dangerouslySetInnerHTML equivalente, eval(), new Function(), ou biblioteca de "
        "renderização de Markdown/HTML de terceiros (confirmado via package.json). Os únicos bindings :src "
        "encontrados apontam para assets estáticos importados (logos), não para dado controlado por usuário.",
    ),
    (
        "Segredos reais nunca versionados no repositório",
        ".gitignore (seções 1 e 4) + varredura do histórico completo do git",
        "Cobertura explícita para *.pfx, *.p12, *.pem, *.key, config.toml, .env, _agente_cache.json, "
        "certificados/, notas/. Busca em todo o histórico do git (`git log --all --diff-filter=A`) não "
        "encontrou nenhum desses arquivos jamais commitado.",
    ),
    (
        "Criptografia bem projetada para o blob de configuração do handshake do agente",
        "ContabOne.Api/Security/ConfiguracaoCipher.cs:18-50",
        "AES-256-GCM com nonce aleatório de 12 bytes por operação e chave derivada por HMAC-SHA256 da "
        "própria API key do agente — não introduz nenhum segredo novo em variáveis de ambiente.",
    ),
    (
        "Cobertura de teste automatizado dedicada ao isolamento multi-tenant",
        "ContabOne.Api.Tests/IsolamentoTest.cs",
        "Suíte de integração testa explicitamente que um agente (via X-Api-Key) ou usuário (via JWT) de um "
        "escritório não alcança dados de outro, inclusive tentando furar o filtro via parâmetro de query — "
        "com o comentário \"a quebra disso seria o pior defeito possível neste produto\".",
    ),
    (
        "CORS fail-closed em produção",
        "ContabOne.Api/Program.cs:142-164",
        "Se a variável CORS_ORIGINS não for configurada em produção, a lista de origens permitidas fica "
        "vazia — bloqueando toda requisição cross-origin — em vez de permitir qualquer origem por omissão.",
    ),
    (
        "Rate limiting aplicado ao endpoint de login e aos endpoints de agente",
        "ContabOne.Api/Program.cs:175-206,274-283",
        "Política \"auth\" (10 req/min por IP) no grupo /api/auth e política \"agent\" (60 req/min) no grupo "
        "/api/agent, com fila e status 429 correto em vez do 503 padrão do ASP.NET Core.",
    ),
]

RECOMMENDATIONS = [
    ("P1", "Remover DadosAcesso.txt do repositório (git rm + reescrita do histórico se o repositório for "
           "considerado sensível) e mover a instrução de seed para o README, sem credenciais reais em "
           "texto claro.", "F1"),
    ("P1", "Adicionar uma verificação de startup em Program.cs que recuse subir se JWT_SIGNING_KEY ou "
           "HMAC_CNPJ_KEY baterem com os literais de appsettings.Development.json e IsDevelopment() for "
           "falso — defesa em profundidade contra erro de configuração de ambiente.", "F2, F5"),
    ("P2", "Adicionar um SEED_TOKEN (header ou variável de ambiente comparada a um valor) exigido pelos "
           "endpoints /api/seed/*, além do gate de IsDevelopment(), como segunda camada independente da "
           "variável de ambiente.", "F5"),
    ("P2", "Escopar o segredo de hashing de CNPJ por escritório (ou parar de devolver a chave mestre para "
           "o agente), derivando uma chave por-tenant a partir do segredo global — mesmo padrão já usado "
           "em ConfiguracaoCipher para a chave de configuração.", "F6"),
    ("P3", "Trocar a senha do Postgres do docker-compose.yml por um valor gerado (ou ao menos restringir o "
           "bind de porta a 127.0.0.1:5432 em vez de 0.0.0.0:5432) para reduzir a superfície em ambientes "
           "de nuvem compartilhados.", "F3"),
    ("P3", "Adicionar um teste automatizado que falhe o build se algum valor literal dos segredos de "
           "appsettings.Development.json for detectado configurado fora de um ambiente de Development.",
           "F2, F4"),
]

ISSUES = [
    {
        "titulo": "[Segurança] Credenciais de ambiente de dev versionadas em texto claro (DadosAcesso.txt)",
        "labels": "security, media",
        "corpo": """## Problema
O arquivo `DadosAcesso.txt`, na raiz do repositório, contém e-mail e senha em texto claro de três contas
de desenvolvimento (admin, escritório e usuário), commitado no git (commit `f16576b`). As credenciais
correspondem exatamente às contas criadas por `POST /api/seed/dev`
(`ContabOne.Api/Features/Seed/SeedEndpoints.cs:137-164`).

## Por que é explorável
Credenciais reais no histórico do git permanecem lá indefinidamente (mesmo após um `git rm` posterior),
são capturadas por scanners de segredo (gerando ruído permanente) e, caso qualquer ambiente compartilhado
suba com `ASPNETCORE_ENVIRONMENT=Development` por engano, dão acesso administrativo (PlatformAdmin)
completo e imediato a quem tiver acesso de leitura ao repositório.

## Evidência
`DadosAcesso.txt:1-15`
```
Login admin: admin@nfse.local / Admin123!
Login escritório: escritorio@nfse.local / Admin123!
Login usuario: usuario@nfse.local / Admin123!
```

## Impacto
Médio — exige um erro de configuração de ambiente adicional para ser explorável diretamente, mas o hábito
de commitar credenciais reais (mesmo de dev) é uma prática de risco permanente no histórico do repositório.

## Sugestão de correção
- Remover o arquivo do controle de versão (`git rm DadosAcesso.txt`) e adicioná-lo ao `.gitignore`.
- Mover a lista de credenciais de exemplo para o `README.md`, deixando claro que só existem após rodar
  `POST /api/seed/dev` localmente.
- Se o repositório for público ou tiver múltiplos colaboradores externos, considerar reescrever o
  histórico para remover o arquivo (`git filter-repo` ou BFG).

## Critérios de aceite
- [ ] `DadosAcesso.txt` removido do working tree e do índice do git
- [ ] `.gitignore` atualizado para impedir reintrodução do arquivo
- [ ] Instruções de seed movidas para README.md sem credenciais reais versionadas
- [ ] Avaliação feita sobre reescrever o histórico do git (documentar decisão, mesmo que seja "não fazer")
""",
    },
    {
        "titulo": "[Segurança] Reforçar defesa em profundidade contra erro de configuração de ambiente "
                   "(segredos de dev, endpoints de seed e senha padrão do Postgres local)",
        "labels": "security, baixa",
        "corpo": """## Problema
Três controles distintos dependem, hoje, unicamente da variável `ASPNETCORE_ENVIRONMENT` estar correta
para não expor risco real:

1. `ContabOne.Api/appsettings.Development.json:7-9` guarda `JWT_SIGNING_KEY`, `HMAC_CNPJ_KEY` e a senha do
   Postgres local como literais conhecidos publicamente no repositório, sem checagem de startup que os
   rejeite fora de Development.
2. `ContabOne.Api/Features/Seed/SeedEndpoints.cs:17-79` expõe `/api/seed/admin` (cria PlatformAdmin com
   senha arbitrária) e `/api/seed/status` (despeja todos os usuários via SQL bruto) como `AllowAnonymous()`,
   gateados apenas por `env.IsDevelopment()`.
3. `docker-compose.yml:8-9,11-12` usa `POSTGRES_PASSWORD: contabone` com a porta 5432 publicada em todas as
   interfaces do host (`"5432:5432"`), e o mesmo valor aparece hardcoded como fallback de design-time em
   `ContabOne.Api/Infra/AppDbContextFactory.cs:20`.

## Por que é explorável
Nenhum destes é explorável no comportamento padrão documentado (produção não carrega o appsettings de
Development, e o Postgres do compose não é o banco usado em produção). O risco é de configuração
incorreta: se `ASPNETCORE_ENVIRONMENT` for setado como `Development` em qualquer ambiente real (erro comum
em PaaS), os itens 1 e 2 se tornam, respectivamente, uma chave de assinatura JWT pública (forja de token de
qualquer papel) e um endpoint anônimo de criação de PlatformAdmin.

## Evidência
`ContabOne.Api/appsettings.Development.json:7-9`
```json
"ConnectionStrings": { "Default": "...;Password=contabone;..." },
"JWT_SIGNING_KEY": "dev-key-change-in-production-min-32-chars!!",
"HMAC_CNPJ_KEY": "dev-hmac-cnpj-key-change-in-production!!"
```
`ContabOne.Api/Features/Seed/SeedEndpoints.cs:51-58`
```csharp
app.MapPost("/api/seed/admin", async (SeedAdminRequest req, ...) => {
    if (!env.IsDevelopment()) return Results.NotFound();
    ...
}).AllowAnonymous();
```
`docker-compose.yml:8-12`
```yaml
POSTGRES_PASSWORD: contabone
ports:
  - "5432:5432"
```

## Impacto
Baixo isoladamente (todos exigem uma pré-condição de configuração incorreta), mas os três compartilham a
mesma causa raiz — ausência de defesa em profundidade além de uma única variável de ambiente — e por isso
foram agrupados.

## Sugestão de correção
- Adicionar checagem de startup em `Program.cs` que recuse subir se `JWT_SIGNING_KEY`/`HMAC_CNPJ_KEY`
  baterem com os literais de exemplo e `IsDevelopment()` for falso.
- Exigir um `SEED_TOKEN` (header comparado a uma variável de ambiente) nos endpoints `/api/seed/*`, além
  do gate de ambiente.
- Trocar a senha do Postgres local por um valor gerado e restringir o bind de porta a `127.0.0.1:5432`.

## Critérios de aceite
- [ ] Startup falha explicitamente se segredos de exemplo forem detectados fora de Development
- [ ] `/api/seed/*` exige um token adicional configurável, não só `IsDevelopment()`
- [ ] `docker-compose.yml` usa senha gerada (ou variável sem default) e porta restrita a loopback
- [ ] `AppDbContextFactory.cs` não depende mais de um literal de senha (usar variável obrigatória ou
      arquivo `.env` local ignorado pelo git)
""",
    },
    {
        "titulo": "[Segurança] HMAC_CNPJ_KEY global devolvido em texto claro a todo agente autenticado",
        "labels": "security, media",
        "corpo": """## Problema
`ContabOne.Api/Features/Agent/AgentEndpoints.cs:122` devolve `HMAC_CNPJ_KEY` — uma chave única para toda a
plataforma — em texto claro no corpo da resposta de `/api/agent/handshake`, para qualquer agente de campo
que se autentique com sucesso via `X-Api-Key`.

## Por que é explorável
O mecanismo de isolamento por-tenant do ContabOne é feito via Global Query Filters do EF Core
(`AppDbContext.cs`), mas este segredo criptográfico específico não é escopado por escritório — é o mesmo
para todos. Um agente de campo é um executável Python rodando em máquinas de terceiros (escritórios
contábeis), com a própria API key guardada em `config.toml` local em texto claro (ver
`Nfse.Agent/CLAUDE.md`, seção "Sensitive local data"). Esse é objetivamente o componente mais exposto do
sistema. Comprometer um único agente expõe o segredo usado para gerar `Escritorio.CnpjHash` e
`Cliente.CnpjHash` de TODOS os escritórios da plataforma, permitindo calcular o hash determinístico de
qualquer CNPJ e testar sua presença na base — uma quebra da garantia de isolamento por tenant no nível
criptográfico, mesmo que os filtros de banco permaneçam corretos.

## Evidência
`ContabOne.Api/Features/Agent/AgentEndpoints.cs:105-124`
```csharp
return Results.Ok(new HandshakeResponse {
    ...
    HmacCnpjKey = config["HMAC_CNPJ_KEY"]!, // same for all agents of this escritorio (§PLANO_SAAS_AGENTE §6)
    ConfiguracaoCifrada = configuracaoCifrada,
});
```
Consumido em `ContabOne.Api/Security/CnpjHasher.cs:15-20` (`HMACSHA256` sobre o CNPJ limpo).

## Impacto
Médio — não foi encontrado, na superfície de API revisada, um endpoint que aceite comparar/consultar
`CnpjHash` bruto entre tenants, o que limita a exploração prática imediata. Ainda assim, é uma violação do
princípio de segredo por-tenant que aumenta o raio de explosão de qualquer comprometimento de agente.

## Sugestão de correção
- Derivar uma chave de hashing de CNPJ por-escritório a partir do segredo mestre (ex.:
  `HMAC-SHA256(key=HMAC_CNPJ_KEY_mestre, msg=escritorioId)`), no mesmo espírito do que já é feito em
  `ConfiguracaoCipher` para a chave de configuração — e devolver ao agente apenas a chave derivada do seu
  próprio escritório.
- Avaliar se o hashing de CNPJ pode ser movido inteiramente para o servidor (o agente envia o CNPJ
  mascarado + hash calculado localmente hoje) para eliminar a necessidade de distribuir qualquer segredo
  de hashing a um processo fora do perímetro do servidor.

## Critérios de aceite
- [ ] Chave de hashing de CNPJ devolvida ao agente é específica do escritório dele, não a chave mestre
- [ ] Migração de dados existentes (CnpjHash já gravados com a chave antiga) planejada e documentada
- [ ] Teste de regressão comprovando que a chave de um escritório não permite recalcular hash válido
      para outro escritório
""",
    },
]

# ── Gráficos ────────────────────────────────────────────────────────────

def build_charts():
    sev_order = ["Critica", "Alta", "Media", "Baixa", "Informativa"]
    sev_counts = {s: 0 for s in sev_order}
    for f in FINDINGS:
        sev_counts[f["severidade"]] += 1

    # Donut por severidade
    labels = [SEV_LABEL[s] for s in sev_order if sev_counts[s] > 0]
    sizes = [sev_counts[s] for s in sev_order if sev_counts[s] > 0]
    colors_pie = [SEV_COLOR[s] for s in sev_order if sev_counts[s] > 0]

    fig, ax = plt.subplots(figsize=(4.6, 4.0), dpi=200)
    wedges, _texts = ax.pie(
        sizes, colors=colors_pie, startangle=90, counterclock=False,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
    )
    ax.text(0, 0.08, str(len(FINDINGS)), ha="center", va="center",
            fontsize=30, fontweight="bold", color=COLOR_HEADER)
    ax.text(0, -0.22, "achados", ha="center", va="center",
            fontsize=11, color=COLOR_MUTED)
    legend_labels = [f"{lab} ({n})" for lab, n in zip(labels, sizes)]
    ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1.0, 0.5),
              frameon=False, fontsize=10)
    ax.set_aspect("equal")
    fig.tight_layout()
    donut_path = os.path.join(ASSETS, "donut_severidade.png")
    fig.savefig(donut_path, transparent=True, bbox_inches="tight")
    plt.close(fig)

    # Barras por categoria
    cat_ids = sorted(CATEGORIES.keys())
    cat_counts = {c: 0 for c in cat_ids}
    for f in FINDINGS:
        cat_counts[f["categoria"]] += 1
    cat_labels = [f"{c}. {CATEGORIES[c]}" for c in cat_ids]
    cat_values = [cat_counts[c] for c in cat_ids]

    fig2, ax2 = plt.subplots(figsize=(6.4, 3.6), dpi=200)
    bar_colors = [COLOR_SUBHEADER if v > 0 else "#94A3B8" for v in cat_values]
    bars = ax2.barh(cat_labels, cat_values, color=bar_colors, height=0.55)
    ax2.invert_yaxis()
    ax2.set_xlabel("Nº de achados", fontsize=10, color=COLOR_MUTED)
    ax2.tick_params(axis="y", labelsize=10, colors=COLOR_TEXT)
    ax2.tick_params(axis="x", labelsize=9, colors=COLOR_MUTED)
    max_v = max(cat_values) if max(cat_values) > 0 else 1
    ax2.set_xlim(0, max_v + 1)
    ax2.set_xticks(range(0, max_v + 2))
    for spine in ["top", "right", "left"]:
        ax2.spines[spine].set_visible(False)
    ax2.spines["bottom"].set_color(COLOR_BORDER)
    for bar, v in zip(bars, cat_values):
        ax2.text(bar.get_width() + 0.08, bar.get_y() + bar.get_height() / 2,
                  str(v), va="center", fontsize=10, color=COLOR_TEXT, fontweight="bold")
    fig2.tight_layout()
    bar_path = os.path.join(ASSETS, "barras_categoria.png")
    fig2.savefig(bar_path, transparent=True, bbox_inches="tight")
    plt.close(fig2)

    return donut_path, bar_path, sev_counts


# ── Estilos ─────────────────────────────────────────────────────────────

styles = getSampleStyleSheet()

def style(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor(COLOR_TEXT))
    base.update(kw)
    return ParagraphStyle(name, **base)

S_TITLE_COVER = style("TitleCover", fontName="Helvetica-Bold", fontSize=26, leading=32,
                       textColor=colors.HexColor(COLOR_HEADER), alignment=TA_LEFT)
S_SUBTITLE_COVER = style("SubtitleCover", fontName="Helvetica", fontSize=14, leading=20,
                          textColor=colors.HexColor(COLOR_SUBHEADER), alignment=TA_LEFT)
S_COVER_META = style("CoverMeta", fontName="Helvetica", fontSize=10.5, leading=16,
                      textColor=colors.HexColor(COLOR_MUTED))
S_COVER_META_LABEL = style("CoverMetaLabel", fontName="Helvetica-Bold", fontSize=10.5, leading=16,
                            textColor=colors.HexColor(COLOR_HEADER))
S_H1 = style("H1", fontName="Helvetica-Bold", fontSize=17, leading=22,
             textColor=colors.HexColor(COLOR_HEADER), spaceBefore=4, spaceAfter=10)
S_H2 = style("H2", fontName="Helvetica-Bold", fontSize=13, leading=17,
             textColor=colors.HexColor(COLOR_SUBHEADER), spaceBefore=14, spaceAfter=6)
S_H3 = style("H3", fontName="Helvetica-Bold", fontSize=11, leading=15,
             textColor=colors.HexColor(COLOR_HEADER), spaceBefore=8, spaceAfter=4)
S_BODY = style("Body", alignment=TA_JUSTIFY, spaceAfter=6)
S_BODY_TIGHT = style("BodyTight", alignment=TA_JUSTIFY, spaceAfter=2)
S_MUTED = style("Muted", textColor=colors.HexColor(COLOR_MUTED), fontSize=9, spaceAfter=4)
S_CODE = style("Code", fontName="Courier", fontSize=8, leading=11,
               textColor=colors.HexColor("#0F172A"), backColor=colors.HexColor("#F1F5F9"))
S_LABEL_BOLD = style("LabelBold", fontName="Helvetica-Bold", fontSize=9.5, leading=13,
                      textColor=colors.HexColor(COLOR_HEADER))
S_FINDING_TITLE = style("FindingTitle", fontName="Helvetica-Bold", fontSize=11.5, leading=15,
                         textColor=colors.white)
S_STRENGTH_TITLE = style("StrengthTitle", fontName="Helvetica-Bold", fontSize=10.5, leading=14,
                          textColor=colors.HexColor(COLOR_FORTE))
S_ISSUE_TITLE = style("IssueTitle", fontName="Helvetica-Bold", fontSize=12, leading=16,
                       textColor=colors.HexColor(COLOR_HEADER))
S_ISSUE_META = style("IssueMeta", fontName="Helvetica-Oblique", fontSize=9, leading=13,
                      textColor=colors.HexColor(COLOR_MUTED), spaceAfter=6)
S_ISSUE_BODY = style("IssueBody", fontName="Courier", fontSize=7.6, leading=10.6,
                      textColor=colors.HexColor("#0F172A"))


def chip(text, bg_hex, fg_hex="#FFFFFF"):
    t = Table([[Paragraph(f"<b>{text}</b>", style("chip", fontName="Helvetica-Bold", fontSize=8,
                                                    textColor=colors.HexColor(fg_hex), alignment=TA_CENTER))]],
              colWidths=[2.6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def escape_html(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def code_block(text):
    escaped = escape_html(text)
    escaped = escaped.replace("\n", "<br/>").replace(" ", "&nbsp;")
    return Paragraph(escaped, S_CODE)


# ── Header / Footer ─────────────────────────────────────────────────────

def on_page(cnv: canvas_mod.Canvas, doc):
    cnv.saveState()
    width, height = A4
    if doc.page > 1:
        cnv.setStrokeColor(colors.HexColor(COLOR_BORDER))
        cnv.setLineWidth(0.6)
        cnv.line(2 * cm, height - 1.55 * cm, width - 2 * cm, height - 1.55 * cm)
        cnv.setFont("Helvetica", 8.2)
        cnv.setFillColor(colors.HexColor(COLOR_MUTED))
        cnv.drawString(2 * cm, height - 1.35 * cm, "Relatório de Auditoria de Segurança — ContabOne")
        cnv.drawRightString(width - 2 * cm, height - 1.35 * cm, REPORT_DATE)

        cnv.setStrokeColor(colors.HexColor(COLOR_BORDER))
        cnv.line(2 * cm, 1.55 * cm, width - 2 * cm, 1.55 * cm)
        cnv.setFont("Helvetica", 8.2)
        cnv.drawString(2 * cm, 1.15 * cm, "Confidencial — uso interno")
        cnv.drawRightString(width - 2 * cm, 1.15 * cm, f"Página {doc.page - 1}")
    cnv.restoreState()


# ── Montagem do documento ────────────────────────────────────────────────

def build_pdf():
    donut_path, bar_path, sev_counts = build_charts()

    doc = SimpleDocTemplate(
        OUT_PDF, pagesize=A4,
        topMargin=2.0 * cm, bottomMargin=2.0 * cm,
        leftMargin=2.0 * cm, rightMargin=2.0 * cm,
        title=f"{REPORT_TITLE} — {PROJECT_NAME}",
        author="Auditoria de Segurança",
    )

    story = []

    # ── Capa ──
    story.append(Spacer(1, 3.2 * cm))
    story.append(Table([[Paragraph("AUDITORIA DE SEGURANÇA", style(
        "kicker", fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor(COLOR_SUBHEADER)))]],
        colWidths=[10 * cm]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(REPORT_TITLE, S_TITLE_COVER))
    story.append(Paragraph(PROJECT_NAME, S_SUBTITLE_COVER))
    story.append(Spacer(1, 1.4 * cm))

    meta_rows = [
        ["Data do relatório", REPORT_DATE],
        ["Escopo auditado", "ContabOne.Api (.NET 10 / ASP.NET Core minimal APIs + EF Core + PostgreSQL), "
                             "ContabOne.Frontend (Vue 3 + TypeScript + Pinia + PrimeVue), Det.Agent e "
                             "Nfse.Agent (automações Python), arquivos de deploy (docker-compose, "
                             "railway.json, .gitignore) e histórico do git"],
        ["Categorias avaliadas", "5 — isolamento de tenant, permissão no navegador, IDOR, chaves expostas, "
                                  "XSS/entradas sem tratamento"],
        ["Achados", f"{len(FINDINGS)} (0 crítica, 0 alta, {sev_counts['Media']} média, "
                     f"{sev_counts['Baixa']} baixa, {sev_counts['Informativa']} informativa)"],
        ["Metodologia", "Revisão manual, arquivo por arquivo, de 100% dos handlers de rota do backend "
                         "(13 arquivos de Features, ~55 arquivos .cs), do frontend (70 arquivos .vue/.ts) "
                         "e dos artefatos de configuração/deploy — sem amostragem"],
    ]
    meta_table = Table(
        [[Paragraph(k, S_COVER_META_LABEL), Paragraph(v, S_COVER_META)] for k, v in meta_rows],
        colWidths=[3.6 * cm, 11.4 * cm],
    )
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor(COLOR_BORDER)),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 1.0 * cm))
    story.append(Paragraph("Nota metodológica — mapeamento das categorias para a stack detectada", S_H3))
    nota = (
        "O projeto <b>não usa Supabase/RLS</b>: é uma API própria em ASP.NET Core com EF Core sobre "
        "PostgreSQL, autenticação via ASP.NET Identity + JWT (usuários web) e uma chave de API dedicada "
        "para agentes de campo (X-Api-Key). Cada categoria da auditoria foi adaptada a este contexto: "
        "<b>(1) isolamento de tenant</b> foi verificado como os Global Query Filters do EF Core em "
        "AppDbContext.cs, populados por um TenantContext resolvido em middleware a partir de claims do "
        "JWT/API key; <b>(2) permissão no navegador</b> foi verificada cruzando os papéis exigidos pelas "
        "rotas do Vue Router com as policies de autorização (RequireAuthorization) de cada grupo de "
        "endpoints no backend; <b>(3) IDOR</b> foi verificado em cada handler que busca/altera/remove "
        "objeto por Guid, considerando que FindAsync/consultas LINQ do EF Core aplicam os Global Query "
        "Filters automaticamente (comportamento confirmado) — exceto onde IgnoreQueryFilters() é usado "
        "explicitamente, cada ocorrência das quais foi auditada individualmente; <b>(4) chaves expostas</b> "
        "cobriu código-fonte, appsettings, docker-compose, railway.json, arquivos de exemplo dos agentes "
        "Python e o histórico completo do git; <b>(5) XSS</b> cobriu os equivalentes Vue (v-html) e "
        "bindings dinâmicos de href/src, já que o frontend é Vue 3, não React."
    )
    story.append(Paragraph(nota, S_BODY))

    story.append(PageBreak())

    # ── Resumo executivo ──
    story.append(Paragraph("Resumo executivo", S_H1))
    total_txt = (
        f"Foram identificados <b>{len(FINDINGS)} achados</b> nas 5 categorias avaliadas, todos de "
        f"severidade média, baixa ou informativa — <b>nenhum achado crítico ou alto</b>. As categorias "
        f"<b>isolamento de tenant</b> (fora do achado pontual sobre um segredo compartilhado), "
        f"<b>permissão definida no navegador</b>, <b>IDOR</b> e <b>XSS</b> foram revisadas integralmente "
        f"sem vulnerabilidade explorável encontrada — o backend aplica controles equivalentes ou mais "
        f"restritivos que a UI em todos os casos verificados. Os achados concentram-se em "
        f"<b>chaves/segredos expostos</b>, principalmente ligados a ambiente de desenvolvimento."
    )
    story.append(Paragraph(total_txt, S_BODY))

    story.append(Spacer(1, 0.3 * cm))
    charts_table = Table([
        [Image(donut_path, width=8.0 * cm, height=7.0 * cm),
         Image(bar_path, width=8.8 * cm, height=5.0 * cm)],
    ], colWidths=[8.2 * cm, 8.8 * cm])
    charts_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(charts_table)
    cap_table = Table([[
        Paragraph("<b>Achados por severidade</b>", style("capL", fontSize=9, alignment=TA_CENTER,
                                                            textColor=colors.HexColor(COLOR_MUTED))),
        Paragraph("<b>Achados por categoria</b>", style("capR", fontSize=9, alignment=TA_CENTER,
                                                          textColor=colors.HexColor(COLOR_MUTED))),
    ]], colWidths=[8.2 * cm, 8.8 * cm])
    story.append(cap_table)

    story.append(Spacer(1, 0.4 * cm))
    resumo_cat_rows = [["Categoria", "Achados", "Situação"]]
    for cid in sorted(CATEGORIES.keys()):
        n = sum(1 for f in FINDINGS if f["categoria"] == cid)
        situacao = "Revisado — sem vulnerabilidade explorável" if n == 0 else f"{n} achado(s) — ver detalhamento"
        resumo_cat_rows.append([f"{cid}. {CATEGORIES[cid]}", str(n), situacao])
    resumo_table = Table(resumo_cat_rows, colWidths=[6.4 * cm, 2.2 * cm, 8.4 * cm])
    resumo_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_HEADER)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(COLOR_BG_LIGHT)]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(COLOR_BORDER)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(resumo_table)

    story.append(PageBreak())

    # ── Pontos fortes ──
    story.append(Paragraph("Pontos fortes", S_H1))
    story.append(Paragraph(
        "Controles verificados no código real e confirmados como corretos, com a respectiva evidência. "
        "Esta seção documenta a cobertura da auditoria tanto quanto os controles em si.", S_MUTED))
    for titulo, evidencia, texto in STRENGTHS:
        block = [
            Paragraph(f"✓ {titulo}", S_STRENGTH_TITLE),
            Paragraph(f"<font face='Courier' size='8'>{escape_html(evidencia)}</font>", S_MUTED),
            Paragraph(texto, S_BODY_TIGHT),
            Spacer(1, 0.15 * cm),
        ]
        story.append(KeepTogether(block))

    story.append(PageBreak())

    # ── Achados detalhados ──
    story.append(Paragraph("Achados detalhados", S_H1))
    story.append(Paragraph(
        "Cada achado lista categoria, severidade, localização exata (arquivo:linha), trecho de código, "
        "justificativa de explorabilidade e condições necessárias para exploração.", S_MUTED))
    story.append(Spacer(1, 0.2 * cm))

    for f in FINDINGS:
        sev = f["severidade"]
        header_bar = Table(
            [[Paragraph(f"{f['id']} · {f['titulo']}", S_FINDING_TITLE)]],
            colWidths=[17 * cm],
        )
        header_bar.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(SEV_COLOR[sev])),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))

        meta_line = Table([[
            chip(SEV_LABEL[sev], SEV_COLOR[sev]),
            Paragraph(f"<b>Categoria {f['categoria']}</b> — {CATEGORIES[f['categoria']]}",
                      style("catmeta", fontSize=9, textColor=colors.HexColor(COLOR_MUTED))),
            Paragraph(f"<font face='Courier'>{escape_html(f['arquivo'])}:{f['linhas']}</font>",
                      style("locmeta", fontSize=8.4, textColor=colors.HexColor(COLOR_MUTED))),
        ]], colWidths=[2.8 * cm, 7.2 * cm, 7 * cm])
        meta_line.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        rows = [header_bar, meta_line]
        rows.append(Paragraph("Trecho:", S_LABEL_BOLD))
        rows.append(code_block(f["trecho"]))
        rows.append(Spacer(1, 0.15 * cm))
        rows.append(Paragraph("Por que é explorável:", S_LABEL_BOLD))
        rows.append(Paragraph(f["por_que"], S_BODY_TIGHT))
        rows.append(Paragraph("Condição de explorabilidade:", S_LABEL_BOLD))
        rows.append(Paragraph(f["condicao"], S_BODY_TIGHT))
        rows.append(Spacer(1, 0.35 * cm))

        story.append(KeepTogether(rows))

    story.append(PageBreak())

    # ── Recomendações ──
    story.append(Paragraph("Recomendações priorizadas", S_H1))
    rec_rows = [["Prior.", "Recomendação", "Achados"]]
    for pri, texto, achs in RECOMMENDATIONS:
        rec_rows.append([pri, Paragraph(texto, S_BODY_TIGHT), achs])
    rec_table = Table(rec_rows, colWidths=[1.6 * cm, 12.4 * cm, 3 * cm])
    rec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_HEADER)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(COLOR_BG_LIGHT)]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(COLOR_BORDER)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
    ]))
    story.append(rec_table)

    story.append(PageBreak())

    # ── Issues para o GitHub ──
    story.append(Paragraph("Issues para o GitHub", S_H1))
    story.append(Paragraph(
        "Texto completo, pronto para copiar e colar, de cada issue acionável. Achados triviais do mesmo "
        "tema foram agrupados numa única issue para não gerar spam.", S_MUTED))
    story.append(Spacer(1, 0.2 * cm))

    for i, issue in enumerate(ISSUES, start=1):
        story.append(Paragraph(f"--- ISSUE {i} ---", style(
            "issuemark", fontName="Courier-Bold", fontSize=9, textColor=colors.HexColor(COLOR_MUTED))))
        story.append(Spacer(1, 0.1 * cm))
        story.append(Paragraph(issue["titulo"], S_ISSUE_TITLE))
        story.append(Paragraph(f"Labels sugeridas: {issue['labels']}", S_ISSUE_META))
        body_escaped = escape_html(issue["corpo"]).replace("\n", "<br/>").replace("  ", "&nbsp;&nbsp;")
        story.append(Paragraph(body_escaped, S_ISSUE_BODY))
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(f"--- FIM ISSUE {i} ---", style(
            "issuemarkend", fontName="Courier-Bold", fontSize=9, textColor=colors.HexColor(COLOR_MUTED))))
        story.append(Spacer(1, 0.5 * cm))
        if i < len(ISSUES):
            story.append(HRFlowable(width="100%", color=colors.HexColor(COLOR_BORDER), thickness=0.5))
            story.append(Spacer(1, 0.3 * cm))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF gerado em: {OUT_PDF}")


if __name__ == "__main__":
    build_pdf()
