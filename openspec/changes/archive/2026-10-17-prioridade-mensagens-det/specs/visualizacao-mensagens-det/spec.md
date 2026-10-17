## ADDED Requirements

### Requirement: A página exibe a prioridade do assunto com cores de sinalização

A página de mensagens DET DEVE (MUST) exibir um selo com o nome do nível — "Alta", "Média" ou "Baixa" — nas cores de sinalização vermelho, amarelo e verde, respectivamente, obtidas de tokens do design system (nenhuma cor literal). O nível DEVE (MUST) sempre aparecer por texto além da cor. Assunto sem classificação DEVE (MUST) ser mostrado como "Sem prioridade", em estilo neutro. O selo DEVE (MUST) aparecer na linha do grupo da visão agrupada, em cada mensagem da lista plana e no modal de leitura, sempre com a prioridade do assunto da mensagem.

#### Scenario: Assunto de prioridade alta

- **WHEN** o assunto de um grupo tem prioridade Alta
- **THEN** a linha do grupo mostra o selo "Alta" em vermelho

#### Scenario: Assunto sem classificação

- **WHEN** o assunto não tem prioridade
- **THEN** a página mostra "Sem prioridade" em estilo neutro

#### Scenario: Lista plana e modal

- **WHEN** o usuário vê uma mensagem na lista plana ou abre a leitura dela
- **THEN** o selo exibido é o da prioridade do assunto dessa mensagem e não oferece edição

### Requirement: A classificação é feita por assunto, na linha do grupo

A página DEVE (MUST) oferecer o controle para definir a prioridade (Alta, Média, Baixa) ou limpá-la **somente na linha do grupo por assunto** da visão agrupada. A página NÃO DEVE (MUST NOT) oferecer classificação por mensagem individual. O controle DEVE (MUST) ser operável por teclado, indicar o nível atual de forma acessível e refletir imediatamente a mudança em todas as mensagens do assunto, inclusive na lista plana. Se a gravação falhar, a página DEVE (MUST) restaurar o nível anterior. Acionar o controle NÃO DEVE (MUST NOT) expandir ou recolher o grupo.

#### Scenario: Classificar um assunto

- **WHEN** o usuário escolhe "Alta" no controle da linha de um grupo
- **THEN** a prioridade do assunto é gravada e o selo do grupo passa a "Alta" em vermelho

#### Scenario: Reflexo na lista plana

- **WHEN** o usuário classifica um assunto e depois troca para a visão "Lista"
- **THEN** todas as mensagens desse assunto mostram o selo da nova prioridade

#### Scenario: Limpar a classificação

- **WHEN** o usuário escolhe limpar a prioridade de um assunto classificado
- **THEN** o grupo volta a "Sem prioridade"

#### Scenario: Falha ao gravar

- **WHEN** a gravação da prioridade falha
- **THEN** o selo volta ao nível anterior

#### Scenario: Controle não expande o grupo

- **WHEN** o usuário aciona o controle de prioridade de um grupo
- **THEN** o estado de expansão do grupo não muda

#### Scenario: Sem classificação por mensagem

- **WHEN** o usuário vê as mensagens expandidas de um grupo, a lista plana ou o modal de leitura
- **THEN** não há controle para alterar a prioridade da mensagem individual
