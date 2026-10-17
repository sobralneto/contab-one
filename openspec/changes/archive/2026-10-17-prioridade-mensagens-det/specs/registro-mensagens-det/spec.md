## ADDED Requirements

### Requirement: A API guarda a prioridade por assunto de mensagem DET

A API DEVE (MUST) guardar, por escritório, uma prioridade (Baixa, Média ou Alta) associada a um assunto de mensagem DET. O assunto DEVE (MUST) ser identificado após normalização — remoção de espaços nas pontas e comparação sem diferença de maiúsculas/minúsculas — de modo que variações triviais do mesmo assunto compartilhem a mesma prioridade. Mensagens sem assunto DEVEM (MUST) compartilhar uma única prioridade própria. A prioridade NÃO DEVE (MUST NOT) ser guardada na mensagem individual. O valor DEVE (MUST) atravessar a rede como inteiro, como os demais enums.

#### Scenario: Assunto ainda não classificado

- **WHEN** não há prioridade definida para o assunto de uma mensagem
- **THEN** a consulta devolve `prioridade` nula para essa mensagem

#### Scenario: Variação de caixa e espaços

- **WHEN** a prioridade Alta é definida para "Aviso de pendência" e existe uma mensagem com o assunto " aviso de pendência "
- **THEN** a consulta devolve prioridade Alta para essa mensagem

#### Scenario: Prioridade isolada por escritório

- **WHEN** o escritório A define Alta para um assunto e o escritório B tem mensagens com o mesmo assunto
- **THEN** as mensagens do escritório B continuam sem prioridade

### Requirement: A consulta devolve a prioridade do assunto em cada mensagem

A consulta de mensagens DET DEVE (MUST) incluir, em cada mensagem, a prioridade vigente do seu assunto (nula quando não classificado). Todas as mensagens de um mesmo assunto DEVEM (MUST) trazer a mesma prioridade, incluindo mensagens coletadas depois da classificação.

#### Scenario: Mensagens já existentes

- **WHEN** a prioridade de um assunto é definida e o painel consulta as mensagens
- **THEN** todas as mensagens desse assunto trazem essa prioridade

#### Scenario: Mensagem coletada depois

- **WHEN** o agente envia uma mensagem nova cujo assunto já foi classificado
- **THEN** a consulta devolve essa mensagem já com a prioridade do assunto

### Requirement: O painel define ou limpa a prioridade de um assunto

A API DEVE (MUST) oferecer uma operação autenticada como usuário do escritório para definir a prioridade de um assunto como Baixa, Média ou Alta, ou limpá-la (nula). A operação DEVE (MUST) rejeitar valor fora dos níveis definidos, DEVE (MUST) atuar somente sobre o escritório em foco e NÃO DEVE (MUST NOT) alterar nenhuma mensagem. A chave de API de agente NÃO DEVE (MUST NOT) alcançar essa operação. Definir a prioridade de um assunto que já tinha uma DEVE (MUST) substituí-la, sem criar duplicata.

#### Scenario: Usuário classifica um assunto

- **WHEN** um usuário do escritório define a prioridade Média para um assunto
- **THEN** a prioridade é gravada e passa a ser devolvida, para todos os usuários do escritório, em todas as mensagens desse assunto

#### Scenario: Reclassificar

- **WHEN** o usuário define Alta para um assunto que estava Média
- **THEN** o assunto passa a Alta e continua havendo um único registro de prioridade para ele

#### Scenario: Limpar a classificação

- **WHEN** o usuário define a prioridade do assunto como nula
- **THEN** as mensagens desse assunto voltam a vir sem prioridade

#### Scenario: Valor inválido

- **WHEN** a operação recebe um valor que não é nenhum dos níveis
- **THEN** a API responde com erro de validação e não altera nada

#### Scenario: Chave de agente

- **WHEN** a operação é chamada com a chave de API de um agente
- **THEN** a API nega o acesso
