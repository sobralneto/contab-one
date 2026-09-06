## ADDED Requirements

### Requirement: A listagem de clientes é ordenável pelo usuário

A tela de clientes DEVE (MUST) permitir escolher por qual coluna a listagem é
ordenada e em que direção, acionando o cabeçalho da própria coluna.

DEVEM (MUST) ser ordenáveis: código, nome, validade do certificado e data da
última atualização; e, para quem enxerga a coluna de escritório, também o
escritório. O CNPJ NÃO DEVE (MUST NOT) ser ordenável — o valor guardado é
mascarado, e ordenar por ele ordenaria por um texto parcialmente oculto,
parecendo um recurso sem ser um.

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

### Requirement: A ordenação da listagem é estável entre páginas

O sistema DEVE (MUST) garantir que clientes empatados na coluna escolhida
tenham entre si uma ordem **determinística**, igual a cada pedido, aplicando um
critério de desempate próprio depois da coluna escolhida.

Sem esse desempate, o banco fica livre para ordenar o empate como quiser a cada
consulta, e a paginação passa a mentir: com nomes repetidos ou vários
certificados nulos, o mesmo cliente pode aparecer em duas páginas enquanto outro
não aparece em nenhuma — e o usuário não tem como perceber.

#### Scenario: Empate na coluna ordenada

- **WHEN** vários clientes têm o mesmo valor na coluna escolhida e a listagem é
  pedida mais de uma vez
- **THEN** eles saem sempre na mesma ordem relativa

#### Scenario: Paginação sobre empate

- **WHEN** o usuário percorre todas as páginas de uma listagem ordenada por uma
  coluna com muitos valores repetidos
- **THEN** cada cliente aparece exatamente uma vez no conjunto das páginas,
  nenhum é repetido e nenhum é omitido

### Requirement: Cliente sem certificado não encabeça a ordenação por certificado

Ao ordenar pela validade do certificado, o sistema DEVE (MUST) colocar os
clientes **sem certificado registrado** no fim do resultado, **nas duas
direções**.

Ordem decrescente que começasse pelos ausentes abriria a lista com quem não tem
certificado nenhum, empurrando para baixo justamente o que a coluna existe para
mostrar. Ausência não é o maior valor nem o menor: é ausência, e vai para o fim.

#### Scenario: Ordem crescente por certificado

- **WHEN** o usuário ordena por certificado em ordem crescente
- **THEN** os clientes aparecem do vencimento mais próximo ao mais distante, e
  os sem certificado vêm depois de todos eles

#### Scenario: Ordem decrescente por certificado

- **WHEN** o usuário ordena por certificado em ordem decrescente
- **THEN** os clientes aparecem do vencimento mais distante ao mais próximo, e
  os sem certificado continuam depois de todos eles
