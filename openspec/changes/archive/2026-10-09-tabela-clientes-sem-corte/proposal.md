## Why

Na tela `/clientes` a tabela é mais larga que o cartão que a contém e o excesso é cortado: os botões de ícone da última coluna (onboarding, editar, inativar, excluir) ficam parcialmente ou totalmente ocultos, e o usuário não tem como alcançá-los. A causa é a soma de duas regras: a view limita a largura em `max-width: 1200px` e o `.table-card` compartilhado usa `overflow: hidden` — o que passa do cartão simplesmente some, sem barra de rolagem.

Ao mesmo tempo, a tabela é estreita demais para o conteúdo: sobra quebra de linha em dados que deveriam ficar numa linha só (CNPJ partido em `07.467.651/0001-` / `35`, nome do escritório em duas linhas), o que alonga as linhas e dificulta a leitura.

## What Changes

- A tela de clientes deixa de limitar a largura a 1200px e passa a ocupar toda a largura útil da área de conteúdo, para a tabela ter espaço onde antes quebrava linha.
- CNPJ, escritório (visão admin), regime e data de atualização deixam de quebrar linha: cada um fica numa linha só. O **nome** do cliente continua podendo quebrar — é o único texto de comprimento imprevisível, e é ele que absorve a sobra de largura.
- A coluna de ações nunca é cortada: se a janela for estreita demais para todas as colunas, o cartão da tabela rola na horizontal em vez de esconder o excesso.
- Nenhuma coluna, ordenação, filtro ou botão muda de lugar ou de comportamento.

## Capabilities

### New Capabilities

### Modified Capabilities
- `gestao-clientes`: nova regra de apresentação da listagem — a tabela usa a largura disponível, não quebra linha em CNPJ/escritório/regime/data e nunca oculta a coluna de ações.

## Impact

- `ContabOne.Frontend/src/views/ClientesView.vue` (CSS scoped: `max-width` da view, `white-space` das colunas, rolagem horizontal do cartão).
- `ContabOne.Frontend/src/assets/styles/components.css`: **sem alteração** — `.table-card` é compartilhado por ~12 telas; o ajuste fica local à view, com comentário (mesmo precedente de `ResultadoSimulacao.vue`).
- Sem mudança de API, banco, agente ou dependências.
