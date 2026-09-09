## 1. API — precedência na sincronização

- [x] 1.1 Em `UpsertClientesAsync` (`ContabOne.Api/Features/Agent/AgentEndpoints.cs`),
      trocar a atribuição incondicional de `CertificadoValidade` no bloco do
      cliente existente por uma que só grava quando a data recebida é posterior
      à gravada (nulo recebido não altera; campo vazio aceita qualquer data).
- [x] 1.2 Comentar a regra no ponto da atribuição, no padrão do bloco vizinho —
      o que ela protege e por que a comparação é contra a data gravada, e não
      contra hoje; sem isso a próxima pessoa "corrige" para incondicional.
- [x] 1.3 Deixar `CertificadoNomeArquivo`, nome e CNPJ como estão: atualização
      incondicional, sem acoplar ao resultado da comparação.

## 2. API — testes de contrato

- [x] 2.1 Em `ContabOne.Api/tests/ContratoAgenteTest.cs`, cobrir data recebida
      posterior à gravada (atualiza) e anterior (mantém, com nome e CNPJ ainda
      atualizados na mesma chamada).
- [x] 2.2 Cobrir data igual à gravada, ausência de data no payload e cliente sem
      validade registrada recebendo data vencida (grava).
- [x] 2.3 Cobrir cliente novo cadastrado com validade já vencida — nasce com ela.
- [x] 2.4 Rodar `dotnet test --filter "FullyQualifiedName~ContratoAgenteTest"`.
      26/26 aprovados. Com a regra desligada à força, caem exatamente 2
      (`NaoRetrocedeAValidadeDoCertificado` e `SemValidadeNaoApagaAGravada`) —
      os outros quatro descrevem caminhos que a regra não altera.

## 3. Painel — campo liberado

- [x] 3.1 Em `ContabOne.Frontend/src/views/ClientesView.vue`, remover o
      `:disabled` do input de validade do certificado, mantendo o do CNPJ.
- [x] 3.2 Reescrever a dica do campo: hoje diz "Atualizado automaticamente pelo
      agente" ao lado de um campo morto; passa a explicar que o agente
      sobrescreve o valor quando encontra um certificado de validade mais longa.
- [x] 3.3 Em `ClientesView.spec.ts`, afirmar que o campo de validade está
      habilitado para cliente de origem agente (o teste vizinho do aviso de
      código é o modelo).
- [x] 3.4 Rodar `npm --prefix ContabOne.Frontend exec vitest run src/views/ClientesView.spec.ts`.
      33/33 aprovados.

## 4. Fechamento

- [x] 4.1 Rodar `npm test` (runner seletivo) e `npm --prefix ContabOne.Frontend run build`
      para o gate de tipos.
- [x] 4.2 `openspec validate validade-certificado-editavel --strict`.
