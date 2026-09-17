# simulacao-simples-nacional Specification

## Purpose

Define o Simulador Simples Nacional: uma calculadora do escritório que estima
o DAS mês a mês — RBT12 proporcionalizado, alíquota efetiva, imposto — a
partir do anexo escolhido e de até 12 valores de faturamento digitados. Vive
como rota transversal do painel (`/simulador`, na área Escritório), fora do
catálogo de ferramentas: não é produto, não exige contratação nem
licenciamento, e não é módulo do PGDAS-D, ainda que o domínio fiscal seja o
mesmo.

O cálculo em si roda inteiramente no navegador — é estimativa, não apuração,
e não gera execução nem entra no histórico do cliente. A única exceção
controlada é a persistência opcional por ação explícita do usuário: o botão
"Salvar simulação" grava nome, CNPJ, anexo e os 12 valores de faturamento —
nunca o resultado calculado, que é sempre recalculado ao reabrir — e sem
qualquer vínculo com o cadastro do cliente (ver capability
`historico-simulador-simples-nacional` para a consulta e a reabertura do que
foi salvo).

## Requirements

### Requirement: A simulação mora no painel, como página da área do escritório

O sistema DEVE (MUST) oferecer a simulação de Simples Nacional como página da
área **Escritório** do menu, sob o nome **Simulador Simples Nacional** — rota
transversal (`/simulador`), como Arquivos, não página de ferramenta. A página
NÃO DEVE (MUST NOT) ser um arquivo aberto fora do painel, nem pertencer ao
catálogo de ferramentas, nem exigir produto, contratação ou licenciamento
próprios: a simulação é calculadora do escritório, não módulo do PGDAS-D.
(A primeira versão a declarava como página da ferramenta PGDAS-D, no submenu
dela; o uso real mostrou que não pertence a um produto e ela mudou de lugar —
feedback do usuário.)

#### Scenario: Simulador no menu do escritório

- **WHEN** o usuário abre o menu do painel
- **THEN** a área Escritório oferece o Simulador Simples Nacional ao lado de
  Arquivos, para todo usuário de escritório, e o endereço `/simulador` abre
  dentro do painel

#### Scenario: Simulador fora do catálogo de ferramentas

- **WHEN** o admin cadastra ou edita uma ferramenta
- **THEN** a simulação não é uma página declarável da ferramenta — o conjunto
  fechado de páginas por produto não a contém

#### Scenario: Identidade do escritório vem do painel

- **WHEN** a página do simulador é aberta
- **THEN** o título aparece na barra superior do painel, e a página não
  exibe cabeçalho, marca d'água, logo ou rodapé próprios do formulário
  original

### Requirement: A simulação só trafega dado para o servidor quando o usuário pede para salvar

A simulação DEVE (MUST) ser calculada inteiramente no navegador. Nenhum valor
digitado — identificação, anexo escolhido ou faturamento — DEVE (MUST NOT) ser
enviado à API nem gravado em banco **antes de o usuário clicar em "Salvar
simulação"**. A simulação é estimativa, e NÃO DEVE (MUST NOT) ser confundida
com apuração do Simples Nacional: não gera execução, não entra no histórico
de execuções e NÃO DEVE (MUST NOT) ser vinculada ao cadastro do cliente,
mesmo depois de salva.

#### Scenario: Preenchimento sem salvar

- **WHEN** o usuário identifica a empresa, escolhe o anexo e preenche os
  meses, sem clicar em "Salvar simulação"
- **THEN** nenhuma requisição carrega os valores digitados, e nada é
  persistido

#### Scenario: Recarregar a página sem ter salvado

- **WHEN** o usuário recarrega a página do simulador sem ter clicado em
  "Salvar simulação"
- **THEN** a simulação anterior não é restaurada, porque não foi gravada em
  lugar algum

#### Scenario: Resultado calculado nunca é enviado

- **WHEN** o usuário salva uma simulação
- **THEN** a requisição carrega só nome, CNPJ, anexo e os 12 valores de
  faturamento — indicadores, tabelas semestrais e RBT12 não fazem parte do
  corpo enviado

### Requirement: A simulação pode ser salva e reaberta

A página DEVE (MUST) oferecer um botão **"Salvar simulação"** que grava, para
o escritório da sessão, nome, CNPJ, anexo e os 12 valores de faturamento
digitados. O CNPJ DEVE (MUST) ser gravado exatamente como digitado, em texto
puro — sem hash e sem normalização de máscara. A simulação salva DEVE (MUST)
poder ser reaberta a partir do histórico (ver capability
`historico-simulador-simples-nacional`), recarregando os 4 campos no
formulário e recalculando o resultado a partir deles.

