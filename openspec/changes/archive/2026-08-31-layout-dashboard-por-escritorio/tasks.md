## 1. Modelo e migration

- [x] 1.1 Criar `enum LayoutDashboard { ContabOne, Lj, Mudahr }` em
      `ContabOne.Api/Domain/Enums.cs`, com comentário explicando por que este
      enum é persistido como string (design.md, decisão 2) enquanto os vizinhos
      são inteiros — e que nenhum agente Python o lê.
- [x] 1.2 Adicionar `public LayoutDashboard LayoutDashboard { get; set; } = LayoutDashboard.ContabOne;`
      a `Escritorio` em `ContabOne.Api/Domain/Entities.cs`.
- [x] 1.3 Configurar a coluna em `Infra/AppDbContext.cs`: `.HasConversion<string>()`
      e `.HasDefaultValue(LayoutDashboard.ContabOne)`, junto do resto do
      `modelBuilder.Entity<Escritorio>`.
- [x] 1.4 Gerar a migration com
      `dotnet ef migrations add LayoutDashboardEscritorio --project ContabOne.Api`
      e conferir que ela sai como `text NOT NULL DEFAULT 'ContabOne'`, sem
      `UPDATE` de backfill. Não editar `AppDbContextModelSnapshot.cs` à mão.
- [x] 1.5 Rodar `dotnet test --filter "Category=Banco"` só para confirmar que a
      migration aplica limpa no Postgres efêmero (nunca com `DATABASE_URL`
      setado).

## 2. Endpoints de administração

- [x] 2.1 `AdminEndpoints.ObterEscritorioAsync` e `ListarEscritoriosAsync`:
      incluir `LayoutDashboard = escritorio.LayoutDashboard.ToString()` no DTO
      anônimo, ao lado de `Status`, seguindo o mesmo par `ToString()`/`TryParse`
      já usado por `StatusEscritorio`.
- [x] 2.2 Acrescentar `string? LayoutDashboard` a `CriarEscritorioRequest` e a
      `AtualizarEscritorioRequest`.
- [x] 2.3 `CriarEscritorioAsync`: `Enum.TryParse<LayoutDashboard>(req.LayoutDashboard, true, out var layout)`,
      caindo em `LayoutDashboard.ContabOne` quando o campo vier ausente ou nulo
      — o mesmo default do banco.
