## Context

`SimuladorView.vue` hoje monta duas seções sempre presentes: `.topo` (os três
cartões de entrada) e `.resultado` (`<section ref="resultadoEl"
class="resultado">`, sempre no DOM, sempre recalculada por reatividade). O
botão "Calcular imposto estimado" só chama `resultadoEl.value?.scrollIntoView(...)`
— não existe hoje nenhum estado de "resultado ainda não pedido".

O documento original, `formulario_simples_nacional.html`, tem a ordem exata
que o usuário pediu de volta (linhas ~336–370): divisor de etapa → cartão
`#anexoDescResult` com `#empresaIdentificacao` (identificação, texto mono
pequeno) **antes** do `<h2>` do anexo e da descrição → alerta de limite →
`.kpis` → bloco do 1º semestre (`.semester-title`: "1º Semestre" + "1º ao 6º
mês de atividade") → bloco do 2º semestre (mesmo padrão) → `.chart-panel` →
`<footer>` com o aviso final. `SimuladorView.vue` já preserva quase tudo
disso, exceto: a ordem identificação/anexo está invertida, não há rótulo de
semestre acima de cada tabela, e não há aviso final.

O leiaute por escritório já existe, só que para outro consumidor.
`Escritorio.LayoutDashboard` (`ContabOne | Lj | Mudahr`) é lido em
`PgdasEndpoints.DashboardAsync` e devolvido junto com os dados da dashboard
de um cliente; no frontend, `src/features/pgdas/dashboard/temas.ts` define
`TEMAS` (as três paletas, com `bg`/`card`/`ink`/`muted`/`line`/`wine`/
`charcoal`/…) e `temaPorCodigo()`, consumidos por `PgdasDashboardView.vue`
para montar um documento HTML completo, renderizado num `<iframe>` e
recapturado com `html2canvas` para PDF (`apuracao-simples-nacional`,
"A identidade visual da dashboard vem do escritório"). O leiaute `lj` já é,
literalmente, a paleta do `formulario_simples_nacional.html`: `wine:
'#9c2b25'` é o mesmo `--gold` (vermelho-vinho) do arquivo original, e
`charcoal: '#5a5a50'` é o `--teal` dele.

## Goals / Non-Goals

**Goals:**

- Resultado oculto até o primeiro "Calcular imposto estimado" (ou até
  reabrir uma simulação salva), continuando reativo depois de revelado.
- Reordenar o cabeçalho do resultado (identificação antes do anexo),
  acrescentar os rótulos de semestre e o aviso final, replicando a ordem do
  documento original.
- O bloco de resultado usa a identidade visual do escritório da sessão —
  mesma fonte de dado (`Escritorio.LayoutDashboard`) e mesmas três
  identidades da dashboard de apuração.
- Um botão "Baixar PDF" no resultado, com logo e nome do escritório no
  cabeçalho do documento — pedido do usuário no uso real, depois de ver o
  resultado retemado na tela (ver Decisão 8, que substitui o Non-Goal
  original sobre exportação).

**Non-Goals:**

- Renderizar o resultado do Simulador num `<iframe>`, ou gerar um documento
  HTML completo (`dashHTML`/`dashCss`) como a dashboard de apuração faz —
  o PDF (Decisão 7) é gerado por captura direta do DOM Vue já renderizado,
  sem esse passo intermediário.
- Mudar o cálculo, a persistência (`SalvarSimulacaoRequest`/
  `SimulacaoSimplesNacional`) ou o histórico — nenhum desses três muda.
- Tocar em `PgdasDashboardView.vue` além do caminho do import de `temas.ts`.
- Reintroduzir logo, marca d'água ou tipografia própria do documento
  original (Baloo/Poppins/IBM Plex Mono) — isso já foi decidido contra na
  change anterior (decisão 7) e continua valendo; só a paleta de cor volta,
  pelo mecanismo do escritório, não pelo arquivo.

## Decisions

**1. Um novo endpoint próprio, `GET /api/simulador/layout`, em vez de
reaproveitar o payload da dashboard de apuração.** O `layoutDashboard` que já
trafega em `/api/pgdas/clientes/{clienteId}/dashboard` está amarrado a um
cliente específico — o Simulador não tem cliente (decisão 13 da change
anterior: sem FK para `Cliente`). O endpoint novo lê
`Escritorio.LayoutDashboard` direto pelo `TenantContext.EscritorioId` da
sessão, sem depender de nenhum cliente existir. Fica no mesmo grupo
`/api/simulador`, mesma policy `EscritorioUsuario` dos demais.

**2. O tema é aplicado sobrescrevendo os TOKENS do design system dentro do
bloco de resultado, não com uma folha de estilo nova.** `KpiCard.vue`,
`.card-painel`, `.data-table` e o restante do painel já leem
`var(--surface-card)`, `var(--border)`, `var(--accent)`,
`var(--text-primary)`, etc. — variáveis CSS herdam por cascata
independentemente do `scoped` do Vue (que só isola seletores, não a herança
de custom properties). Um `:style` computado no `<section class="resultado">`
redeclara essas mesmas variáveis com os valores do `Tema` do escritório:

  | token do painel | campo do `Tema` |
  |---|---|
  | `--surface-page` | `bg` |
  | `--surface-card`, `--surface-header` | `card` |
  | `--border` | `line` |
  | `--text-primary` | `ink` |
  | `--text-secondary`, `--text-muted` | `muted` |
  | `--accent` | `wine` |
  | `--accent-suave` | `soft` |
  | `--accent-gradient` | `linear-gradient(135deg, wine, wineDark)` |

  Com isso, `KpiCard`, as tabelas (`.data-table`, `.tabela-wrap`) e o
  `.card-painel` do gráfico retemam sozinhos, sem editar o CSS deles.
  O `--surface-page` é a exceção: nenhum desses componentes o consome, então
  quem o usa é o próprio `<section class="resultado">`, que pinta o fundo do
  escritório (`background: var(--surface-page)` + padding e raio) como o
  `--bg` da página no documento original — sem isso o token não teria efeito
  visível nenhum. Continua sendo identidade fixa do escritório: como o
  `:style` sobrescreve o token dentro do bloco, o fundo não acompanha o
  claro/escuro do painel (requisito "Tema do painel não afeta o resultado").
  Alternativa descartada: portar o HTML/CSS gerado por `dashCss`/`dashHTML`
  (o gerador da dashboard de apuração) para o Simulador — geraria um
  documento paralelo, duplicando toda a marcação que o Simulador já tem em
  Vue, só para um resultado que nunca precisa virar PDF.

**3. `--erro`/`--erro-suave` e `--atencao`/`--atencao-suave` NÃO são
retemados — o alerta de limite excedido e a marcação de excedido na tabela
continuam nas cores semânticas do painel.** `Tema` não tem um campo de
"erro"/aviso (o documento original tinha `--red`, sem equivalente na
paleta), e correção/aviso é semântica de estado, não de marca — mesmo
raciocínio da decisão 6 da change anterior ("a marca é semântica no
painel"). Sombra (`--shadow-*`) e raios (`--radius-*`) também não mudam:
são geometria, não identidade.

**4. O gráfico usa as cores do `Tema` diretamente, sem ler
`getComputedStyle`.** Hoje `corDoToken()` lê `document.documentElement` — a
raiz do documento, não o container retemado — porque o Chart.js exige cor
literal (não aceita `var(--x)`, precisa resolvida). Ler a raiz continuaria
devolvendo os tokens neutros do painel, não os do tema do escritório. Como
já existe um `Tema` completo em memória, as duas séries usam `tema.charcoal`
(faturamento) e `tema.wine` (imposto) diretamente — a mesma dupla que o
documento original descreve na legenda ("barra cinza = faturamento, barra
vinho = imposto estimado"). Eixos e grade usam `tema.muted`/`tema.line`.

**5. `temas.ts` muda de `features/pgdas/dashboard/` para
`features/identidade-escritorio/`, conteúdo idêntico.** A change anterior
fixou que "a simulação não fala com o produto PGDAS-D" (decisão 1); importar
um arquivo de dentro de `features/pgdas/` no Simulador contradiria isso na
prática, mesmo sendo só uma tabela de cores sem lógica de apuração. Mover é
mecânico: `PgdasDashboardView.vue` passa a importar do novo caminho, sem
mudança de comportamento — `temas.spec.ts` muda de pasta junto.

**6. Revelar o resultado é um booleano (`mostrarResultado`), não um
`v-if` amarrado a "algum mês tem valor".** Calcular com todos os meses em
zero ainda é uma simulação válida (o requisito "Simulação sem nenhum valor"
já cobre indicadores zerados) — o gate é a AÇÃO do usuário (clicar em
Calcular, ou abrir do histórico), não o conteúdo dos campos. Trocar de anexo
ou editar um mês depois de revelado não esconde o resultado de novo: o
`v-if` some do DOM, não da reatividade por baixo, então o recálculo ao
digitar continua valendo sem ligação nova nenhuma.

**7. A ordem do cabeçalho de resultado inverte: identificação primeiro, anexo
depois.** É a ordem do `#anexoDescResult` original
(`#empresaIdentificacao` antes do `<h2>`/`<p>` do anexo) e a que o usuário
pediu de volta. Hoje `resultado-cabecalho` monta `<h2>` do anexo antes do
parágrafo de identificação — as duas linhas trocam de posição, sem mudar
conteúdo nem classes.

**8. O PDF é gerado capturando o DOM Vue já renderizado (`html2canvas` +
`jsPDF`), com um cabeçalho fora da tela só para a foto — não um documento
HTML/CSS paralelo.** Reaproveita a biblioteca e a matemática de quebra de
página de `PgdasDashboardView.addBlocoPdf` (captura em `scale:2`, divide em
mais de uma página A4 quando a imagem não cabe numa só), mas **duplicada**
em `SimuladorView.vue`, não extraída para um módulo comum: o Non-Goal
"Tocar em `PgdasDashboardView.vue` além do caminho do import de `temas.ts`"
continua valendo, e a Decisão 5 já argumentou que o Simulador não importa
de dentro de `views/pgdas/` nem o inverso. ~25 linhas duplicadas custam
menos do que reabrir uma tela sem cobertura de teste para extrair uma
função em comum.

A logo e o nome do escritório (`tema.logo`/`tema.nome`, os mesmos campos já
usados pela dashboard de apuração) aparecem **só no PDF**, num nó de
cabeçalho montado por JS e capturado à parte. Isso preserva a Decisão 7 da
change anterior ("o painel mostra uma única identidade, a da barra
superior") sem abrir uma exceção nova: a identidade da marca aparece no
documento que sai do painel, não dentro dele. Alternativa descartada:
desenhar o cabeçalho direto no `jsPDF` via `pdf.addImage`/`pdf.text` —
exigiria pré-carregar `tema.logo` como `HTMLImageElement`/base64 antes de
chamar `addImage` (a lib não aceita só a URL do asset), contra a captura de
DOM que já resolve isso de graça.

**8.1. Correção (uso real): o cabeçalho ficava minúsculo, e as tabelas
saíam com colunas cortadas — as duas causas eram opções copiadas do
contexto errado.** A primeira versão desta decisão posicionava o cabeçalho
com `position: fixed; left: -10000px` dentro do template, e capturava o
resultado com `windowWidth: 1160` (o valor que `PgdasDashboardView` usa).
Nenhum dos dois se aplica aqui:

- `html2canvas` tem bugs conhecidos ao fotografar elementos `position:
  fixed` longe da viewport — o cabeçalho saía minúsculo e fora de lugar.
  Corrigido montando o nó em JS (`document.createElement`) e anexando
  direto no `<body>` com `position: absolute; top:0; left:0`, só durante a
  captura — o padrão que a comunidade do `html2canvas` recomenda para
  conteúdo fora da tela, e removido logo em seguida.
- `windowWidth: 1160` faz sentido em `PgdasDashboardView` porque ali a
  captura é de um documento à parte, dentro de um `<iframe>`, desenhado
  para essa largura fixa. Aqui a captura é do **próprio DOM da página**, já
  desenhado na largura real da tela — forçar uma largura menor (1160 é
  estreito para uma tabela de 8 colunas) empurrava as últimas colunas para
  fora da área visível de `.tabela-wrap` (que tem `overflow-x: auto`, pensado
  para tela estreita), e o `html2canvas` fotografa só o que está visível,
  não o que rolaria. Corrigido removendo o `windowWidth` (a captura usa a
  largura real) e desligando `overflow-x` de cada `.tabela-wrap` durante a
  captura.
- O modelo "cada bloco vira uma página nova" (`addBlocoPdf` original)
  também não se encaixava: com um cabeçalho pequeno numa página A4 inteira,
  a página 1 saía quase toda em branco. Trocado por um fluxo contínuo — o
  resultado começa logo abaixo do cabeçalho, na mesma primeira página, e só
  transborda para páginas novas se não couber.

## Risks / Trade-offs

- [Perda de fidelidade em texto secundário] O documento original tem três
  tons de tinta (`--ink`, `--ink-dim`, `--ink-faint`); `Tema` só tem `ink` e
  `muted` — dois tons. `--text-secondary` e `--text-muted` do painel caem os
  dois em `tema.muted`. → Aceito: a diferença é sutil (dois tons de cinza
  próximos) e introduzir um terceiro tom em `Tema` afetaria também a
  dashboard de apuração, fora do escopo desta mudança.
- [Tema resolvido depois da primeira pintura] Diferente da dashboard de
  apuração, que espera o `layoutDashboard` chegar junto dos dados antes de
  desenhar qualquer coisa (requisito "sem estado intermediário em que o
  painel já apareceu e ainda vai trocar de cores"), o resultado do Simulador
  só existe depois do clique em Calcular — na prática não há janela visível
  de "cor errada", porque o `GET /api/simulador/layout` já teve tempo de
  responder enquanto o usuário preenchia os 12 meses. → Mitigação: buscar o
  layout já no `onMounted` da página (junto da eventual reabertura via
  `?id=`), não no clique de Calcular, para o tema já estar pronto quando o
  resultado for revelado pela primeira vez.
- [Endpoint novo de leitura pura] `GET /api/simulador/layout` expõe um dado
  que hoje só sai por uma rota de admin (`EscritoriosView`) ou pelo payload
  por-cliente do PGDAS-D. → Aceito: é metadado de identidade visual, não
  dado fiscal ou de cliente, e a policy já é a mesma (`EscritorioUsuario`)
  de tudo mais no grupo `/api/simulador`.
- [Lógica de PDF duplicada entre Simulador e apuração] `adicionarBlocoPdf`
  (Decisão 8) é uma cópia de `addBlocoPdf`, não uma função compartilhada —
  um bug corrigido num lado não se propaga para o outro sozinho. → Aceito
  por ora, dado o Non-Goal de não tocar em `PgdasDashboardView.vue`; se a
  duplicação incomodar numa mudança futura, extrair para
  `features/identidade-escritorio/` com teste de regressão nos dois
  consumidores é o caminho natural.

## Migration Plan

1. API: endpoint `GET /api/simulador/layout` em
   `Features/Simulador/SimulacoesEndpoints.cs`.
2. Frontend: mover `temas.ts`/`temas.spec.ts` para
   `features/identidade-escritorio/`, ajustar o import em
   `PgdasDashboardView.vue`.
3. Frontend: `obterLayoutSimulador()` em `api/endpoints/simulador.ts`;
   `SimuladorView.vue` busca o layout no `onMounted`, monta o `Tema`, expõe
   `mostrarResultado`, reordena o cabeçalho, acrescenta os rótulos de
   semestre e o aviso final, aplica as variáveis de tema ao `<section
   class="resultado">` e troca as cores do gráfico para `tema.charcoal`/
   `tema.wine`.
4. Frontend: botão "Baixar PDF" (`SimuladorView.vue`), cabeçalho oculto
   (`.cabecalho-pdf`) com `tema.logo`/`tema.nome`, `adicionarBlocoPdf`
   duplicado de `PgdasDashboardView` (Decisão 8), usando `jsPDF`/
   `html2canvas` já presentes no bundle.
5. `npm run build` e os specs afetados (`SimuladorView`, `temas`) antes de
   commitar.

Rollback: reverter o commit do frontend restaura o resultado sempre visível
e nas cores neutras; reverter o da API remove o endpoint (nenhuma tabela
nova, nada para migrar de volta).

## Open Questions

- O rótulo do semestre deve ficar dentro do tema retemado (cor `wine` como
  no original, `.semester-title .num`) ou neutro? Fica dentro do tema, por
  consistência com o resto do bloco — sem indicação em contrário do usuário.
