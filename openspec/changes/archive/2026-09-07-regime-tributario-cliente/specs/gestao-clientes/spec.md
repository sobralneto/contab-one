## ADDED Requirements

### Requirement: O cadastro do cliente registra o regime tributário

O cadastro e a edição de um cliente DEVEM (MUST) permitir escolher o regime
tributário da empresa entre um conjunto **fechado** de cinco opções: Simples
Nacional, Lucro Presumido, Lucro Real, MEI e Outros.

A escolha é **opcional**. Cliente sem regime informado é um cadastro válido, e
não é o mesmo que "Outros": "Outros" é a empresa cujo regime é conhecido e não
está entre os quatro nomeados, enquanto a ausência é a empresa cujo regime
ninguém informou ainda. O sistema NÃO DEVE (MUST NOT) tratar uma como a outra,
nem preencher a ausência com um valor por conta própria.

O conjunto é fechado no servidor: o sistema DEVE (MUST) recusar por validação a
gravação com um valor que não esteja entre os cinco, e NÃO DEVE (MUST NOT)
aceitá-lo gravando qualquer coisa em seu lugar. Regime tributário decide qual
obrigação o escritório apura; valor livre aqui viraria dado fiscal errado
gravado em silêncio.

A edição DEVE (MUST) permitir tanto trocar o regime quanto **limpar** a escolha,
voltando o cliente ao estado de regime não informado.

#### Scenario: Cadastro escolhendo o regime

- **WHEN** o usuário cadastra um cliente e escolhe um dos cinco regimes
- **THEN** o cliente é gravado com aquele regime, e a listagem passa a exibi-lo

#### Scenario: Cadastro sem escolher regime

- **WHEN** o usuário cadastra um cliente sem escolher regime
- **THEN** o cadastro é aceito, e o cliente fica com o regime não informado —
  não com "Outros"

#### Scenario: Troca de regime na edição

- **WHEN** o usuário edita um cliente e escolhe um regime diferente do que ele
  tinha
- **THEN** o regime novo é gravado, e nenhum outro dado do cliente é alterado

#### Scenario: Limpar a escolha na edição

- **WHEN** o usuário edita um cliente que tem regime e remove a escolha
- **THEN** o cliente volta ao estado de regime não informado

#### Scenario: Valor fora do conjunto

- **WHEN** a gravação informa um regime que não está entre os cinco
- **THEN** o pedido é recusado por validação, e o cliente não é gravado nem
  alterado

#### Scenario: Cliente já cadastrado antes do campo existir

- **WHEN** o usuário abre a edição de um cliente cadastrado antes de o regime
  existir
- **THEN** o campo aparece sem escolha alguma, e ele pode informar o regime sem
  precisar mexer em nenhum outro campo

### Requirement: A listagem de clientes exibe o regime tributário

A tela de clientes DEVE (MUST) exibir o regime tributário de cada cliente em
coluna própria, com o mesmo rótulo que o formulário oferece — quem escolhe
"Lucro Presumido" no cadastro reencontra "Lucro Presumido" na tabela, não uma
sigla nem um número.

Cliente sem regime informado DEVE (MUST) ser exibido com o mesmo marcador de
ausência que a tela já usa nas demais colunas ("—"), e NÃO DEVE (MUST NOT)
aparecer como "Outros" nem com a célula em branco, que se confundiria com falha
de carregamento.

A coluna vale para **todos os papéis** que enxergam a listagem: o regime é
atributo da empresa, não do papel de quem olha.

#### Scenario: Cliente com regime informado

- **WHEN** o usuário vê na listagem um cliente cujo regime foi informado
- **THEN** a coluna de regime mostra o nome daquele regime, por extenso

#### Scenario: Cliente sem regime informado

- **WHEN** o usuário vê na listagem um cliente sem regime informado
- **THEN** a coluna de regime mostra "—", e não "Outros"

#### Scenario: Coluna visível para o administrador

- **WHEN** um administrador de plataforma abre a tela de clientes
- **THEN** a coluna de regime aparece para ele como para os demais papéis

### Requirement: A listagem de clientes filtra por regime tributário

A tela de clientes DEVE (MUST) oferecer um controle para restringir a listagem a
um regime tributário, com as **mesmas cinco opções** que o cadastro oferece e os
mesmos rótulos — quem escolhe "Lucro Presumido" no formulário reencontra "Lucro
Presumido" no filtro.

O controle DEVE (MUST) oferecer também a opção **"Não informado"**, que restringe
a listagem aos clientes sem regime. É a consulta que o escritório faz para saber
quem ainda falta classificar; sem ela, os clientes que mais precisam de atenção
são justamente os únicos que o filtro não alcança.

