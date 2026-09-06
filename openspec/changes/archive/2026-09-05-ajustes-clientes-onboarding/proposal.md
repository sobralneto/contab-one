## Why

Três arestas ficaram para trás depois que o checklist de onboarding entrou no ar:

1. **O código do cliente é imutável na edição.** O campo vem `:disabled` na tela e
   `AtualizarAsync` sequer copia `req.Codigo` para a entidade. O código é a chave
   que o escritório usa para casar o cliente com as próprias pastas — errar um
   dígito no cadastro hoje só se resolve excluindo e recriando o cliente, o que
   leva junto o checklist e o histórico de execuções.
2. **Não há como achar quem ainda está em onboarding.** A listagem de clientes
   filtra por escritório e por vencimento de certificado, mas o único jeito de
   saber quem ainda está sendo implantado é abrir cliente por cliente.
3. **O hub não conta o onboarding, e conta mal os certificados.** Ele mostra
   tarefas do dia e uma lista de certificados — nada diz quantas implantações
   estão em curso, e a lista obriga a contar na mão para saber quantos já
   venceram e quantos vencem esta semana.

## What Changes

- A edição de cliente passa a aceitar alteração do **código**, com a mesma regra
  de unicidade por escritório que já vale no cadastro (o índice
  `(EscritorioId, Codigo)` é único). Conflito responde 409, como em `CriarAsync`.
- `GET /api/clientes` ganha o filtro `emOnboarding`, e a barra de ferramentas da
  listagem ganha o seletor correspondente — disponível para todos os papéis, ao
  lado dos filtros que hoje são exclusivos de admin ou de escritório.
- A **página inicial deixa de ser um lançador de ferramentas e vira o painel do
  escritório**: os cards de ferramenta agrupados por domínio (Fiscal e DP, os
  únicos que existem hoje) saem dela. A navegação por ferramenta continua
  inteira no menu lateral, que já agrupa por domínio — nada fica inalcançável.
- No lugar deles: uma faixa de três contadores de certificado em degradê
  (vencidos, vencendo em até 3 dias, vencendo de 4 a 30 dias) e, abaixo, duas
  colunas — tarefas do dia e **clientes em onboarding com barra de progresso por
  cliente**. Na página inicial, e não na visão geral de uma ferramenta, porque
  certificado e onboarding são do cliente e não de ferramenta alguma: em
  `/f/nfse` o escritório que não usa NFS-e nunca veria os números.
- **BREAKING (produto, não contrato):** com os cards fora, some também o card
  informativo de ferramenta **não contratada** — o escritório perde a única
  vitrine que a aplicação tinha do que ele ainda não assinou. Nenhum endereço
  muda e nenhum guard de rota é afetado; o que sai é a vitrine.
- A lista de certificados que ocupava a segunda coluna **sai**: os contadores
  respondem "quantos", e o detalhe já vive na tela de Clientes, que filtra por
  vencimento. Mostrar os mesmos certificados somados e listados na mesma tela
  era redundância.
- `GET /api/dashboard/kpis` passa a devolver `certificadosVencidos`,
  `certificadosVencendo3d`, `certificadosVencendoMais3d` e `clientesEmOnboarding`.
  `GET /api/clientes` passa a devolver `percentualOnboarding` por cliente, que é
  o que alimenta as barras de progresso.
- A listagem de clientes passa a aceitar `?emOnboarding=true` na URL, para o
  atalho do hub chegar já filtrado — sem isso o número lido no hub não bateria
  com a tela aberta em seguida.
- **Uma única definição** de "cliente em onboarding", compartilhada pelo filtro
  da listagem e pela lista do hub: cliente **com modelo escolhido** que **ainda
  não tem checklist concluído** (sem checklist, ou com checklist abaixo de
  100%). Os dois não podem divergir — se divergirem, o que o hub mostra não bate
  com a lista que o usuário abre logo em seguida.

Sem mudança de banco: nenhuma entidade, coluna ou enum novo.

## Capabilities

### New Capabilities

