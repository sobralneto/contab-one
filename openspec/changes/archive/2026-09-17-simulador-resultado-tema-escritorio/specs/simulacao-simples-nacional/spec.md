## ADDED Requirements

### Requirement: A última linha e a última coluna das tabelas semestrais têm destaque na cor do leiaute

A última linha e a última coluna de cada tabela semestral DEVEM (MUST) ter destaque visual — a linha do Imposto estimado (DAS) e a coluna de subtotal do semestre, como no documento original (`tr.row-imposto`, `.col-total`) —
usando a cor de acento do leiaute do escritório da sessão, não uma cor fixa:
a mesma `--accent`/`--accent-suave` retemada no restante do bloco de
resultado (ver "O resultado adota a identidade visual do escritório").

#### Scenario: Última linha em destaque

- **WHEN** o resultado está visível
- **THEN** a linha "Imposto estimado (DAS)", em cada tabela semestral,
  aparece com texto em negrito na cor de acento do leiaute e fundo tingido
  com essa mesma cor

#### Scenario: Última coluna em destaque

- **WHEN** o resultado está visível
- **THEN** a coluna de subtotal do semestre, do cabeçalho até a última
  linha, aparece com texto em negrito na cor de acento do leiaute e fundo
  tingido com essa mesma cor

#### Scenario: Destaque acompanha o leiaute do escritório

- **WHEN** dois escritórios com leiautes diferentes (por exemplo L&J e
  MUDAHR) abrem a mesma simulação
- **THEN** a cor do destaque na última linha e na última coluna muda
  conforme o leiaute de cada um — nunca uma cor fixa

### Requirement: O resultado fica oculto até o usuário pedir o cálculo

A página DEVE (MUST) mostrar, na abertura, apenas os cartões de entrada
(Identificação, Anexo da atividade, Faturamento) e a toolbar — nenhum
indicador, tabela, gráfico ou alerta de limite DEVE (MUST) aparecer antes
disso. Clicar em **"Calcular imposto estimado"** DEVE (MUST) revelar o
resultado pela primeira vez. Reabrir uma simulação salva a partir do
histórico DEVE (MUST) também revelar o resultado direto, sem exigir o
clique.

