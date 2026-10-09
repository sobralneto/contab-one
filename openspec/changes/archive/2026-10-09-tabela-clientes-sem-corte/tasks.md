## 1. Largura e quebra de linha

- [x] 1.1 Em `ContabOne.Frontend/src/views/ClientesView.vue`, remover `max-width: 1200px` de `.clientes-view` (a view passa a ocupar a largura da área de conteúdo)
- [x] 1.2 Acrescentar `white-space: nowrap` a `.col-cnpj`, `.col-escritorio` e `.col-data` (`.col-regime` já tem); deixar `.col-nome` sem `nowrap`
- [x] 1.3 Remover as larguras fixas (`width: 140px`, `100px`) de `.col-cnpj` e `.col-data` (o `nowrap` já dá o piso); dar `min-width: 220px` ao nome para que, com o cartão rolando, ele não colapse em 3–4 linhas

## 2. Coluna de ações nunca cortada

- [x] 2.1 Em `ClientesView.vue` (CSS scoped), dar ao `.table-card` desta view `overflow-x: auto` — com comentário dizendo que é layout local, não chrome, e citando o precedente de `ResultadoSimulacao.vue`
- [x] 2.2 ~~`min-width` na `.data-table`~~ — dispensado: medido no navegador, o piso natural da tabela (colunas `nowrap`) já é o certo e varia com o papel (≈1090px escritório, ≈1320px admin); um número fixo erraria para um dos dois
- [x] 2.3 Garantir que a coluna de ações não seja espremida (`.col-actions` já é `nowrap`; não usar `display:flex` em `<td>`) — confirmado pelo E2E
- [x] 2.4 Confirmar que `components.css` (`.table-card` compartilhado) **não** foi alterado

## 3. Verificação

- [x] 3.1 Conferir visualmente em janela larga (≈1920px) e em janela estreita (≈1100px), com perfil de escritório e de administrador (coluna Escritório): CNPJ/escritório/regime/data em uma linha, botões inteiros, rolagem horizontal só na janela estreita
- [x] 3.2 Conferir com cliente de razão social longa (nome quebra, resto da linha intacto) e com cliente inativo (botão Reativar no lugar de Inativar)
- [x] 3.3 Acrescentado em `ContabOne.Frontend/e2e/clientes.spec.ts`: janela larga (botão dentro do cartão, sem rolagem) e janela estreita (`overflow-x` auto/scroll — falha no CSS antigo — e botão alcançável); os testes apagam o cliente que criam (`excluirClientePorCodigo` em `helpers.ts`)
- [x] 3.4 Rodar `npm --prefix ContabOne.Frontend run build` (typecheck) e `npm test` na raiz — `ClientesView.spec.ts` deve seguir verde
