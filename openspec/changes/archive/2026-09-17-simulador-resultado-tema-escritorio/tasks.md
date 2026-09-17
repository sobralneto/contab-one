## 1. API — layout do escritório

- [x] 1.1 Criar `ObterLayoutAsync` em `ContabOne.Api/Features/Simulador/SimulacoesEndpoints.cs`: `GET /layout`, escopo `TenantContext.EscritorioId`, devolve `{ layoutDashboard: db.Escritorios.Where(e => e.Id == escritorioId).Select(e => e.LayoutDashboard.ToString()) }` — 403 se não houver escritório em foco (mesmo padrão de `EscopoOuNull` dos demais handlers)
- [x] 1.2 Registrar `group.MapGet("/layout", ObterLayoutAsync)` em `MapSimulacoesEndpoints()` — confirmar que não colide com `GET /{id:guid}` (constraint de GUID já resolve)
- [x] 1.3 Teste de endpoint: `GET /api/simulador/layout` devolve o `layoutDashboard` do escritório da sessão; dois escritórios com leiautes diferentes recebem valores diferentes (isolamento)

## 2. Frontend — mover o módulo de paletas para fora de `features/pgdas/`

- [x] 2.1 Mover `src/features/pgdas/dashboard/temas.ts` e `temas.spec.ts` para `src/features/identidade-escritorio/temas.ts`/`.spec.ts`, conteúdo idêntico
- [x] 2.2 Ajustar o import em `PgdasDashboardView.vue` para o novo caminho
- [x] 2.3 Rodar `temas.spec.ts` e os specs de `PgdasDashboardView` (se existirem) para confirmar que nada quebrou com a mudança de pasta

## 3. Frontend — obter o layout do escritório no Simulador

- [x] 3.1 Criar `obterLayoutSimulador()` em `src/api/endpoints/simulador.ts`, chamando `GET /api/simulador/layout`
- [x] 3.2 Em `SimuladorView.vue`, buscar o layout no `onMounted` (em paralelo com a eventual reabertura via `?id=`), montar `const tema = ref<Tema>(temaPorCodigo(...))` — layout desconhecido ou erro na chamada cai no tema neutro (`temaPorCodigo` já trata isso)

## 4. Frontend — ocultar o resultado até calcular

- [x] 4.1 Criar `const mostrarResultado = ref(false)` em `SimuladorView.vue`
- [x] 4.2 Envolver a `<section class="resultado">` num `v-if="mostrarResultado"`
- [x] 4.3 `calcularImposto()` passa a setar `mostrarResultado.value = true` antes de rolar a tela até `resultadoEl` (usar `nextTick` se o `scrollIntoView` precisar do elemento já montado)
- [x] 4.4 No `onMounted` que reabre uma simulação salva (`?id=...`), setar `mostrarResultado.value = true` também — a reabertura já revela o resultado, sem exigir o clique

## 5. Frontend — reordenar e completar a estrutura do resultado

- [x] 5.1 Em `.resultado-cabecalho`, mover o parágrafo de identificação (`nome`/`cnpjMascarado`) para ANTES do `<h2>` do anexo e do `<p class="anexo-desc">` — ordem: identificação, título do anexo, descrição do anexo
- [x] 5.2 Acrescentar um rótulo de semestre acima de cada tabela: "1º Semestre — 1º ao 6º mês de atividade" e "2º Semestre — 7º ao 12º mês de atividade" (usar o `semestre.rotulo`/índice já calculado em `semestres` para diferenciar 1º/2º, sem hardcode duplicado)
- [x] 5.3 Acrescentar, como último elemento do `<section class="resultado">`, depois do `.card-painel` do gráfico, um `<p>` centralizado com `<small>Simulação de caráter estimativo · valores em centavos, sem arredondamento · não substitui apuração oficial via PGDAS-D</small>`

## 6. Frontend — tema do escritório aplicado ao resultado

