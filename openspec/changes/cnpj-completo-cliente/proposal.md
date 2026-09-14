## Why

O CNPJ completo hoje nunca é persistido em lugar nenhum da plataforma — não é um
detalhe de implementação, é um requisito MUST documentado nas specs
`gestao-clientes` e `apuracao-simples-nacional`, e reforçado por um teste
dedicado no agente NFS-e (`teste_payload_vazamento.py`) que garante que o valor
nunca sai da máquina do escritório. O pedido original foi remover a
anonimização do CNPJ no extrato do PGDAS
(`/f/pgdas/dashboard/{clienteId}`), mas como o valor pleno nunca chega a ser
capturado, não existe "desmascarar" possível sem antes passar a armazená-lo —
isso é uma mudança de arquitetura e de contrato de privacidade, não um ajuste
de exibição.

## What Changes

- Nova coluna em `Cliente` para o CNPJ completo, **cifrado em repouso**
  (AES-256-GCM, mesmo padrão de `ConfiguracaoCipher`) — migration em
  `ContabOne.Api`.
- **BREAKING**: cadastro/edição manual de cliente (`ClientesEndpoints.cs`)
  passa a persistir o CNPJ completo informado, em vez de descartá-lo depois de
  derivar hash e máscara.
- **BREAKING**: importação de extrato/declaração do PGDAS-D
  (`PgdasEndpoints.cs`) passa a persistir o CNPJ completo lido do documento,
  em vez de descartá-lo depois de derivar hash e máscara.
- A dashboard do PGDAS (`/f/pgdas/dashboard/{clienteId}`) passa a exibir o
  CNPJ completo quando disponível, em vez do mascarado.
- Clientes cadastrados antes desta mudança — e os de origem `Agente` cujo
  CNPJ ninguém confirmou manualmente ainda — continuam sem o CNPJ completo:
  não há backfill possível (o hash é HMAC, irreversível). A tela precisa
  continuar funcionando para esses casos, com a máscara como fallback.
- **BREAKING**: o campo de CNPJ na edição de cliente
  (`ClientesView.vue`) fica **editável também para cliente de origem
  `Agente`** — hoje é bloqueado de propósito (decisão explícita da change
  `validade-certificado-editavel`: "o agente é a única fonte, não há caso de
  uso de correção manual"). Essa premissa deixa de valer: editar/confirmar o
  CNPJ manualmente passa a ser exatamente o caminho para um cliente de origem
  agente ganhar o CNPJ completo sem esperar o agente ser atualizado.
- Igual à regra "só avança" da validade do certificado, a sincronização do
  agente precisa de uma regra de precedência para não sobrescrever
  silenciosamente um CNPJ confirmado manualmente — diferente da validade,
  CNPJ não é comparável (não existe "mais recente"), então a regra é por
  marcação: uma vez confirmado pela tela, o agente para de escrever
  `CnpjMascarado`/`CnpjHash`/CNPJ completo daquele cliente.
- **Fora do escopo desta change, de propósito**: o agente NFS-e
  (`Nfse.Agent`) continua enviando só hash e máscara — não passa a enviar o
  CNPJ completo automaticamente. Isso significa que cliente de origem
  `Agente` só ganha o CNPJ completo por confirmação manual pela tela (o item
  acima), não sozinho. Fazer o agente enviar o valor pleno é maior (binário
  já em campo nas máquinas dos escritórios, reconciliar o teste de
  vazamento) e fica para uma change futura — ver design.md, Decisão 4.

## Capabilities

### Modified Capabilities
- `gestao-clientes`: o requirement "O cadastro aceita o CNPJ e deriva hash e
  máscara no servidor" muda — o CNPJ completo informado no cadastro/edição
  manual passa a ser persistido (não mais descartado). Dois requirements
  novos: a sincronização do agente passa a respeitar um CNPJ confirmado
  manualmente (não sobrescreve), e o campo de CNPJ na edição fica habilitado
  para cliente de qualquer origem.
- `apuracao-simples-nacional`: o requirement "O CNPJ do documento nunca é
  persistido inteiro" é revertido — o CNPJ completo lido no PGDAS-D passa a
  ser persistido, e a dashboard passa a exibi-lo por extenso em vez de
  mascarado.

## Impact

- **Banco**: migration nova adicionando coluna de CNPJ completo cifrado em
  `Cliente`, mais uma marcação de "CNPJ confirmado manualmente" (booleano)
  usada pela regra de precedência da sincronização.
- **API**: `ClientesEndpoints.cs`, `PgdasEndpoints.cs`, `AgentEndpoints.cs`
  (bloco de upsert em `UpsertClientesAsync`, mesmo método que já tem a regra
  "só avança" da validade do certificado), `Domain/Entities.cs`, e uma
  classe nova `Security/CnpjCipher.cs` (`CnpjHasher.cs` não muda).
- **Agente NFS-e**: nenhuma mudança nesta change (ver Non-Goals em
  design.md) — continua enviando só hash e máscara.
- **Frontend**: `features/pgdas/dashboard/documento.ts`,
  `views/pgdas/PgdasDashboardView.vue`, tipos em
  `features/pgdas/dashboard/tipos.ts`, e `views/ClientesView.vue` (atributo
  `disabled` e dica do campo de CNPJ no modal de edição).
- **Testes**: `ContabOne.Api/tests/ContratoAgenteTest.cs`,
  `ContabOne.Api/tests/ClientesTest.cs`,
  `ContabOne.Frontend/src/views/ClientesView.spec.ts`.
- **Segurança**: CNPJs completos passam a existir no Postgres multi-tenant
  compartilhado — cifrados em repouso (Decisão 1 do design.md), não em
  texto puro, então um dump isolado do banco não os expõe; quem também
  precisaria do segredo do lado da API (`HMAC_CNPJ_KEY`) para decifrar. Ainda
  assim, muda o perfil de risco: hoje nenhum agente malicioso com acesso à
  API/banco recupera CNPJ algum, porque o valor não existe em lugar nenhum;
  depois desta mudança, alguém com acesso à API (não só ao banco) passa a
  poder decifrar os CNPJs completos que existirem. O requirement de
  `handshake-agente` sobre a entrega da chave HMAC não muda, mas sua
  justificativa hoje cita a "premissa de que o CNPJ nunca é persistido" como
  o que está em jogo; essa premissa deixa de valer para os clientes que
  passarem a ter o valor completo.
- **Dados existentes**: sem backfill possível para clientes já cadastrados;
  o valor completo só existe para clientes cadastrados, editados,
  sincronizados ou importados depois desta mudança.
