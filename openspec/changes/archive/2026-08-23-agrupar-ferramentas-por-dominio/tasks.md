## 1. Domínio e páginas no catálogo (API)

- [x] 1.1 Criar a entidade `Dominio` (`Codigo`, `Nome`, `Ordem`, `Icone`) em
      `ContabOne.Api/Domain/Entities.cs`, com `Codigo` como chave e a
      documentação de por que o catálogo é dado
- [x] 1.2 Acrescentar `DominioCodigo` (FK) e `Paginas` ao `Produto`, com a
      constante do conjunto fechado de páginas (`visao-geral`, `clientes`,
      `execucoes`, `agentes`, `configuracao`) e um validador ao lado de
      `ProdutoCodigo`
- [x] 1.3 Mapear `Dominio` e as colunas novas no `AppDbContext`
- [x] 1.4 Migration: criar `Dominio`, semear `fiscal` ("Fiscal"), `dp`
      ("DP") e `contabil` ("Contábil") — nome único, sem coluna de nome
      curto —, adicionar as colunas como anuláveis, fazer o backfill (NFS-e
      em `fiscal` com todas as páginas; DET em `dp` sem `configuracao`) e só
      então torná-las obrigatórias
- [x] 1.5 Rodar a migration no Postgres local e conferir o estado das duas
      ferramentas já cadastradas

## 2. Catálogo entregue à sessão (API)

- [x] 2.1 `GET /api/produtos`: incluir domínio (código, nome, ordem, ícone) e
      páginas na resposta, mantendo a ordenação por ordem do domínio e depois
      do produto
- [x] 2.2 `GET /api/produtos`: para `PlatformAdmin`, devolver o catálogo ativo
      inteiro com a flag `contratado` por escritório em foco, em vez de
      omitir o não contratado — sem mudar o comportamento da sessão de
      escritório
- [x] 2.3 Endpoints de admin de produtos: aceitar e validar domínio e páginas
      no cadastro e na edição, recusando domínio inexistente e página fora do
      conjunto
- [x] 2.4 Endpoint de listagem de domínios para alimentar o formulário de
      cadastro de ferramenta
- [x] 2.5 Testes de API: catálogo do escritório só com o contratado, catálogo
      do admin com a flag, recusa de domínio inexistente, recusa de página
      desconhecida, escopo ignorando `escritorioId` para usuário de
      escritório
- [x] 2.6 Tela de cadastro de ferramentas (admin, `views/admin/ProdutosView.vue`):
      seletor de domínio (obrigatório) e checklist de páginas no formulário de
      criar/editar. Sem isto o cadastro de ferramenta nova quebra na validação
      da API, e uma ferramenta criada sem página nenhuma some do menu por
      completo — gap descoberto durante a implementação da tarefa 2.3, não
      previsto na proposta original

## 3. Catálogo na sessão do frontend

- [x] 3.1 Estender `api/types.ts` com domínio, páginas e `contratado` no
      `ProdutoDto`, e criar o tipo de domínio
- [x] 3.2 Criar `stores/catalogo.ts`: carrega o catálogo, expõe as
      ferramentas agrupadas por domínio, o estado de carga e o de falha
- [x] 3.3 Carregar o catálogo no `router/guards.ts` em paralelo à restauração
      da sessão, e limpá-lo em `auth.clearSession()`
- [x] 3.4 Testes: catálogo limpo no logout, menu do segundo login sem resíduo
      do primeiro, falha de carga não derruba a sessão

## 4. Rotas por ferramenta

- [x] 4.1 Registrar a família `/f/:produto/:pagina` em `router/index.ts`, com
      `/f/:produto` levando à visão geral
- [x] 4.2 Mover `DashboardView` para a visão geral da ferramenta e apontar
      `/f/nfse` para ela, sem alterar o conteúdo da tela
- [x] 4.3 Redirects de `/dashboard`, `/clientes`, `/execucoes`, `/agentes` e
      `/configuracao` para o equivalente em `/f/nfse/`, preservando query
      string
- [x] 4.4 Guard: recusar produto fora do catálogo da sessão e página não
      declarada pela ferramenta, devolvendo ao hub ou à visão geral
- [x] 4.5 Indexar `EXPLICACOES_PAGINA` por `${produto}.${pagina}` com
      fallback para `${pagina}`, e ajustar `ExplicacaoPagina.vue`
- [x] 4.6 Testes de guard: produto inexistente, produto não contratado,
      página não declarada, admin acessando qualquer ferramenta

## 5. Hub e menu

- [x] 5.1 Criar `views/HubView.vue`: seções por domínio, card por ferramenta
      com nome, descrição, estado e atalho
- [x] 5.2 Card de ferramenta não contratada: informativo apenas — marcado
      como não contratada, sem número, sem atalho para as páginas e sem
      nenhum elemento acionável (nem contato comercial)
- [x] 5.3 Números no card apenas para ferramenta cujo resumo a API já escopa
      (hoje, só o NFS-e)
- [x] 5.4 Gerar o menu lateral do `AppLayout.vue` a partir do catálogo:
      domínios como seções, ferramentas como itens, páginas declaradas como
      submenu
- [x] 5.5 Mapa nome→ícone com genérico de fallback, substituindo os SVG
      escritos à mão nos itens de ferramenta