- [x] 6.1 Criar um `computed` `temaVars` em `SimuladorView.vue` mapeando `tema.value` para as variáveis do design system: `--surface-page`→`bg`, `--surface-card`/`--surface-header`→`card`, `--border`→`line`, `--text-primary`→`ink`, `--text-secondary`/`--text-muted`→`muted`, `--accent`→`wine`, `--accent-suave`→`soft`, `--accent-gradient`→`linear-gradient(135deg, wine, wineDark)` (design.md, decisão 2) — **não** sobrescrever `--erro`/`--erro-suave`/`--atencao`/`--atencao-suave` (decisão 3)
- [x] 6.2 Ligar `temaVars` via `:style` no `<section class="resultado">`
- [x] 6.3 Trocar as cores do gráfico (`chartData`): faturamento usa `tema.value.charcoal`, imposto usa `tema.value.wine`, eixos/grade usam `tema.value.muted`/`tema.value.line` diretamente — sem `getComputedStyle`/`corDoToken` dentro do bloco retemado (design.md, decisão 4)

## 7. Testes e verificação

- [x] 7.1 Atualizar `SimuladorView.spec.ts`: resultado ausente do DOM na abertura; aparece ao clicar em "Calcular imposto estimado"; aparece já visível ao reabrir via `?id=`; permanece visível e recalcula ao editar um mês depois de revelado
- [x] 7.2 Teste de ordem: identificação aparece antes do título/descrição do anexo no cabeçalho do resultado
- [x] 7.3 Teste dos rótulos de semestre e do aviso final (texto exato, `<small>`, é o último elemento do resultado)
- [x] 7.4 Teste do tema: mockar `GET /api/simulador/layout` devolvendo `Lj`, calcular, e verificar que o `<section class="resultado">` recebe as variáveis de cor da paleta L&J (`tema.wine` etc. em `style`) — e que `--erro`/`--atencao` não são sobrescritas
- [x] 7.5 Rodar `npm --prefix ContabOne.Frontend run build`, `dotnet test --filter "FullyQualifiedName~Simulador"` e `npm test` antes de commitar

## 8. Correção pós-revisão: cartão do cabeçalho e ordem CNPJ/nome

> A revisão apontou que o cabeçalho (identificação + anexo) não tinha estilo
> de cartão nenhum, e que a identificação mostrava "Nome · CNPJ" — o pedido
> original era CNPJ antes do nome, ambos legíveis, dentro de um cartão.

- [x] 8.1 Aplicar a classe `card-painel` em `.resultado-cabecalho`, para o cabeçalho ganhar fundo/borda/raio do design system (que já retemam sozinhos via `temaVars`)
- [x] 8.2 Trocar a ordem de exibição para CNPJ antes do nome (`[cnpjMascarado, nome]`)
- [x] 8.3 Aumentar a legibilidade da linha de identificação: `font-size` de 12px para 14px, `font-weight: 600`, cor de `--text-muted` para `--text-primary`
- [x] 8.4 Atualizar `SimuladorView.spec.ts` para cobrir a classe `card-painel` no cabeçalho e a ordem CNPJ antes do nome
- [x] 8.5 Rodar `npm --prefix ContabOne.Frontend run build` e `SimuladorView.spec.ts` — 15/15 verdes

## 9. Correção pós-revisão: destaque de última linha/coluna nas tabelas semestrais

> Comparando com o documento original (`tr.row-imposto`, `.col-total`), a
> tabela entregue não destacava nem a linha do Imposto estimado (DAS) nem a
> coluna de subtotal — as duas apareciam iguais às demais linhas/colunas.

- [x] 9.1 Adicionar a classe `linha-imposto` na `<tr>` de "Imposto estimado (DAS)" em cada tabela semestral
- [x] 9.2 Estilizar `.linha-imposto td` com `color: var(--accent)`, `font-weight: 700` e `background: var(--accent-suave)` — a mesma cor de acento retemada pelo leiaute do escritório, não uma cor fixa
- [x] 9.3 Estilizar `.col-subtotal` (cabeçalho e corpo, já usado na última coluna) com `background: var(--accent-suave)` e `color: var(--accent)`, no lugar do `--surface-header` neutro
- [x] 9.4 Atualizar `SimuladorView.spec.ts`: última linha do `tbody` tem a classe `linha-imposto`; última célula de cada linha (e do cabeçalho) tem `col-subtotal`
- [x] 9.5 Rodar `npm --prefix ContabOne.Frontend run build` e `SimuladorView.spec.ts` — 16/16 verdes

