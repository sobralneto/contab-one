## Context

A simulação de Simples Nacional existe como `formulario_simples_nacional.html`
na raiz do repositório: um documento HTML autônomo de ~128 KB, com folha de
estilo própria, fontes próprias (Baloo 2 / Poppins / IBM Plex Mono), logo em
base64, marca d'água, cabeçalho "L&J Contabilidade" e rodapé. O corpo é uma
coluna única de 720 px com três blocos empilhados — identificação da empresa,
seleção do anexo e grade de 12 cartões de faturamento — seguidos de alerta de
limite, 4 indicadores, duas tabelas semestrais e um gráfico de barras montado à
mão em CSS. Os valores começam preenchidos com R$ 160.000,00 em todos os meses.
Os cartões de faturamento têm `border-left: 4px solid var(--gold)`, e nesse
arquivo `--gold` é `#9c2b25` — um vermelho vinho, não dourado.

O cálculo vive em JavaScript embutido, acoplado ao DOM: `ANEXOS` (faixas I a V,
6 faixas cada), `calcular()` (RBT12 proporcionalizado, alíquota efetiva,
imposto), e funções de render que escrevem `innerHTML`. Nada disso é testado —
não há teste algum sobre o arquivo.

Do lado do painel, a ferramenta PGDAS-D é um produto sem agente
(`TemAgente: false`) semeado em `ImportarApuracaoSimplesNacional.cs`, que
declara `Paginas = ARRAY['visao-geral','importacao']`. As páginas são um
conjunto fechado e codificado: membro em `PaginaFerramenta` (`Entities.cs`),
união em `src/api/types.ts`, uma `RouteRecordRaw` por slug em
`src/router/index.ts`, rótulo em `PAGINA_META` (`AppLayout.vue`) e caixa em
`PAGINAS_DISPONIVEIS` (`ProdutosView.vue`). O submenu é derivado de
`produto.paginas` — não há item de menu escrito à mão. Fora dessa família há
as rotas transversais do escritório (`/clientes`, `/tarefas`, `/arquivos`):
item de menu escrito à mão na área Escritório do `AppLayout.vue`, rota
própria sem `:produto`, sem gate de catálogo — é a família a que a simulação
acabou pertencendo.

Duas telas do PGDAS-D estabelecem o "controle de layout" a seguir:
`PgdasImportacaoView.vue` e `PgdasDashboardView.vue` usam
`div.<nome>.animate-fade-in` + `.view-header` com `<h1>` e ações, contêiner de
largura limitada por CSS scoped, o título real na barra superior via
`meta.titulo`, e as classes globais de `components.css`
(`.btn-primary`/`.btn-secondary`/`.btn-icon`, `.table-card`/`.data-table`,
`.form-field`/`.req`, `.loading-msg`, `.status-chip`, `.icone-inline`). O
componente `EstadoVazio` é reusado. A explicação de primeira visita vem de
`ExplicacaoPagina.vue`, montado uma vez no `AppLayout`.

A máscara de moeda pedida já existe: `useInputMask()` expõe
`moedaDigitada`/`moedaFormatada` (digitação, dígito = centavo) e
`currencyMask`/`parseCurrency` (string já formada). O único consumidor em
produção é `PlanosView.vue`, com um `computed` gravável e um
`bloquearNaoDigito` que barra o caractere não-dígito na origem.

Do lado da API, `ArquivoEscritorio` (`Features/Arquivos`) é o precedente mais
próximo para a persistência desta revisão: entidade escopada só por
`EscritorioId`, sem relação com `Cliente`, com filtro de tenant fail-closed em
`AppDbContext` e endpoints de listar/criar/excluir escopados à sessão
(`ArquivosEndpoints.cs`). `Cliente`/`Escritorio` são o precedente — descartado
aqui de propósito (Decisão 11) — para CNPJ tratado como identidade: os dois
guardam `CnpjMascarado` + `CnpjHash` via `CnpjHasher`, nunca o valor inteiro.

