## Context

A página `OnboardingClienteView.vue` já carrega tudo o que o PDF precisa: o
`ClienteDto` (código e nome) e o `ChecklistOnboardingClienteDto` (grupos,
tarefas, status, observação, responsáveis, `concluidoEm`/`concluidoPorNome`).
Nada de novo precisa vir da API.

O repositório já tem um exportador para PDF em produção: o "Baixar PDF" da
dashboard do PGDAS-D (`views/pgdas/PgdasDashboardView.vue` +
`features/pgdas/dashboard/documento.ts`). Ele estabelece o padrão desta casa —
um módulo que monta um **documento HTML autônomo** a partir dos dados, e uma
função que rasteriza esse documento com `html2canvas` e o costura em páginas A4
com `jsPDF`. `jspdf@^4.2.1` e `html2canvas@^1.4.1` já estão no `package.json`.

Ele também estabelece o defeito que este change não pode repetir. Em
`addBlocoPdf`, quando o bloco é mais alto que a página, há o ramo:

```
const fator = dispH / imgH
if (fator >= 0.55) { imgW = pw * fator; imgH = dispH; pdf.addImage(img, ..., (pw - imgW) / 2, ...) }
```

Reduzir pela **altura** encolhe junto a **largura** (`imgW = pw * fator`) e ainda
centraliza — resultado: faixas brancas laterais, e blocos diferentes do mesmo PDF
saindo em escalas diferentes. É exatamente o que o requisito "o conteúdo ocupa a
largura inteira" proíbe. Esse ramo não é reaproveitado aqui.

A página tem estados que não podem virar PDF: grupos recolhidos (`v-show`),
`textarea` de observação, `select` de responsáveis, checkbox clicável, botão de
recolher, banner de erro. Alguns já carregam `no-print` — herança de uma
tentativa de impressão via CSS que nunca foi levada adiante (não existe `@media
print` no repositório).

## Goals / Non-Goals

**Goals:**

- Um botão na página de onboarding do cliente que baixa o checklist em PDF.
- Conteúdo ocupando a largura útil da página A4 em **todas** as páginas, na
  **mesma** escala, para qualquer volume de conteúdo.
- Documento completo e independente do estado da tela (grupos recolhidos entram).
- Quebra de página entre blocos sempre que possível.
- Zero mudança em API, banco ou agentes.

**Non-Goals:**

- PDF com texto selecionável/pesquisável. O documento sai rasterizado, como o do
  PGDAS-D. Texto vetorial exigiria reescrever o leiaute na API de desenho do
  jsPDF — trabalho desproporcional para o ganho, e divergente do padrão da casa.
- Geração no servidor. Contraria a arquitetura (o painel monta o documento no
  navegador) e não traz nada: o dado já está no cliente.
- Exportar vários clientes de uma vez, ou exportar em HTML como o PGDAS-D faz.
- Reformar `addBlocoPdf` do PGDAS-D. Ele tem o mesmo defeito, mas alterá-lo muda
  um documento em produção que ninguém pediu para mudar — fica registrado como
  candidato a change própria.

## Decisions

### D1 — Documento de exportação próprio, não foto da tela

O PDF é montado de um HTML gerado a partir do checklist
(`features/onboarding/exportacao/documento.ts`), no molde de
`features/pgdas/dashboard/documento.ts` — e **não** rasterizando a `.dashboard-card`
da própria view.

*Por quê:* fotografar a view obrigaria a abrir todos os grupos antes de exportar
e restaurar depois (mexe no que o usuário está vendo), esconder cada controle
interativo com CSS de impressão, e trocar `textarea`/`select` por texto — três
correções frágeis, cada uma quebrável por qualquer ajuste futuro de leiaute. O
documento próprio decide o que entra, é testável sem DOM da view, e não depende
do estado de `gruposAbertos`.

*Alternativa considerada:* `window.print()` + `@media print`. Sai barato, mas
entrega o controle do resultado ao navegador: margens, cabeçalho/rodapé do
browser e paginação variam por navegador e por configuração do usuário, e o
requisito de largura não teria como ser garantido. Descartada.

### D2 — Renderização em largura fixa, fora da tela

O documento é montado numa `<div>` anexada ao `body` com
`position: fixed; left: -10000px; top: 0; width: LARGURA_DOC px`, rasterizada
bloco a bloco, e removida no `finally`.

