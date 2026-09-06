## 1. Predicado compartilhado de "em onboarding"

- [x] 1.1 Criar `ContabOne.Api/Features/Onboarding/OnboardingFiltros.cs` expondo
  `public static Expression<Func<Cliente, bool>> EmOnboarding(AppDbContext db)`
  com o predicado do design (D1): `ModeloOnboardingId != null` e nenhum
  `ChecklistOnboardingCliente` daquele cliente com `PercentualConclusao >= 100`.
  Comentar por que é `Expression` e não método `bool` (D2) e por que o
  percentual persistido é a fonte (D3).
- [x] 1.2 Acrescentar caso em `ContabOne.Api.Tests/TraducaoLinqTest.cs` provando
  com `ToQueryString()` que `db.Clientes.Where(OnboardingFiltros.EmOnboarding(db))`
  traduz sem banco.

## 2. API — edição do código do cliente

- [x] 2.1 Em `Features/Clientes/ClientesEndpoints.cs`, `AtualizarAsync`: depois de
  carregar o cliente, recusar com `409 Conflict` (`{ erro = "Código já existe para
  este escritório" }`) quando outro cliente do MESMO escritório já usar
  `req.Codigo` — escopo tirado de `cliente.EscritorioId`, nunca de
  `req.EscritorioId`, e excluindo o próprio `id` (D4).
- [x] 2.2 Passar a gravar `cliente.Codigo = req.Codigo` em `AtualizarAsync`.

## 3. API — filtro e indicador

- [x] 3.1 Em `ListarAsync`, aceitar `bool? emOnboarding` e aplicar
  `query.Where(OnboardingFiltros.EmOnboarding(db))` apenas quando for `true`
  (D6) — a contagem `total` e a paginação já derivam de `query`, então
  acompanham sozinhas.
- [x] 3.2 Em `Features/Dashboard/DashboardEndpoints.cs`, `KpisAsync`: contar
  `db.Clientes.CountAsync(OnboardingFiltros.EmOnboarding(db))` e devolver o
  resultado como `clientesEmOnboarding` (D7).

## 4. Frontend — contratos

- [x] 4.1 `src/api/types.ts`: acrescentar `clientesEmOnboarding: number` a
  `DashboardKpis`.
- [x] 4.2 `src/api/endpoints/clientes.ts`: acrescentar `emOnboarding?: boolean`
  aos parâmetros de `listarClientes`.

## 5. Frontend — tela de clientes

- [x] 5.1 `views/ClientesView.vue`: tirar o `:disabled="editando"` do campo de
  código no modal.
- [x] 5.2 Exibir, abaixo do campo de código, um `.field-hint` visível apenas
  quando `editando && clienteEdit?.origem === 'Agente'`, avisando que o
  certificado na máquina do escritório precisa ser renomeado junto, sob pena de
  a próxima sincronização recadastrar o cliente (D5). O campo continua
  habilitado.
- [x] 5.3 Acrescentar à barra de ferramentas um terceiro `select`, FORA do
  `v-if="auth.isPlatformAdmin"` que separa os dois seletores atuais, com "Todos
  os clientes" e "Em onboarding", ligado a `filtroEmOnboarding` e chamando
  `aplicarFiltros` no `change`.
- [x] 5.4 Repassar `emOnboarding: filtroEmOnboarding.value || undefined` na
  chamada de `listarClientes` dentro de `carregar()`.

## 6. Frontend — os cartões do hub

- [x] 6.1 `views/HubView.vue`: mover o indicador de onboarding para o hub e
  renomear o `ref` `kpisNfse` para `kpis`, que passa a servir o card do NFS-e e
  o conteúdo transversal (D7).
  <br>**Nota:** primeiro foi para `DashboardView.vue` (`/f/nfse`) e de lá foi
  movido — aquela tela é a visão geral do NFS-e, e escritório sem NFS-e nunca
  veria o número.
- [x] 6.2 `assets/styles/tokens.css`: `--grad-erro`, `--grad-atencao` e
  `--grad-alerta`, cada um com a tinta correspondente, nos dois temas — par
  degradê/tinta junto, com o contraste medido (D9).
- [x] 6.3 `components/dashboard/CartaoContador.vue` (novo): cartão em degradê
  com `rotulo`, `valor`, `tom`, `descricao` opcional e `para` opcional. Cor só
  por token; hover só quando é link.
- [x] 6.4 `components/dashboard/ClientesOnboarding.vue` (novo): lista de
  clientes em onboarding com barra de progresso, ordenada por progresso
  decrescente e limitada a 5, com rodapé de truncamento, estado vazio e estado
  de falha próprios (D10).