## Goals / Non-Goals

**Goals:**

- A simulação como página do painel, na área Escritório do menu, com o mesmo
  controle de layout das demais telas.
- O arranjo de duas colunas no topo: identificação + anexo à esquerda,
  faturamento à direita.
- Máscara de moeda do sistema aplicada ao digitar nos 12 campos de faturamento.
- Borda vermelha só no mês sem valor, com os meses começando vazios.
- O cálculo idêntico ao do formulário original, e agora testável.

- Salvar, opcionalmente, os 4 campos de entrada de uma simulação (nome, CNPJ,
  anexo, faturamento) e reabri-los depois — sem gravar nenhum resultado
  calculado.
- Uma página de histórico das simulações salvas do escritório.

**Non-Goals:**

- ~~Persistir a simulação, criar endpoint, ou ligá-la ao cadastro do
  cliente.~~ **Superado nesta revisão**: agora há persistência opt-in (ver
  Decisões 10-13). O que continua non-goal é **gravar o resultado
  calculado** (indicadores, tabelas, RBT12) e **qualquer vínculo com
  `Cliente`** — os dois seguem de fora.
- Qualquer alteração nas faixas, na fórmula do RBT12 ou na regra de alíquota.
- Substituir ou alterar a apuração do PGDAS-D, a importação ou a dashboard.
- Ferramenta nova, produto novo, licenciamento novo ou mudança de domínio —
  nenhum membro novo em `PaginaFerramenta`, a simulação não é página
  declarável de ferramenta.
- Tocar em agente Python ou em contrato C#↔Python.

## Decisions

**1. Rota transversal `/simulador`, na área Escritório do menu — não página de
ferramenta.** A primeira versão desta change viajou pelo caminho oposto: slug
`simulacao` no conjunto fechado (`PaginaFerramenta`, união em `types.ts`,
`PAGINA_META`, `PAGINAS_DISPONIVEIS`), rota `/f/:produto/simulacao`, tudo
declarado pelo catálogo. No uso real o usuário rejeitou o enquadramento — "o
simulador não é um produto do PGDAS" — e a página mudou de família: item de
menu escrito à mão na área Escritório (`AppLayout.vue`), ao lado de Arquivos,
rota `/simulador` sem `:produto` e sem `meta.pagina`, acessível a todo usuário
de escritório, sem gate de catálogo. Tudo o que a primeira versão tocou no
lado do catálogo foi revertido: membro, migration, união, `PAGINA_META`,
`PAGINAS_DISPONIVEIS` e o delta da spec `catalogo-dominios-ferramentas`.

O argumento que sustentou a primeira versão — "é opção de menu da ferramenta
existente, não ferramenta nova" — confundiu "não é ferramenta nova" com "é
página da ferramenta": a simulação não fala com o produto PGDAS-D, não lê
apuração, não toca no cliente; a única coisa que ela tem a ver com a
ferramenta é o domínio fiscal do cálculo. Arquivos é o precedente que prova o
ponto: tela transversal, do escritório inteiro, fora do catálogo por produto.

**2. Sem migration, sem mudança na API.** A primeira versão declarava a página
por migration (`ARRAY_APPEND` em `Paginas` do produto `pgdas`, com `Down()`
removendo o valor antes de qualquer remoção do membro). Com a mudança para
rota transversal, nada sobra no banco: a página não é declarável, o conjunto
fechado não a contém e o dev local já foi limpo (o valor saiu da linha do
pgdas e a migration, não publicada, foi apagada com a entrada de histórico
dela). Consequência: a API não recebe commit nenhum desta change.