`LARGURA_DOC = 1160px` — o mesmo `windowWidth` que o exportador do PGDAS-D já
usa, então o CSS do documento é escrito para uma largura conhecida e o resultado
não depende do tamanho da janela de quem exporta. Dois usuários com monitores
diferentes geram PDFs idênticos.

*Alternativa considerada:* `<iframe srcdoc>`, como a pré-visualização do PGDAS-D.
Lá o iframe existe porque o documento é **exibido** na tela e precisa de
isolamento de CSS; aqui ele nunca é exibido, e o iframe só acrescentaria a espera
pelo `load`. A `<div>` fora de tela herda o CSS da aplicação, o que se resolve
escrevendo o CSS do documento com classes próprias e prefixadas.

### D3 — Escala única, derivada só da largura

```
escala = (LARGURA_PAGINA_MM - 2 * MARGEM_MM) / LARGURA_DOC_PX
```

Uma constante para o documento inteiro. Todo bloco entra no PDF com
`largura = LARGURA_PAGINA_MM - 2 * MARGEM_MM` e
`altura = canvas.height / canvas.width * largura`, sempre em `x = MARGEM_MM`.

A altura **nunca** participa do cálculo de escala. Bloco que não cabe é
paginado (D4), nunca reduzido. É essa regra, e só ela, que satisfaz o requisito
de largura — e é a diferença essencial em relação a `addBlocoPdf`.

A4 retrato, `210 × 297 mm`, `MARGEM_MM = 8` dos quatro lados: o conteúdo sai com
`194 mm` úteis. Margem uniforme e não-zero porque impressoras domésticas cortam
a borda; o requisito admite margem, o que ele proíbe é sobra irregular.

### D4 — Paginação por blocos, com empacotamento

Cada bloco (`#exp-cabecalho`, e um `#exp-grupo-<n>` por grupo) vira um canvas
próprio. A costura mantém um cursor `y` na página corrente:

1. bloco cabe em `alturaUtil - y` → desenha em `y`, avança o cursor;
2. não cabe no que resta mas cabe em uma página inteira → `addPage()`, desenha
   no topo;
3. não cabe nem em página inteira → `addPage()` se a corrente já tem conteúdo, e
   então fatia: cada fatia é o mesmo `addImage` deslocado por `-offset` dentro de
   um `<div>` de recorte, uma página por fatia, sempre na largura cheia.

*Por quê um canvas por bloco:* com um canvas único do documento inteiro, toda
quebra é cega — cai onde a régua mandar, no meio de uma tarefa. Com um canvas por
grupo, a quebra natural é entre grupos, e o fatiamento (caso 3) só acontece no
grupo que sozinho passa de 281 mm úteis — dezenas de tarefas.

*Custo aceito:* N+1 chamadas de `html2canvas` em vez de uma. Cada uma custa
dezenas de milissegundos numa página cujo conteúdo já está em memória; o botão
mostra "Gerando..." e desabilita durante a operação.

### D5 — `scale: 2` no html2canvas

Mesmo valor do PGDAS-D. Rasterizar 1160px na largura de 194 mm significa ~152 dpi
em `scale: 1` — texto de 12px sai borrado na impressão. Com `scale: 2`, ~304 dpi,
que imprime limpo. JPEG a 0.92, como no PGDAS-D, mantém o arquivo em ordem de
grandeza aceitável para anexo de e-mail.

### D6 — Fonte de verdade é o estado da página, não a API

O documento é montado do `checklist.value` em memória, incluindo o percentual
**recalculado no cliente** (`percentual`, `concluidas`, `totalTarefas` — os mesmos
`computed` que alimentam o círculo e a barra), e não do `percentualConclusao`
devolvido pelo servidor.

*Por quê:* a marcação de tarefa é otimista e a observação é salva com `debounce`
de 550 ms. Ler do servidor faria o PDF divergir do que a tela mostra a quem
acabou de marcar uma tarefa ou digitar uma observação — e a spec exige que o
documento reflita o que o usuário está vendo. Efeito colateral aceito e explícito:
uma marcação que o servidor venha a rejeitar já terá saído no PDF; a página faz
rollback e o usuário reexporta.

### D7 — O botão vive no cabeçalho da página, junto do link de voltar

