## Why

A sidebar de detalhe da visão geral do PGDAS-D (`/f/pgdas`, ícone "Detalhes")
mostra hoje uma tabela operacional de competências: faturamento, DAS,
vencimento, situação e pendências. O que o escritório precisa entregar ao
cliente é outra coisa. Bancos, fornecedores e licitações pedem a **declaração
de faturamento mês a mês**, assinada pelo sócio-administrador e pelo contador.
Hoje esse papel é montado à mão, fora do sistema, mesmo com todos os números já
gravados.

O modelo que o escritório usa é o `Relatorio_Faturamento_2025_2026.pdf`, um
"Demonstrativo Mensal de Faturamento". A sidebar passa a ser esse documento,
pronto para exportar em PDF ou imprimir.

## What Changes

- **BREAKING (visual):** o conteúdo da sidebar de detalhe passa a reproduzir,
  bloco a bloco, o leiaute do PDF de referência. A tabela atual de competências
  (DAS, vencimento, situação, pendências) sai da sidebar. Esses dados continuam
  na lista principal e na dashboard do cliente.
  1. Título **DEMONSTRATIVO MENSAL DE FATURAMENTO** com um filete escuro abaixo.
  2. Quadro de identificação em fundo cinza-claro: **Razão social**; e, numa
     linha de três colunas, **CNPJ**, **Data de abertura** e **Regime
     tributário** ("Simples Nacional").
  3. Tabela **Mês × Faturamento <ano anterior> × Faturamento <ano corrente>**,
     de Janeiro a Dezembro. Meses sem apuração aparecem como `R$ 0,00`. A
     tabela fecha com a linha **TOTAL GERAL** de cada ano, separada por um
     filete escuro.
  4. Nota de rodapé: "Ressalta-se que os valores informados neste
     demonstrativo têm como base de cálculo os dados declarados à Receita
     Federal do Brasil, conforme Nº da Declaração: **<número>**."
  5. Linha **Local:** com traço em branco para preenchimento e **Data:** com
     a data de emissão por extenso ("14 de Outubro de 2026").
  6. Bloco de assinaturas com duas linhas: **SÓCIO-ADMINISTRADOR** e
     **CONTADOR**.
- No topo da sidebar entram duas ações: **Exportar PDF**, que baixa o
  demonstrativo em A4 retrato, uma página, e **Imprimir**, que abre a
  impressão do navegador só com o documento, sem o painel ao redor.
- O extrator do PGDAS-D, que roda no navegador, passa a ler dois campos que o
  documento já traz e hoje são descartados: a **data de abertura no CNPJ** e o
  **Nº da Declaração**.
- A API passa a guardar esses dois dados. `Cliente.DataAbertura` é uma coluna
  nova e nula, escrita na gravação do lote. `ApuracaoSimples.NumeroDeclaracao`
  é uma coluna nova e nula, por competência. A listagem
  `GET /api/pgdas/apuracoes` devolve os dois.

## Capabilities

### New Capabilities

- `demonstrativo-faturamento`: o documento "Demonstrativo Mensal de
  Faturamento" do cliente. Cobre o conteúdo, a escolha dos dois anos, os
  totais, o texto legal, os campos de local, data e assinatura, e a exportação
  em PDF e impressão.

### Modified Capabilities

- `apuracao-simples-nacional`: o requisito "A sidebar mostra a identidade do
  cliente e o histórico de competências" passa a dizer que a sidebar exibe o
  demonstrativo. O requisito "A listagem carrega a identidade do cliente" passa
  a incluir a data de abertura do cliente e o nº da declaração da apuração. A
  extração passa a capturar esses dois campos, e a gravação passa a
  persisti-los.

## Impact

- **Frontend:** `src/views/pgdas/PgdasVisaoGeralView.vue`, onde o template e o
  CSS da sidebar são substituídos. Novo componente do documento e um módulo
  puro de montagem dos dados em `src/features/pgdas/demonstrativo/`.
  Extração em `src/features/pgdas/parser/parseApuracao.ts` e `tipos.ts`. Tipos
  em `src/api/types.ts`. Tokens novos de "papel" em `tokens.css`, porque o
  documento é branco também no tema escuro. Exportação reaproveita
  `html2canvas` e `jspdf`, que já são dependências.
- **API:** `Domain/Entities.cs` (`Cliente.DataAbertura`,
  `ApuracaoSimples.NumeroDeclaracao`), uma migration,
  `Features/Pgdas/PgdasEndpoints.cs` (request de gravação, projeção da
  listagem) e o validador do request.
- **Testes:** Vitest do parser, do módulo de montagem e da view. xUnit da
  gravação e da listagem.
- **Privacidade:** nenhuma mudança no contrato. Data de abertura e número da
  declaração são metadados de identificação, não conteúdo fiscal. O PDF do
  PGDAS-D continua sem sair do navegador. O demonstrativo é gerado no
  navegador a partir de valores que já estão no banco.
- **Convivência:** a change `importacao-pgdas-em-lote`, em andamento, também
  mexe na importação. Esta change toca só a extração de dois campos e o
  payload de gravação, sem conflito de desenho. Quem aplicar a segunda faz o
  rebase dos campos novos.
