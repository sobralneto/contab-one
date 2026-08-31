## 1. Catálogo: ferramenta sem agente e página nova (API)

- [x] 1.1 Acrescentar `TemAgente` (bool) ao `Produto` em
      `ContabOne.Api/Domain/Entities.cs`, documentando que ele governa só a
      **oferta** de chave nova — nunca o caminho de autenticação, que continua
      comparando o código da chave com o `Produto.Codigo` do próprio agente
- [x] 1.2 Acrescentar `Importacao = "importacao"` a `PaginaFerramenta.Todas`,
      com o comentário de qual componente do frontend ela corresponde
- [x] 1.3 Expor `temAgente` em `GET /api/produtos` (`ProdutoDto`) e nos
      endpoints de admin de produtos (criar e atualizar), com default `true`
      quando ausente
- [x] 1.4 Testes de API: catálogo devolve `temAgente`; página `importacao`
      aceita no cadastro; página desconhecida continua recusada

## 2. Modelo de dados e migration (API)

- [x] 2.1 Entidades `ApuracaoSimples`, `ApuracaoSegregacao` e
      `ReceitaMensalCliente` em `Domain/Entities.cs`, com a nota de que
      **não existe coluna `Confere`** — é derivada da soma dos oito tributos
      contra o DAS (tolerância R$ 0,05) e não pode virar propriedade
      computada usada em `Where`
- [x] 2.2 Enums `TipoDocumentoPgdas` (`Extrato`, `Declaracao`) e
      `CategoriaReceita` (`Tributado`, `TributadoMonofasico`, `ComSt`,
      `ComStMonofasico`) em `Domain/Enums.cs`; acrescentar `Importacao`
      **ao fim** de `OrigemCliente`
- [x] 2.3 Mapear no `AppDbContext`: `HasQueryFilter` por `EscritorioId` nas
      três entidades novas, índice único
      `(EscritorioId, ClienteId, Competencia)` em `ApuracaoSimples`, PK
      composta em `ApuracaoSegregacao` e `ReceitaMensalCliente`, colunas de
      dinheiro como `numeric(18,2)`, cascade da segregação
- [x] 2.4 Migration única: criar as três tabelas, acrescentar
      `Produto.TemAgente` como `NOT NULL DEFAULT TRUE`, semear o produto
      `pgdas` (domínio `fiscal`, ordem 3, páginas `visao-geral` e
      `importacao`, `TemAgente = FALSE`) e **fazer o backfill de
      `EscritorioProdutos`** habilitando `pgdas` para todos os escritórios
      existentes, no padrão de `20260823052601_EscritorioProdutoContratado`
- [x] 2.5 Rodar a migration no Postgres local e conferir: as três ferramentas
      no catálogo, `nfse`/`det` com `TemAgente = TRUE`, `pgdas` habilitado
      para os escritórios existentes

## 3. Slice `Features/Pgdas` (API)

- [x] 3.1 `POST /api/pgdas/apuracoes` — grava o lote conferido de um cliente.
      Competência já existente devolve **409 listando quais**, indicando
      quais delas foram editadas manualmente; `substituir: true` sobrescreve.
      Grava a segregação e faz upsert em `ReceitaMensalCliente`
- [x] 3.2 `GET /api/pgdas/apuracoes` — lista paginada, filtros por cliente e
      por intervalo de competência
- [x] 3.3 `GET /api/pgdas/clientes/{clienteId}/dashboard` — o payload único
      da dashboard: apurações do intervalo, segregação, série mensal e
      identificação do cliente (nome e **CNPJ mascarado**)
- [x] 3.4 `PUT /api/pgdas/apuracoes/{id}` (marca `EditadoManualmente`) e
      `DELETE /api/pgdas/apuracoes/{id}`
- [x] 3.5 `GET /api/pgdas/resumo` — KPIs da visão geral: clientes com
      apuração, competências gravadas, DAS em aberto, apurações que não
      conferem. O "não confere" escrito como aritmética na query, nunca como
      propriedade computada
- [x] 3.6 Registrar o grupo `/api/pgdas` no `Program.cs`, com a mesma
      exigência de autenticação humana das demais rotas de painel
- [x] 3.7 Testes de API: gravação de lote; 409 na competência repetida;
      substituição com a flag; upsert da série mensal sobrescrevendo o mês
      repetido; **isolamento multi-tenant** (escritório A não lê nem
      sobrescreve apuração de B, nem forçando `escritorioId` na query);
      guarda de tradução LINQ com `ToQueryString()` no filtro de "não
      confere"

## 4. Cliente identificado pelo CNPJ (API)

- [x] 4.1 `POST /api/pgdas/clientes/identificar` — recebe CNPJ cru, deriva
      hash **em memória**, procura por `CnpjHash`; não achando, procura por
      `CnpjMascarado` e **preenche o hash que faltava** ao casar. Devolve o
      cliente ou a sugestão de cadastro
- [x] 4.2 `ClienteRequest` aceita `Cnpj` cru opcional; quando presente, a API
      deriva `CnpjHash` e `CnpjMascarado` e descarta o CNPJ. Cliente criado
      por esse caminho recebe `Origem = Importacao`
- [x] 4.3 `GET /api/clientes/proximo-codigo` — próximo código numérico livre
      de quatro dígitos para o escritório em escopo
