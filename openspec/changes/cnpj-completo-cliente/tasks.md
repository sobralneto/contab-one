## 1. Banco de dados

- [ ] 1.1 Adicionar `CnpjCifrado` (`string?`) e `CnpjConfirmadoManualmente`
      (`bool`, default `false`) em `Cliente` (`ContabOne.Api/Domain/Entities.cs`).
- [ ] 1.2 `dotnet ef migrations add CnpjCompletoCliente --project ContabOne.Api`;
      conferir `AppDbContextModelSnapshot.cs` gerado (nunca editar à mão).

## 2. Segurança — cifra do CNPJ completo

- [ ] 2.1 Criar `ContabOne.Api/Security/CnpjCipher.cs`: AES-256-GCM, chave
      `HMAC-SHA256(key = HMAC_CNPJ_KEY, msg = "cnpj-completo-v1")`, envelope
      `base64(nonce[12] ‖ ciphertext ‖ tag[16])` — mesmo formato de
      `ConfiguracaoCipher.cs`. Expor `Cifrar(cnpjLimpo, hmacCnpjKey)` e
      `Decifrar(envelopeBase64, hmacCnpjKey)`.
- [ ] 2.2 Adicionar `CnpjHasher.Formatar(cnpjLimpo)` devolvendo o CNPJ
      pontuado por extenso (`00.000.000/0000-00`), para exibir o valor
      decifrado de forma consistente com a formatação já usada na máscara.
- [ ] 2.3 Testes de `CnpjCipher` (round-trip, e que adulterar o envelope
      falha a autenticação do GCM) espelhando a cobertura de
      `ConfiguracaoCipherTest`/equivalente.

## 3. API — cadastro e edição manual de cliente

- [ ] 3.1 `ClientesEndpoints.cs`: estender `DerivarCnpj` (ou o ponto de
      chamada) para também cifrar o CNPJ limpo com `CnpjCipher.Cifrar`.
- [ ] 3.2 `CriarAsync` e `AtualizarAsync`: quando `req.Cnpj` vier informado,
      gravar `CnpjCifrado` e marcar `CnpjConfirmadoManualmente = true`.
      Quando `req.Cnpj` vier vazio/ausente, não mexer no que já está
      gravado (comportamento atual de hash/máscara para esse caso não muda).
- [ ] 3.3 `ClientesTest.cs`: criar/editar informando CNPJ persiste
      `CnpjCifrado` e marca confirmação manual; editar sem CNPJ mantém os
      valores existentes; listagem/busca de clientes nunca inclui
      `CnpjCifrado` no payload.

## 4. API — importação do PGDAS-D

- [ ] 4.1 `PgdasEndpoints.cs` (fluxo de importação, em torno de onde
      `CnpjHasher.Mascarar`/`Hash` já são chamados a partir de `req.Cnpj`):
      também cifrar e persistir `CnpjCifrado` no cliente localizado ou
      criado. Não mexe em `CnpjConfirmadoManualmente` — fica reservado ao
      formulário de cliente (ver design.md, Decisão 4 / Non-Goals).
- [ ] 4.2 `PgdasTest.cs`: importar um documento persiste `CnpjCifrado` no
      cliente correspondente.

## 5. API — sincronização do agente

- [ ] 5.1 `AgentEndpoints.cs` (`UpsertClientesAsync`, bloco de atualização de
      cliente existente): envolver a gravação de `CnpjMascarado`/`CnpjHash`
      em `if (!existente.CnpjConfirmadoManualmente)`. Cliente novo continua
      nascendo com `CnpjConfirmadoManualmente = false` (default da entidade).
- [ ] 5.2 `ContratoAgenteTest.cs`: sincronizar um cliente com CNPJ confirmado
      manualmente não altera `CnpjMascarado`/`CnpjHash`/`CnpjCifrado`;
      sincronizar um cliente sem confirmação atualiza normalmente, como
      antes desta mudança; cliente novo criado pelo agente nasce sem
      confirmação.

## 6. API — dashboard do PGDAS

- [ ] 6.1 `PgdasEndpoints.DashboardAsync`: incluir `CnpjCifrado` na projeção
      inicial de `cliente` (hoje só `{ Id, Nome, CnpjMascarado }`), decifrar
      quando presente (`CnpjCipher.Decifrar` + `CnpjHasher.Formatar`) e
      expor como `CnpjCompleto` (nulo quando não disponível) nas duas
      respostas do endpoint — a de "sem apurações" e a completa — ao lado de
      `CnpjMascarado`, que continua existindo para o fallback.
- [ ] 6.2 `PgdasTest.cs`: payload da dashboard traz `cnpjCompleto` quando o
      cliente tem `CnpjCifrado` gravado, e vem nulo/ausente quando não tem;
      `GET /api/pgdas/apuracoes` (listagem) e qualquer export continuam sem
      o campo.

## 7. Frontend — tela de Clientes

- [ ] 7.1 `ClientesView.vue`: remover a condição
      `:disabled="editando && clienteEdit?.origem === 'Agente'"` do campo de
      CNPJ. Atualizar a dica ao lado do campo (hoje "Atualizado
      automaticamente pelo agente") para explicar que o agente só substitui
      o valor até alguém confirmar pela tela — mesmo espírito da dica já
      existente no campo de validade do certificado.
- [ ] 7.2 `ClientesView.spec.ts`: campo de CNPJ habilitado ao editar cliente
      de origem `Agente`; salvar um CNPJ envia o valor no payload de
      atualização.

## 8. Frontend — dashboard do PGDAS

- [ ] 8.1 `features/pgdas/dashboard/tipos.ts`: acrescentar `cnpjCompleto?:
      string` ao tipo do payload da dashboard.
- [ ] 8.2 `features/pgdas/dashboard/documento.ts`: `DashboardDados.cliente`
      ganha `cnpjCompleto?: string`; `montarDadosDashboard` repassa o campo;
      em `dashHTML`, a linha `sub` passa a preferir `cnpjCompleto` e cai
      para `cnpjMascarado` quando ausente. `baixarHtml`/`baixarPdf`
      (`PgdasDashboardView.vue`) não precisam mudar — reusam `dashHTML`.
- [ ] 8.3 `documento.spec.ts`: cobre a montagem da dashboard com e sem
      `cnpjCompleto` disponível.

## 9. Validação final

- [ ] 9.1 `npm test` (roda só o afetado); como a mudança toca migration +
      API + frontend juntos, rodar também `npm run test:tudo` antes de
      abrir o PR.
- [ ] 9.2 `npm --prefix ContabOne.Frontend run build` (gate de typecheck)
      depois das mudanças de tipos em `tipos.ts`/`documento.ts`.
