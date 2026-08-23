# autorizacao-endpoints-agente Specification

## Purpose

Define quem pode alcançar os endpoints que servem o agente instalado no escritório, separando esse canal das sessões humanas do painel para que segredos e ativos técnicos entregues ao agente não fiquem ao alcance de qualquer usuário logado.

## Requirements

### Requirement: Os endpoints do agente só atendem agentes

O sistema DEVE (MUST) exigir credencial de agente (API key de um agente ativo, de um escritório ativo) em todos os endpoints do grupo `/api/agent`, e NÃO DEVE (MUST NOT) atendê-los com uma sessão humana do painel, qualquer que seja o papel dessa sessão — incluindo `PlatformAdmin`.

A separação DEVE (MUST) ser feita por autorização declarada no grupo, e não depender de o handler quebrar por falta de dados do agente.

#### Scenario: Usuário do painel chama endpoint do agente

- **WHEN** um usuário autenticado no painel, de qualquer papel, chama qualquer endpoint sob `/api/agent`
- **THEN** a API responde 403 sem executar o handler

#### Scenario: Agente com API key válida

- **WHEN** um agente ativo de um escritório ativo chama um endpoint sob `/api/agent`
- **THEN** o pedido é atendido normalmente

#### Scenario: Agente revogado

- **WHEN** um agente cuja chave foi revogada chama um endpoint sob `/api/agent`
- **THEN** a API responde 401

### Requirement: O bundle de regras de coleta não é público para usuários do painel

O sistema DEVE (MUST) restringir a leitura do conteúdo do bundle de regras de coleta a agentes autenticados e a administradores da plataforma. Um usuário de escritório NÃO DEVE (MUST NOT) conseguir baixá-lo.

O bundle descreve o protocolo de raspagem dos portais e é o ativo técnico do produto.

#### Scenario: Usuário de escritório pede o bundle

- **WHEN** um usuário com papel `EscritorioUsuario` ou `EscritorioAdmin` pede o bundle de regras
- **THEN** a API responde 403 e nenhum conteúdo de regra é devolvido

#### Scenario: Agente pede o bundle

- **WHEN** um agente autenticado pede o bundle de regras
- **THEN** a API devolve a versão ativa do bundle

#### Scenario: PlatformAdmin consulta regras pela área administrativa

- **WHEN** um `PlatformAdmin` consulta uma regra pela área administrativa
- **THEN** o conteúdo é devolvido normalmente

### Requirement: Cadastro de cliente pelo canal do agente exige agente

O sistema DEVE (MUST) recusar escrita de clientes pelo canal do agente quando o pedido não vier de um agente. Usuários do painel DEVEM (MUST) cadastrar clientes apenas pelo canal do painel, onde a origem do registro é marcada como manual e as validações do painel se aplicam.

#### Scenario: Usuário do painel tenta gravar cliente pelo canal do agente

- **WHEN** um usuário do painel envia clientes para o endpoint de upsert do agente
- **THEN** a API responde 403 e nenhum cliente é criado ou alterado

#### Scenario: Agente envia clientes

- **WHEN** um agente envia seus clientes para o endpoint de upsert
- **THEN** os clientes do escritório daquele agente são criados ou atualizados com origem marcada como agente
