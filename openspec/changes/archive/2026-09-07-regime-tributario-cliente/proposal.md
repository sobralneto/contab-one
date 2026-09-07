## Why

O regime tributário é o primeiro dado que um escritório precisa saber sobre uma
empresa — ele decide qual obrigação vence, qual guia é gerada e qual ferramenta
do painel se aplica àquele cliente. Hoje o cadastro de cliente não guarda essa
informação em lugar nenhum: ela vive na cabeça do contador ou numa planilha
paralela, e a listagem de clientes não distingue um MEI de uma empresa do Lucro
Real.

## What Changes

- O cliente passa a ter um **regime tributário**, escolhido entre cinco opções
  fixas: Simples Nacional, Lucro Presumido, Lucro Real, MEI e Outros.
- O formulário de novo cliente e o de edição ganham o seletor correspondente. A
  escolha é **opcional**: cliente sem regime informado continua válido.
- A listagem de clientes ganha a coluna **Regime**, ordenável como as demais, e
  quem não tem regime informado aparece como "—".
- A barra de filtros da tela ganha um seletor de regime, ao lado dos que já
  existem, com as cinco opções mais **"Não informado"** — a consulta que o
  escritório faz justamente para saber quem falta classificar.
- Clientes já cadastrados **não são convertidos**: nascem sem regime e ficam
  assim até alguém informar. Ninguém sabe o regime dos clientes que o agente
  cadastrou, e escolher um por eles seria inventar dado fiscal.
- A sincronização do agente **não mexe** no regime — ele lê certificados na
  máquina do escritório e não tem como saber o regime de ninguém.

Não é breaking change: o campo é anulável, ausente no request significa "sem
regime", e nenhum contrato existente muda de forma.

## Capabilities

### New Capabilities

Nenhuma. O regime tributário é um atributo do cliente, e o cadastro de cliente
já é uma capability existente — criar uma capability só para um campo separaria
da `gestao-clientes` regras que valem para o mesmo formulário e para a mesma
listagem.

### Modified Capabilities

- `gestao-clientes`: acrescenta o regime tributário ao cadastro e à edição do
  cliente (conjunto fechado de cinco opções, escolha opcional, validação do
  valor recebido), à listagem (coluna própria, ordenável, "—" para quem não
  tem) e à sincronização do agente (o regime informado pela tela sobrevive à
  próxima sincronização).

## Impact

**API (`ContabOne.Api/`)**
- `Domain/Enums.cs` — novo enum `RegimeTributario` (persistido como inteiro,
  como a maioria dos vizinhos: só acrescentar ao fim, nunca reordenar).
- `Domain/Entities.cs` — `Cliente.RegimeTributario` anulável.
- `Features/Clientes/ClientesEndpoints.cs` — campo no `ClienteDto` e no
  `ClienteRequest`, leitura nas duas projeções, gravação no `CriarAsync` e no
  `AtualizarAsync`, validação no `ClienteRequestValidator`, nova entrada no
  conjunto fechado de `Ordenar`.
- Nova migration EF (coluna anulável, sem backfill).
- `Features/Agent/AgentEndpoints.cs` — nada muda no código; o comportamento
  desejado (não sobrescrever) é o que já acontece, e passa a ter teste.

**Frontend (`ContabOne.Frontend/`)**
- `src/api/types.ts` — `RegimeTributario` como union de strings, campo no
  `ClienteDto` e no `ClienteRequest`.
- `src/views/ClientesView.vue` — seletor no modal, coluna na tabela, entrada em
  `colunas`, campo no `form` e no payload de gravação, e o seletor de regime na
  barra de filtros.
- `src/api/endpoints/clientes.ts` — parâmetro `regimeTributario` em
  `listarClientes`.

**Testes**
- `ContabOne.Api/tests/ClientesTest.cs` — cadastro com e sem regime, edição
  (inclusive limpar), valor inválido recusado, ordenação pela coluna nova.
- `ContabOne.Api/tests/` (agente) — sincronização preserva o regime.
- `ContabOne.Frontend/src/views/ClientesView.spec.ts` — seletor no formulário,
  coluna na listagem e o filtro por regime.

**Fora de escopo**
- Usar o regime para gatear ferramentas (ex.: oferecer o PGDAS-D só a quem é
  Simples Nacional) ou para pré-selecionar modelo de onboarding. São decisões
  de produto que merecem proposta própria; este change só passa a guardar o
  dado.
