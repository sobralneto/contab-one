## Why

Na execução da L&J em 14/10/2026, a própria L&J (17.409.737/0001-65) estava
na carteira e falhou na etapa "Selecionar perfil": o DET recusa procuração
para o próprio usuário logado ("CNPJ deve ser diferente do usuário logado").
O certificado do escritório entra no gov.br com a identidade da L&J, então a
Caixa Postal dela já é a do perfil aberto. Não há procuração a assumir.

## What Changes

- O `Det.Agent` volta a ler o CNPJ do titular do certificado `.pfx` (OID
  ICP-Brasil ou sufixo do CN), só para reconhecer esse CNPJ na carteira. A
  leitura não interrompe a execução e não é conferida contra o cadastro do
  escritório no painel.
- A empresa da carteira cujo CNPJ é o do titular não passa pela troca de
  perfil. O agente vai direto à Caixa Postal e lê as mensagens no perfil
  próprio, mantendo a conferência do empregador em tela antes de ler.
- Sem CNPJ legível no certificado, ou num modo sem `.pfx` (`manual`,
  `politica_chrome`), nada muda: toda empresa passa pela troca de perfil.

## Capabilities

### New Capabilities

### Modified Capabilities

- `agente-det-integracao-api`: o CNPJ do titular do certificado deixa de ser
  digitado na troca de perfil; a empresa titular é consultada no próprio
  perfil.

## Impact

- `Det.Agent`: `certificado.py` (volta, só com a leitura do CNPJ),
  `settings.py`, `runner.py`, `govbr.py`, testes, `README.md` e o `LEIA-ME`
  do `build.py`.
- Sem mudança na API nem no painel.
- Distribuição: novo `det.exe` para os escritórios que usam o DET.
