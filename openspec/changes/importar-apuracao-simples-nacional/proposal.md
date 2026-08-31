## Why

Existe hoje, fora do monorepo, uma ferramenta autônoma de página única que lê
os extratos e declarações do **PGDAS-D** em PDF, extrai as competências do
Simples Nacional e monta um painel de apuração — faturamento, DAS, carga
efetiva, sublimite estadual, segregação da receita — exportável em PDF para
entregar ao cliente. Ela funciona e já é usada; o problema é o que ela **não**
tem por ser uma página solta:

- **Nada fica gravado.** Fechou a aba, acabou. Reabrir o painel do mesmo
  cliente em outubro exige carregar os PDFs de novo, um por competência.
- **Não conhece cliente.** Digita-se razão social e CNPJ à mão em cada uso,
  sem qualquer ligação com a carteira de clientes do escritório.
- **Não conhece escritório.** A identidade visual é escolhida num botão, e o
  arquivo precisa ser reeditado para atender um terceiro escritório.
- **A série histórica de 12 meses morre em memória**, mesmo estando dentro do
  documento (seção 2.2.1) — é o dado que faz o gráfico de evolução valer.

O hub já tem o lugar certo para ela: o domínio **Fiscal**, hoje com o NFS-e
sozinho. E o catálogo de ferramentas já é dado, não código.

## What Changes

- Nova ferramenta no catálogo: **`pgdas` — PGDAS-D**, domínio `fiscal`, ao
  lado do NFS-e.
- **Primeira ferramenta sem agente.** O catálogo ganha `Produto.TemAgente`;
  ferramenta sem agente deixa de aparecer no seletor de nova chave de API,
  onde hoje qualquer produto contratado apareceria.
- Conjunto fechado de páginas ganha **`importacao`**. O `pgdas` declara
  `visao-geral` e `importacao`; a dashboard gerada vive numa rota de detalhe,
  alcançável mas fora do menu.
- **Três tabelas novas**: `ApuracaoSimples` (uma linha por cliente ×
  competência, com os oito tributos e o DAS), `ApuracaoSegregacao` (receita
  por categoria fiscal) e `ReceitaMensalCliente` (a série mensal do
  documento, por upsert — passa a servir o gráfico de 12 meses mesmo para
  meses cujo PDF nunca foi carregado).
- **O PDF não sobe para a API.** A leitura acontece no navegador, como já
  acontece hoje; para o servidor vão só os valores já conferidos pelo
  usuário. É a mesma promessa que sustenta o agente — conteúdo fiscal não
  trafega —, aplicada a uma ferramenta que não tem agente.
- **Identificar-ou-cadastrar cliente pelo CNPJ do documento.** O CNPJ é usado
  em memória para derivar hash e máscara e é descartado; nunca é persistido
  inteiro. Como efeito colateral, `POST /api/clientes` passa a aceitar o CNPJ
  cru e derivar o hash no servidor — hoje o cadastro pela tela grava
  `CnpjHash` vazio, e esses clientes não casam com nada.
- **Layout**: passos de carga e conferência viram telas Contab One, com os
  componentes centralizados. A **dashboard gerada mantém o layout atual**, nas
  duas identidades (L&J e MUDAHR), renderizada dentro de um `iframe srcdoc`
  para não se misturar com os tokens da plataforma.
- Novo grupo de rotas `/api/pgdas`, incluindo o endpoint que devolve tudo que
  a dashboard precisa a partir do banco — é o que permite reabrir o painel sem
  reprocessar PDF nenhum.

## Capabilities

### New Capabilities
- `apuracao-simples-nacional`: leitura dos documentos do PGDAS-D no
  navegador, conferência antes de gravar, persistência das competências por
  cliente, e a dashboard reconstruída a partir do banco.

### Modified Capabilities
- `catalogo-dominios-ferramentas`: ferramenta passa a declarar se tem agente,
  e o conjunto fechado de páginas ganha `importacao`.
- `navegacao-por-dominio`: uma ferramenta pode ter rota de detalhe além das
  páginas declaradas — endereço próprio, fora do menu, sujeita ao mesmo
  gate de contratação.
- `gestao-clientes`: cadastro aceita CNPJ cru e deriva hash e máscara no
  servidor; identificação de cliente existente pelo CNPJ; sugestão do próximo
  código livre; nova origem `Importacao`.

## Impact

**API** — `Domain/Entities.cs` (`ApuracaoSimples`, `ApuracaoSegregacao`,
`ReceitaMensalCliente`, `Produto.TemAgente`), `Domain/Enums.cs`
(`TipoDocumentoPgdas`, `CategoriaReceita`, `OrigemCliente.Importacao`),
`Infra/AppDbContext.cs` (query filters e índices), migration com as tabelas +
seed do produto + backfill de `EscritorioProdutos`, nova slice
`Features/Pgdas/`, `Features/Clientes/ClientesEndpoints.cs` (CNPJ cru,
próximo código), `Features/Produtos/` e `Features/Admin/` (`temAgente`),
`ContabOne.Api.Tests`.

**Frontend** — novo `src/features/pgdas/parser/` (tradução do parser para
TypeScript, com testes), `src/features/pgdas/dashboard/` (o gerador de HTML
e os temas), `views/pgdas/` (três telas), `router/index.ts`,
`layouts/AppLayout.vue` (`PAGINA_META`), `api/types.ts`,
`api/endpoints/pgdas.ts`, `constants/explicacoesPagina.ts`,
`views/AgentesView.vue` (filtro `temAgente`), `views/HubView.vue` (números do
card), `assets/marcas/`, dependências `pdfjs-dist`, `jspdf`, `html2canvas`.

**Nada é removido.** `Execucao`, `Agente` e `RegraColeta` não são tocados: a
ferramenta não tem agente, não tem execução e não tem regra de coleta.
