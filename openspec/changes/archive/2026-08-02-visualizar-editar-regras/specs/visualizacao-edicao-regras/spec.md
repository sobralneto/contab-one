## Purpose

Permite que administradores da plataforma visualizem o conteúdo JSON de versões existentes das regras de coleta e utilizem esse conteúdo como ponto de partida para a criação de novas versões, reduzindo o risco de erro de digitação e facilitando ajustes pontuais.

## ADDED Requirements

### Requirement: Admin pode visualizar o conteúdo de uma regra existente

O sistema DEVE permitir que um PlatformAdmin visualize o conteúdo JSON completo de qualquer versão de regra publicada, sem precisar recriá-lo ou inspecionar o banco de dados.

#### Scenario: Admin expande uma linha do histórico

- **WHEN** o admin clica em uma linha da tabela de histórico de versões
- **THEN** o conteúdo JSON completo daquela versão é exibido abaixo da linha, formatado e somente leitura

#### Scenario: Admin recolhe o conteúdo expandido

- **WHEN** o admin clica novamente na linha expandida ou no botão de fechar
- **THEN** o conteúdo JSON é recolhido e a tabela volta ao estado normal

### Requirement: API retorna conteúdo de uma regra individual

O sistema DEVE expor um endpoint que retorna uma regra individual incluindo seu conteúdo completo.

#### Scenario: Frontend solicita detalhes de uma regra

- **WHEN** o frontend faz `GET /api/admin/regras/{id}` com um id válido
- **THEN** a API retorna `200` com o objeto da regra incluindo os campos `id`, `versao`, `publicadaEm`, `ativa`, `tamanhoConteudo` e `conteudo`

#### Scenario: Regra não encontrada

- **WHEN** o frontend faz `GET /api/admin/regras/{id}` com um id inexistente
- **THEN** a API retorna `404`

### Requirement: Admin pode carregar regra existente no editor

O sistema DEVE permitir que o admin carregue o conteúdo de uma versão existente no editor de nova versão, para usar como ponto de partida.

#### Scenario: Admin carrega versão anterior no editor

- **WHEN** o admin visualiza o conteúdo de uma versão existente e clica em "Carregar no editor"
- **THEN** o conteúdo JSON daquela versão é copiado para o textarea do editor de nova versão, e a tela rola até o editor

#### Scenario: Editor já contém texto não salvo

- **WHEN** o admin clica em "Carregar no editor" e o editor já contém texto não publicado
- **THEN** o sistema DEVE confirmar com o admin antes de sobrescrever o conteúdo atual do editor

### Requirement: Admin pode copiar JSON de uma regra

O sistema DEVE permitir que o admin copie o conteúdo JSON de uma versão existente para a área de transferência.

#### Scenario: Admin copia JSON para clipboard

- **WHEN** o admin visualiza o conteúdo de uma versão e clica em "Copiar JSON"
- **THEN** o JSON completo daquela versão é copiado para a área de transferência e uma confirmação visual é exibida ("Copiado!")
