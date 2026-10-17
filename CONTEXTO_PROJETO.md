# Contab One — contexto do projeto

> Arquivo para ser anexado como conhecimento de um Projeto no Claude. É um
> resumo do produto, da arquitetura e das regras que não podem ser quebradas.
> Para detalhes de código, a fonte de verdade é o repositório (`README.md`,
> `AGENTS.md`, `Nfse.Agent/CLAUDE.md`, `openspec/`). Onde este resumo e o código
> divergirem, **o código vence**.

## 1. O que é

**Contab One** é um micro-SaaS (hub) para **escritórios de contabilidade
brasileiros**. Um único painel web reúne várias *ferramentas*, cada uma
automatizando uma obrigação fiscal ou trabalhista. A flagship é a coleta
automática de **NFS-e do Portal Nacional**.

Ferramentas hoje:

| Ferramenta | Código da chave | Tem agente? | O que faz |
|---|---|---|---|
| NFS-e | `nfse_` | sim (`nfse.exe`) | baixa XML das NFS-e recebidas/emitidas e gera DANFSe v2.0 em PDF, via mTLS com certificado A1 |
| DET | `det_` | sim (Playwright) | leitura da caixa postal do DET |
| RFB consumo-tributos | — | sim (Playwright) | credenciais/consulta RFB (certificado A1 no store do Windows, modo manual) |
| PGDAS-D | `pgdas_` | **não** | assistente de importação dentro do painel: o PDF é lido no navegador e só os números extraídos vão à API |

## 2. Vocabulário (usar sempre assim)

| Termo | Significado |
|---|---|
| **Plataforma** | o dono do SaaS (admin único) |
| **Escritório** (tenant) | o cliente pagante, ex.: "Contabilidade Silva ME" |
| **Cliente** | empresa dona do certificado, cliente do escritório |
| **Agente** | o robô Python rodando na máquina do escritório (`nfse.exe` etc.), 1..N por escritório |

Atenção: "agente" aqui é termo de **domínio** (o robô), não o assistente de IA.

## 3. A regra de privacidade que define o produto

- O certificado `.pfx` **nunca sai da máquina do escritório**.
- O conteúdo fiscal (XML/PDF de notas, documentos do PGDAS-D) **nunca chega à API**.
- Sobe apenas contagem, metadado e status. CNPJ trafega como **hash HMAC + máscara**, nunca completo.
- Isso permite vender sem virar custodiante da identidade digital de centenas de empresas de terceiros. É restrição dura de escopo, não preferência.
- **Única exceção deliberada:** "Arquivos do escritório" (contrato social, procuração, alvará), enviados **à mão por um humano** para armazenamento de objetos (Railway Bucket). Lista fechada de formatos; `.pfx`/`.p12` e XML/PDF fiscais são barrados por extensão e assinatura binária.

## 4. Stack e estrutura do monorepo

| Pasta | O que é | Stack |
|---|---|---|
| `ContabOne.Api/` | licenciamento, multi-tenant, métricas, catálogo | .NET 10 minimal APIs + EF Core + PostgreSQL |
| `ContabOne.Frontend/` | painel (hub, dashboards, admin) | Vue 3 `<script setup>` + TypeScript + Vite + PrimeVue 4 + Tailwind |
| `Nfse.Agent/` | coletor de NFS-e | Python 3.14 + PyInstaller |
| `Det.Agent/`, `Rfb.Agent/` | DET e RFB | Python + Playwright |
| `openspec/` | specs e histórico de mudanças | fluxo OpenSpec |

`Api`, `Frontend`, `Nfse.Agent` e `Det.Agent` são **repositórios git independentes**
dentro do monorepo (ignorados pelo repo raiz).

**Convenção de idioma:** identificadores, comentários, colunas, JSON e rotas em
**português** (`Escritorio`, `Execucao`, `/api/execucoes`). Nomes impostos por
framework ficam em inglês. Nunca "traduzir" nomes existentes.

## 5. Arquitetura — o que atravessa vários arquivos

### Multi-tenancy
`TenantContext` é preenchido pelo middleware a partir do JWT ou da API key do
agente — **nunca** de parâmetro de rota/query (evita IDOR). Toda entidade com
escopo de tenant tem *global query filter*, **fail-closed**: sem escritório e
sem a flag de admin, retorna zero linhas. Entidade nova precisa do filtro, ou
vaza entre escritórios. **Exceção:** `Tarefa` só é visível a quem participa
(responsável ou criador), inclusive para admins.

