## Purpose

Corrige a tela de gerenciamento de escritórios: modal de edição deve carregar plano e status corretamente, a tabela deve exibir o nome do status e a edição deve persistir os dados.

## ADDED Requirements

### Requirement: Modal de edição carrega dados completos

Ao abrir o modal de edição de um escritório, o sistema DEVE carregar e exibir o plano e o status atualmente vinculados ao escritório.

#### Scenario: Admin abre modal de edição

- **WHEN** o admin clica em editar um escritório
- **THEN** o modal exibe os campos preenchidos com os dados atuais, incluindo plano e status corretos

### Requirement: Tabela exibe nome do status

Na tabela de escritórios, o sistema DEVE exibir o nome do status (ex: "Ativo", "Inativo") em vez do código numérico.

#### Scenario: Visualização da tabela de escritórios

- **WHEN** um admin acessa a tela de escritórios
- **THEN** a coluna de status exibe o nome legível do status, não um número

### Requirement: Edição de escritório funcional

O sistema DEVE persistir corretamente as alterações feitas no modal de edição de um escritório.

#### Scenario: Admin edita e salva um escritório

- **WHEN** o admin altera dados de um escritório no modal e clica em salvar
- **THEN** os dados são atualizados e refletidos na tabela

#### Scenario: Admin cancela edição

- **WHEN** o admin abre o modal de edição e clica em cancelar
- **THEN** nenhuma alteração é persistida e o modal é fechado

### Requirement: Edição de CNPJ do escritório

O sistema DEVE persistir a alteração do CNPJ feita no modal de edição de um escritório.

#### Scenario: Admin altera o CNPJ e salva

- **WHEN** o admin altera o CNPJ de um escritório no modal de edição e clica em salvar
- **THEN** a tabela exibe o CNPJ atualizado após a recarga da listagem

### Requirement: Cadastro de escritório com os mesmos campos da edição

O modal de cadastro de escritório DEVE exibir os mesmos campos do modal de edição: Nome, CNPJ, Plano e Status.

#### Scenario: Admin cadastra escritório com plano e status

- **WHEN** o admin preenche Nome, CNPJ, seleciona um plano e um status no modal de cadastro e salva
- **THEN** o escritório é criado com o plano e o status selecionados

### Requirement: Cadastro de escritório sem CNPJ não falha

O sistema DEVE permitir cadastrar escritórios sem informar CNPJ, inclusive múltiplos escritórios consecutivos nessa condição.

#### Scenario: Dois cadastros consecutivos sem CNPJ

- **WHEN** o admin cadastra dois escritórios sem preencher o CNPJ
- **THEN** ambos os escritórios são criados com sucesso, sem erro de persistência