**3. O cálculo é portado para um módulo TypeScript puro, com teste.** Um
diretório novo `src/features/simulacao/` com a tabela de anexos e `calcular()`
como funções puras (entrada: anexo + 12 valores; saída: as 12 linhas
calculadas), mais `*.spec.ts` cobrindo faixas, proporcionalização, primeiro mês
sem histórico, extrapolação do limite e divisão por zero. Alternativa
descartada: manter a lógica inline na view, como no HTML — é justamente a parte
cuja preservação a proposta afirma, e inline ela não é verificável. Também
descartado compartilhar módulo com `features/pgdas/`: apuração lê documento
parseado e registro persistido, simulação não conhece nenhum dos dois; não há
código comum hoje além da aritmética de faixas, e forçar um módulo comum
acoplaria dois conceitos que só se parecem no nome.

**4. Dinheiro: `computed` gravável sobre `moedaDigitada`/`moedaFormatada`,
com `bloquearNaoDigito`.** O padrão de `PlanosView.vue:105-108`, replicado por
mês. Alternativa descartada: `currencyMask` no `@change` — é a função que a
própria documentação do composable marca com "NÃO usar em digitação", e o
comportamento pedido é a formatação a cada tecla. Uma divergência deliberada
do padrão, a pedido do usuário no uso real: o cartão de mês já exibe o
prefixo `R$` fora do campo (`.mes-prefix`), então o `computed` tira o
`"R$ "` do que `moedaFormatada` devolve e o campo mostra só o número — em
`PlanosView` não há prefixo externo, lá o `R$` dentro do campo é o único.

**5. "Sem valor" é `0`, e `moedaFormatada(0)` devolve string vazia.** Não é
preciso estado paralelo: o valor do mês é a única fonte, e vazio e zero
coincidem. É o que faz a marcação dos cartões ser derivada
(`meses[i] === 0`) em vez de um sinalizador que pode dessincronizar. O preço
está em Riscos.

**6. A marcação de mês vazio NÃO é um `.status-chip`.** O design system fixa
que ausência de dado usa o neutro e nunca a cor de atenção, e que estado nunca
é comunicado só por cor. A marcação aqui é estado de **entrada obrigatória por
preencher** — o mesmo caso do campo de formulário, cuja regra no design system
é "erro = borda `--erro` + mensagem abaixo" — e não um dado ausente exibido.
Implementá-la como chip neutro ("Não informado") contradiria o pedido;
implementá-la como chip de atenção contradiria a regra do chip.

A primeira versão seguiu a regra do design system até o fim: borda do cartão
em `--erro` **mais** um sinal textual por cartão ("sem valor preenchido",
associado ao campo via `aria-describedby`), de modo que quem não percebe a
cor continuasse sabendo o que falta. No uso real o texto se mostrou barulho —
12 repetições na abertura, todas dizendo o que a borda já diz — e o usuário
o removeu; a decisão registrada aqui é **remover o sinal textual de vez** e
manter a borda como marcação única, derivada do valor do mês. O estado
continua acessível sem cor: a conta dos meses pendentes está no próprio
formulário (12 cartões, e a toolbar limpa tudo), e a ausência de texto é o
que a borda assinala.

A cor vem do token `--erro`, não de literal e não do `--gold: #9c2b25` do
arquivo original: aquele vermelho vinho é o accent de marca daquele documento,
sem significado de erro, e no painel a marca é semântica. `--kpi-vermelho` /
`--kpi-grad-vermelho` ficam de fora: são tintas de cartão de estatística, não
de estado de campo.

**7. O cabeçalho de marca do arquivo original não é portado.** Logo em base64,
marca d'água, o par de fontes próprias, o rodapé e o "L&J Contabilidade" saem.
A identidade do escritório já é a da barra superior, que compõe
`escritorio-em-foco` com `produto.nome · ui.pageTitle`; manter uma segunda
identidade, fixa e de um escritório só, contradiria o `escritorio-em-foco` e a
multi-tenancy. Tipografia, cores e raios passam a vir de `tokens.css`, e o
tema escuro passa a funcionar por troca de token.

