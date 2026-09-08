## 1. Documento de exportação

- [x] 1.1 Criar `src/features/onboarding/exportacao/documento.ts` com a função
      que monta o HTML do documento a partir de `ClienteDto` +
      `ChecklistOnboardingClienteDto` (+ percentual/concluídas/total já
      calculados pela view — D6): cabeçalho (código, nome, percentual,
      contagem, data-hora de geração) e um bloco por grupo (título, contagem
      "x/y finalizadas", e cada tarefa com nome, status, badge 2FA, link,
      responsáveis, observação e "concluída em/por" quando existirem).
- [x] 1.2 Escrever o CSS do documento com classes prefixadas `exp-`, leiaute
      conservador (`table`/`block`, bordas, cores chapadas — ver Risks de
      design.md sobre limitações do `html2canvas`), sem depender de nenhuma
      classe de `components.css` ou `tokens.css` da aplicação.
- [x] 1.3 Tratar os casos vazios sem erro: tarefa sem link/responsável/
      observação (campo simplesmente ausente) e grupo/checklist sem tarefas
      (mensagem "sem tarefas" no lugar da lista).
- [x] 1.4 Implementar `slug()` e `nomeArquivo(codigo, nome)` no próprio módulo
      (não importar de `features/pgdas/`, ver D8) retornando
      `onboarding_<codigo>_<slug(nome)>.pdf`.
- [x] 1.5 Escrever `documento.spec.ts` (Vitest): grupos recolhidos/todos
      presentes, todos os campos condicionais aparecem quando existem e somem
      quando não, nenhum `<textarea>`/`<select>`/`<button>` no HTML gerado,
      cabeçalho com os cinco dados exigidos pela spec.

## 2. Exportador PDF (costura por blocos)

- [x] 2.1 Criar `src/features/onboarding/exportacao/pdf.ts` com a função de
      costura: recebe uma lista de blocos já rasterizados (canvas ou
      dimensões), calcula a escala única a partir da largura
      (`LARGURA_PAGINA_MM - 2*MARGEM_MM) / LARGURA_DOC_PX`, D3) e decide, por
      bloco, entre continuar na página corrente, iniciar página nova, ou
      fatiar (D4) — nunca reduzindo pela altura.
- [x] 2.2 Isolar a chamada ao `html2canvas` (um canvas por bloco: cabeçalho e
      cada grupo) atrás de uma dependência injetável, para que 2.1 seja
      testável sem `canvas` real no jsdom (ver D9).
- [x] 2.3 Escrever a função pública `exportarChecklistPdf(cliente, checklist,
      percentual, concluidas, totalTarefas)`: monta o HTML (etapa 1), anexa a
      `<div>` fora de tela (`position: fixed; left: -10000px`, largura fixa
      `LARGURA_DOC_PX`) no `body`, rasteriza e costura, salva com `pdf.save()`
      e remove a `<div>` do DOM em `finally` mesmo se a geração falhar.
- [x] 2.4 Escrever `pdf.spec.ts`: com blocos de alturas conhecidas e
      `html2canvas`/rasterização mockados, verificar que todo `addImage` usa a
      mesma largura e o mesmo `x` (nenhuma redução por altura, nenhuma
      centralização), que um bloco maior que o espaço restante mas menor que
      uma página inteira começa em página nova, e que um bloco maior que a
      página inteira é fatiado em várias páginas na largura cheia.

## 3. Integração na página de onboarding

- [x] 3.1 Adicionar o botão "Exportar PDF" em `OnboardingClienteView.vue`, no
      cabeçalho da página, visível apenas no ramo `v-else-if="checklist"`
      (nunca nos estados `semModelo` ou `checklistInexistente` — spec).
      Acessível a `EscritorioUsuario`, sem checagem de papel.
- [x] 3.2 Adicionar `exportando = ref(false)`; o clique chama
      `exportarChecklistPdf(...)` passando `cliente.value`, `checklist.value`
      e os `computed` já existentes (`percentual`, `concluidas`,
      `totalTarefas`); desabilitar o botão e trocar o rótulo para "Gerando..."
      durante a chamada, ignorando cliques repetidos enquanto `exportando` for
      `true`.
- [x] 3.3 Em caso de falha, usar o banner `erroAcao` já existente na página
      (mesmo padrão das demais ações) e garantir que o checklist carregado
      permanece intacto na tela.
- [x] 3.4 Marcar o botão com `no-print`, como os demais controles de navegação
      da página.
- [x] 3.5 Atualizar/estender `OnboardingClienteView.spec.ts`: botão presente
      com checklist carregado; ausente nos dois estados sem checklist;
      desabilitado e com rótulo "Gerando..." durante a exportação; banner de
      erro exibido quando a exportação (mockada) rejeita. Mockar o módulo de
      `features/onboarding/exportacao/` — a view não deve gerar PDF de
      verdade no Vitest.

## 4. Validação final

- [x] 4.1 Rodar `npm --prefix ContabOne.Frontend run build` (checagem de tipos
      + build) e `npm --prefix ContabOne.Frontend test` para confirmar que
      nada quebrou.
- [x] 4.2 Testar manualmente com `npm run dev`: exportar um checklist com
      grupo recolhido, tarefa com todos os campos preenchidos, tarefa "vazia",
      e um checklist longo o bastante para gerar mais de uma página — conferir
      visualmente que o conteúdo ocupa a largura inteira em todas as páginas.