As opções DEVEM (MUST) ser mutuamente exclusivas: escolher uma substitui a
anterior. Sem escolha alguma, a listagem NÃO DEVE (MUST NOT) ser restringida por
regime.

O filtro DEVE (MUST) estar disponível para **todos os papéis** que enxergam a
listagem, e DEVE (MUST) combinar com os demais controles da tela — busca,
escritório, certificado e onboarding —, restringindo o resultado a quem atende a
todos ao mesmo tempo. A paginação e o total exibido DEVEM (MUST) refletir o
conjunto filtrado, e a escolha DEVE (MUST) levar de volta à primeira página.

O sistema DEVE (MUST) resolver a opção pedida a partir de um conjunto fechado
definido no servidor. Pedido com valor desconhecido NÃO DEVE (MUST NOT) filtrar
por regime e NÃO DEVE (MUST NOT) devolver erro — mesma regra das faixas de
certificado e da coluna de ordenação: endereço antigo ou digitado à mão mostra a
lista, não uma falha.

#### Scenario: Filtrar por um regime

- **WHEN** o usuário escolhe um regime no filtro
- **THEN** a listagem exibe apenas os clientes daquele regime, e o total exibido
  acompanha

#### Scenario: Filtrar por quem não tem regime

- **WHEN** o usuário escolhe "Não informado"
- **THEN** a listagem exibe apenas os clientes sem regime informado, e nenhum dos
  que já foram classificados — inclusive nenhum dos marcados como "Outros"

#### Scenario: Filtro desligado

- **WHEN** o usuário não escolhe regime algum
- **THEN** a listagem exibe todos os clientes do escopo, com e sem regime

#### Scenario: Filtro combinado com a busca

- **WHEN** o usuário digita um termo de busca e escolhe um regime
- **THEN** a listagem exibe apenas os clientes que atendem ao termo E estão
  naquele regime

#### Scenario: Filtro disponível para o administrador

- **WHEN** um administrador de plataforma abre a tela de clientes
- **THEN** o filtro de regime está disponível para ele como para os demais
  papéis, e combina com o filtro de escritório

#### Scenario: Valor desconhecido

- **WHEN** a listagem é pedida com um regime que não existe
- **THEN** o resultado sai sem filtro de regime, e nenhum erro é devolvido

#### Scenario: Troca de filtro volta à primeira página

- **WHEN** o usuário está numa página adiante e escolhe um regime
- **THEN** a listagem volta para a primeira página do conjunto filtrado

### Requirement: Cliente sem regime não encabeça a ordenação por regime

Ao ordenar pelo regime tributário, o sistema DEVE (MUST) colocar os clientes
**sem regime informado** no fim do resultado, **nas duas direções** — a mesma
regra que já vale para a ordenação por certificado.

Ausência não é o primeiro regime nem o último: é ausência, e vai para o fim.
Duas colunas da mesma tabela tratando o vazio de maneiras opostas obrigariam o
usuário a decorar qual é qual.

#### Scenario: Ordem crescente por regime

- **WHEN** o usuário ordena por regime em ordem crescente
- **THEN** os clientes com regime informado aparecem primeiro, agrupados por
  regime, e os sem regime vêm depois de todos eles

#### Scenario: Ordem decrescente por regime

- **WHEN** o usuário ordena por regime em ordem decrescente
- **THEN** a ordem dos regimes se inverte, e os clientes sem regime continuam
  depois de todos eles

### Requirement: A sincronização do agente preserva o regime tributário

A sincronização de clientes feita pelo agente NÃO DEVE (MUST NOT) alterar o
regime tributário de um cliente já existente, nem preenchê-lo ao cadastrar um
cliente novo.

O agente deriva o que sabe do nome e do conteúdo dos certificados na máquina do
escritório — código, nome, CNPJ e validade. O regime tributário não está em
lugar nenhum desse material: só uma pessoa informa. Se a sincronização
escrevesse nesse campo, escreveria "não informado" por cima da escolha feita na
tela, e o regime sumiria sozinho na próxima execução do agente, sem ninguém
entender por quê.

#### Scenario: Sincronização de cliente com regime informado

- **WHEN** o agente sincroniza um cliente que já existe e cujo regime foi
  informado pela tela
- **THEN** o cliente continua com o mesmo regime depois da sincronização, ainda
  que nome, CNPJ e validade do certificado tenham sido atualizados

#### Scenario: Cliente cadastrado pelo agente

- **WHEN** o agente cadastra um cliente que ainda não existia
- **THEN** o cliente nasce com o regime não informado, disponível para alguém
  informar pela tela

## MODIFIED Requirements

### Requirement: A listagem de clientes é ordenável pelo usuário

A tela de clientes DEVE (MUST) permitir escolher por qual coluna a listagem é
ordenada e em que direção, acionando o cabeçalho da própria coluna.

