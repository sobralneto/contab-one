## MODIFIED Requirements

### Requirement: `Det.Agent` consulta a carteira de clientes vinda da API

`Det.Agent` DEVE (MUST) obter a lista de empresas a consultar exclusivamente
da API (`carteira-clientes-agente-det`), depois do handshake e antes de abrir
o navegador, e NÃO DEVE (MUST NOT) ler planilha ou qualquer outra lista local
de empresas. Cada empresa consultada é identificada pelo `Cliente.Id`
recebido, e é o CNPJ completo recebido que o agente digita na troca de perfil
do DET, exceto o da empresa titular do certificado, consultada sem troca de
perfil. Quando a API informa clientes sem CNPJ completo, o agente DEVE (MUST)
registrar a quantidade no log como aviso e seguir com os demais.

#### Scenario: Execução normal

- **WHEN** `Det.Agent` roda e a API devolve três clientes
- **THEN** o agente consulta a Caixa Postal dos três, na troca de perfil com o
  CNPJ de cada um, sem precisar de nenhum `empresas.xlsx`

#### Scenario: Carteira vazia

- **WHEN** a API devolve a carteira sem nenhum cliente
- **THEN** o agente não abre o navegador, finaliza a execução sem mensagens
  e explica no log que não há cliente com CNPJ completo a consultar

#### Scenario: API indisponível ao buscar a carteira

- **WHEN** a chamada que busca a carteira falha por rede ou 5xx
- **THEN** a execução é encerrada com erro, sem abrir o navegador — não há
  lista local para cair de volta

#### Scenario: Filtro por empresa na linha de comando

- **WHEN** o operador passa `--empresa` com um CNPJ que está na carteira
- **THEN** só esse cliente é consultado

## ADDED Requirements

### Requirement: A empresa titular do certificado é consultada sem troca de perfil

Quando o CNPJ do titular do certificado `.pfx` estiver na carteira,
`Det.Agent` DEVE (MUST) consultar a Caixa Postal dessa empresa no perfil com
que entrou no DET, sem abrir a troca de perfil, e DEVE (MUST) manter a
conferência do empregador em tela antes de ler as mensagens. O CNPJ do
titular vem do conteúdo do certificado, nunca do nome do arquivo, e serve só
para reconhecer essa empresa: não interrompe a execução nem é conferido
contra o cadastro do escritório no painel.

#### Scenario: Escritório na própria carteira

- **WHEN** a carteira traz o CNPJ do titular do certificado junto com outros
  clientes
- **THEN** o agente lê as mensagens do titular sem abrir a troca de perfil, e
  os demais clientes passam pela troca de perfil como antes

#### Scenario: Tela exibe outro empregador na vez do titular

- **WHEN** o agente vai ler a Caixa Postal do titular e a tela exibe outro
  empregador
- **THEN** a leitura é interrompida com erro e nenhuma mensagem é atribuída
  ao titular

#### Scenario: Certificado sem CNPJ legível ou modo sem `.pfx`

- **WHEN** o agente não consegue ler o CNPJ do titular do certificado, ou
  roda num modo em que o navegador escolhe o certificado
- **THEN** a execução segue normalmente e toda empresa da carteira passa pela
  troca de perfil
