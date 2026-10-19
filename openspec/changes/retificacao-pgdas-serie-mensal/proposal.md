## Why

Retificar um PGDAS-D de competência antiga deixa a dashboard do cliente
contradizendo a si mesma. A apuração do mês é substituída ("Substituir e
gravar"), e os cards passam a mostrar o faturamento corrigido. Já o gráfico de
evolução de 12 meses continua com o valor antigo.

O gráfico lê `ReceitasMensaisCliente`, e o upsert dessa série só sobrescreve um
mês quando o documento novo é de competência igual ou mais recente que a do
documento que gravou o mês por último. Um exemplo:

- Março/2026 foi gravado pelo histórico do PGDAS de 08/2026.
- Depois, a retificadora de 03/2026 é importada. Ela é a única fonte que sabe o
  valor corrigido de março, mas a regra a trata como "mais antiga" e a
  descarta.

A regra "o documento mais recente prevalece" vale para o histórico. Para o mês
que o próprio documento declara, ela erra.

## What Changes

- No upsert da série mensal (`POST /api/pgdas/apuracoes`), a receita do mês que
  o documento **declara** (cada competência de `apuracoes`) passa a sempre
  sobrescrever a linha da série daquele mês, independentemente da competência
  de origem gravada antes.
- A receita de um mês que chega **só pelo histórico** (seção 2.2.1) de outro
  documento deixa de sobrescrever mês que tenha apuração gravada para o
  cliente. Para mês sem apuração, segue valendo a regra atual: prevalece o
  documento de competência mais recente.
- Com isso, para todo mês que tem apuração gravada, a série mensal passa a
  espelhar o faturamento da apuração. Cards e gráfico deixam de divergir.
- Correção dos dados já gravados: uma migration de dados alinha
  `ReceitasMensaisCliente.ReceitaBruta` ao `ApuracaoSimples.Faturamento` em
  todo mês em que os dois existem para o mesmo cliente. Sem ela, a divergência
  só some na próxima importação de cada cliente.
- Fora de escopo: histórico de versões da apuração (original × retificadoras),
  identificar o documento como retificador, ou mudar o fluxo de conflito 409 e
  confirmação de substituição. Esses itens continuam como hoje.

## Capabilities

### New Capabilities

_Nenhuma._

### Modified Capabilities

- `apuracao-simples-nacional`: o requisito "A série mensal do documento
  alimenta a evolução de 12 meses" passa a distinguir o mês declarado pelo
  documento do mês que vem só pelo histórico. O mês com apuração gravada passa
  a ter a apuração como autoridade.

## Impact

- **API:** `Features/Pgdas/PgdasEndpoints.cs`, `GravarApuracoesAsync`, no bloco
  de upsert da série mensal. O contrato de `POST /api/pgdas/apuracoes` não
  muda: o pedido já traz as competências declaradas em `apuracoes`.
- **Migration:** uma migration só de dados (`migrationBuilder.Sql`), sem
  alteração de modelo nem do `AppDbContextModelSnapshot`.
- **Testes:** `ContabOne.Api/tests/PgdasTest.cs` (Category=Banco), com os
  cenários de retificadora antiga, histórico de documento mais novo contra mês
  com apuração, e histórico contra mês sem apuração.
- **Frontend:** nenhuma mudança. `montarSerieMensal` já envia o mês declarado
  com o faturamento da própria competência, e a dashboard já lê a série do
  banco. Não há sobreposição com a change em andamento
  `importacao-pgdas-em-lote`, que mexe só no frontend da importação.
- **Privacidade:** inalterada. Só trafegam e são gravados os mesmos números que
  já trafegavam.
