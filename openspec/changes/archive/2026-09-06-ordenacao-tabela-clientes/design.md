## Context

`ListarAsync` fecha com `OrderBy(c => c.Nome).Skip(...).Take(...)`. A ordenação
é fixa e ninguém escolhe nada; a paginação já convive com o empate de nomes
iguais desde sempre, mas em ordem única o estrago é pequeno e constante.

Tornar a ordenação escolhível muda isso: colunas com muito empate (certificado
nulo, escritório) entram no jogo, e aí a paginação passa a depender de uma ordem
que o banco não é obrigado a repetir.

## Goals / Non-Goals

**Goals:**

- Escolher coluna e direção pelo cabeçalho.
- Ordem determinística entre páginas.
- Padrão inalterado (nome crescente) para quem não escolhe nada.

**Non-Goals:**

- Não ordenar por CNPJ (valor mascarado).
- Não ordenar por mais de uma coluna ao mesmo tempo.
- Não guardar a preferência de ordenação entre sessões.
- Não levar a ordenação para o endereço — os filtros só ganharam isso porque o
  painel precisava abrir a lista pronta; ninguém liga para uma ordem.

## Decisions

### D1 — Coluna resolvida por conjunto fechado, nunca por texto do cliente

`ordenarPor` chega como string e é traduzida por um `switch` para a expressão de
ordenação. Nada do que o cliente manda vira nome de coluna, e um valor
desconhecido cai no padrão em vez de estourar.

Vale dizer por que não é só higiene de injeção (o EF já parametriza): o `switch`
é também o que mantém o conjunto ordenável **igual ao que a tela oferece**. Uma
coluna nova só passa a ser ordenável quando alguém a acrescenta aqui, de
propósito.

### D2 — Todo `OrderBy` termina em `ThenBy(c => c.Id)`

Este é o ponto da change, não um detalhe.

`Skip`/`Take` sobre uma ordenação com empates é indefinido: o banco pode
devolver os empatados em ordem diferente a cada consulta, e como cada página é
uma consulta nova, o mesmo cliente pode cair na página 1 e na 2 enquanto outro
não cai em nenhuma. Com "ordenar por certificado" e metade da base sem
certificado, o empate deixa de ser exceção e vira o caso comum.

`Id` é o desempate: único e estável. `Codigo` não serviria — é único por
escritório, e o admin sem foco vê vários escritórios ao mesmo tempo.

### D3 — Nulos de certificado sempre no fim, nas duas direções

O Postgres coloca `NULL` por último no `ASC` e primeiro no `DESC`. Herdar isso
faria a ordem decrescente abrir com quem não tem certificado — exatamente o que
a coluna não é sobre.

A ordenação por certificado passa então por
`OrderBy(c => c.CertificadoValidade == null)` antes do critério real, o que
empurra os nulos para o fim independentemente da direção. O padrão já existe no
repositório (`TarefasEndpoints` ordena por `t.Vencimento == null` primeiro) e é
traduzível — `TraducaoLinqTest` já cobre a forma.

### D4 — Cabeçalho clicável com dois estados, não três

Clicar alterna crescente ↔ decrescente; clicar em outra coluna começa crescente.
Não existe terceiro estado "sem ordenação": ele obrigaria o usuário a passar por
um estado invisível (a lista volta para nome, mas o cabeçalho que ele clicou não
mostra nada) para voltar ao início do ciclo.

O cabeçalho da coluna ativa carrega `aria-sort`, e a seta indica a direção. Sem
indicação visível, ordem decrescente e crescente são indistinguíveis quando o
usuário não conhece os dados.

### D6 — O convite a clicar tem de estar na coluna inativa

Marcar só a coluna ativa parecia bastar e não bastava: as outras ordenáveis
ficavam **idênticas** à de CNPJ, que não ordena. A única pista de que eram
acionáveis era o `cursor: pointer` — que se revela depois de o usuário já ter
levado o ponteiro até lá, ou seja, só para quem já desconfiava.

Então toda coluna ordenável carrega um glifo neutro em opacidade baixa, que
ganha contraste no `hover`; a que está ordenando troca o glifo por uma seta
direcional em cor de destaque. São dois estados visuais distintos — "dá para
ordenar por aqui" e "é por aqui que está ordenado" —, contra um só antes.

O mesmo raciocínio levou ao `tabindex` e ao Enter/Espaço: um cabeçalho que só
responde a clique é um controle que existe para quem usa mouse e não existe para
os demais. O foco recebe contorno visível pela mesma razão — sem ele, quem
navega por teclado não sabe onde está.

### D5 — O estilo do cabeçalho ordenável entra em `components.css`

`.data-table th` já é compartilhado; a variante ordenável entra ao lado dele,
não em CSS scoped de `ClientesView`. Qualquer tabela do sistema que ganhe
ordenação usa a mesma coisa — é a regra que o repositório já documenta para
tabela, botão e cartão de painel.

## Risks / Trade-offs

- **Ordenar por escritório só existe para o admin** → a coluna também só existe
  para ele; o servidor aceita o pedido de qualquer papel, mas para os demais a
  ordenação por escritório é constante (só há um) e inofensiva.
- **`ThenBy(Id)` acrescenta uma coluna ao `ORDER BY` de toda consulta** → custo
  irrelevante (é a chave primária, já indexada) diante de paginação que repete
  linha.
- **A preferência se perde ao sair da tela** → aceito (Non-Goals). Guardar
  ordenação por usuário é outra conversa, e ninguém pediu.
