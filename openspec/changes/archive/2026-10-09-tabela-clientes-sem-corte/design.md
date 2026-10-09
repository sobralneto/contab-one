## Context

`ClientesView.vue` envolve a tabela num `.table-card` (`components.css`) que tem `overflow: hidden` — necessário para o cabeçalho respeitar o raio do canto. A view, por sua vez, declara `.clientes-view { max-width: 1200px }`. Descontada a barra lateral, a área de conteúdo de uma janela comum tem bem mais que 1200px; mesmo assim a view se prende a esse teto, e as 9 colunas (10 para o admin, com Escritório) não cabem nele sem quebrar texto. O que ainda assim passa da largura do cartão é cortado em silêncio pelo `overflow: hidden`, e a coluna cortada é sempre a última: a de ações.

Os outros cartões de tabela do sistema (`.table-card` é usado em ~12 telas) têm poucas colunas e não sofrem disso; `/clientes` é a tabela mais larga do produto e continua ganhando colunas (regime, 2FA, escritório).

## Goals / Non-Goals

**Goals:**
- A coluna de ações é sempre alcançável, em qualquer largura de janela.
- Em janela larga, CNPJ, escritório, regime e data aparecem numa linha só.
- Nenhuma mudança de colunas, ordem, filtros, ordenação ou comportamento dos botões.

**Non-Goals:**
- Não mexer no `.table-card` compartilhado nem no `max-width` das outras telas.
- Não tornar colunas ocultáveis/configuráveis, nem trocar a tabela por cartões em tela estreita.
- Não fixar (`sticky`) a coluna de ações.

## Decisions

**1. Tirar o `max-width: 1200px` de `.clientes-view`.** A tabela passa a usar toda a largura da área de conteúdo, que já tem padding próprio (`.main-content { padding: 1.5rem }`). É a resposta direta ao pedido ("a tabela deve ser mais larga"). *Alternativa:* subir o teto para um número maior (ex.: 1600px) — descartada: é outro número arbitrário que volta a cortar na próxima coluna que entrar, e em monitor largo deixaria uma faixa vazia à direita sem ganho.

**2. `white-space: nowrap` nas colunas de dado curto e previsível** (CNPJ, escritório, regime — que já tem —, data de atualização com sua etiqueta de origem). **O nome fica de fora**: é o único texto de comprimento livre (razão social longa), então é ele que quebra quando falta largura, em vez de empurrar a tabela para fora. Como as colunas `nowrap` pedem sua largura natural e o nome divide o restante, o nome encolhe primeiro. O nome ganha um piso de `min-width: 220px`: sem ele, com o cartão rolando, a coluna encolhia até a palavra mais longa e cada linha ficava com 3–4 linhas de nome. *Alternativa:* `nowrap` também no nome — descartada: uma razão social longa forçaria rolagem horizontal mesmo em janela larga.

**3. Rede de segurança: o cartão da tabela rola na horizontal** (`overflow-x: auto` no `.table-card` **apenas nesta view**). Sem isso, a decisão 2 só trocaria um corte por outro: numa janela estreita, as colunas `nowrap` empurrariam as ações para fora do `overflow: hidden`. Rolar é o comportamento honesto: o conteúdo continua alcançável.
- **Sem `min-width` na tabela.** A ideia inicial era fixar um piso de largura, mas medido no navegador a tabela já não encolhe abaixo do conteúdo `nowrap` (≈1090px para o escritório, ≈1320px para o admin, que tem a coluna Escritório) — e esse piso varia com o papel e com os dados. Um número fixo estaria errado para um dos dois e envelheceria a cada coluna nova; o piso natural da tabela é o certo, e é ele que o cartão rola.
- O override é local e comentado como layout, não chrome — mesmo precedente de `ResultadoSimulacao.vue` ("override local do overflow:hidden de .table-card"). `overflow-x: auto` mantém o canto arredondado, pois o cartão continua cortando o próprio raio.
- `overflow-x: auto` computa `overflow-y` para `auto` também; o cartão não tem altura fixa, então não aparece barra vertical.
- *Alternativa:* mudar `.table-card` em `components.css` para todos — descartada: altera 12 telas para resolver uma, e o `overflow: hidden` ali é decisão documentada.

**4. A coluna de ações não precisa de largura explícita.** `.col-actions` já é `nowrap`, e como todas as demais colunas de dado também são, o algoritmo automático de tabela usa o conteúdo dos 4 botões como piso da coluna. Nada a declarar.

## Risks / Trade-offs

- [Linhas de tabela muito largas em monitor ultrawide, com o olho percorrendo distância longa até as ações] → o nome absorve a sobra e as colunas de dado mantêm largura natural; se incomodar, um teto alto pode ser reintroduzido depois sem desfazer o resto.
- [Barra de rolagem horizontal aparece em janela estreita, o que é novo] → é o comportamento desejado: antes o conteúdo sumia. A barra só existe quando a janela é menor que o `min-width` da tabela.
- [Nova coluna alarga o piso da tabela] → sem número fixo para atualizar; o E2E (tarefa 3) pega um eventual corte da coluna de ações pelo resultado.
- [Não dá para validar layout em jsdom (Vitest não calcula largura)] → verificação visual manual em duas larguras e, se viável, um E2E Playwright que checa que o botão da última coluna está dentro da área visível do cartão.
