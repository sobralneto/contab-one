## Context

`Cliente.CnpjCifrado` guarda `base64(nonce ‖ ciphertext ‖ tag)` com chave
derivada de `HMAC_CNPJ_KEY`. Decisão do produto: o CNPJ completo deve ser
legível no banco. Decifrar AES-GCM não é possível em SQL puro, então a
migração dos dados existentes precisa de código com acesso à chave.

## Goals / Non-Goals

**Goals:** coluna legível `Cnpj`; nenhum cliente perde o CNPJ já gravado;
contrato de API inalterado.

**Non-Goals:** remover `CnpjCifrado`/`CnpjCipher` agora; mudar hash, máscara,
precedência do agente ou o agente Python.

## Decisions

**1. Coluna nova `Cliente.Cnpj`, só dígitos (14).** Formatação
(`CnpjHasher.Formatar`) continua só na apresentação. Alternativa: reaproveitar
`CnpjCifrado` com texto puro — rejeitada, o nome mentiria e dados cifrados e
claros conviveriam na mesma coluna sem distinção.

**2. Backfill em código no startup, depois do `Migrate()`.** Para cada
cliente com `CnpjCifrado != null` e `Cnpj == null`, decifra com
`CnpjCipher.Decifrar` e grava em `Cnpj`. Idempotente (só toca quem falta); um
envelope que falhe na autenticação (chave rotacionada) é logado e ignorado,
sem derrubar o boot. Roda sem filtro de tenant (`IgnoreQueryFilters`).
Alternativa: migration EF com SQL — impossível decifrar AES-GCM no banco.

**3. `CnpjCifrado` fica como legado nesta change.** Para de ser escrito e
lido (exceto pelo backfill). Remoção da coluna e de `CnpjCipher` numa change
própria, após o backfill ser confirmado em produção — evita perda de dados
irreversível num único deploy.

**4. Escrita e leitura.** `DerivarCnpj` devolve o CNPJ limpo em vez do cifrado;
cadastro/edição, importação PGDAS-D e sync do agente gravam `Cnpj`. A
dashboard formata `Cnpj`. `TemCnpjCompleto = Cnpj != null`.

## Risks / Trade-offs

- Dump do banco expõe o CNPJ completo de clientes de terceiros. Aceito por
  decisão do dono do produto; a fronteira passa a ser só "que DTO inclui o
  campo" (listagem, busca e CSV seguem mascarados).
- Se `HMAC_CNPJ_KEY` não for a mesma da gravação original, o backfill não
  decifra: clientes ficam sem `Cnpj` até o CNPJ ser reconfirmado pela tela.

## Migration Plan

1. Deploy: migration adiciona `Cnpj`; startup executa o backfill.
2. Conferir no banco: `SELECT count(*) FROM "Clientes" WHERE "CnpjCifrado" IS
   NOT NULL AND "Cnpj" IS NULL` deve dar 0.
3. Change seguinte remove `CnpjCifrado` e `CnpjCipher`.
Rollback: o código anterior continua lendo `CnpjCifrado`, que não é apagado.