- [x] 4.4 Testes de API: identificação por hash; identificação por máscara
      preenchendo o hash; cliente inexistente devolvendo sugestão; cadastro
      com CNPJ cru gravando hash e máscara e **nunca o CNPJ inteiro**;
      limite `MaxClientes` do plano respeitado; próximo código pulando os
      ocupados

## 5. Parser em TypeScript (frontend)

- [x] 5.1 Dependências: `pdfjs-dist`, `jspdf`, `html2canvas`; worker do
      `pdf.js` resolvido pelo Vite (`?url`), sem CDN
- [x] 5.2 `src/features/pgdas/parser/extrairTexto.ts` — reconstrução das
      linhas por coordenada Y, tradução direta do original
- [x] 5.3 `dividirApuracoes.ts` — corte por `Informações da Apuração` (extrato)
      e pelo cabeçalho `Declaratório` (declaração)
- [x] 5.4 `parseApuracao.ts` — os dois leiautes, com todos os fallbacks de
      regex por campo, `semMovimento`, `pago` e o vencimento no dia 20 do mês
      seguinte
- [x] 5.5 `segregacao.ts` e `historico.ts` — as quatro categorias fiscais e a
      série mensal da seção 2.2.1
- [x] 5.6 `conferencia.ts` — soma dos oito tributos contra o DAS, tolerância
      R$ 0,05; a mesma regra que a API usa no resumo
- [x] 5.7 Suíte Vitest do parser com fixtures de **texto já extraído** e
      **anonimizado** (CNPJ, razão social e valores alterados): extrato de um
      mês, declaração de um mês, PDF com várias competências, competência sem
      movimento, documento com segregação por ST/monofásico

## 6. Gerador da dashboard (frontend)

- [x] 6.1 `src/features/pgdas/dashboard/temas.ts` — `lj`, `mudahr` e o
      terceiro tema neutro `contabone` derivado de `tokens.css`; logos em
      `src/assets/marcas/`, fora do base64
- [x] 6.2 `documento.ts` — as funções puras que já existem (`dashHTML`,
      `dashCss`, `rebuildChartsScript`), recebendo os dados do endpoint em
      vez do estado global, e exibindo o **CNPJ mascarado**
- [x] 6.3 Testes Vitest do gerador como string: blocos `dashPart1`/`dashPart2`
      presentes, tributo zerado ausente da composição, competência sem
      movimento com a leitura própria, insights de pendência de pagamento

## 7. Telas da ferramenta (frontend)

- [x] 7.1 `views/pgdas/PgdasImportacaoView.vue` — carga e conferência com o
      layout da plataforma (`.view-header`, `.table-card`, `.data-table`,
      `.btn-*`, `.status-chip`, `.modal-*`), bibliotecas por `import()`
      dinâmico, e o fluxo identificar-ou-cadastrar cliente antes de gravar
- [x] 7.2 `views/pgdas/PgdasVisaoGeralView.vue` — apurações gravadas por
      cliente e competência, KPIs do resumo e as pendências em destaque
- [x] 7.3 `views/pgdas/PgdasDashboardView.vue` — `iframe srcdoc` com o
      documento gerado; aguardar `load` antes de desenhar gráficos e antes de
      exportar
- [x] 7.4 Exportação em PDF e em HTML a partir do `contentDocument` do
      iframe, preservando a quebra de página entre `dashPart1` e `dashPart2`
- [x] 7.5 `api/endpoints/pgdas.ts` e os tipos correspondentes em
      `api/types.ts`
- [x] 7.6 Testes Vitest de componente com MSW: conferência marcando a linha
      que não bate, confirmação de substituição ao receber 409, cadastro de
      cliente novo a partir da sugestão

## 8. Catálogo e navegação no frontend

- [x] 8.1 `api/types.ts`: `'importacao'` em `PaginaFerramenta` e `temAgente`
      em `ProdutoDto`/`ProdutoAdminDto`
- [x] 8.2 `PAGINA_META` em `layouts/AppLayout.vue`: rótulo "Importar
      extratos" para `importacao`
- [x] 8.3 `router/index.ts`: `/f/:produto/importacao` (com
      `meta.pagina: 'importacao'`) e `/f/:produto/dashboard/:clienteId`
      (**sem** `meta.pagina` — rota de detalhe fora do menu)
- [x] 8.4 `views/AgentesView.vue`: o seletor de nova chave passa a filtrar por
      `contratado && temAgente`
- [x] 8.5 `views/admin/ProdutosView.vue`: checkbox "Tem agente" no formulário
      e a página `importacao` no checklist
- [x] 8.6 `constants/explicacoesPagina.ts`: explicação das duas páginas novas
      da ferramenta
- [x] 8.7 Testes de guard: rota de detalhe alcançável para ferramenta
      contratada e recusada para não contratada; `/f/pgdas/execucoes` (página
      não declarada) devolvendo à visão geral da ferramenta

## 9. Fechamento

- [x] 9.1 E2E Playwright: entrar, abrir o `pgdas` pelo hub, importar um
      documento de fixture, cadastrar o cliente sugerido, gravar, abrir a
      dashboard e voltar à visão geral vendo a competência gravada
- [x] 9.2 Rodar as suítes: `dotnet test` e `npm test`; conferir que nenhuma
      fixture de PDF ou texto real de cliente entrou no repositório
- [x] 9.3 Atualizar o `README.md` da raiz: a terceira ferramenta, e a
      distinção entre ferramenta com agente e sem agente no catálogo
- [x] 9.4 Registrar no `design.md` as respostas das Open Questions que forem
      decididas durante a implementação
