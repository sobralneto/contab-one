## Context

O "Baixar PDF" vive em `PgdasDashboardView.vue` e depende da tela aberta: um
`iframe` com o `dashHTML`, os quatro gráficos desenhados pelo Chart.js do
documento pai e o `html2canvas` capturando `#dashPart1` e `#dashPart2`, cada um
começando numa página. Como o usuário clica depois que a tela assentou, a
animação dos gráficos já terminou quando a captura acontece. Um lote não tem
essa folga.

A visão geral (`PgdasVisaoGeralView.vue`) já lista uma linha por cliente, com
filtros de cliente e de competência aplicados no servidor. O payload da dashboard
vem de `GET /api/pgdas/clientes/{clienteId}/dashboard`, que aceita
`competenciaInicio` e `competenciaFim`, traz o leiaute do escritório e não tem
limite de taxa no grupo `/api/pgdas`.

O PDF é uma imagem rasterizada em escala 2, então custa CPU na thread principal
e memória proporcional ao número de clientes.

## Goals / Non-Goals

**Goals:**

- Gerar, sem abrir a dashboard de cada cliente, o mesmo documento do "Baixar PDF".
- Um único ZIP, com um PDF por cliente.
- Falha de um cliente não derruba o lote, e dá para refazer só os que falharam.
- Manter tudo no navegador, sem mudar a API.

**Non-Goals:**

- Exportar o demonstrativo de faturamento ou o HTML em lote.
- Juntar os clientes num único PDF.
- Mudar o conteúdo ou o leiaute do documento da dashboard.
- Gerar no servidor ou em segundo plano fora da aba.
- Seleção que atravesse filtros ou clientes fora da lista.

## Decisions

### D1. Separar a geração do PDF da view

Um módulo novo, `src/features/pgdas/dashboard/pdf.ts`, recebe da view o
`addBlocoPdf` e o desenho dos gráficos:

- `desenharGraficos(doc, dados, tema, { animar })` devolve as instâncias de `Chart`.
- `montarPdfDashboard(doc, fundo, rasterizar?)` devolve o `jsPDF`. O `rasterizar`
  é injetável, como em `demonstrativo/pdf.ts`.
- `gerarPdfDashboardForaDeTela(dados, tema)` devolve os bytes do PDF (D2).

A `PgdasDashboardView` passa a chamar os dois primeiros, e o "Baixar PDF" continua
capturando o `iframe` visível.

**Por quê:** uma só implementação da paginação. Duplicar `addBlocoPdf` é o caminho
para os dois PDFs divergirem, e a spec exige que sejam o mesmo documento.

### D2. Um `iframe` fora de tela por cliente, sem animação

Para cada cliente, `gerarPdfDashboardForaDeTela`:

1. Cria um `iframe` com `position: fixed`, `left: -10000px`, largura de 1160 px e
   `aria-hidden`, com o mesmo `srcdoc` da dashboard.
2. Aguarda o `load` e o `decode()` das imagens. O logo do tema precisa estar pronto
   antes da captura.
3. Desenha os gráficos com `animar: false`, que aplica `animation: false` às
   opções vindas de `configsGraficos`.
4. Captura com `montarPdfDashboard`.
5. Destrói os gráficos e remove o `iframe` no `finally`, mesmo em erro.

**Por quê:** reaproveita o `dashCss`, o `dashHTML` e o `configsGraficos` sem
alteração. O `iframe` isola o CSS do documento do CSS do painel, como já faz a
tela. O `animation: false` é o que garante o gráfico completo: com a animação
padrão, a captura pegaria o gráfico pela metade ou vazio.

**Alternativas:**

- Um `iframe` reaproveitado entre clientes: menos custo, mas o estado de um
  cliente poderia vazar para o seguinte.
- Abrir a rota da dashboard por cliente: lento e dependente de navegação.
- Redesenhar o PDF em vetor no `jsPDF`: arquivo menor, mas seria outro documento.

### D3. Orquestrador puro, sequencial e com dependências injetadas

Um módulo novo, `src/features/pgdas/dashboard/exportacaoLote.ts`, expõe
`exportarLote(clientes, deps, { signal, aoProgredir })`. `deps` traz `obterDados`
e `gerarPdf`, para testar sem navegador. Cada cliente passa por:

1. Ler o payload da dashboard com o período do filtro.
2. Montar os dados com `montarDadosDashboard`. `null` conta como falha, com o
   motivo "sem apuração no período".
3. Gerar o PDF.

Antes de cada cliente, verifica o `signal` e cede a thread com um `setTimeout(0)`,
para a barra de progresso pintar. O resultado traz `{ arquivos, falhas, cancelado }`.

**Por quê sequencial:** o `html2canvas` ocupa a thread principal, então paralelizar
não ganharia tempo e somaria memória e leituras simultâneas.

### D4. ZIP com `fflate`, sem recomprimir

