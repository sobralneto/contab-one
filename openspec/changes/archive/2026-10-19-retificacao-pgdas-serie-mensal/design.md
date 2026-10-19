## Context

`POST /api/pgdas/apuracoes` (`GravarApuracoesAsync`) grava duas coisas a
partir do mesmo documento:

- `ApuracaoSimples`: uma linha por cliente e competência, substituída no lugar
  quando o usuário confirma o 409. É dela que vêm os cards, a tabela e os
  totais da dashboard.
- `ReceitasMensaisCliente`: a série de receita bruta por mês, com chave
  `(EscritorioId, ClienteId, Competencia)`. É dela que vem o gráfico de
  evolução de 12 meses. O upsert de hoje só sobrescreve quando
  `req.CompetenciaDocumento >= linha.OrigemCompetencia`.

No frontend, `montarSerieMensal()` (`PgdasImportacaoView.vue`) já monta a série
dando prioridade ao mês declarado sobre o histórico, mas só **dentro do lote**.
Entre lotes, quem decide é o servidor. Ele compara só a competência do
documento, que é a mais recente do lote, e não sabe quais meses o documento
declara e quais só cita no histórico.

`ReceitasMensaisCliente` só é lida pelo `DashboardAsync`. Nenhum outro endpoint
ou relatório a consulta hoje.

## Goals / Non-Goals

**Goals:**

- Para todo mês com apuração gravada, a série mensal tem a mesma receita que o
  faturamento da apuração, e isso vale também depois de uma retificação.
- Corrigir os dados que já divergem em produção sem pedir reimportação.
- Não mudar o contrato do endpoint nem o frontend.

**Non-Goals:**

- Versionar a apuração (original × retificadoras) ou guardar o valor anterior.
- Reconhecer o documento como retificador pelo PDF.
- Mudar o fluxo de 409 e substituição.

## Decisions

### 1. Corrigir na gravação, não na leitura da dashboard

A regra fica no upsert, e uma migration de dados conserta o passivo.

*Alternativa considerada:* no `DashboardAsync`, sobrepor
`ApuracaoSimples.Faturamento` à série nos meses que têm apuração. É mais curta e
conserta o passivo sozinha. Foi descartada porque deixa
`ReceitasMensaisCliente` com valor errado gravado: cada consumidor futuro da
tabela (demonstrativo, exportação, simulador lendo RBT12) teria que repetir a
mesma sobreposição, e o primeiro que esquecer reintroduz a divergência. A
tabela deve estar certa por si.

### 2. "Mês declarado" = competência presente em `req.Apuracoes`

O servidor já recebe a lista das competências que o lote grava como apuração.
Esses são os meses que o documento declara. Para eles:

- a série recebe `item.Faturamento` da própria apuração, e não o valor de
  `req.SerieMensal` para o mesmo mês. A autoridade é a apuração, então o
  invariante vale mesmo que o frontend mande uma série inconsistente;
- `OrigemCompetencia` passa a ser a própria competência do mês;
- a escrita é incondicional, sem comparar com a origem anterior.

Isso não exige campo novo no pedido nem confiança na ordenação do frontend.

### 3. Histórico não sobrescreve mês com apuração

Para cada mês de `req.SerieMensal` que **não** é declarado no pedido, uma única
consulta carrega as competências em que o cliente tem `ApuracaoSimples`
gravada. Se o mês está nesse conjunto, a linha da série não é tocada. Caso
contrário, vale a regra atual (`CompetenciaDocumento >= OrigemCompetencia`).

*Alternativa considerada:* uma coluna `Declarado` em `ReceitaMensalCliente`.
Foi descartada porque duplica um fato que o banco já sabe (existe apuração
para o mês?) e exige manter o flag ao excluir uma apuração. Com a consulta,
excluir uma apuração devolve o mês naturalmente à regra do histórico.

### 4. Migration de dados idempotente, SQL testável

A migration usa só `migrationBuilder.Sql`, sem mudança de modelo e sem tocar o
snapshot. Ela tem dois comandos:

1. `UPDATE "ReceitasMensaisCliente" r SET "ReceitaBruta" = a."Faturamento", "OrigemCompetencia" = a."Competencia" FROM "ApuracoesSimples" a WHERE` mesmo
   escritório, cliente e competência, `AND r."ReceitaBruta" <> a."Faturamento"`;
2. `INSERT ... SELECT` a partir de `ApuracoesSimples` para os meses com
   apuração e sem linha na série, com `ON CONFLICT DO NOTHING`.

O SQL fica numa constante pública da classe da migration, para que um teste
`Category=Banco` semeie dados divergentes e execute exatamente o mesmo texto.
A migration roda num banco vazio no Testcontainers e, sozinha, não provaria
nada. `Down` é vazio: o valor antigo e errado não é recuperável nem desejável.

## Risks / Trade-offs

- **[Reimportar um PDF original velho depois da retificadora]** → a série
  volta ao valor original. Mas isso só acontece se o usuário confirmar a
  substituição no 409. A série segue a apuração, que é o que ele escolheu
  gravar. Os dois continuam coerentes.
- **[Faturamento editado à mão na conferência]** → a série recebe o valor
  editado, porque passa a vir de `item.Faturamento`. Isso é desejado: o
  gráfico mostra o que os cards mostram.
- **[Consulta extra por gravação]** → uma única consulta por pedido
  (`Select(Competencia)` filtrada por cliente). É desprezível perto do upsert
  linha a linha que já existe.
- **[Migration altera valores exibidos em produção]** → é o objetivo, e só
  muda meses em que a série contradiz a apuração do mesmo mês. O efeito
  visível é o gráfico passar a bater com os cards.

## Migration Plan

1. Deploy da API. A migration roda no startup e alinha o passivo.
2. Rollback: reverter o código. A migration de dados não precisa ser desfeita,
   porque os valores alinhados continuam corretos sob a regra antiga, que
   apenas pode voltar a desalinhá-los numa próxima retificação.