Aparece apenas no ramo `v-else-if="checklist"` do template — os estados
`semModelo` e `checklistInexistente` não têm o que exportar, e o requisito manda
não oferecer a ação neles. Ganha `no-print` como os demais controles, por
coerência com o que já está lá. Sem verificação de papel: `EscritorioUsuario`
exporta.

`exportando: ref<boolean>` desabilita o botão e troca o rótulo para "Gerando...",
espelhando `exportandoPdf` do PGDAS-D. Falha reaproveita o banner `erroAcao` que
a página já tem — não há por que inventar um segundo canal de erro.

### D8 — Nome do arquivo

`onboarding_<codigo>_<slug(nome)>.pdf`. O código entra porque é o identificador
que o escritório usa, e o slug do nome porque é o que se lê na pasta de
downloads. A função `slug` de `features/pgdas/dashboard/documento.ts` (normaliza
NFD, remove diacríticos, colapsa em `_`) é replicada no módulo novo em vez de
importada: puxar um símbolo interno de `features/pgdas/` para dentro de
`features/onboarding/` criaria um acoplamento entre duas ferramentas que não têm
relação de domínio nenhuma. Oito linhas duplicadas custam menos que essa aresta.

### D9 — Superfície de teste

- `documento.spec.ts` (Vitest, sem DOM de canvas): o HTML gerado contém todos os
  grupos e tarefas, traz link/2FA/responsáveis/observação/`concluidoEm` quando
  existem e os omite quando não, não contém `<textarea>`, `<select>` nem
  `<button>`, e o cabeçalho traz código, nome, percentual, contagem e data-hora.
  É aqui que quase toda a spec fica coberta.
- `pdf.spec.ts`: a função de costura recebe uma lista de blocos com alturas
  conhecidas (rasterização injetada como dependência, `html2canvas` mockado) e o
  teste afirma sobre as chamadas de `addImage`/`addPage` — que todo `addImage`
  usa a mesma largura e o mesmo `x`, e que um bloco que não cabe no resto da
  página começa em página nova. Esse é o teste que guarda o requisito de largura;
  ele falha se alguém reintroduzir o encolhimento por altura.
- `OnboardingClienteView.spec.ts`: botão presente com checklist, ausente nos dois
  estados sem checklist, desabilitado durante a geração, banner de erro na falha.
  O módulo de exportação é mockado — a view não gera PDF de verdade no Vitest.

`jsdom` não implementa `canvas`, então `html2canvas` nunca roda em teste; daí a
injeção de dependência em vez de chamada direta dentro da função de costura.

## Risks / Trade-offs

- **`html2canvas` renderiza CSS moderno de forma incompleta** (`gap` em alguns
  contextos, gradientes cônicos, `mask`) → o CSS do documento de exportação usa
  apenas leiaute conservador: `table`/`block`, `border`, `padding`, cores chapadas.
  O visual do documento é uma versão sóbria da tela, não uma cópia dela — o
  círculo de progresso em SVG, por exemplo, vira barra e número.
- **CSS da aplicação vazando na `<div>` fora de tela** → todas as classes do
  documento são prefixadas `exp-`, e o bloco de estilo é injetado com seletores
  descendentes a partir do contêiner raiz. Testado pelo `documento.spec.ts`
  indiretamente (o HTML não usa classe alguma da aplicação).
- **PDF pesado com checklists grandes** (`scale: 2` + JPEG por grupo) → um
  checklist real tem dezenas de tarefas em poucos grupos; o custo cresce com o
  número de grupos, não de tarefas. Se virar problema, `scale` é uma constante
  num só lugar.
- **Documento rasterizado não é pesquisável nem acessível a leitor de tela** →
  aceito conscientemente (Non-Goals). O checklist acessível continua sendo a
  página, que não muda.
- **Fatiamento (caso 3 de D4) pode cortar uma tarefa ao meio** → só ocorre em
  grupo com altura acima de uma página inteira, e a spec admite explicitamente a
  quebra nesse caso. A alternativa — paginar por tarefa em vez de por grupo —
  multiplicaria as chamadas de `html2canvas` para resolver um caso de borda.
- **O `addBlocoPdf` do PGDAS-D continua com o defeito de largura** → fora de
  escopo por decisão (Non-Goals), registrado aqui para não se perder.
