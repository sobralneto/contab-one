## ADDED Requirements

### Requirement: O cadastro do cliente escolhe o modelo de onboarding

O cadastro e a edição de um cliente DEVEM (MUST) oferecer a escolha de qual modelo
de onboarding aquele cliente usa, entre os modelos disponíveis para o escritório.
A escolha é OPCIONAL: o cliente pode ficar sem modelo, e nesse caso simplesmente
não tem onboarding.

O sistema DEVE (MUST) recusar a gravação quando o modelo informado não existir ou
não estiver disponível para o escritório do cliente, e DEVE (MUST) permitir limpar
a escolha (voltar a "sem onboarding") na edição.

#### Scenario: Escolher modelo ao cadastrar

- **WHEN** o usuário cadastra um cliente e escolhe um modelo de onboarding
- **THEN** o cliente é gravado apontando para aquele modelo

#### Scenario: Cadastrar sem escolher modelo

- **WHEN** o usuário cadastra um cliente sem escolher modelo
- **THEN** o cliente é gravado sem modelo, e nenhuma ação de onboarding é oferecida
  para ele

#### Scenario: Trocar o modelo na edição

- **WHEN** o usuário edita um cliente e troca (ou limpa) o modelo de onboarding
- **THEN** a escolha nova é gravada, e o checklist do cliente passa a refletir o
  modelo atual

#### Scenario: Modelo inexistente

- **WHEN** a gravação informa um modelo que não existe ou não está disponível para o
  escritório
- **THEN** o pedido é recusado por validação, e o cliente não é gravado com esse
  modelo

### Requirement: A listagem de clientes dá acesso ao onboarding de quem tem modelo

Na coluna de ações da listagem de clientes, o sistema DEVE (MUST) oferecer a ação de
onboarding APENAS para clientes que já têm modelo escolhido. Para cliente sem
modelo, nenhuma ação de onboarding DEVE (MUST) aparecer — não há o que montar.

Quando a ação aparece, o efeito dela depende de o cliente já ter checklist: sem
checklist, a ação o cria e leva à página dele; com checklist, apenas abre a página.
As duas nunca aparecem juntas na mesma linha.

#### Scenario: Cliente sem modelo

- **WHEN** o usuário vê na listagem um cliente sem modelo de onboarding escolhido
- **THEN** a linha dele não oferece ação de onboarding alguma, mantendo as demais
  ações (editar, excluir)

#### Scenario: Cliente com modelo e sem checklist

- **WHEN** o usuário aciona a ação de onboarding na linha de um cliente que tem
  modelo mas ainda não tem checklist
- **THEN** o checklist é criado para aquele cliente e a aplicação abre a página de
  onboarding dele

#### Scenario: Cliente com checklist

- **WHEN** o usuário aciona a ação de onboarding na linha de um cliente que já tem
  checklist
- **THEN** a aplicação abre a página de onboarding existente daquele cliente, sem
  criar um novo
