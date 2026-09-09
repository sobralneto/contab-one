## Why

A listagem de clientes só existe paginada na tela. O escritório trabalha com
aquele conjunto fora do painel — conciliação, cobrança de certificado,
relatório ao cliente — e não tem como tirá-lo de lá. A tela acabou de ganhar
os filtros que faltavam (regime, 2FA, certificado, onboarding) justamente
para *selecionar um conjunto*; agora esse conjunto precisa poder sair do
painel como arquivo.

## What Changes

- Nova ação **"Exportar CSV"** na barra da tela de clientes, disponível para
  todos os papéis que enxergam a listagem — exportar não é ato de
  administração.
- A exportação gera **o conjunto inteiro que passou pelos filtros**, não só a
  página visível, na mesma ordem que a tabela mostra, e baixa um arquivo CSV.
- Novo endpoint `GET /api/clientes/exportar` devolvendo `text/csv` — a
  primeira resposta não-JSON da API — com os mesmos query parameters de filtro
  e ordenação da listagem.
- A cadeia de filtros de `ListarAsync` sai do corpo do método para um builder
  compartilhado entre listagem e exportação: o arquivo e a tabela têm de
  filtrar igual por construção, não por coincidência.
- O arquivo segue as convenções de planilha pt-BR: separador `;`, UTF-8 com
  BOM, linha de cabeçalho, valores com `;` ou aspas escapados. CNPJ sai só na
  forma mascarada — o arquivo viaja por e-mail e vai além do painel.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `gestao-clientes`: a listagem passa a exigir a exportação em CSV — ação na
  tela, conjunto idêntico ao filtrado (não à página), colunas e valores como a
  tabela mostra, CNPJ mascarado, escopo por escritório preservado, formato de
  planilha que abre sem quebrar acentos nem colunas.

## Impact

- `ContabOne.Api/Features/Clientes/ClientesEndpoints.cs` — extração do
  builder de filtros compartilhado + novo endpoint de exportação. Nenhuma
  mudança no comportamento da listagem.
- `ContabOne.Api/Program.cs` — nada novo a declarar: o endpoint entra no
  grupo `/api/clientes` já montado, herdando a política `EscritorioUsuario`
  (o grupo não tem rate limit hoje e a exportação não introduz um).
- `ContabOne.Frontend/src/views/ClientesView.vue` — botão na barra de
  filtros, guarda contra duplo acionamento; `src/api/endpoints/clientes.ts` —
  função de exportação com download via Blob (primeiro uso do padrão no
  painel).
- Testes: `ContabOne.Api/tests/ClientesTest.cs` (endpoint, filtros, formato,
  BOM), `IsolamentoTest.cs` (exportação não vaza escritório),
  `ClientesView.spec.ts` (botão dispara o pedido com os filtros da tela; MSW
  exige handler novo).
- Sem migração, sem dependência nova, sem envolvimento de agente
  (`Nfse.Agent` intocado) — a exportação é leitura de dados que já existem na
  API.