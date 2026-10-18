## Context

**Busca de clientes.** `ClientesEndpoints.AplicarFiltros` é o predicado único
de `GET /api/clientes` e `GET /api/clientes/exportar`. Para o termo de texto
ele usa `c.Nome.Contains(busca)` (e o mesmo para `Codigo` e `CnpjMascarado`).
No Npgsql isso vira `strpos(...) > 0` / `LIKE '%…%'` com a collation padrão do
banco — **sensível a maiúsculas e a acentos**. Como os nomes vêm, na maioria,
gravados em maiúsculas (cadastro pelo agente e pelo PGDAS-D), só um termo em
maiúsculas e com a acentuação exata encontra o cliente. O usuário espera o
comportamento do `LIKE` do SQL Server com a collation padrão (`…_CI_…`).

**Filtro do PGDAS-D.** `PgdasVisaoGeralView.vue` carrega até 10 páginas de 100
apurações (`listarTodas`) e filtra pelo nome do cliente **em memória**, com um
`<input>` de texto. `GET /api/pgdas/apuracoes` já aceita `clienteId`, mas a
visão geral não o usa. Quando a amostra é truncada, um cliente com apurações
só antigas não aparece de jeito nenhum.

Restrições: multi-tenancy pelo `TenantContext` (escopo nunca de parâmetro);
nenhum dado fiscal novo na API; o frontend não tem biblioteca de componentes
(nada de combobox pronto); cores e estilos só por tokens/classes do design
system.

## Goals / Non-Goals

**Goals:**
- Busca de clientes por "contém", sem distinção de caixa e de acentos, na
  listagem e na exportação, com o mesmo predicado.
- Filtro de cliente do PGDAS-D por seleção, aplicado no servidor, imune ao
  truncamento da lista geral.

**Non-Goals:**
- Mudar outras buscas da plataforma (`Arquivos` já usa `ToLower().Contains`;
  DET, tarefas etc.). Ficam como estão — podem adotar o mesmo helper depois.
- Busca por similaridade/erros de digitação (trigram, full-text).
- Índice para a busca: as listas são por escritório (centenas a poucos milhares
  de linhas) e o `Contains` atual já não usa índice.
- Combobox com digitação dentro do select do PGDAS-D.
- Fazer os KPIs do resumo seguirem o cliente escolhido.

## Decisions

### 1. `ILIKE` sobre `unaccent(...)`, via `EF.Functions`

O predicado passa a ser, para cada coluna de texto:

```csharp
EF.Functions.ILike(EF.Functions.Unaccent(c.Nome), EF.Functions.Unaccent(padrao))
```

com `padrao = "%" + EscaparLike(termo.Trim()) + "%"`, num helper estático
reaproveitado pelas três colunas (nome, código, CNPJ mascarado). A busca pelos
dígitos do CNPJ completo (`c.Cnpj.Contains(digitos)`) não muda — só tem
dígitos.

Alternativas consideradas:
- **`ToLower().Contains(...)`** (como em Arquivos): resolve a caixa, mas não o
  acento — "joao" continuaria sem achar "JOÃO". Para nomes brasileiros, o
  acento é metade do problema.
- **Coluna `citext`**: troca o tipo da coluna (migration de dados), também não
  resolve acento, e espalha a semântica para todo `==` sobre a coluna.
- **Collation ICU não determinística** (`und-u-ks-level1`): elegante, mas
  `LIKE` sobre collation não determinística só existe a partir do PostgreSQL
  18, e não queremos amarrar a correção à versão do Postgres do Railway.

`ILIKE` + `unaccent` é o equivalente mais próximo do `LIKE` do SQL Server com
collation `CI_AI`, traduz direto pelo provedor Npgsql e não toca o esquema das
colunas.

### 2. Curingas digitados são literais