#### Scenario: Salvar uma simulação preenchida

- **WHEN** o usuário preenche nome, CNPJ, anexo e ao menos um mês, e clica em
  "Salvar simulação"
- **THEN** a simulação é gravada e passa a aparecer no histórico do
  escritório

#### Scenario: Reabrir uma simulação salva

- **WHEN** o usuário abre uma simulação a partir do histórico
- **THEN** o formulário do simulador é preenchido com o nome, CNPJ, anexo e
  os 12 valores gravados, e o resultado é recalculado a partir deles — não
  restaurado de um valor gravado

#### Scenario: Salvar não cria nem consulta cliente

- **WHEN** o usuário salva uma simulação, com ou sem CNPJ preenchido
- **THEN** nenhum cliente é criado, alterado ou consultado no cadastro

### Requirement: O topo da página tem duas colunas

A página DEVE (MUST) dispor, no topo, a identificação da empresa e a seleção
do anexo na **coluna à esquerda**, e o preenchimento do faturamento na
**coluna à direita**. É a única diferença de arranjo em relação ao formulário
original, que empilhava os três blocos numa coluna única.

#### Scenario: Topo da página

- **WHEN** o usuário abre a simulação
- **THEN** o bloco de identificação e o cartão de seleção do anexo aparecem
  na mesma coluna, à esquerda, e os campos de faturamento aparecem na coluna
  à direita, na mesma faixa horizontal

#### Scenario: Tela estreita

- **WHEN** a largura disponível não comporta duas colunas
- **THEN** as colunas passam a se empilhar, com a identificação e o anexo
  antes do faturamento, sem rolagem horizontal

### Requirement: Identificação da empresa em texto livre

A página DEVE (MUST) permitir identificar a simulação por nome empresarial e
CNPJ digitados, ambos opcionais, sem exigir nem oferecer cliente cadastrado. O
CNPJ DEVE (MUST) receber a máscara `XX.XXX.XXX/XXXX-XX` conforme o usuário
digita.

A identificação titula a simulação; ela não cria, altera ou consulta cliente.

#### Scenario: Identificação preenchida

- **WHEN** o usuário digita o nome empresarial e o CNPJ
- **THEN** o CNPJ é exibido com a máscara conforme a digitação, e a
  identificação acompanha o resultado da simulação

#### Scenario: Identificação em branco

- **WHEN** o usuário não preenche nome nem CNPJ
- **THEN** a simulação é calculada do mesmo modo, e nada é exigido para
  prosseguir

### Requirement: A seleção do anexo define a tabela do cálculo, sobre uma única série de faturamento

A página DEVE (MUST) oferecer a seleção de um Anexo do Simples Nacional (I a
V), com um selecionado por vez, e DEVE (MUST) apresentar, para o anexo
selecionado, a descrição que o identifica. O faturamento dos 12 meses É (IS)
uma série ÚNICA da simulação — vinculada ao nome/CNPJ informados, não ao
anexo escolhido. Trocar o anexo DEVE (MUST) apenas refazer o cálculo com a
tabela do novo anexo sobre essa mesma série; NÃO DEVE (MUST NOT) zerar,
duplicar ou manter séries de faturamento separadas por anexo. (Uma primeira
versão guardava um array de faturamento por anexo, o que fazia os valores
digitados "sumirem" ao trocar de anexo, como se pertencessem a ele em vez de
à empresa simulada — corrigido no uso real.)

#### Scenario: Troca de anexo

- **WHEN** o usuário tem faturamento preenchido e seleciona outro anexo
- **THEN** o cálculo e o resultado passam a usar a tabela do novo anexo, e os
  12 valores de faturamento digitados permanecem exatamente os mesmos

#### Scenario: Ida e volta entre anexos não altera o faturamento

- **WHEN** o usuário preenche faturamento, troca de anexo e volta ao anexo
  original
- **THEN** os 12 valores de faturamento são os mesmos em qualquer anexo
  selecionado — nunca uma série separada por anexo

#### Scenario: Anexo selecionado é visível

- **WHEN** a página é aberta
- **THEN** exatamente um anexo aparece como selecionado, e a descrição
  exibida corresponde a ele

### Requirement: Faturamento com máscara de moeda ao digitar

Cada um dos 12 campos de faturamento mensal DEVE (MUST) formatar o valor
digitado como moeda brasileira conforme a digitação, usando a mesma regra
dos demais campos monetários do sistema. O prefixo `R$` DEVE (MUST) vir
FORA do campo, no cartão (`.mes-prefix`), e NÃO DEVE (MUST NOT) repetir-se
dentro do campo: o campo exibe apenas o número formatado, sem "R$" — a
primeira versão carregava o prefixo no próprio valor exibido, duplicando a
moeda com o rótulo do cartão, e foi corrigido a pedido do usuário no uso
real.

