## Why

O `Det.Agent` comparava o HMAC do CNPJ lido do `.pfx` com o `CnpjHash` do
escritório da chave. Escritório cadastrado pelo painel admin não tem esse
HMAC: o cadastro grava um valor provisório (`manual-<guid>`). Com isso, a
conferência bloqueava toda execução do DET desses escritórios, mesmo com o
certificado certo. Foi o que aconteceu com a L&J em 14/10/2026. O dono do
produto decidiu que o escritório é identificado só pela chave de API.

## What Changes

- O `Det.Agent` deixa de ler o CNPJ do certificado e de comparar hashes. O
  certificado da pasta não interrompe mais a execução: o escritório é o da
  chave, e a carteira já vem escopada por ela.
- `GET /api/agent/det/clientes` deixa de devolver `escritorioCnpjHash`.
- Saem do agente `certificado.py` e os helpers de hash e máscara de CNPJ, que
  só serviam à conferência.
- Compatível nos dois sentidos, sem ordem de deploy. O agente 1.0.0 já
  distribuído, falando com a API nova, não recebe o hash, avisa e segue. O
  agente novo, falando com a API antiga, ignora o campo.
- **BREAKING (segurança):** um certificado de outra empresa esquecido em
  `certificado/` não é mais barrado antes do login no gov.br. Continua valendo
  a conferência do empregador em tela depois da troca de perfil
  (`ErroEmpregadorDivergente`). Por isso nenhuma mensagem é atribuída a um
  CNPJ que não seja o da tela.

## Capabilities

### New Capabilities

### Modified Capabilities

- `agente-det-integracao-api`: sai o requisito de que o certificado da pasta
  tem de ser do escritório da chave.
- `carteira-clientes-agente-det`: a resposta deixa de trazer o hash do CNPJ do
  escritório.

## Impact

- `Det.Agent`: `runner.py`, `api_client.py`, `certificado.py` (removido),
  testes (`teste_carteira`, `teste_api_client`, `_fake_api`), `README.md` e o
  `LEIA-ME` gerado pelo `build.py`.
- `ContabOne.Api`: `AgentEndpoints.cs` (`CarteiraDetAsync`,
  `CarteiraDetResponse`) e `tests/CarteiraDetTest.cs`.
- Sem migration. `Escritorio.CnpjHash` continua existindo, só não vai mais
  para o agente. O `hmacCnpjKey` do handshake fica: o `Nfse.Agent` usa.
- Distribuição: novo `det.exe` para os escritórios que usam o DET.