- [x] 2.4 `AtualizarEscritorioAsync`: gravar o novo leiaute quando informado,
      preservando o atual quando o campo vier ausente (nulo ≠ "voltar ao
      padrão").
- [x] 2.5 Adicionar aos dois validators a regra que recusa leiaute
      desconhecido com 400 (design.md, decisão 3), aplicada só quando o campo
      vem preenchido. **Não** alterar o comportamento tolerante de `Status`.

## 3. Payload da dashboard

- [x] 3.1 `PgdasEndpoints.DashboardAsync`: buscar o leiaute do escritório em
      foco a partir de `EscopoOuNull(tenant)`, com
      `db.Escritorios.Where(e => e.Id == escritorioId).Select(e => e.LayoutDashboard)`.
- [x] 3.2 Incluir `layoutDashboard` no retorno principal.
- [x] 3.3 Incluir `layoutDashboard` **também no early return** de
      `apuracoes.Count == 0` — é o passo que o design sinaliza como fácil de
      esquecer e que deixaria a tela de "sem apurações" fora do tema.

## 4. Frontend — tipos e CRUD de escritórios

- [x] 4.1 `src/api/types.ts`: adicionar `layoutDashboard` a `EscritorioDto` e o
      campo opcional a `CriarEscritorioRequest`/`AtualizarEscritorioRequest`,
      com um tipo `LayoutDashboard = 'ContabOne' | 'Lj' | 'Mudahr'` no mesmo
      estilo de `StatusEscritorio`.
- [x] 4.2 `EscritoriosView.vue`: acrescentar ao `form` reativo o campo
      `layoutDashboard`, e ao modal um `<select>` com as três opções, rotuladas
      pelo escritório dono da marca — `Contab One (padrão)`,
      `L&J Contabilidade (laranja)`, `MUDAHR Contabilidade (roxo)`.
- [x] 4.3 Em `abrirCriar()`, inicializar `form.layoutDashboard = 'ContabOne'`
      junto com os demais resets, para o cadastro nascer no neutro sem o admin
      tocar no campo.
- [x] 4.4 Em `abrirEditar()`, carregar o leiaute do escritório no `form`, como
      já é feito com plano e status.
- [x] 4.5 Adicionar um `field-hint` abaixo do `<select>`, visível quando a
      escolha for `Lj` ou `Mudahr`, avisando que o leiaute traz também o
      logotipo daquela marca no documento entregue ao cliente final — a
      mitigação de tela do risco central do design.
- [x] 4.6 Usar as classes compartilhadas de `components.css` (`form-field`,
      `field-hint`) em vez de CSS por view.

## 5. Frontend — dashboard

- [x] 5.1 `src/features/pgdas/dashboard/temas.ts`: normalizar com
      `codigo?.toLowerCase()` em `temaPorCodigo` para aceitar os valores
      PascalCase que a API envia, mantendo os minúsculos. Atualizar o comentário
      que hoje cita a chave `marca` de `ConfiguracaoEscritorio`. **Não tocar em
      nenhuma cor.**
- [x] 5.2 `src/features/pgdas/dashboard/tipos.ts`: adicionar `layoutDashboard`
      ao `DashboardPayload`.
- [x] 5.3 `PgdasDashboardView.vue`: em `carregar()`, tirar o tema de
      `payload.layoutDashboard` e remover a chamada paralela a
      `obterConfiguracao('pgdas')` e seu import — a view deixa de depender do
      endpoint de configuração.

## 6. Testes

- [x] 6.1 `ContabOne.Api.Tests`: escritório criado sem informar leiaute fica em
      `ContabOne`.
- [x] 6.2 Criar e depois atualizar o leiaute para `Mudahr` persiste, e um PUT
      sem o campo preserva o valor gravado.
- [x] 6.3 PUT com leiaute inválido devolve 400 e não altera o valor anterior.
- [x] 6.4 `PgdasTest.cs`: o payload da dashboard traz o leiaute do escritório em
      foco — e o traz também quando o cliente não tem apuração no período
      (cobre a task 3.3).
- [x] 6.5 `IsolamentoTest.cs`: confirmar que o leiaute devolvido é o do
      escritório em foco, não o de outro, quando há dois escritórios no banco.
- [x] 6.6 Vitest em `temas.spec.ts`: `temaPorCodigo` devolve o tema certo para
      os três valores em PascalCase e os três em minúsculo, e cai no neutro para
      valor desconhecido, nulo e indefinido.
- [x] 6.7 Vitest de `EscritoriosView`: o modal de criação abre com `ContabOne`
      selecionado; o de edição abre com o leiaute do escritório carregado.
- [x] 6.8 E2E em `e2e/escritorios.spec.ts`: o admin escolhe um leiaute, salva, e
      reabrir o modal mostra a escolha — o cenário de persistência da spec de
      `gestao-escritorios`.

## 7. Fechamento

- [x] 7.1 `npm --prefix ContabOne.Frontend run build` — único gate de typecheck
      do repositório, obrigatório depois das edições de frontend.
- [x] 7.2 `dotnet test` completo e
      `npm --prefix ContabOne.Frontend test` verdes.
- [x] 7.3 Conferir manualmente em `/f/pgdas/dashboard` os três leiautes, na tela
      e no PDF exportado, incluindo com a plataforma em modo escuro — o
      documento tem de sair idêntico nos dois modos.
- [x] 7.4 Rodar `openspec validate layout-dashboard-por-escritorio` e sincronizar
      as specs com `/opsx:sync` antes de arquivar.