#### Scenario: Digitação de faturamento

- **WHEN** o usuário digita `150` num campo de faturamento
- **THEN** o campo exibe `1,50`, com a máscara aplicada a cada tecla, e o
  prefixo `R$` do cartão acompanha o campo

#### Scenario: Colagem de valor formatado

- **WHEN** o usuário cola `160.000,00` num campo de faturamento
- **THEN** o campo passa a valer R$ 160.000,00, e o cálculo usa esse valor

### Requirement: Mês sem valor é marcado, e a marcação some ao preencher

Cada cartão de faturamento DEVE (MUST) exibir a marca de "sem valor
preenchido" enquanto o mês não tiver valor, e DEVE (MUST) deixar de exibi-la
assim que o mês receber valor. A marcação NÃO DEVE (MUST NOT) aparecer em mês
preenchido — em particular, o cartão não pode nascer marcado e permanecer
marcado depois de o usuário digitar.

Os 12 meses DEVEM (MUST) começar sem valor: a página NÃO DEVE (MUST NOT)
abrir com faturamento previamente preenchido.

A marcação É (IS) exclusivamente a borda esquerda do cartão em `--erro`,
derivada do próprio valor do mês (`meses[i] === 0`). A primeira versão
exibia também um sinal textual por cartão ("sem valor preenchido", via
`aria-describedby`); foi removido a pedido do usuário no uso real — a borda
é o único sinal, e a página DEVE (MUST) dispensar qualquer indicação
adicional.

#### Scenario: Página recém-aberta

- **WHEN** o usuário abre a simulação
- **THEN** os 12 meses estão vazios e todos exibem a marcação de sem valor

#### Scenario: Mês preenchido deixa de ser marcado

- **WHEN** o usuário digita um valor num mês marcado
- **THEN** a marcação daquele mês desaparece, e a dos demais permanece

#### Scenario: Mês esvaziado volta a ser marcado

- **WHEN** o usuário apaga o valor de um mês preenchido
- **THEN** o mês volta a exibir a marcação de sem valor

#### Scenario: Total de meses marcados

- **WHEN** o usuário preenche `n` dos 12 meses
- **THEN** exatamente `12 - n` meses exibem a marcação de sem valor

### Requirement: O cálculo do RBT12 proporcionalizado é preservado

A página DEVE (MUST) calcular, para cada mês de atividade simulado, o RBT12
proporcionalizado a partir do faturamento acumulado, a alíquota nominal e a
parcela dedutível da faixa do anexo selecionado, a alíquota efetiva e o
imposto estimado — com a mesma tabela de faixas e a mesma regra do formulário
original, incluindo a alíquota mínima do anexo aplicada ao primeiro mês de
atividade.

#### Scenario: Meses iniciais sem histórico

- **WHEN** o usuário preenche apenas os primeiros meses de atividade
- **THEN** os meses sem faturamento acumulado anterior usam a primeira faixa
  do anexo, sinalizada como alíquota mínima

#### Scenario: RBT12 excede o limite do Simples

- **WHEN** o RBT12 proporcionalizado de um mês ultrapassa R$ 4.800.000,00
- **THEN** o mês é sinalizado em vermelho na tabela, o aviso de extrapolação
  do limite é exibido, e o indicador de RBT12 do 12º mês aponta o excesso

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

### Requirement: O resultado é apresentado em indicadores, tabelas e gráfico

A página DEVE (MUST) apresentar o resultado da simulação, nesta ordem: a
identificação (CNPJ, depois nome) e os dados do anexo selecionado, dentro de
um mesmo cartão visível (fundo, borda e raio do design system — não uma
`<div>` sem estilo); o alerta de limite (quando aplicável); os indicadores
de 12 meses (faturamento, imposto estimado, alíquota efetiva média e RBT12
do 12º mês); o rótulo **"1º Semestre — 1º ao 6º mês de atividade"** seguido
da tabela do primeiro semestre; o rótulo **"2º Semestre — 7º ao 12º mês de
atividade"** seguido da tabela do segundo semestre; o gráfico comparativo
mensal de faturamento × imposto estimado, com legenda; e por fim,
centralizado, o aviso "Simulação de caráter estimativo · valores em
centavos, sem arredondamento · não substitui apuração oficial via
PGDAS-D".

O resultado DEVE (MUST) acompanhar o preenchimento: alterar um mês ou trocar o
anexo DEVE (MUST) atualizar tudo o que depende dele.

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
