## Context

Ver proposal.md, seção Why. A conferência morava em dois lados. A API
devolvia `Escritorio.CnpjHash` na carteira do DET. O agente lia o CNPJ do
`.pfx` (OID ICP-Brasil ou sufixo do CN), calculava o HMAC com o
`hmacCnpjKey` do handshake e saía com código `3` quando os hashes divergiam.
O cadastro admin de escritório nunca calcula esse HMAC: sem `cnpjHash` no
request, grava `manual-<guid>`, para não colidir no índice único.

## Goals / Non-Goals

**Goals:**

- O agente roda com a chave certa e o certificado da pasta, seja qual for o
  CNPJ cadastrado (ou não) para o escritório no painel.
- Nenhuma ordem obrigatória entre o deploy da API e a troca do `det.exe`.

**Non-Goals:**

- Calcular o HMAC do CNPJ do escritório no cadastro admin.
- Mexer em `Escritorio.CnpjHash`, no índice único ou no `hmacCnpjKey` do
  handshake, que o `Nfse.Agent` usa para os clientes.

## Decisions

- **Remover a conferência, em vez de consertar o hash do escritório.** Uma
  alternativa era o cadastro admin receber o CNPJ completo e calcular o
  HMAC, como `ClientesEndpoints.DerivarCnpj` faz para clientes. A outra era a
  API mandar vazio quando o hash é provisório. A primeira exige recadastrar
  todo escritório. A segunda só troca o bloqueio por um aviso que nunca some.
  O dono do produto escolheu confiar só na chave.
- **Tirar o campo da resposta, não só ignorá-lo no agente.** Um campo que
  nenhum consumidor lê convida alguém a religar a conferência sem rever esta
  decisão. O agente 1.0.0 já trata a ausência como hash vazio. Então a
  remoção não quebra quem está em campo.
- **Apagar `certificado.py` e os helpers de hash e máscara do agente.** Eles
  só serviam à conferência. `DecisaoLicenca.hmac_cnpj_key` fica: espelha o
  handshake, como os demais campos que o DET não usa.

## Risks / Trade-offs

- [Certificado de outra empresa em `certificado/` não é mais barrado antes
  do login] → O portal só deixa trocar para perfis com procuração do titular.
  A conferência do empregador em tela (`ErroEmpregadorDivergente`) continua
  impedindo que mensagens sejam atribuídas ao CNPJ errado.
- [Agente 1.0.0 com a API nova loga "escritorio nao tem CNPJ cadastrado"] →
  O aviso é inofensivo e some quando o `det.exe` novo for distribuído.

## Migration Plan

1. Publicar a API e distribuir o `det.exe` novo, em qualquer ordem.
2. Rollback: reverter os dois repositórios. Escritório sem HMAC real volta a
   ficar bloqueado no DET, como antes.