Nenhuma. Tudo aqui são requisitos novos ou revistos sobre capacidades que já
existem.

### Modified Capabilities

- `gestao-clientes`: o código do cliente passa a ser editável (hoje a spec só
  trata do código **sugerido no cadastro**, e nada diz sobre alterá-lo depois);
  e a listagem ganha o filtro por clientes em onboarding.
- `checklist-onboarding`: fixa a definição de "cliente em fase de onboarding"
  como regra de domínio única, para que filtro e lista leiam a mesma coisa; e
  descreve a lista de onboarding do hub, com progresso por cliente. A capacidade
  que é dona do assunto é dona da própria presença no hub — mesmo padrão de
  `controle-tarefas`, que descreve ali a própria coluna de tarefas do dia.
- `navegacao-por-dominio`: a requisição que descreve a página inicial dizia
  "hub das ferramentas … três colunas: tarefas, certificados e uma reservada".
  Passa a descrever o painel — faixa de contadores e duas colunas — e a dizer
  que ferramenta se navega pelo menu lateral. A requisição "Ferramenta não
  contratada aparece só como informativa no hub" é **removida**: ela descrevia
  exclusivamente os cards que deixaram de existir.
- `catalogo-dominios-ferramentas`: duas requisições diziam que a ordem do
  catálogo vale "no menu e na página inicial" e que ferramenta sem agente
  "continua aparecendo no menu e no hub". Passam a falar só do menu lateral.

`dashboard-exibicao` NÃO muda: ela descreve a visão geral de ferramenta, que não
é onde nada disto ficou.

## Impact

**API** (`ContabOne.Api`)

- `Features/Clientes/ClientesEndpoints.cs` — `AtualizarAsync` (grava e valida o
  código), `ListarAsync` (parâmetro `emOnboarding`).
- `Features/Dashboard/DashboardEndpoints.cs` — `KpisAsync` (as três faixas de
  certificado e a contagem de onboarding).
- `Features/Onboarding/` — passa a expor o predicado de "em onboarding" usado
  pelos dois slices acima.

**Frontend** (`ContabOne.Frontend`)

- `views/ClientesView.vue` — campo de código habilitado na edição, seletor novo
  na barra de ferramentas.
- `views/HubView.vue` — faixa de ferramentas removida (com o CSS, o
  `IconeCatalogo`, o `EstadoVazio` e o `useAuthStore` que só ela usava); no
  lugar, faixa de contadores + duas colunas. O catálogo passa a ser consultado
  só para sinalizar falha, e essa falha vira faixa estreita em vez de tela
  cheia — o painel não depende dele e não pode ficar escondido atrás dela.
- `components/dashboard/CartaoContador.vue` (novo) — cartão em degradê; o par
  degradê/tinta vem de token, nunca de cor literal.
- `components/dashboard/ClientesOnboarding.vue` (novo) — lista com barra de
  progresso, ordenada por progresso decrescente.
- `components/dashboard/CertificadosVencimento.vue` — **removido**, substituído
  pelos contadores.
- `assets/styles/tokens.css` — `--grad-erro`/`--grad-atencao`/`--grad-alerta`
  e a tinta de cada um, nos dois temas.
- `api/endpoints/clientes.ts`, `api/endpoints/dashboard.ts` e `api/types.ts` —
  parâmetro e campo novos.

**Testes**

- `ContabOne.Api.Tests/ClientesTest.cs` — edição de código e conflito, filtro
  `emOnboarding`, `percentualOnboarding`, e as bordas das três faixas de
  certificado (ontem, hoje, +3, +4, +30, +31), que é onde contador de faixa
  erra.
- `ContabOne.Api.Tests/TraducaoLinqTest.cs` — o predicado novo tem de ser
  traduzível por EF.
- `ContabOne.Frontend/src/views/ClientesView.spec.ts` e
  `components/dashboard/ClientesOnboarding.spec.ts` (ordem por progresso,
  truncamento, vazio, falha).

**Não muda**: banco de dados, contratos com os agentes Python, o contrato de
privacidade (o filtro e a contagem só leem metadados que já trafegam).