- [x] 5.6 Não renderizar item de ferramenta enquanto o catálogo não resolver;
      manter hub e itens transversais quando a carga falhar, com aviso e nova
      tentativa
- [x] 5.7 Identificar a ferramenta no cabeçalho de toda página de ferramenta,
      junto do título da página
- [x] 5.8 Menu recolhido: conferir os três títulos de domínio e o
      comportamento do submenu a 68px

## 6. Fechamento

- [x] 6.1 Atualizar as specs em `e2e/` para os endereços novos e cobrir o
      hub e o card não contratado, inclusive a ausência de elemento
      acionável nele
- [x] 6.2 Rodar a suíte de testes do frontend e a da API
- [x] 6.3 Conferir na aplicação as duas visões: admin com catálogo completo,
      escritório com um domínio a menos
- [x] 6.4 Atualizar o `README.md` do frontend com a estrutura de navegação e
      o que é preciso para publicar uma ferramenta nova

## 7. Correção pós-implementação: Clientes/Agentes fora de `/f/:produto/`

Descoberto testando a aplicação de verdade: Cliente e Agente nunca foram
conceitos por ferramenta (a listagem de cada um é uma tabela só para o
escritório inteiro), então `/f/:produto/clientes` e `/f/:produto/agentes`
prometiam um recorte que o dado não tinha. Não estava no plano original.

- [x] 7.1 Tirar `clientes` e `agentes` de `PaginaFerramenta` (API e front) e
      do backfill da migration `AdicionarDominioEPaginasAoProduto` (ainda não
      commitada — corrigida em vez de gerar uma migration nova)
- [x] 7.2 Registrar `/clientes` e `/agentes` como rotas próprias em
      `router/index.ts`, fora de `/f/:produto/`
- [x] 7.3 Atualizar `AppLayout.vue`: os dois viram itens fixos na seção
      Escritório, sem depender do catálogo para escolher o endereço
      (`produtoParaPaginaTransversal` removido)
- [x] 7.4 Atualizar `ProdutosView.vue` (checklist de páginas do cadastro),
      testes de guard e e2e para o conjunto de páginas reduzido

## 8. Correção pós-implementação: Execução e Configuração escopadas de verdade

Descoberto testando a aplicação: `/f/nfse/execucoes` e `/f/det/execucoes`
mostravam a mesma lista — a API nunca filtrava por produto, só a URL
prometia. Ao contrário de Clientes/Agentes, aqui o conceito por ferramenta é
real (uma execução pertence ao agente de uma ferramenta), só faltava
implementar. Não estava no plano original.

- [x] 8.1 Migration: `ConfiguracaoEscritorio` ganha `ProdutoId` na chave
      primária (`EscritorioId, ProdutoId, Chave`), com FK para `Produtos` e
      backfill atribuindo todo registro existente ao NFS-e
- [x] 8.2 `GET`/`PUT /api/configuracao` passam a exigir `produtoCodigo`,
      escopando leitura e escrita por (escritório, produto)
- [x] 8.3 Handshake do agente (`AgentEndpoints.cs`) filtra a configuração
      entregue pelo `ProdutoId` do próprio agente
- [x] 8.4 `GET /api/execucoes` ganha `produtoCodigo` opcional (via
      `Agente.ProdutoId`), aplicado nos três modos de listagem (plana,
      agrupada por escritório, agrupada por cliente)
- [x] 8.5 Frontend: `ConfiguracaoView.vue` e `ExecucoesView.vue` passam o
      `:produto` da rota para a API; `api/endpoints/configuracao.ts` e
      `execucoes.ts` atualizados
- [x] 8.6 Testes de API cobrindo o isolamento (configuração de uma
      ferramenta não vaza para outra, handshake só recebe a própria,
      execuções filtradas por produto nos três modos, ferramenta inexistente
      recusada)
- [x] 8.7 Rodar as suítes de testes (API e frontend) e o e2e completo

## 9. Correção pós-implementação: Regras de Coleta para dentro do NFS-e

Pedido explícito do usuário: `/admin/regras` deveria ficar dentro de
Fiscal → NFS-e, abaixo de Configuração, restrita a PlatformAdmin. Não
estava no plano original.

- [x] 9.1 `regras` adicionada ao conjunto fechado `PaginaFerramenta` (API e
      front); NFS-e passa a declarar `['visao-geral','execucoes','configuracao','regras']`
      (migration ainda não commitada corrigida, DB local sincronizado)
- [x] 9.2 Rota `/f/:produto/regras` registrada (papeis: `PlatformAdmin`
      só), `/admin/regras` removida e virou redirect permanente
- [x] 9.3 `AppLayout.vue`: item Regras sai da seção Admin e entra no
      submenu do NFS-e; `PAGINA_META` ganha um segundo nível de restrição
      (`platformAdmin`, mais estrito que `escritorioAdmin`)
- [x] 9.4 `explicacoesPagina.ts` (`admin-regras` → `regras`, chave bare para
      o fallback do texto), `ProdutosView.vue` (checklist do cadastro),
      `global-setup.ts` (chave composta do tour)
- [x] 9.5 Testes de guard cobrindo a restrição (EscritorioAdmin bloqueado,
      PlatformAdmin acessa) e verificação visual (posição no submenu,
      ausência para EscritorioAdmin, redirect do endereço antigo)
