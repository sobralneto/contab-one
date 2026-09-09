## Why

Hoje a validade do certificado de um cliente de origem `Agente` é um campo morto
no painel: aparece desabilitado na edição, com a dica "Atualizado
automaticamente pelo agente". Quem renovou o certificado mas ainda não o
instalou na máquina do escritório não tem como registrar a data nova — e o
cliente segue aparecendo como vencido no dashboard, nos alertas e no filtro de
faixa de certificado, sem que ninguém possa corrigir.

Liberar o campo, sozinho, não resolve: a próxima sincronização do agente
gravaria por cima a validade do `.pfx` antigo, e a correção sumiria sem
explicação — exatamente o problema que a requirement do regime tributário já
descreve para outro campo.

## What Changes

- A sincronização do agente passa a **só avançar** a validade do certificado: se
  a data recebida for posterior à que já está gravada, atualiza; se for igual,
  anterior, ou nula, mantém a que está lá. Cliente novo continua nascendo com a
  data que o agente enviar, vencida ou não — é o primeiro registro, não um
  retrocesso.
- O campo "Validade do certificado" fica **editável no painel para qualquer
  cliente**, inclusive os de origem `Agente`. A trava de UI sai; a dica ao lado
  do campo passa a explicar quando o agente sobrescreve o valor informado.
- O CNPJ continua travado para cliente de origem `Agente` — não faz parte desta
  mudança.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `gestao-clientes`: a sincronização do agente ganha uma regra de precedência
  para a validade do certificado (só avança), e a edição manual da validade
  deixa de ser bloqueada por origem do cliente.

## Impact

- `ContabOne.Api/Features/Agent/AgentEndpoints.cs` — bloco de atualização do
  upsert de clientes (`UpsertClientesAsync`).
- `ContabOne.Frontend/src/views/ClientesView.vue` — campo de validade no modal
  de edição (atributo `disabled` e texto da dica).
- Testes: `ContabOne.Api/tests/ContratoAgenteTest.cs` e
  `ContabOne.Frontend/src/views/ClientesView.spec.ts`.
- Sem migration: nenhuma coluna muda. `PUT /api/clientes/{id}` já aceitava a
  validade de qualquer usuário do escritório — o contrato da API não muda.
