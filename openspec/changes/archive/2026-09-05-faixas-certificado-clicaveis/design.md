## Context

O cartão de Certificados do painel traz três contagens, apuradas por três
`CountAsync` escritos inline em `KpisAsync`. A tela de Clientes tem um filtro de
vencimento próprio, `diasVencimentoCert`, escrito inline em `ListarAsync`. Os
dois nasceram separados e nunca precisaram concordar, porque nada ligava um ao
outro.

Ligar os cards à listagem cria essa obrigação: o número clicado tem de ser o
tamanho da lista aberta.

## Goals / Non-Goals

**Goals:**

- As três contagens levam à listagem com a faixa aplicada.
- Uma definição só de cada faixa, compartilhada entre contagem e filtro.
- Filtro de certificado disponível a todos os papéis.

**Non-Goals:**

- Não mexer no horizonte de 30 dias.
- Não remover `diasVencimentoCert` da API — só deixar de usá-lo na tela.
- Não transformar o filtro em intervalo livre de datas.
- Não fazer o mesmo pelos indicadores de outras telas.

## Decisions

### D1 — `faixaCertificado` com as três faixas, e um vocabulário só

`diasVencimentoCert` filtra sempre `>= hoje && <= hoje+N`. Isso expressa a faixa
de 3 dias exatamente (N=3), e **nenhuma** das outras duas: vencido é `< hoje`, e
"de 4 a 30" precisa de piso em `hoje+4`.

Entra `faixaCertificado`, com os três tokens que correspondem um a um às três
contagens do painel: `vencidos`, `vencendo3d`, `vencendoMais3d`. O seletor da
listagem passa a oferecer exatamente essas três, e os períodos avulsos (1, 2, 7
e 15 dias) saem da tela.

O ganho não é de código, é de vocabulário: o usuário lê "vencendo em até 3 dias"
no painel, clica, e encontra o mesmo rótulo selecionado na listagem. Com os
períodos convivendo, a mesma faixa tinha dois nomes — "vencendo em até 3 dias" no
painel e "vence em 3 dias" no filtro —, e as outras duas não tinham equivalente
nenhum entre os períodos.

`diasVencimentoCert` **continua aceito pela API**, inalterado. Ninguém o envia
mais a partir da interface, mas removê-lo seria mexer em contrato especificado
para não ganhar nada — a tela já não o usa. Fica como filtro genérico para quem
consome a API diretamente.

Alternativas descartadas:

- *Estender `diasVencimentoCert` com negativos ou faixas codificadas no número.*
  `-1` para vencido é o tipo de convenção que ninguém lembra seis meses depois.
- *Manter os períodos avulsos ao lado das faixas.* Foi o desenho inicial, e é o
  que o pedido corrigiu: duas maneiras de dizer a mesma coisa na mesma barra,
  uma delas sem correspondência com o painel.

### D2 — As faixas viram predicado compartilhado

`Features/Clientes/CertificadoFiltros.cs` passa a expor as três faixas como
`Expression<Func<Cliente, bool>>`, e tanto `KpisAsync` quanto `ListarAsync` as
consomem. É o mesmo remédio de `OnboardingFiltros`, pelo mesmo motivo — e agora
com uma consequência mais visível: aqui o usuário clica no número e vê a lista no
segundo seguinte, então qualquer divergência aparece na hora.

Mora em `Features/Clientes/` porque a faixa é uma condição sobre `Cliente`;
Dashboard já importa de outro slice (`Features/Onboarding`) pelo mesmo motivo.

As três continuam disjuntas e presas ao horizonte de 30 dias, como antes:
vencido (`< hoje`), até 3 dias (`hoje..hoje+3`), de 4 a 30 (`hoje+3 <
validade <= hoje+30`). Certificado que vence em 90 dias não entra em nenhuma.

### D3 — O filtro de certificado sai do `v-if` de papel

Hoje o seletor de certificado só é renderizado para quem **não** é admin de
plataforma (o admin vê, no lugar, o seletor de escritório), e `carregar()` só
manda `diasVencimentoCert` quando `!auth.isPlatformAdmin`.

Como os cards do painel são vistos por todos, um admin que clicasse cairia numa
lista sem filtro nenhum — o número não bateria, que é exatamente o defeito que
esta change existe para evitar. O seletor passa a ficar fora do `v-if`, junto do
de onboarding, que já saiu dali pelo mesmo motivo. Nada vaza: a listagem é
escopada pelos query filters globais, não pelo que o frontend manda.

### D4 — Um seletor só, com as três faixas

O seletor oferece Todos, Vencidos, Vencendo em até 3 dias, Vencendo de 4 a 30
dias — em ordem de urgência, e nada além disso. Dois seletores de certificado na
mesma barra seriam duas perguntas para uma decisão só, e nada impediria
combinações contraditórias.

O valor é o próprio token que vai para a API, então não há tabela de conversão
entre o que a tela mostra e o que o servidor entende — o que some é justamente
onde os dois vocabulários podiam divergir.

## Risks / Trade-offs

- **`diasVencimentoCert` fica na API sem nenhum chamador** → superfície que
  ninguém exercita tende a apodrecer. Aceito por ora porque é contrato
  especificado e remover pede decisão própria; se ninguém o consumir de fora,
  vale aposentá-lo numa change seguinte.
- **Some a possibilidade de filtrar por 1, 2, 7 ou 15 dias** → é a troca que o
  pedido faz de propósito: um vocabulário só, alinhado ao painel. Quem precisar
  de um recorte diferente ainda o tem pela API, via `diasVencimentoCert`.
- **Admin passa a ver um seletor a mais** → é ganho, não perda: hoje ele não tem
  como filtrar por certificado em tela alguma.
