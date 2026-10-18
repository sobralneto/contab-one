## Context

A sidebar de detalhe fica em `src/views/pgdas/PgdasVisaoGeralView.vue`, num
`<aside class="sidebar-detalhe">`. Ela é fixa à direita, não tem overlay, e
fecha com Esc devolvendo o foco ao gatilho. Ao abrir, chama
`listarTodas({ clienteId })`, que pagina `GET /api/pgdas/apuracoes` até 10×100.
A sidebar mostra uma tabela operacional de competências.

O modelo a reproduzir é `Relatorio_Faturamento_2025_2026.pdf`: uma página A4
retrato, só imagem, sem camada de texto. As medidas foram tiradas da
renderização. Com margem lateral de ~8% da largura, os blocos são:

- **título:** ~22 pt, peso 800, com filete preto de ~1,5 pt;
- **quadro de identificação:** fundo `#f7f7f7` e raio ~8 px. Rótulos de
  ~7,5 pt, em caixa alta, peso 600, cinza `#777`, com espaçamento entre letras.
  Valores de ~10 pt, peso 600, quase pretos;
- **tabela:** cabeçalho no mesmo estilo dos rótulos, sobre filete preto de
  ~1,5 pt. Linhas de ~10 pt, peso 400, com zebra branco/`#fafafa` e separador
  `#e5e5e5`. A primeira coluna fica à esquerda e as duas de valor à direita. A
  coluna do ano anterior termina por volta de 62% da largura. Um filete preto
  vem antes do `TOTAL GERAL`, que é negrito;
- **nota:** ~8,5 pt, cinza-escuro, justificada, com o número em negrito;
- **local e data:** `Local:` com traço de ~22% da largura, à esquerda, e a
  data alinhada à direita;
- **espaço livre de ~20% da altura, seguido das assinaturas:** dois traços
  cinza de ~28% da largura, centrados em cada metade, com o rótulo ~9 pt em
  caixa alta, cinza, centralizado abaixo.

Hoje faltam dois dados do modelo: **data de abertura** (não existe em
`Cliente`) e **Nº da Declaração** (não existe em `ApuracaoSimples`, e o parser
descarta). O PGDAS-D traz os dois no cabeçalho do documento.

`html2canvas` e `jspdf` já são dependências, usadas na dashboard PGDAS e na
exportação do checklist de onboarding (`features/onboarding/exportacao/pdf.ts`).

## Goals / Non-Goals

**Goals:**

- Sidebar visualmente idêntica ao modelo, com todos os blocos, inclusive
  local, data e assinaturas.
- Exportar PDF (A4, uma página) e imprimir, com o mesmo conteúdo da tela.
- Data de abertura e Nº da Declaração reais, vindos do documento importado.

**Non-Goals:**

- Edição manual da data de abertura no cadastro do cliente. Pode vir numa
  change posterior; por ora só o documento a preenche.
- Escolher os anos do demonstrativo. Ficam fixos em `A-1` e `A` (decisão 3).
- Preencher local, nome ou CPF dos signatários. O modelo deixa em branco
  para preenchimento à mão.
- Mudar a dashboard do cliente ou a lista principal.
- Gerar PDF com texto selecionável. É imagem, como as outras exportações do
  painel (decisão 5).

## Decisions

### 1. Componente próprio + módulo puro de montagem

`src/features/pgdas/demonstrativo/montar.ts` exporta uma função pura,
`montarDemonstrativo(apuracoes, identidade, hoje)`, que devolve
`{ anos: [a1, a2], linhas: [{ mes, valores: [v1, v2] }] x12, totais, numeroDeclaracao, dataExtenso }`.
A view `DemonstrativoFaturamento.vue` (em `src/components/pgdas/`) só desenha.

**Por quê:** as regras (escolha dos anos, `R$ 0,00` para mês sem apuração ou
sem movimento, soma, número da declaração mais recente, data por extenso) são
testáveis em Vitest sem DOM. É o mesmo corte de `features/onboarding/exportacao/documento.ts`.
**Alternativa:** computeds dentro da view. Rejeitada porque a view já é longa
e as regras ficariam testáveis só pela renderização.

### 2. Dados vêm da listagem já carregada, enriquecida