DEVEM (MUST) ser ordenáveis: código, nome, regime tributário, validade do
certificado e data da última atualização; e, para quem enxerga a coluna de
escritório, também o escritório. O CNPJ NÃO DEVE (MUST NOT) ser ordenável — o
valor guardado é mascarado, e ordenar por ele ordenaria por um texto
parcialmente oculto, parecendo um recurso sem ser um.

Acionar o cabeçalho da coluna já ordenada DEVE (MUST) inverter a direção;
acionar o de outra coluna DEVE (MUST) passar a ordenar por ela, em ordem
crescente.

**Toda coluna ordenável DEVE (MUST) se anunciar como tal**, esteja ou não
ordenando no momento, e DEVE (MUST) ser distinguível à primeira vista de uma
coluna que não ordena. Indicar apenas a coluna ativa não basta: as demais ficam
idênticas às que não ordenam, e a única pista de que são acionáveis aparece
depois que o usuário já levou o ponteiro até lá — ou seja, só para quem já
desconfiava.

A coluna e a direção vigentes DEVEM (MUST) ficar visíveis no cabeçalho, com
destaque distinto do que marca as demais como ordenáveis, para que a ordem
exibida nunca seja adivinhada. Isso vale **desde a abertura da tela**: a ordem
padrão DEVE (MUST) estar indicada antes de o usuário acionar qualquer coisa.

Os cabeçalhos DEVEM (MUST) ser acionáveis também por teclado, e receber foco
visível — ordenação que só responde a clique fica inalcançável para quem não usa
mouse.

Sem escolha alguma, a listagem DEVE (MUST) sair ordenada por **nome, crescente**
— o comportamento que já existia.

A ordenação DEVE (MUST) se aplicar ao conjunto inteiro que passou pelos filtros,
e não apenas à página exibida.

Trocar a ordenação DEVE (MUST) levar de volta à primeira página: a página em que
o usuário estava não tem relação com a lista reordenada.

O sistema DEVE (MUST) resolver a coluna pedida a partir de um conjunto fechado,
definido no servidor. Pedido com coluna desconhecida DEVE (MUST) cair no padrão,
sem erro — endereço antigo ou digitado à mão mostra a lista, não uma falha.

#### Scenario: Ordenar por uma coluna

- **WHEN** o usuário aciona o cabeçalho de uma coluna ordenável
- **THEN** a listagem passa a sair ordenada por ela em ordem crescente, e o
  cabeçalho indica a coluna e a direção

#### Scenario: Inverter a direção

- **WHEN** o usuário aciona o cabeçalho da coluna que já ordena a listagem
- **THEN** a direção se inverte, e a indicação no cabeçalho acompanha

#### Scenario: Trocar de coluna

- **WHEN** o usuário aciona o cabeçalho de uma coluna diferente da atual
- **THEN** a listagem passa a ser ordenada pela coluna nova, em ordem crescente

#### Scenario: Ordem padrão

- **WHEN** o usuário abre a tela sem escolher ordenação
- **THEN** a listagem sai ordenada por nome, em ordem crescente, e o cabeçalho
  de nome já indica que é ele quem ordena, e em que direção

#### Scenario: Coluna ordenável que não está ordenando

- **WHEN** o usuário olha o cabeçalho de uma coluna ordenável que não é a ativa
- **THEN** ela se apresenta como ordenável, distinguível da coluna que não
  ordena, e sem se confundir com a que está ordenando

#### Scenario: Ordenar pelo teclado

- **WHEN** o usuário leva o foco a um cabeçalho ordenável e o aciona pelo teclado
- **THEN** a listagem é reordenada por aquela coluna, como no acionamento por
  clique

#### Scenario: Ordenação alcança além da página

- **WHEN** o usuário ordena uma listagem que ocupa várias páginas
- **THEN** a ordem vale para todos os clientes filtrados, e a primeira página
  traz os primeiros dessa ordem — não os primeiros da página anterior
  reordenados

#### Scenario: Troca de ordenação volta à primeira página

- **WHEN** o usuário está numa página adiante e troca a ordenação
- **THEN** a listagem volta para a primeira página da ordem nova

#### Scenario: Coluna desconhecida

- **WHEN** a listagem é pedida com uma coluna de ordenação que não existe
- **THEN** o resultado sai na ordem padrão, e nenhum erro é devolvido

#### Scenario: CNPJ não é ordenável

- **WHEN** o usuário percorre os cabeçalhos da tabela
- **THEN** o de CNPJ não oferece ordenação

#### Scenario: Ordenar por regime tributário

- **WHEN** o usuário aciona o cabeçalho da coluna de regime tributário
- **THEN** a listagem passa a sair ordenada por regime, com os clientes de um
  mesmo regime juntos