Depois de revelado, o resultado continua acompanhando o preenchimento em
tempo real — a visibilidade muda uma vez; o recálculo reativo ao editar um
mês ou trocar de anexo (ver "O resultado é apresentado em indicadores,
tabelas e gráfico") não depende de clicar em Calcular de novo.

#### Scenario: Página recém-aberta não mostra resultado

- **WHEN** o usuário abre `/simulador` pela primeira vez, sem vir do
  histórico
- **THEN** só os cartões de entrada e a toolbar aparecem — nenhum
  indicador, tabela ou gráfico está no DOM

#### Scenario: Calcular revela o resultado

- **WHEN** o usuário preenche os dados e clica em "Calcular imposto
  estimado"
- **THEN** o bloco de resultado aparece, com os valores calculados a partir
  do que foi preenchido, e a tela rola até ele

#### Scenario: Reabrir do histórico revela o resultado sem clique

- **WHEN** o usuário abre uma simulação salva a partir do histórico
- **THEN** o bloco de resultado já aparece calculado, sem exigir um clique
  em "Calcular imposto estimado"

#### Scenario: Editar depois de revelado não esconde o resultado

- **WHEN** o resultado já foi revelado e o usuário altera um mês ou troca
  de anexo
- **THEN** o resultado permanece visível e é recalculado — não volta a
  ficar oculto

### Requirement: O resultado adota a identidade visual do escritório

O bloco de resultado DEVE (MUST) usar a identidade visual configurada para
o escritório da sessão (`Escritorio.LayoutDashboard`) — a mesma fonte de
dado e as mesmas três identidades (neutra da plataforma, L&J, MUDAHR) já
usadas pela dashboard de apuração do PGDAS-D (capability
`apuracao-simples-nacional`): cor de fundo, cor dos cartões (indicadores,
tabelas, painel do gráfico), bordas e cor de acento vêm do leiaute
escolhido, não dos tokens neutros do painel. Escritório sem leiaute
configurado ou com leiaute não reconhecido usa a identidade neutra.

O leiaute do resultado NÃO DEVE (MUST NOT) ser afetado pelo tema do
painel (claro/escuro) — é identidade fixa do escritório, como na dashboard
de apuração. Os indicadores de erro e de atenção (alerta de limite
excedido, marcação de mês/mês do RBT12 que ultrapassa o limite) NÃO DEVEM
(MUST NOT) ser retemados — continuam nas cores semânticas do painel,
porque sinalizam estado, não marca.

#### Scenario: Escritório com identidade própria

- **WHEN** o escritório da sessão tem o leiaute L&J ou MUDAHR configurado
- **THEN** o bloco de resultado do Simulador usa a paleta dessa identidade

#### Scenario: Escritório sem identidade configurada

- **WHEN** o escritório está no leiaute neutro, ou o leiaute não é
  reconhecido
- **THEN** o bloco de resultado usa a identidade neutra da plataforma, sem
  erro

#### Scenario: Tema do painel não afeta o resultado

- **WHEN** o usuário alterna o painel entre claro e escuro
- **THEN** as cores do bloco de resultado do Simulador não mudam

#### Scenario: Alerta de limite continua com cor semântica

- **WHEN** o RBT12 de algum mês excede o limite do Simples, com o
  escritório num leiaute de marca (L&J ou MUDAHR)
- **THEN** o alerta e a marcação de excedido na tabela continuam na cor de
  erro do painel, não na paleta da marca

### Requirement: O resultado pode ser baixado em PDF, com a logo e o nome do escritório

A página DEVE (MUST) oferecer um botão **"Baixar PDF"**, visível somente
com o resultado revelado, que gera um arquivo PDF do resultado da
simulação. O documento gerado DEVE (MUST) trazer, como cabeçalho, a logo e
o nome do escritório configurados para o leiaute em uso (o mesmo mecanismo
de `Escritorio.LayoutDashboard`), no mesmo espírito do cabeçalho de marca
do documento original (`formulario_simples_nacional.html`). O cabeçalho de
marca NÃO DEVE (MUST NOT) aparecer na tela do painel — só no PDF gerado.

O PDF NÃO DEVE (MUST NOT) incluir os cartões de entrada (Identificação,
Anexo da atividade, Faturamento) nem a toolbar — só o cabeçalho de marca e
o bloco de resultado (identificação/anexo, indicadores, tabelas semestrais
e gráfico).

#### Scenario: Botão aparece só com o resultado visível

- **WHEN** o usuário ainda não clicou em "Calcular imposto estimado" (ou
  ainda não reabriu uma simulação salva)
- **THEN** o botão "Baixar PDF" não aparece

#### Scenario: Baixar PDF com o resultado calculado

- **WHEN** o usuário calcula a simulação e clica em "Baixar PDF"
- **THEN** um arquivo PDF é baixado, com a logo e o nome do escritório no
  topo, seguidos do bloco de resultado — sem os cartões de entrada

#### Scenario: Logo e nome seguem o leiaute do escritório

- **WHEN** dois escritórios com leiautes diferentes (por exemplo L&J e
  MUDAHR) geram o PDF da mesma simulação
- **THEN** cada PDF traz a logo e o nome da identidade configurada para o
  respectivo escritório

## MODIFIED Requirements

### Requirement: O resultado é apresentado em indicadores, tabelas e gráfico

A página DEVE (MUST) apresentar o resultado da simulação, nesta ordem: a
identificação (CNPJ, depois nome) e os dados do anexo selecionado, dentro de
um mesmo cartão visível (fundo, borda e raio do design system — não uma
`<div>` sem estilo); o alerta de
limite (quando aplicável); os indicadores de 12 meses (faturamento, imposto
estimado, alíquota efetiva média e RBT12 do 12º mês); o rótulo **"1º
Semestre — 1º ao 6º mês de atividade"** seguido da tabela do primeiro
semestre; o rótulo **"2º Semestre — 7º ao 12º mês de atividade"** seguido
da tabela do segundo semestre; o gráfico comparativo mensal de faturamento
× imposto estimado, com legenda; e por fim, centralizado, o aviso "Simulação
de caráter estimativo · valores em centavos, sem arredondamento · não
substitui apuração oficial via PGDAS-D".

O resultado DEVE (MUST) acompanhar o preenchimento: alterar um mês ou trocar
o anexo DEVE (MUST) atualizar tudo o que depende dele.

#### Scenario: Identificação vem antes dos dados do anexo, CNPJ antes do nome

- **WHEN** o resultado está visível, com nome e CNPJ informados
- **THEN** o CNPJ aparece antes do nome, e os dois aparecem antes do título
  e da descrição do anexo selecionado — todos dentro do mesmo cartão visível

#### Scenario: Rótulos de semestre acima de cada tabela

- **WHEN** o resultado está visível
- **THEN** "1º Semestre — 1º ao 6º mês de atividade" aparece imediatamente
  acima da tabela do primeiro semestre, e "2º Semestre — 7º ao 12º mês de
  atividade" imediatamente acima da tabela do segundo

#### Scenario: Aviso final abaixo do gráfico

- **WHEN** o resultado está visível
- **THEN** o texto "Simulação de caráter estimativo · valores em centavos,
  sem arredondamento · não substitui apuração oficial via PGDAS-D" aparece
  centralizado, depois do gráfico, como último elemento do resultado

#### Scenario: Preenchimento alterado

- **WHEN** o usuário altera o faturamento de um mês já preenchido
- **THEN** indicadores, tabelas e gráfico refletem o novo valor

#### Scenario: Simulação sem nenhum valor

- **WHEN** nenhum mês tem valor
- **THEN** os indicadores exibem zero ou vazio, e as tabelas e o gráfico não
  apresentam valores inventados