A sidebar continua chamando `listarTodas({ clienteId })`, sem filtro de
competência, como já faz. `ApuracaoListaDto` ganha `clienteDataAbertura` e
`numeroDeclaracao`.

**Por quê:** nenhuma chamada nova. A listagem já carrega a identidade do
cliente (`clienteCodigo`, `clienteCnpj`), e a data de abertura é mais um campo
dessa identidade.
**Alternativa:** usar `GET /api/pgdas/clientes/{id}/dashboard`. Rejeitada
porque traz tributos, segregação e layout que o demonstrativo não usa, e
mudaria o contrato da dashboard.

### 3. Anos: o da última competência e o anterior

`A` é o ano da competência mais recente do cliente, não o ano civil corrente.
Assim, um cliente cujo último PGDAS-D é de dezembro de 2025 gera "2024 × 2025",
que é o demonstrativo útil, e não um "2025 × 2026" com a coluna nova zerada.
Esse comportamento reproduz o modelo (2025 × 2026 com último mês em agosto de
2026).

### 4. Documento "papel" com tokens próprios

O documento usa tokens novos em `tokens.css`, sob o prefixo `--papel-*`
(`--papel-fundo`, `--papel-texto`, `--papel-texto-suave`, `--papel-rotulo`,
`--papel-quadro`, `--papel-zebra`, `--papel-filete`, `--papel-filete-forte`,
`--papel-assinatura`). Esses tokens **não são redefinidos** no tema escuro.

**Por quê:** a regra do repositório proíbe cor literal em componente, e o
documento tem de continuar branco no tema escuro. Por isso o modelo é
"papel", e o PDF gerado também é branco.
**Alternativa:** reaproveitar `--surface-card` e `--text-primary`. Rejeitada
porque escurecem no tema escuro, o que quebra a promessa de "idêntico ao PDF"
e deixa a tela diferente do arquivo exportado.

A fonte é a `--font-family` do painel (Plus Jakarta Sans). O modelo usa uma
sans geométrica de aparência equivalente. Não entra fonte nova; se a revisão
visual reprovar, o ajuste é a primeira pendência das Open Questions.

O documento tem largura fixa de **794 px** (A4 a 96 dpi) e proporção
`210 / 297`. Na sidebar (`min(820px, 94vw)`), ele aparece como uma folha com
sombra sutil, centralizada. Em telas estreitas, a folha é escalada com
`transform: scale()` para caber, e nunca reflui o leiaute: reflow faria a tela
divergir do PDF.

### 5. Exportar PDF: rasterizar a folha inteira, uma página

`exportarDemonstrativoPdf(el, nomeArquivo)`, em
`features/pgdas/demonstrativo/pdf.ts`, faz um `html2canvas(el, { scale: 2, backgroundColor: <--papel-fundo resolvido>, windowWidth: 794 })`
e desenha a imagem com `jsPDF('p','mm','a4').addImage(..., 0, 0, 210, 297)`.

A folha já tem a proporção exata do A4, então não há costura nem paginação.
O elemento é clonado num contêiner fora de tela, sem `transform`, como faz
`exportarChecklistPdf`. Isso evita que a escala de tela estreita e o
`overflow` da sidebar entrem na captura.

**Alternativa:** gerar o PDF vetorial com a API de texto do jsPDF. Rejeitada
nesta change porque duplicaria o leiaute em coordenadas de mm, criando uma
segunda fonte de verdade para o mesmo documento. As outras exportações do
painel também são imagem.

### 6. Imprimir: `window.print()` + `@media print`

Uma folha de estilo de impressão global e mínima, em
`src/assets/styles/impressao.css`, importada em `src/style.css` ao lado de
`tokens.css` e `components.css`, esconde tudo e mostra só
o elemento marcado com `.imprimivel`, com `@page { size: A4 portrait; margin: 0 }`.
O documento recebe essa classe; a barra de ações e a moldura da sidebar não.
O `transform` de escala é anulado em `@media print`.

**Por quê:** usa a impressão nativa, que também oferece "Salvar como PDF" do
navegador, e não precisa de iframe nem de janela nova.
**Alternativa:** abrir uma janela com o HTML do documento. Rejeitada porque
seria preciso copiar estilos e fontes e o pop-up pode ser bloqueado.