`EscaparLike` prefixa `\`, `%` e `_` com `\`, e o `ILike` usa a sobrecarga de
três argumentos com `\` como caractere de escape explícito — a de dois faz o
Npgsql emitir `ESCAPE ''`, que desliga o escape e deixaria o `\%` sem efeito
(descoberto na implementação, coberto pelo teste do "%" literal). Hoje o `Contains` já trata o termo como literal; manter isso
evita que um "%" digitado devolva a carteira inteira e mantém a semântica
"contém" que o usuário pediu.

### 3. Extensão `unaccent` por migration

`AppDbContext.OnModelCreating` declara `modelBuilder.HasPostgresExtension("unaccent")`
e uma migration gerada pelo `dotnet ef` cria a extensão
(`CREATE EXTENSION IF NOT EXISTS unaccent`). É um módulo contrib presente na
imagem oficial (`postgres:18-alpine` dos Testcontainers e o Postgres do
Railway) e é marcado como *trusted* desde o PostgreSQL 13 — o dono do banco
consegue criá-la sem superusuário. Como as migrations rodam também no
Testcontainers a cada `dotnet test`, uma extensão ausente falharia a suíte, não
a produção.

### 4. Novo `GET /api/pgdas/clientes` para alimentar o select

Retorna `{ id, codigo, nome }` dos clientes do escritório da sessão que têm ao
menos uma `ApuracaoSimples` (`db.Clientes.Where(c => db.ApuracoesSimples.Any(a => a.ClienteId == c.Id))`),
ordenados por nome, sem paginação. Mesmo guarda dos demais endpoints PGDAS
(`EscopoOuNull` → 403) e os query filters globais já escopam as duas tabelas.
Não filtra por situação do cliente: a visão geral lista apurações de cliente
inativo, então o select precisa poder escolhê-lo.

Alternativas consideradas:
- **Derivar as opções das apurações já carregadas**: zero backend, mas herda
  exatamente o defeito do truncamento que queremos eliminar.
- **Reusar `GET /api/clientes`** (como faz `TarefasView`, com `tamanho: 200`):
  traz clientes sem apuração (seleções que sempre dão vazio), é paginado e
  carrega campos que o select não usa.

### 5. Select nativo, filtro aplicado no servidor

`<select>` nativo com `<option :value="null">Todos os clientes</option>` e um
`<option>` por cliente ("código — nome"), seguindo o padrão do filtro de
cliente de `TarefasView.vue`. O select nativo já permite pular por digitação,
o que basta para carteiras de centenas de clientes. Trocar o valor chama
`carregar()`, que passa `clienteId` para `listarTodas` junto das competências;
o `computed` de agrupamento perde o filtro por termo em memória. As opções são
carregadas uma vez no `onMounted`, em paralelo com a lista e o resumo. O
estilo do select reaproveita o mesmo bloco do `.view-toolbar` que hoje estiliza
os inputs (tokens, sem cor literal).

## Risks / Trade-offs

- [`unaccent` indisponível em algum ambiente] → `IF NOT EXISTS` na migration;
  a suíte com Testcontainers detecta antes do deploy; se o Railway recusar,
  a migration falha no boot da API e o deploy anterior continua no ar.
- [`unaccent()` não é `IMMUTABLE`, logo não indexável por expressão] → aceito:
  volume por escritório é pequeno e a busca atual já faz varredura.
- [Busca mais permissiva traz mais resultados] → é o comportamento pedido;
  os demais filtros continuam combinando para afunilar.
- [Select longo em escritórios grandes] → select nativo com salto por
  digitação; se virar dor, um combobox fica para uma mudança própria.
- [Predicado novo não traduzir para SQL em runtime] → teste em
  `TraducaoLinqTest.cs` com `ToQueryString()`, que já pegou esse tipo de defeito
  antes.

## Migration Plan

1. Deploy da API: a migration cria `unaccent` no boot; nenhuma alteração de
   dados.
2. Deploy do frontend (o select depende do novo endpoint — subir a API antes).
3. Rollback: reverter o código da API volta ao `Contains`; a extensão pode
   ficar instalada sem efeito colateral.

## Open Questions

- Insensibilidade a acentos vai além do `LIKE` do SQL Server com a collation
  mais comum (`…_CI_AS`, sensível a acento). A decisão aqui foi incluí-la por
  ser o caso típico de nome brasileiro ("JOAO" × "JOÃO"); se não for desejada,
  basta remover o `Unaccent` do helper e a migration.