**8. O gráfico adota a convenção do sistema, com as duas séries num eixo
comum.** O original desenha barras em CSS e normaliza faturamento e imposto
cada um pelo próprio máximo, com as duas escalas escondidas ("escala própria",
diz a legenda). Passa a ser Chart.js via PrimeVue dentro de `.card-painel`, com
legenda, tooltip e cores de série por token — o padrão de `GraficoMensal.vue`,
inclusive o `getComputedStyle` que lê o token para o Chart.js.

A primeira versão portada usou **dois eixos rotulados** (faturamento à
esquerda, imposto à direita) com o argumento de que, com faturamento uma
ordem de grandeza acima do imposto, as barras de imposto sumiriam. Na prática
os eixos independentes reproduziram exatamente a distorção do original: cada
eixo auto-escala para o próprio máximo, então um imposto de R$ 15.000 enche o
eixo dele e aparece com a altura de um faturamento de R$ 160.000 — o
comparativo mente (feedback do usuário no uso real). As duas séries dividem
agora **um único eixo rotulado** ("Valores (R$)"): a barra de imposto fica
pequena de verdade, o que é a proporção honesta. O valor exato de cada série
continua acessível no tooltip, e o total de imposto tem indicador próprio
acima das tabelas. Alternativa descartada: manter as barras CSS — deixaria o
painel com um gráfico fora do design system, sem tooltip. Sendo um gráfico
com duas séries, respeita o teto de 4 e não usa o gradiente da marca.

**9. A toolbar do original é preservada, com a ação de repetir condicionada.**
"Limpar formulário" e "Repetir mês 1 em todos" viram `.btn-secondary`, e
"Calcular imposto estimado" vira `.btn-primary`. Como os meses passam a
começar vazios, "Repetir mês 1 em todos" fica desabilitada enquanto o mês 1 não
tiver valor — sem isso o botão clicaria e não faria nada visível.

**10. Salvar grava só os 4 campos de entrada — nunca o resultado calculado.**
`SimulacaoSimplesNacional` guarda `Nome`, `Cnpj`, `Anexo` e `Faturamentos`
(array de 12 decimais). Indicadores, tabelas semestrais e RBT12 continuam
derivados — recalculados no cliente com o mesmo `calcular()` sempre que uma
simulação salva é reaberta. Alternativa descartada: gravar também o
resultado, para reabrir sem recalcular — duplicaria dado derivável, e uma
mudança futura na tabela de alíquotas (não neste escopo, mas já aconteceu com
o Simples no passado) deixaria simulações antigas com resultado congelado e
divergente do que a mesma entrada produziria hoje.

**11. CNPJ é gravado em texto puro — decisão explícita do usuário, ao
contrário da convenção de `Cliente`/`Escritorio`.** Essas duas entidades
guardam `CnpjMascarado` + `CnpjHash` (nunca o CNPJ inteiro — é o padrão do
`CnpjHasher` e a leitura literal do contrato de privacidade do produto,
AGENTS.md: "CNPJs travel as HMAC hashes plus a mask, never in full"). Para a
simulação o usuário pediu o oposto, de forma explícita e repetida: o campo é
texto livre digitado pelo usuário, não vinculado a nenhum cliente cadastrado
nem a nenhum CPF/CNPJ real necessariamente — é só um rótulo para reencontrar
a simulação depois — e por isso a exceção fica registrada aqui como
deliberada, não como descuido. Nenhuma validação de checksum ou de 14
dígitos é aplicada: o campo grava exatamente o que o usuário digitou (dígitos
e pontuação, se houver), sem limpar nem mascarar.

**12. Histórico é rota transversal própria (`/simulador/historico`), sem
entrada no menu do escritório — alcançada por um botão dentro do
Simulador.** Consistente com a Decisão 1 (rota, não desvio de código dentro
de uma página existente), mas sem duplicar o menu: o escritório já tem um
único ponto de entrada ("Simulador Simples Nacional"), e o histórico é uma
ação de dentro dessa tela, não um destino que alguém procuraria direto no
menu. Alternativa descartada: item de menu próprio — poluiria a área
Escritório com duas entradas para o que é, na prática, uma calculadora e o
apoio dela.