### 7. Extração e persistência dos dois campos

- **Parser:** `parseApuracao.ts` passa a capturar
  `/Data de abertura no CNPJ:\s*(\d{2}\/\d{2}\/\d{4})/i` e
  `/N[ºo°]\s*da\s*Declara[çc][ãa]o:\s*(\d+)/i`, gravando em `_abertura` e
  `numeroDeclaracao` da `Competencia`. Os rótulos exatos são conferidos contra
  um extrato e uma declaração reais, e as fixtures ganham essas linhas.
- **Gravação:** `GravarApuracoesRequest.DataAberturaCliente` (`DateOnly?`) e
  `ApuracaoRequest.NumeroDeclaracao` (`string?`, só dígitos, ≤ 30). O
  validador recusa o resto.
- **Modelo:** `Cliente.DataAbertura` (`DateOnly?`) e
  `ApuracaoSimples.NumeroDeclaracao` (`string?`, `HasMaxLength(30)`), numa
  migration aditiva.
- **Regra de escrita da data:** sobrescreve quando informada. Data de abertura
  não muda; um valor novo vindo do documento corrige uma leitura anterior
  errada. Ausente no pedido, mantém a gravada. O agente NFS-e não escreve esse
  campo.

**Privacidade:** os dois são metadados de identificação. O PDF do PGDAS-D
continua sem sair do navegador; só o valor extraído vai à API, como já
acontece com faturamento e tributos.

### 8. Barra de ações da sidebar

O cabeçalho atual (código, nome, CNPJ, fechar) é substituído por uma barra
fina com o título curto "Demonstrativo de faturamento" e os botões
`btn-secondary` "Exportar PDF" (`FileDown`) e "Imprimir" (`Printer`), mais o
`btn-icon` de fechar (`X`). A identidade do cliente passa a estar só no
quadro do documento, como no modelo. Ícones do `lucide-vue-next` com
`aria-hidden` ao lado do texto. O foco inicial continua no botão de fechar,
e Esc continua fechando.

## Risks / Trade-offs

- **[PDF em imagem]** O texto não é selecionável e o arquivo fica maior →
  `scale: 2` com JPEG 0,92, que dá ~300–600 KB, aceitável para uma página.
  Vetorial fica para depois, se pedirem.
- **[Rótulos do PGDAS-D variam entre extrato e declaração]** → regexes
  tolerantes (`Nº`/`No`/`N°`) e fixtures dos dois leiautes. Campo não achado
  vira vazio, nunca erro.
- **[Clientes antigos sem os campos]** Mostram `—` na data de abertura e a nota
  sem número. Reimportar um documento preenche os dois. O comportamento está
  documentado nos cenários da spec.
- **[`html2canvas` e CSS moderno]** O documento usa só bloco, grid simples,
  bordas e fundos, sem `filter` nem `backdrop`. O mesmo cuidado já foi
  registrado na exportação do onboarding.
- **[Impressão e o resto do app]** O `@media print` global pode afetar outra
  tela que um dia imprima → ele age só quando existe um `.imprimivel` na
  página (`body:has(.imprimivel)`); fora disso, a impressão continua como
  hoje.
- **[Sobreposição com `importacao-pgdas-em-lote`]** As duas mudam o payload de
  gravação e o parser → os campos novos são aditivos e opcionais. Quem
  aplicar por último resolve o merge nos tipos.

## Migration Plan

1. Migration aditiva (`AddDemonstrativoFaturamento`): duas colunas nulas.
   Roda no startup, sem backfill.
2. Deploy da API antes do frontend. A API aceita pedidos sem os campos novos,
   e o frontend antigo continua funcionando.
3. Deploy do frontend.
4. **Rollback:** reverter o frontend devolve a sidebar antiga. As colunas
   ficam sem uso e não precisam ser removidas.

## Open Questions

- **Fonte:** a revisão lado a lado com o modelo pode pedir outra fonte. O
  modelo parece Inter, que já é o segundo da pilha `--font-family`. Se for
  preciso, o documento passa a usar `'Inter', var(--font-family)`.
- **Edição manual da data de abertura** no cadastro do cliente, para quem não
  vai reimportar: fica para outra change, se for pedida.