`fflate` vira dependência direta. O ZIP sai de `zipSync(arquivos, { level: 0 })`,
só armazenando os bytes, porque o PDF já traz JPEG e recomprimir gastaria CPU sem
reduzir o tamanho.

O arquivo se chama `dashboards_pgdas_AAAA-MM-DD.zip`, com a data local. Cada PDF
se chama `dashboard_<codigo>_<slug-do-nome>.pdf`. O código é único por escritório,
mas os dois vão por `slug`, então uma função pura `nomesUnicos` acrescenta `_2`,
`_3` se a sanitização produzir nomes iguais.

**Alternativas:** o `JSZip` é maior e não traz nada que este caso use. O `fflate`
já vem no `node_modules` pelo `jspdf`.

O lote sempre entrega ZIP, mesmo com um cliente: uma regra só, e o PDF avulso já
existe na dashboard.

### D5. Seleção como conjunto de `clienteId` na view

A `PgdasVisaoGeralView` mantém um `Set` de `clienteId`. A coluna de seleção entra à
esquerda da tabela, com uma `<input type="checkbox">` em cada linha, nomeada pelo
`aria-label` com o nome do cliente. A do cabeçalho usa a propriedade
`indeterminate` para a seleção parcial.

Ao fim de cada `carregar()`, a view intersecta a seleção com `clientesAgrupados`. É
isso que faz a seleção conter só clientes visíveis.

A barra de seleção aparece entre a toolbar e a tabela, com a contagem, "Exportar
PDFs" e "Limpar seleção". Durante a geração ela mostra o progresso em uma região
`aria-live="polite"` e o botão "Cancelar".

### D6. Período vem do filtro da tela

O lote repassa `competenciaInicio` e `competenciaFim` da visão geral à leitura da
dashboard. Sem filtro, a leitura é a mesma da dashboard.

**Por quê:** quem filtrou o trimestre e exportou espera o trimestre. Os valores da
exportação ficam guardados no início dela, e os filtros ficam desabilitados
enquanto ela roda.

### D7. Teto de 100 clientes por exportação

Uma constante `LIMITE_LOTE = 100` no orquestrador. Acima dele, a barra explica o
limite e o botão fica desabilitado.

**Por quê:** todos os PDFs ficam em memória até o ZIP sair. Um teto explícito é
melhor do que a aba estourar no meio do lote.

**Medição (Chromium, banco local):** 6 clientes levaram 2 s, cerca de 340 ms por
cliente, com ZIP de 4,9 MB (cerca de 800 KB por PDF). Projetando, 100 clientes dariam
cerca de 35 s e 80 MB, o que sustenta o teto. É projeção: o banco local só tinha 6
clientes com apuração, e documentos com mais competências pesam mais.

### D8. Código carregado sob demanda

A view importa `pdf.ts` com `import()` dinâmico, ao clicar em "Exportar PDFs".
`exportacaoLote` e o `fflate` entram estáticos: a view precisa de `LIMITE_LOTE` para
desenhar a barra, e o `zipSync` isolado pesa pouco.

**Por quê:** `chart.js/auto` é pesado, e quem só consulta a visão geral não precisa
dele. Falha nesse `import()` aparece como erro da exportação, não como tela quebrada.

### D9. Resultado e nova tentativa

Com ao menos um PDF gerado, o ZIP baixa pelo mesmo padrão de `triggerDownload` da
dashboard, levado para um helper compartilhado. Ao final, uma mensagem informa
quantos foram gerados e nomeia os clientes que ficaram de fora, e a seleção passa a
ser só esses. Quando não houve falha, a seleção é limpa.

Cancelar não baixa nada e mantém a seleção. Sair da tela aborta pelo mesmo `signal`,
no `onBeforeUnmount`.

## Risks / Trade-offs

- **Tela lenta durante a geração.** Cada `html2canvas` trava a thread principal por
  instantes. → Cedemos a thread entre clientes e mostramos o progresso.
- **Memória em lote grande.** → Teto de 100 clientes (D7), a medir.
- **Aba em segundo plano.** O navegador reduz os temporizadores e a geração fica mais
  lenta, sem erro. O gráfico não depende de `requestAnimationFrame` porque está sem
  animação. → Aceito; a tarefa de teste manual confere o resultado com a aba em
  segundo plano.
- **PDF do lote diferente do avulso.** A largura do `iframe` visível varia com a
  janela, e a do lote é fixa em 1160 px. → Mesmo documento e mesma paginação. Na
  comparação, seções e valores coincidem; só os gráficos saem mais largos no lote,
  ocupando a caixa inteira.
- **Sessão expira no meio do lote.** O interceptor renova o token; se não conseguir,
  a navegação para o login desmonta a tela e aborta o lote.
- **ZIP sem senha com dados fiscais do cliente.** É o mesmo nível de exposição do PDF
  avulso na pasta de downloads. Nada sai da máquina do usuário.

## Migration Plan

Só frontend, sem migração nem mudança de API. Reverter o deploy desfaz tudo.