- [x] 6.5 `views/HubView.vue`: faixa `.hub-contadores` com os três contadores de
  certificado, `.hub-colunas` de volta a duas trilhas (tarefas + onboarding), e
  remoção de `CertificadosVencimento.vue`, do `fetchCertificadosVencimento` e do
  CSS `.coluna-erro` que ficaram sem uso.
- [x] 6.6 `views/ClientesView.vue`: `filtroEmOnboarding` nasce de
  `route.query.emOnboarding === 'true'`, para o atalho do hub chegar filtrado
  (D11).
- [x] 6.7 `views/HubView.vue`: remover a faixa de ferramentas — as seções de
  domínio (Fiscal e DP), os cards, o `IconeCatalogo`, o `EstadoVazio`, o
  `useAuthStore` e todo o CSS que só ela usava (D12). O catálogo passa a ser
  consultado só para sinalizar falha, e o aviso vira faixa estreita no topo em
  vez de tela cheia: o painel não depende do catálogo e não pode ficar escondido
  atrás da falha dele.

## 6b. API — o que os cartões novos precisam

- [x] 6b.1 `KpisAsync`: `certificadosVencidos`, `certificadosVencendo3d` e
  `certificadosVencendoMais3d`, contados sobre a base do escopo e não derivados
  da lista com `Take(50)` (D8).
- [x] 6b.2 `ClienteDto.PercentualOnboarding`, projetado nas duas consultas
  (`ListarAsync` e `ObterAsync`) com o mesmo subselect correlacionado de
  `TemChecklistOnboarding` — sem checklist, 0.

## 7. Testes

- [x] 7.1 `ContabOne.Api.Tests/ClientesTest.cs`: edição de código para um código
  livre grava o valor novo; para código de outro cliente do mesmo escritório
  responde 409 e não altera nada; salvar mantendo o próprio código é aceito;
  código igual ao de cliente de OUTRO escritório é aceito.
- [x] 7.2 `ContabOne.Api.Tests/ClientesTest.cs`: `GET /api/clientes?emOnboarding=true`
  devolve o cliente com modelo e sem checklist, devolve o cliente com checklist
  abaixo de 100, e NÃO devolve o cliente com checklist em 100 nem o cliente sem
  modelo; sem o parâmetro, todos voltam.
- [x] 7.3 Teste do KPI: `GET /api/dashboard/kpis` devolve `clientesEmOnboarding`
  igual ao total do filtro no mesmo escritório (a coerência que a spec de
  `checklist-onboarding` cobra), e zero quando ninguém está em onboarding.
- [x] 7.4 `ContabOne.Frontend/src/views/ClientesView.spec.ts`: o campo de código
  fica habilitado ao abrir a edição; escolher "Em onboarding" no seletor dispara
  a requisição com `emOnboarding` (handler MSW correspondente — `onUnhandledRequest:
  'error'` derruba o teste sem ele).
- [x] 7.5 `ContabOne.Api.Tests/ClientesTest.cs`: as bordas das três faixas de
  certificado (ontem, hoje, +3, +4, +30, +31 — um cliente em cada) e cliente sem
  certificado fora de todas; `percentualOnboarding` refletindo o checklist ou 0.
- [x] 7.6 `components/dashboard/ClientesOnboarding.spec.ts` (novo): ordem por
  progresso e não por nome, corte em 5 com rodapé "Mostrando N de M", ausência do
  rodapé quando cabe tudo, estado vazio, falha que não derruba o card, link da
  linha para o checklist, atalho do cabeçalho já filtrado, e resposta sem o
  campo `percentualOnboarding` valendo 0% em vez de quebrar a barra e a ordem.

## 8. Verificação

- [ ] 8.1 `dotnet test` — **BLOQUEADO, por causa anterior a esta change.**
  `ContabOne.Api.Tests` não compila contra o `main` da API: `DetMensagensTest.cs`,
  `IsolamentoTest.cs` e `TraducaoLinqTest.cs` usam `AppDbContext.MensagensDet` /
  `MensagemDet`, que só existem no branch `det-agent-paridade-nfse` da API,
  nunca mesclado em `main` (9 erros CS1061/CS0246). Além disso o Docker não
  está de pé, e todo o 7.1–7.3 é `Category=Banco`. Os testes novos foram
  escritos mas **nunca compilados nem executados** — rodar depende de mesclar
  o DET em `main` (ou de rodar a suíte a partir daquele branch) e de subir o
  Docker.
- [x] 8.2 `npm --prefix ContabOne.Frontend run build` passou (`vue-tsc -b` +
  vite, o único portão de tipos do repositório). `ClientesView.spec.ts` +
  `ClientesOnboarding.spec.ts` passaram 18/18; a execução do `vitest` completo
  não chegou a rodar.