## 10. Baixar PDF do resultado, com logo e nome do escritório

> Pedido do usuário no uso real: um botão para gerar o PDF do resultado,
> trazendo a logo e o nome do escritório como no documento original
> (design.md, decisão 8 — substitui o Non-Goal de exportação da v1).

- [x] 10.1 Botão "Baixar PDF" em `.view-header .header-actions`, `v-if="mostrarResultado"`, desabilitado enquanto `exportandoPdf`
- [x] 10.2 Bloco `.cabecalho-pdf` fora da viewport (`position: fixed; left: -10000px`), com `tema.logo`/`tema.nome`, só para o `html2canvas` capturar — nunca visível na tela
- [x] 10.3 `adicionarBlocoPdf` em `SimuladorView.vue` (duplicado de `PgdasDashboardView.addBlocoPdf`, não extraído — design.md, decisão 8 e o Non-Goal de não tocar em `PgdasDashboardView.vue`): captura via `html2canvas`, divide em páginas A4 com `jsPDF`
- [x] 10.4 `baixarPdf()`: monta o PDF com o cabeçalho de marca primeiro, depois o `<section class="resultado">`, salva como `simulacao_simples_nacional_<nome-em-slug>.pdf`
- [x] 10.5 Testes em `SimuladorView.spec.ts` com `html2canvas`/`jspdf` mockados: botão só aparece com resultado visível; clicar gera o PDF com 2 imagens (cabeçalho + resultado, nunca o formulário de entrada) e nome de arquivo correto
- [x] 10.6 Rodar `npm --prefix ContabOne.Frontend run build` e `SimuladorView.spec.ts` — 18/18 verdes

## 11. Correção pós-revisão: PDF saía com o cabeçalho minúsculo e as tabelas cortadas

> O usuário testou o PDF gerado: o cabeçalho (logo + nome) saiu minúsculo
> num canto, com o resto da primeira página em branco, e as tabelas
> semestrais e o gráfico saíram com as últimas colunas/barras cortadas.

- [x] 11.1 Trocar `.cabecalho-pdf` (elemento fixo no template, `position: fixed; left: -10000px`) por um nó criado em JS e anexado direto no `<body>` (`position: absolute; top:0; left:0`) só durante a captura — `html2canvas` tem bugs conhecidos ao fotografar elementos `position: fixed` longe da viewport, causa provável do cabeçalho sair minúsculo e fora de lugar
- [x] 11.2 Esperar a logo carregar antes de capturar (`aguardarImagem`, com timeout de 300ms — nunca trava a exportação por uma imagem lenta ou, em teste, que nunca carrega)
- [x] 11.3 Remover `windowWidth: 1160` da captura do resultado — valor copiado de `PgdasDashboardView` (que fotografa um documento à parte, num iframe, desenhado para 1160px); aqui a captura é do DOM real da página, e forçar uma largura menor que a real fazia a tabela de 8 colunas estourar e as últimas colunas saírem cortadas
- [x] 11.4 Desligar `overflow-x: auto` de cada `.tabela-wrap` antes de capturar (`overflowX = 'visible'`, restaurado depois) — sem isso, o `html2canvas` fotografa só o trecho visível da tabela, não o conteúdo que rolaria
- [x] 11.5 Trocar o modelo "cada bloco vira página nova" por um fluxo contínuo: o cabeçalho fica no topo da página 1, e o resultado começa logo abaixo dele, na MESMA página — página inteira em branco só porque o cabeçalho é menor que uma folha A4 era o outro sintoma relatado
- [x] 11.6 Testes novos em `SimuladorView.spec.ts`: `.tabela-wrap` fica com `overflow-x: visible` durante a captura e volta ao valor original depois; nenhuma chamada ao `html2canvas` usa `windowWidth`
- [x] 11.7 Rodar `npm --prefix ContabOne.Frontend run build` e `SimuladorView.spec.ts` — 20/20 verdes
