## Context

A visão geral do PGDAS-D (`PgdasVisaoGeralView.vue`) hoje lista uma linha por
apuração — cliente × competência — usando `GET /api/pgdas/apuracoes`
(`listarApuracoes`, `ApuracaoListaDto`). A projeção em
`PgdasEndpoints.ListarApuracoesAsync` já devolve `clienteNome`, mas não o
código nem o CNPJ mascarado do cliente, que vivem em `Cliente.Codigo` e
`Cliente.CnpjMascarado` e hoje só chegam ao front via
`POST /api/pgdas/clientes/identificar`.

A ferramenta já tem um endpoint por cliente —
`GET /api/pgdas/clientes/{id}/dashboard` — e a listagem já aceita filtro
`clienteId`, o que reduz o escopo da mudança: nenhuma rota nova é obrigatória.

## Goals / Non-Goals

**Goals:**

- Lista da visão geral compacta: uma linha por cliente com a última
  competência importada.
- Histórico de competências do cliente acessível a um clique (sidebar à
  direita), com a identidade do cliente visível ali.
- "Ver dashboard" inalterado na tabela principal.

**Non-Goals:**

- Novos endpoints de API (reuso da listagem existente).
- Mudança na dashboard do cliente, na importação ou na gravação.
- Editor de apuração na sidebar — ela é somente leitura; edição segue
  onde já está (a importação e a própria lista, para quem usar o filtro
  de competências, continuam sendo os pontos de edição).

## Decisions

**1. Agrupar no frontend, não com endpoint novo.** A lista já vem ordenada
por competência desc e com os filtros atuais; agrupar é um `computed` (mapa
por `clienteId`, mantendo a primeira ocorrência — a competência mais
recente). Alternativa descartada: um endpoint `/apuracoes/por-cliente` que
agrupasse no servidor — mais uma rota e um teste para o mesmo resultado
com menos de 100 linhas por página; se o volume um dia justificar, o
endpoint nasce sem quebrar o front.

**2. Paginação por laço com teto.** O front hoje pede `tamanho: 100` único.
Com o agrupamento, um cliente cuja última importação for velha só aparece
se estiver dentro da janela. O `carregar()` passa a paginar: repete a
chamada com `pagina` incrementado enquanto `dados` acumulado < `total`,
com teto de segurança de 10 páginas (1000 apurações) — acima disso a lista
avisa que a amostra está truncada em vez de laçar sem fim. Alternativa
descartada: subir `tamanho` para o máximo e parar — só empurra o problema
para escritórios maiores.

**3. Sidebar carrega o histórico por demanda, reusando `listarApuracoes`.**
Ao abrir, o front chama `listarApuracoes({ clienteId })` (filtro já
existente) e exibe todas as competências devolvidas, paginando da mesma
forma se necessário. Alternativa descartada: reusar
`GET /api/pgdas/clientes/{id}/dashboard` — payload maior (tributos,
segregação, série mensal) do que a sidebar precisa, e semântica de
intervalo, não de listagem.

**4. Identidade do cliente via projeção estendida.** `ApuracaoListaDto`
ganha `clienteCodigo` e `clienteCnpjMascarado`, projetados de
`a.Cliente.Codigo` e `a.Cliente.CnpjMascarado` — colunas já gravadas, o
CNPJ nunca inteiro. Alternativa descartada: um `GET /api/clientes/{id}`
por linha (N+1, e o endpoint de clientes traz mais do que a sidebar
mostra). Nenhum campo novo de dados sensíveis: mascarado é o formato que
`Cliente` já carrega em disco.

**5. Sidebar como bloco da própria view, com tokens do design system.**
Um `<aside>` fixo à direita (sobreposto com transição), estilizado com os
tokens de `tokens.css`/`components.css` — sem biblioteca nova (PrimeVue
Drawer traria peso e um padrão visual divergente do resto da view, que é
hand-rolled). Ícone de detalhe: `PanelRight` (lucide-vue-next),
decorativo ao lado do `title`, mesmo padrão dos demais botões-ícone da
tabela.

## Risks / Trade-offs

- [Listagem sem identidade para apurações órfãs] — se um `Cliente` for
  excluído (FK `Restrict` impede hoje), a projeção de `Cliente` já
  garantiria o 404 do JOIN; a navegação interna não cria apuração sem
  cliente → nenhuma ação; o comportamento atual (JOIN com `Cliente.Nome`)
  já assume isso.
- [Laço de paginação multiplica requisições em escritórios grandes] —
  teto de 10 páginas + aviso de amostra truncada; a ordenação por
  competência desc garante que a janela corta o histórico antigo, não os
  clientes ativos.
- [`NaoConfere` e pendências na sidebar] — reuso dos mesmos campos da
  lista, sem recalcular no front (a aritmética segue no servidor, como já
  é hoje).
- [A11y da sidebar] — `role="complementary"` com `aria-label`, foco
  movido para o primeiro elemento ao abrir e devolvido ao gatilho ao
  fechar; `Esc` fecha.

## Migration Plan

Aditivo, sem quebra de contrato: dois campos novos em uma resposta
existente (append, camelCase, nenhum enum reordenado) e uma view refeita.
Deploy da API e do front no mesmo ciclo; rollback é redeploy da versão
anterior de cada lado, que ignora campos desconhecidos.