**13. Tabela nova, sem qualquer relação com `Cliente`.** A simulação salva
continua anônima em relação ao cadastro — nome e CNPJ digitados aqui não
apontam para `ClienteId`, e não há FK para `Clientes`. Ligar a um cliente
cadastrado reabriria a discussão que a proposta original fechou ("não entra
no cadastro do cliente") e criaria um caminho indireto de a simulação virar
dado do cliente — o oposto do que a Decisão 1 e o Non-Goal registram.

**14. O campo de CNPJ vira componente reutilizável (`CampoCnpj.vue`), com a
implementação do cadastro de clientes como referência — não a do
Simulador.** No uso real, o campo de CNPJ do Simulador (par `cnpj`
digits-only + computed `cnpjExibicao`, decisão original acima) não respeitava
a máscara ao digitar. Em vez de depurar essa implementação específica, o
padrão que já funciona em produção — `ClientesView.vue`, onde o `v-model` do
campo carrega o próprio **valor mascarado** e o setter reaplica `cnpjMask` a
cada tecla, sem bloquear caractere na origem — foi extraído para
`src/components/comum/CampoCnpj.vue` e passou a ser o único campo de CNPJ do
frontend: `ClientesView.vue` e `SimuladorView.vue` usam o mesmo componente.
Consequência para a persistência (decisão 11): o valor em texto puro que
`SimuladorView.vue` envia ao salvar deixou de vir de um ref de dígitos à
parte e passou a ser derivado do `v-model` mascarado
(`cnpjMascarado.value.replace(/\D/g, '')`) no momento de montar o payload —
o componente não conhece nem precisa conhecer essa regra de gravação, que é
específica do Simulador.

## Risks / Trade-offs

- [Doze cartões vermelhos na abertura] Todos os meses começam vazios, então a
  página abre com 12 marcações — o mesmo "tudo vermelho" que a mudança
  pretende evitar, deslocado para o instante inicial. É a escolha explícita do
  usuário, e o decurso do preenchimento a resolve: cada mês preenchido apaga a
  sua marcação, então o vermelho vira contador de pendência. → Mitigação: a
  marcação é derivada do valor do mês, nunca acumulada, e cada cartão
  preenchido apaga a sua — o vermelho restante é a pendência que falta.
- [Zero e vazio são o mesmo estado] Um mês que o usuário queira deixar
  legitimamente em R$ 0,00 fica marcado como não preenchido, e não há como
  distinguir os dois casos na tela. Na aritmética não há diferença (ambos
  valem 0), mas visualmente há. → Mitigação: aceito como está; se virar
  incômodo, o estado passa a ser "tocado" (um `Set` de meses preenchidos) em
  vez de derivado do valor — mudança pequena, restrita à view.
- [Deriva de spec em `formatacao-campos`] A spec atual afirma que digitar
  `100` exibe `R$ 100,00`, mas o código em produção aplica dígito = centavo e
  exibe `R$ 1,00` (`useInputMask.spec.ts:74-76`). O delta corrige a afirmação.
  → Registrado aqui de propósito: se a intenção original era mesmo `R$ 100,00`
  ao digitar `100`, então o defeito é do código, e não da spec, e o conserto
  não pertence a esta mudança.
- [Página nova quebra o submenu se faltar registro] ~~`PAGINA_META[p]` é um
  `Record` exaustivo sobre a união `PaginaFerramenta`~~ Risco extinto pela
  decisão 1: a página saiu do catálogo, não há membro novo nem `Record`
  exaustivo para atualizar. Fica registrado porque o caminho inverso (voltar
  a uma página de catálogo) o reativa.
- [Modal de explicação intercepta E2E] `e2e/global-setup.ts` pré-marca as
  páginas vistas; para rotas transversais as chaves saem de
  `EXPLICACOES_PAGINA`, então a entrada nova (`simulador`) é coberta sozinha
  — sem lista manual, ao contrário do que a primeira versão precisava
  (`PAGINAS_FERRAMENTA`). → Mitigação: escrever o texto de
  `explicacoesPagina.ts` no mesmo passo da rota.
- [Rollback da migration] ~~`Down()` que apenas apagasse o membro…~~ Risco
  extinto pela decisão 2: não há migration de catálogo. No dev local, onde a
  primeira versão chegou a rodar, o valor `'simulacao'` foi removido da linha
  do pgdas e a entrada de histórico apagada junto com os arquivos da
  migration — uma linha declarando um valor que a validação recusa faria a
  próxima edição do produto falhar. (A migration desta revisão é outra: só
  `CREATE TABLE` para `SimulacaoSimplesNacional`, ver Decisão 13 — `Down()`
  aqui é só `DropTable`, sem o problema do conjunto fechado.)
- [CNPJ em texto puro é uma exceção ao contrato de privacidade do produto]
  A Decisão 11 grava CNPJ sem hash e sem máscara, diferente de toda outra
  entidade do sistema que guarda CNPJ. Um vazamento de banco expõe esses
  CNPJs em claro, o que não acontece com `Cliente`/`Escritorio`. → Mitigação:
  aceito como está, por ser pedido explícito do usuário e por o campo não
  estar vinculado a nenhum cliente real da carteira — é rótulo de simulação,
  não identidade de cliente gerida pela plataforma. Se isso mudar (a
  simulação passar a poder referenciar cliente cadastrado), a decisão 11
  precisa ser revisitada.
- [Histórico cresce sem limite] Não há expurgo automático de simulações
  salvas — a tabela cresce enquanto o escritório salvar e nunca excluir. →
  Mitigação: a página de histórico oferece exclusão manual (Decisão 12); sem
  uso de agente nem execução em lote, o volume esperado por escritório é
  baixo (uso ocasional, uma simulação por vez), então paginação simples na
  listagem já resolve enquanto o expurgo automático não vira necessidade.

## Migration Plan

1. Frontend (já entregue): rota transversal `/simulador`, item de menu na
   área Escritório, `explicacoesPagina.ts` (chave `simulador`, o name da
   rota), view e módulo de cálculo.
2. API (nesta revisão): entidade `SimulacaoSimplesNacional` + migration
   (`CREATE TABLE`, sem tocar em `Produto`/`Paginas`), filtro de tenant em
   `AppDbContext`, endpoints em `Features/Simulador/SimulacoesEndpoints.cs`
   sob `/api/simulador`.
3. Frontend (nesta revisão): `src/api/endpoints/simulador.ts`, botão "Salvar
   simulação" e carregamento de simulação salva em `SimuladorView.vue`, rota
   filha `/simulador/historico` + `HistoricoSimuladorView.vue`, texto de
   primeira visita da rota nova em `explicacoesPagina.ts`.
4. `npm test` (runner seletivo) antes de commitar — agora cobre também o
   layer da API, que volta a mudar nesta revisão.

Rollback: reverter o commit do frontend torna as duas páginas inalcançáveis.
Reverter a migration da API remove a tabela — sem membro de catálogo
envolvido, `Down()` é só `DropTable`, sem o cuidado de ordem que uma migration
de `PaginaFerramenta` exigiria.

## Open Questions

- ~~O texto de primeira visita deve ser chaveado só em `simulacao` ou também
  em `pgdas.simulacao`?~~ Resolvido pela decisão 1: rota transversal não tem
  produto — a chave é o name da rota (`simulador`), como Arquivos.
- Vale manter "Repetir mês 1 em todos" agora que os meses começam vazios? A
  decisão 9 o preserva com guarda; se o uso mostrar que ele não ajuda a
  preencher, sai numa mudança seguinte.
