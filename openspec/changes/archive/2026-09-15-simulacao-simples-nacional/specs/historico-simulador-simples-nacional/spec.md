## ADDED Requirements

### Requirement: O histórico lista as simulações salvas do escritório

O sistema DEVE (MUST) oferecer uma página de histórico, rota transversal
`/simulador/historico`, alcançada por um botão dentro da página do Simulador
— sem entrada própria no menu do escritório. A página DEVE (MUST) listar as
simulações salvas do escritório da sessão (nome, CNPJ, anexo e data de
gravação), ordenadas da mais recente para a mais antiga, e NÃO DEVE (MUST
NOT) exibir resultado calculado (indicadores, tabelas, RBT12) — só o que foi
gravado.

#### Scenario: Histórico com simulações salvas

- **WHEN** o escritório tem simulações salvas
- **THEN** a página lista cada uma com nome, CNPJ, anexo e data, da mais
  recente para a mais antiga

#### Scenario: Histórico vazio

- **WHEN** o escritório não salvou nenhuma simulação ainda
- **THEN** a página exibe um estado vazio, sem erro

#### Scenario: Isolamento por escritório

- **WHEN** dois escritórios diferentes salvaram simulações
- **THEN** o histórico de um não lista as simulações do outro

### Requirement: Uma simulação salva pode ser reaberta a partir do histórico

Cada linha do histórico DEVE (MUST) oferecer uma ação de **abrir**, que leva
o usuário à página do Simulador com nome, CNPJ, anexo e os 12 valores de
faturamento daquela simulação já preenchidos, e o resultado recalculado a
partir deles.

#### Scenario: Abrir uma simulação do histórico

- **WHEN** o usuário clica em abrir numa linha do histórico
- **THEN** a página do Simulador é aberta com os 4 campos daquela simulação
  preenchidos, e indicadores, tabelas e gráfico refletem esses valores

### Requirement: Uma simulação salva pode ser excluída

Cada linha do histórico DEVE (MUST) oferecer uma ação de **excluir**, que
remove definitivamente a simulação salva. A exclusão NÃO DEVE (MUST NOT)
afetar cliente, apuração ou qualquer outro dado do escritório — a simulação
não tem vínculo com nenhum deles.

#### Scenario: Excluir uma simulação

- **WHEN** o usuário confirma a exclusão de uma linha do histórico
- **THEN** a simulação some da listagem e não pode mais ser reaberta
