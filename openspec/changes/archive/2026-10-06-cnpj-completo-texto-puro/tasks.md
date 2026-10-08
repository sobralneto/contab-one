## 1. Banco de dados

- [x] 1.1 `Cliente.Cnpj` (`string?`) em `Domain/Entities.cs`; migration
      `CnpjCompletoTextoPuro` via `dotnet ef migrations add`.

## 2. API

- [x] 2.1 `ClientesEndpoints.DerivarCnpj` devolve o CNPJ limpo; cadastro e
      edição gravam `Cnpj` (não mais `CnpjCifrado`); `TemCnpjCompleto`
      passa a ser `Cnpj != null`.
- [x] 2.2 `PgdasEndpoints` (importação e dashboard) e `AgentEndpoints`
      (sync) gravam/leem `Cnpj`; a dashboard usa `CnpjHasher.Formatar`.
- [x] 2.3 Backfill idempotente no startup (depois do `Migrate()`): decifra
      `CnpjCifrado` para `Cnpj`, ignora e loga envelope inválido.

## 3. Testes

- [x] 3.1 Atualizar `ClientesTest`, `PgdasTest`, `ContratoAgenteTest` para
      `Cnpj`; testar o backfill (preenche, idempotente, envelope inválido).

## 4. Validação

- [x] 4.1 `npm test` (só o afetado) e conferência da query de backfill em
      produção.