### Autenticação
- Humanos: ASP.NET Identity + JWT (access curto + refresh em cookie).
- Agentes: API key por agente (header `X-Api-Key`), guardada com hash. Formato `<codigo>_<prefixo8>_<segredo32>`; lookup por `prefixo8` + `SHA-256(segredo)`.
- **A autenticação nunca lê o catálogo `Produtos`.** `Produto.Codigo` é imutável e a FK é `Restrict`. Editar/desativar um produto não concede nem revoga acesso de agente em campo.
- Gate comercial deliberado: `EscritorioProdutos` (ferramentas contratadas) e `Escritorio.Status`. Escritório não-`Ativo` recebe **401** antes do handshake; o agente trata 401 como "bloqueado", nunca como "API fora do ar" — revogação é imediata, sem carência offline.
- Papéis: `EscritorioUsuario` ⊂ `EscritorioAdmin` ⊂ `PlatformAdmin`, mais a política separada `Agente`.

### API
Vertical slices: `Features/<Area>/<Area>Endpoints.cs`, handlers estáticos, grupos
mapeados em `Program.cs` (com políticas de autorização e rate limit). Todo o
modelo em `Domain/Entities.cs` e `Domain/Enums.cs`. **Enums trafegam como
inteiros**; acrescentar membro é seguro, reordenar é migração de dados. JSON em
camelCase.

Entidades principais: `Escritorio`, `Plano`, `Usuario`, `Agente`, `Cliente`,
`Execucao`, `ExecucaoMetrica`, `RegraColeta`, `ConfiguracaoEscritorio`, `Alerta`,
`Tarefa`, `Produto`, `EscritorioProdutos`, `ArquivoEscritorio`.

### Frontend
- Menu, hub e rotas `/f/:produto/:pagina` são **dirigidos pelo catálogo** (`GET /api/produtos`). Publicar ferramenta é dado, não deploy; só página nova exige código.
- Rotas transversais (sem gate de ferramenta): `/clientes`, `/agentes`, `/usuarios`, `/onboarding/modelos`, `/tarefas`, `/arquivos`.
- Design system: tokens em `tokens.css`, componentes compartilhados em `components.css` (cards do painel = `.card-painel`). Nenhuma cor literal em componente; ícones só de `lucide-vue-next`; nunca `display:flex` em `<td>`.

### Contratos C# ↔ Python (mudam em conjunto, cada um com teste)
1. Hash de CNPJ (`CnpjHasher.cs` ↔ `api_client.py`).
2. Configuração cifrada do handshake (AES-256-GCM, chave derivada da API key).
3. Bundle de regras de coleta (`RegraColetaValidator.cs` ↔ `regras.py`).

## 6. Como o agente NFS-e funciona

Dois modos: **legado** (sem `[api]` no `config.toml`: nenhuma chamada além do
portal) e **conectado** (identifica-se, checa licença com tolerância offline
assinada em cache, baixa regras de coleta, reporta métricas agregadas no fim).
Sem navegador e sem captcha; agendável pela Tarefa Agendada do Windows.

## 7. Variáveis de ambiente da API

`DATABASE_URL`, `JWT_SIGNING_KEY`, `HMAC_CNPJ_KEY` (**permanente** — trocar
invalida todos os `CnpjHash` e duplica clientes; a API recusa subir sem ela),
`CORS_ORIGINS` (só produção), e opcionais `ARQUIVOS_*` para o bucket.

## 8. Desenvolvimento e testes

- Tudo local: `npm install && npm run dev` (Postgres + API + Vite). API em `:5139`, Vite em `:5173`.
- Testes: `npm test` roda só o que mudou; `npm run test:tudo` roda tudo. xUnit com Testcontainers (Docker), Vitest, Playwright E2E, suítes Python offline.
- Typecheck do front: `npm --prefix ContabOne.Frontend run build`.
- **Nunca** rodar `dotnet test` com `DATABASE_URL` definido (migraria o banco de desenvolvimento).
- Migrations: `dotnet ef migrations add Nome --project ContabOne.Api`; nunca editar o snapshot à mão.
- Mudanças seguem o fluxo **OpenSpec** (propor → aplicar → sincronizar → arquivar).

## 9. Dados sensíveis

Certificados `.pfx` (o nome do arquivo embute a senha), pastas de notas, planilhas
de empresas, `config.toml` (a chave de API é credencial) e caches do agente são
dados reais de clientes: nunca versionar, nunca colar em serviço externo.

## 10. Como quero que você ajude

- Responda em português, de forma direta.
- Preserve a regra de privacidade em qualquer proposta de escopo.
- Respeite a convenção de nomes em português e o vocabulário da seção 2.
- Ao sugerir código, aponte arquivos/camadas afetados e os testes que cobrem a mudança.
- Quando algo contradisser este resumo, avise em vez de assumir.
