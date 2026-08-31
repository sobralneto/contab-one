## Why

Hoje um usuário pertence a **no máximo um** escritório: `Usuario.EscritorioId` é uma
chave estrangeira única e o token carrega um único `escritorio_id`. Isso não cobre dois
casos reais da operação: o admin da plataforma, que não pertence a escritório nenhum mas
precisa trabalhar dentro de um por vez, e o contador que atende mais de um escritório e
hoje só consegue isso com uma conta e uma senha por escritório.

Além disso, quando a sessão passa a poder olhar para escritórios diferentes, **qual
escritório está em foco deixa de ser óbvio** — e um usuário que não sabe em qual
escritório está lançando dado contábil é um risco de erro, não só de usabilidade.

## What Changes

- **BREAKING** — o vínculo entre usuário e escritório deixa de ser a coluna
  `Usuario.EscritorioId` e passa a ser uma relação de muitos-para-muitos. Um usuário pode
  ter zero, um ou vários escritórios vinculados.
- O papel `PlatformAdmin` continua sem vínculo obrigatório, mas ganha a capacidade de
  colocar qualquer escritório em foco.
- **BREAKING** — o token de acesso passa a declarar o escritório **em foco** daquela
  sessão, e não mais "o escritório do usuário". O escopo de tenant do pedido passa a ser
  o escritório em foco, validado contra os vínculos do usuário a cada emissão.
- Novo endpoint para trocar o escritório em foco, que reemite o acesso da sessão corrente
  com o novo foco — sem exigir novo login.
- Novo endpoint que lista os escritórios que o usuário logado pode colocar em foco.
- A barra superior passa a exibir o nome do escritório em foco. Quando houver mais de uma
  opção de foco, ela oferece a troca; quando houver apenas uma, exibe só o nome.
- A troca de foco descarta o catálogo de ferramentas e os dados em tela do escritório
  anterior, do mesmo modo que o logout já descarta.
- A gestão de usuários passa a atribuir **um conjunto** de escritórios a um usuário, em
  vez de um único.

## Capabilities

### New Capabilities

- `vinculo-usuario-escritorios`: quem pode ver quais escritórios — como um usuário é
  vinculado a zero, um ou vários escritórios, quem administra esses vínculos e o que
  acontece quando o último vínculo é removido.
- `escritorio-em-foco`: qual escritório a sessão está enxergando agora — como o foco é
  escolhido no login, como é trocado durante a sessão, como é validado contra os vínculos
  e como é apresentado ao usuário na barra superior.

### Modified Capabilities

- `isolamento-multi-tenant`: o escopo do pedido deixa de derivar de "o escritório do
  usuário" e passa a derivar do **escritório em foco declarado na credencial**, que por
  sua vez é validado contra os vínculos. A regra "todo usuário de escritório tem
  escritório" passa a ser "todo usuário de papel de escritório tem ao menos um vínculo".
- `ciclo-de-vida-da-sessao`: a sessão ganha uma operação de troca de foco que reemite o
  acesso; a perda de um vínculo passa a invalidar sessões que estejam com aquele
  escritório em foco.
- `controle-exibicao-layout`: a barra superior passa a exibir o escritório em foco, e o
  descarte do catálogo passa a valer também para a troca de foco, não só para o logout.

## Impact

**API (`ContabOne.Api`)**

- `Domain/Entities.cs` — `Usuario.EscritorioId`/`Usuario.Escritorio` saem; entra a
  entidade de vínculo e as coleções nos dois lados.
- Nova migração EF: cria a tabela de vínculo, migra os `EscritorioId` existentes para
  linhas de vínculo, remove a coluna.
- `Features/Auth/AuthEndpoints.cs` — emissão do claim `escritorio_id` passa a resolver o
  foco; novo endpoint de troca de foco; novo endpoint de listagem de escritórios
  disponíveis.
- `Infra/TenantContextMiddleware.cs` e `Infra/TenantContext.cs` — o foco vira a fonte do
  escopo; `PlatformAdmin` com foco deixa de ser "vê todos" e passa a ser escopado.
- `Infra/AppDbContext.cs` — filtros globais de query seguem o foco resolvido.
- `Features/Usuarios/UsuariosEndpoints.cs` — criação e edição de usuário passam a receber
  uma lista de escritórios.

**Frontend (`ContabOne.Frontend`)**

- `stores/auth.ts` — o usuário da sessão ganha o escritório em foco e a lista de opções.
- `layouts/AppLayout.vue` — indicador de escritório em foco e seletor de troca na topbar.
- `stores/catalogo.ts` — recarga do catálogo na troca de foco.
- Tela de usuários — seleção múltipla de escritórios.

**Testes**

- `ContabOne.Api.Tests` — os testes que hoje montam usuário com `EscritorioId` direto
  passam a montar vínculo.
