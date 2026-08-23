## MODIFIED Requirements

### Requirement: A chave de ofuscação de CNPJ é sempre entregue

O sistema DEVE (MUST) garantir que o handshake **de um agente autenticado** entregue uma chave HMAC de CNPJ não-vazia. A ausência da chave na configuração da API DEVE impedir a inicialização do serviço, em vez de produzir handshakes incompletos.

A chave DEVE (MUST) ser entregue exclusivamente por essa via: nenhuma sessão humana do painel, de qualquer papel, DEVE (MUST NOT) conseguir obtê-la por endpoint algum. A chave é a mesma para toda a plataforma e o espaço de CNPJ é pequeno o bastante para ser varrido por força bruta — quem a obtém reverte todo `CnpjHash` gravado e derruba a premissa de que o CNPJ nunca é persistido.

Sem essa chave o agente não consegue calcular o identificador estável de cada cliente e deixa de enviar o relatório inteiro da execução — uma falha que hoje só aparece como aviso em log local.

#### Scenario: API sobe sem a chave configurada

- **WHEN** a API é iniciada sem a variável de ambiente da chave HMAC de CNPJ
- **THEN** a inicialização falha com mensagem explícita indicando a variável faltante

#### Scenario: Handshake bem-sucedido

- **WHEN** um agente com chave válida faz handshake em uma API corretamente configurada
- **THEN** a resposta inclui a chave HMAC de CNPJ não-vazia

#### Scenario: Usuário do painel tenta o handshake

- **WHEN** um usuário autenticado no painel, de qualquer papel, chama o handshake
- **THEN** a API responde 403 e a chave HMAC de CNPJ não aparece em resposta alguma
