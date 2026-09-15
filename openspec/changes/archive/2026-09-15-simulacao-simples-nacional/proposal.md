## Why

A simulação de Simples Nacional existe hoje como arquivo solto —
`formulario_simples_nacional.html`, na raiz do repositório. Para usá-la o
escritório abre um HTML local, com identidade visual própria (logo, marca
d'água, fontes próprias, cabeçalho L&J Contabilidade), fora do painel: não
tem o título da barra superior, não segue o tema claro/escuro, não tem a
explicação de página, e os campos de faturamento aceitam texto livre, sem a
máscara de moeda que o sistema já aplica ao digitar. Trazer o formulário para
dentro do painel, como página da área do escritório, dá a ele o mesmo
tratamento de layout das telas do sistema e elimina a cópia paralela.

A calculadora é a mesma — a tabela de anexos, o RBT12 proporcionalizado e a
alíquota efetiva não mudam. O que muda é o layout e a máscara dos valores.

Depois de virar rota transversal do escritório (`/simulador`, ver abaixo), o
próximo pedido do uso real foi persistência: fechar a aba perde a simulação
inteira, e o escritório quer poder salvar uma e voltar a ela depois — sem
guardar o resultado calculado, só o que foi digitado.

## What Changes

- Nova página **Simulador Simples Nacional** (`/simulador`), item da área
  **Escritório** do menu, ao lado de Arquivos — rota transversal, não página
  de ferramenta. **Não** é ferramenta nova: nenhum produto, nenhum
  licenciamento, nada no catálogo. A simulação é calculadora do escritório,
  não um módulo do PGDAS-D — nasceu no submenu do PGDAS-D como página de
  catálogo e o uso real (feedback do usuário) mostrou que não pertence a um
  produto; esta é a decisão final registrada aqui.
- A página adota o **mesmo controle de layout das telas do sistema**:
  `animate-fade-in` + `.view-header` com `<h1>`, contêiner de largura
  limitada, título real na barra superior via `meta.titulo`, e as classes do
  design system em vez das classes próprias do HTML.
- **Muda o layout em relação ao original, no topo da página**: o bloco de
  identificação (nome empresarial + CNPJ) e o cartão de seleção do anexo ficam
  na **mesma coluna à esquerda**; o preenchimento do faturamento mês a mês fica
  na **coluna à direita**.
- Os 12 campos de faturamento passam a usar a **formatação de moeda que já
  existe no sistema, aplicada ao digitar** (`moedaDigitada`/`moedaFormatada` em
  `useInputMask`, o padrão de `PlanosView.vue`), no lugar do texto livre do
  original. O prefixo `R$` fica fora do campo, no cartão.
- A borda esquerda dos cartões de faturamento **deixa de ser sempre vermelha**:
  fica vermelha **somente no mês sem valor preenchido**, e deixa de ser assim
  que o mês recebe valor. Os meses passam a **começar vazios** — o original
  abria com R$ 160.000,00 em todos.
- O CNPJ da identificação passa a usar a máscara do sistema (`cnpjMask`), no
  lugar da máscara própria do HTML.
- Sai a identidade do arquivo solto: logo, marca d'água, fontes próprias
  (Baloo/Poppins/IBM Plex Mono), rodapé e o cabeçalho "L&J Contabilidade" — a
  identidade do escritório é a do painel, na barra superior.
- **Nada é gravado e nada vai à API, exceto por ação explícita do usuário.** A
  simulação continua calculada inteiramente no navegador — é estimativa, não
  apuração, e não entra no histórico de execuções. A única exceção é o botão
  de salvar descrito abaixo, e mesmo esse não toca no cadastro do cliente.
- Preservados do original: as faixas dos Anexos I a V, o cálculo do RBT12
  proporcionalizado, a alíquota nominal/dedutível/efetiva, o alerta de
  extrapolação do limite de R$ 4.800.000,00, os indicadores de 12 meses, as
  duas tabelas semestrais e o gráfico de faturamento × imposto (as duas séries
  num único eixo comum, para a proporção ser honesta).

### Persistência (nesta revisão)

- Um botão **"Salvar simulação"** grava, para o escritório da sessão, **só**
  nome, CNPJ, anexo e os 12 valores de faturamento digitados. Nenhum
  resultado calculado (indicadores, tabelas, RBT12) é persistido — ao reabrir
  uma simulação salva, os 4 campos voltam ao formulário e tudo é recalculado
  ali, do mesmo jeito que uma simulação nova.
- **O CNPJ é gravado em texto puro** — sem HMAC hash e sem máscara de
  exibição, ao contrário da convenção usada por `Cliente`/`Escritorio`
  (`CnpjMascarado` + `CnpjHash`). É uma exceção deliberada, pedida pelo
  usuário: este cadastro não representa nem aponta para um cliente da
  carteira, é só o rótulo de uma simulação avulsa.
- Nova página de **Histórico**, rota transversal `/simulador/historico`,
  alcançada por um botão dentro do próprio Simulador — sem entrada própria no
  menu do escritório. Lista as simulações salvas (nome, CNPJ, anexo, data),
  com ação de **abrir** (carrega os 4 campos em `/simulador` e recalcula) e
  **excluir**.
- Continua **sem qualquer vínculo com `Cliente`**: salvar uma simulação não
  cria, não altera e não consulta cliente cadastrado.

## Capabilities

### New Capabilities

- `simulacao-simples-nacional`: a página de simulação dentro do painel — o
  layout em duas colunas do topo, a identificação em texto livre e a seleção
  do anexo à esquerda, o preenchimento do faturamento à direita com máscara de
  moeda ao digitar, a marcação de mês sem valor, os resultados estimados
  (indicadores, tabelas semestrais e gráfico) calculados localmente, e a ação
  opcional de salvar/reabrir uma simulação.
- `historico-simulador-simples-nacional`: a página de histórico — lista as
  simulações salvas do escritório e permite reabrir ou excluir uma.

### Modified Capabilities

- `formatacao-campos`: a formatação monetária ao digitar, hoje exigida
  especificamente no campo de preço dos planos, passa a valer para qualquer
  campo de valor monetário do frontend — e a simulação de faturamento é o
  segundo caso concreto da regra.

## Impact

- **API**: nova entidade `SimulacaoSimplesNacional` (`EscritorioId`, `Nome`,
  `Cnpj` em texto puro, `Anexo`, `Faturamentos` — array de 12 decimais,
  `CriadoEm`), com filtro de tenant fail-closed em `AppDbContext` (mesmo
  padrão de `Cliente`/`ArquivoEscritorio`) — sem qualquer FK para `Cliente`.
  Uma migration cria a tabela; não toca em `Produto`, `Paginas` nem em
  qualquer migration de catálogo. Novo slice
  `Features/Simulador/SimulacoesEndpoints.cs`, grupo `/api/simulador` (POST
  salvar, GET listar, GET por id, DELETE), `RequireAuthorization
  ("EscritorioUsuario")` — mesmo nível de acesso da rota `/simulador` no
  frontend.
- **Frontend**: `src/router/index.ts` (rota transversal `/simulador`, sem
  `meta.pagina`, mais a rota filha `/simulador/historico`),
  `src/layouts/AppLayout.vue` (item de menu na área Escritório, só para
  `/simulador`), `src/constants/explicacoesPagina.ts` (texto de primeira
  visita para as duas rotas), `src/api/endpoints/simulador.ts` (chamadas às
  rotas novas), o botão de salvar e o carregamento de simulação salva em
  `SimuladorView.vue`, e `HistoricoSimuladorView.vue` nova.
- **Testes**: `src/router/guards.spec.ts` (sem mudança de catálogo: as rotas
  transversais não passam pelo guard de produto), `e2e/global-setup.ts` (as
  chaves transversais vêm de `EXPLICACOES_PAGINA`), testes novos do cálculo,
  da view do simulador (botão salvar) e da view de histórico, mais testes de
  endpoint da API (salvar, listar, obter, excluir, isolamento por
  escritório).
- **Sem impacto** em agente (`Nfse.Agent`, `Det.Agent`, `Rfb.Agent`), em
  contrato C#↔Python, em `Cliente`, em catálogo por produto e no conteúdo
  fiscal: a simulação não envia nem recebe dado fiscal, e o que ela grava
  agora é só o que o usuário pede para salvar.