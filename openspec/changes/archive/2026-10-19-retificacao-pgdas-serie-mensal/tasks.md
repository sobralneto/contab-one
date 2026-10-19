## 1. Upsert da série mensal

- [x] 1.1 Em `GravarApuracoesAsync` (`Features/Pgdas/PgdasEndpoints.cs`), gravar a série dos meses declarados (cada competência de `req.Apuracoes`) a partir de `item.Faturamento`, sem condição de origem, com `OrigemCompetencia` = a própria competência, criando a linha quando não existir
- [x] 1.2 Para os meses de `req.SerieMensal` que não são declarados no pedido, carregar numa única consulta as competências com `ApuracaoSimples` gravada para o cliente e pular as que estiverem nesse conjunto; para as demais, manter a regra atual (`CompetenciaDocumento >= OrigemCompetencia`)
- [x] 1.3 Atualizar o comentário do bloco de upsert e o `<summary>` de `ReceitaMensalCliente` (`Domain/Entities.cs`), que hoje dizem só "o documento mais recente sobrescreve", para a nova precedência

## 2. Correção dos dados já gravados

- [x] 2.1 Criar a migration só de dados com `dotnet ef migrations add AlinhaSerieMensalComApuracao --project ContabOne.Api`, sem mudança de modelo e com o snapshot intacto
- [x] 2.2 Expor o SQL como constante pública da migration: `UPDATE ... FROM "ApuracoesSimples"` onde a receita diverge, seguido do `INSERT ... SELECT ... ON CONFLICT DO NOTHING` para mês com apuração e sem linha na série; `Up` executa a constante e `Down` fica vazio, com comentário dizendo por quê

## 3. Testes (`ContabOne.Api/tests/PgdasTest.cs`, Category=Banco)

- [x] 3.1 Retificadora antiga: gravar 2026-08 com histórico de 2026-03 = 1000; gravar 2026-03 com faturamento 1500 e `substituir = true` → série de 2026-03 = 1500, igual ao faturamento da apuração
- [x] 3.2 Histórico não desfaz apuração: com apuração de 2026-03 gravada (faturamento 1500), gravar 2026-09 com histórico de 2026-03 = 900 → série de 2026-03 continua 1500
- [x] 3.3 Mês declarado vence a série do próprio pedido: pedido com apuração 2026-04 de faturamento 700 e `serieMensal` trazendo 2026-04 = 650 → série de 2026-04 = 700
- [x] 3.4 Garantir que `GravarLote_ComSerieMensalRepetida_DocumentoMaisRecentePrevalece` (mês sem apuração) continua passando sem alteração
- [x] 3.5 Migration de dados: semear apuração e série divergentes, mais um mês com apuração e sem linha na série; executar a constante SQL via `ExecuteSqlRawAsync` → série alinhada e linha criada; executar de novo → nada muda (idempotência)

## 4. Verificação

- [x] 4.1 Rodar `npm test` na raiz e confirmar que a suíte da API (incluindo Category=Banco) passa
- [x] 4.2 Conferir na dashboard de um cliente local, após retificar uma competência antiga, que o card e o gráfico de 12 meses mostram o mesmo faturamento para o mês
