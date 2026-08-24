## Context

O painel tem hoje sete rotas de aplicação escritas à mão em
`router/index.ts` e um menu lateral com um `<router-link>` por item dentro de
`layouts/AppLayout.vue`. Todas as páginas operacionais (`/clientes`,
`/execucoes`, `/agentes`, `/configuracao`, `/dashboard`) são, de fato, as
páginas da coleta de NFS-e — o produto está implícito.

Do lado da API o caminho oposto já foi andado: o catálogo de ferramentas
saiu do enum e virou tabela (`a4e32a2`), e a contratação por escritório virou
`EscritorioProduto` (`601791a`). `GET /api/produtos` já devolve, para a
sessão de escritório, exatamente as ferramentas contratadas e ativas — é a
fundação que falta o frontend usar para algo além do seletor de chave de
agente.

Restrição que atravessa tudo: o escopo de tenant nunca vem da query string
para usuário de escritório (`isolamento-multi-tenant`). O catálogo da sessão
tem que sair do token, não do que o front pedir.

## Goals / Non-Goals

**Goals:**

- Agrupar as ferramentas por domínio (Fiscal, DP, Contábil) no menu e numa
  página inicial em cards.
- Tirar a navegação do template: menu e submenu derivados do catálogo.
- Dar endereço próprio a cada página de cada ferramenta.
- Uma regra só de visibilidade — o catálogo da sessão — valendo para menu,
  hub e guard de rota.

**Non-Goals:**

- Escopar `Cliente` por produto no banco. Ao contrário de Execução e
  Configuração (ver Decisions — acabaram entrando no escopo desta mudança),
  Cliente nunca foi um conceito por ferramenta: uma empresa é cliente do
  escritório, não "cliente do NFS-e". Continua global.
- Telas do DET. Esta mudança prepara o lugar delas, não as constrói.
- Mexer no que o dashboard atual mostra. Ele é a visão geral do NFS-e e
  passa a viver como tal, sem alteração de conteúdo. Os resumos que ele lê
  (KPIs, série mensal, ranking, últimas execuções) continuam sem filtro de
  produto — só a tela dedicada de Execuções passou a filtrar.
- Cobrança, planos ou autosserviço de contratação de ferramenta.

## Decisions

### Domínio é tabela, não coluna livre nem enum

Tabela `Dominio` (`Codigo`, `Nome`, `Ordem`, `Icone`) e
`Produto.DominioCodigo` com chave estrangeira.

*Alternativa considerada:* coluna `string Dominio` no `Produto` mais um mapa
de rótulos no frontend. Mais barata em migration, mas devolve ao código a
decisão de quais domínios existem e como se chamam — exatamente o
acoplamento que `a4e32a2` desfez para as ferramentas. Domínio novo passaria a
exigir deploy do front.

*Alternativa considerada:* enum em C#. Mesma objeção, agravada por precisar
de deploy dos dois lados.

O preço da tabela é uma chave estrangeira e um seed. Com três linhas que
mudam raramente, é barato o bastante para não valer o atalho.

O domínio de Departamento Pessoal é semeado com o nome **"DP"**, não com o
nome por extenso. DP é como o escritório contábil chama o departamento — o
nome longo seria mais formal, não mais claro — e resolve de graça o
enquadramento no menu, que tem 260px abertos e 68px recolhido. Por isso o
`Dominio` não ganha uma coluna de nome curto: existe um nome só, e ele serve
no menu, no hub e no cadastro. Se algum dia um domínio precisar de dois
nomes, aí sim entra a coluna — não antes.

### `GET /api/produtos` devolve sempre o catálogo ativo inteiro

A primeira versão deste desenho tinha a sessão de escritório recebendo só o
que contratou (preservando o comportamento anterior do endpoint) e só o
admin recebendo o catálogo inteiro com a marca `contratado`. Isso quebra o
requisito do card informativo no hub (navegacao-por-dominio): sem saber que
uma ferramenta existe, o escritório não tem como vê-la como indisponível —
ela simplesmente nunca chegaria ao frontend. Corrigido durante a
implementação: o endpoint devolve o mesmo catálogo ativo inteiro, marcado
por `contratado`, para os dois papéis. Sem escopo resolvido (admin sem
escritório em foco), tudo vem como não contratado.

O seletor de nova chave de agente (`AgentesView.vue`), que dependia da
omissão para filtrar, passa a filtrar por `contratado` no próprio
componente — o servidor para de decidir isso por ele.

### As páginas da ferramenta são dado, e é isso que sequencia a entrega

`Produto.Paginas` guarda um subconjunto de um conjunto fechado conhecido pela
aplicação (`visao-geral`, `execucoes`, `configuracao`). O conjunto é fechado
de propósito: cada valor corresponde a um componente que existe no front,
então aceitar valor arbitrário só produziria item de menu que leva a lugar
nenhum. A validação vive na API, junto do cadastro.

**Clientes e Agentes NÃO entram nesse conjunto.** A primeira versão deste
desenho os tratava como página de ferramenta (`/f/:produto/clientes`,
`/f/:produto/agentes`), mas as duas telas mostram dado do escritório
inteiro — `Cliente` não é particionado por produto no banco, e a listagem de
`Agente` é uma tabela só para o escritório inteiro, com o produto como
coluna, não uma tela por produto. Modelar como página de ferramenta
implicava um endereço `/f/nfse/clientes` mostrando exatamente o mesmo dado
de `/f/det/clientes` — a URL prometia um recorte por ferramenta que não
existe. Corrigido: `Clientes` e `Agentes` são rotas transversais
(`/clientes`, `/agentes`), no mesmo nível de `/usuarios`, fora de
`/f/:produto/`.

Isso resolveu a ordem entre esta mudança e o escopo por produto no banco:
`Configuracao` era chave-valor só por escritório, e exibir essa página sob
duas ferramentas faria o DET herdar os ajustes do NFS-e. **Correção
aplicada ainda nesta mudança** (não estava no plano original — ver a
decisão seguinte): `ConfiguracaoEscritorio` ganhou `ProdutoId` na chave, e
`Execucao` ganhou filtro por produto na API via `Agente.ProdutoId`. DET
continua sem declarar `configuracao` só porque não tem ajuste nenhum
definido ainda para expor — o mecanismo já suporta, é só declarar a página
quando (se) precisar.

### Execução e Configuração passaram a filtrar por produto de verdade

A primeira versão desta mudança deixava `Execucao` e `Configuracao` sob
`/f/:produto/…` só na aparência: a API não filtrava por produto, então
`/f/nfse/execucoes` e `/f/det/execucoes` mostravam a mesma lista. Descoberto
ao testar a aplicação de verdade, não em revisão de código — e corrigido:

- `ConfiguracaoEscritorio` (antes só `(EscritorioId, Chave)`) ganhou
  `ProdutoId` na chave primária, com FK para `Produtos`. Migration com a
  mesma disciplina das anteriores (coluna anulável, backfill atribuindo todo
  registro existente ao NFS-e — a única ferramenta que tinha Configuração
  até aqui —, só então obrigatória). `GET`/`PUT /api/configuracao` passam a
  exigir `produtoCodigo`, e o handshake do agente (`AgentEndpoints.cs`)
  filtra pelo `Agente.ProdutoId` de quem está perguntando — um agente do
  DET nunca recebe a configuração do NFS-e.
- `GET /api/execucoes` ganhou `produtoCodigo` **opcional** (via join com
  `Agente.ProdutoId`), nos três modos (lista plana, agrupado por escritório,
  agrupado por cliente). Opcional de propósito: o resumo da visão geral
  (`DashboardView.vue`, "últimas execuções") continua chamando sem o
  parâmetro, exatamente como antes — só a tela dedicada de Execuções passou
  a mandar.
- `Cliente` NÃO seguiu o mesmo caminho — ao contrário dos outros dois,
  nunca foi um conceito por ferramenta (não é "um cliente que ainda não
  filtra direito", é um cliente do escritório, ponto), então continua fora
  de `/f/:produto/`.
- O dashboard/visão geral (KPIs, série mensal, ranking, "últimas execuções")
  continua sem filtro de produto — mexer nisso é escopo maior (a própria
  visão geral) do que o que foi pedido aqui.

### Regras de coleta virou página de ferramenta, exclusiva do NFS-e e de PlatformAdmin

`/admin/regras` vivia solto na seção Admin do menu, ao lado de Escritórios e
Planos — mas o pacote de regras que ele cadastra é especificamente do
Portal Nacional, isto é, do NFS-e; nenhuma outra ferramenta tem (ou precisa
ter) esse conceito. Passou a ser `/f/nfse/regras`, declarada só pelo NFS-e
em `Produto.Paginas` (`regras`, adicionado ao conjunto fechado), no submenu
da ferramenta logo abaixo de Configuração.

A diferença para Configuração/Execuções: aqui a restrição de papel é mais
estrita — só PlatformAdmin, nunca EscritorioAdmin, porque publicar uma
versão quebrada afeta a coleta de todos os escritórios de uma vez (o mesmo
risco que já motivava `/admin/regras` ser PlatformAdmin-only). Isso exigiu
um segundo nível em `PAGINA_META` no frontend (`AppLayout.vue`): antes só
existia "aberta a todos" ou "EscritorioAdmin+"; agora existe também
"só PlatformAdmin", usado exclusivamente por `regras`.

`/admin/regras` vira redirect permanente para `/f/nfse/regras`, mesmo
critério das outras rotas legadas. O endpoint da API (`/api/admin/regras`)
não mudou de lugar nem de política de autorização — já era
`PlatformAdmin`-only antes desta mudança; só a rota e o menu do frontend se
moveram.

### Uma família de rotas com o produto no caminho

`/f/:produto/:pagina`, com `:produto` sendo o `Codigo` do catálogo — o mesmo
valor que já prefixa a chave de API do agente (`nfse_…`, `det_…`).

*Alternativa considerada:* um conjunto de rotas por ferramenta
(`/nfse/clientes`, `/det/comunicados`). Dá endereço mais bonito e permite
página exclusiva de uma ferramenta, mas devolve ao `router/index.ts` a lista
de ferramentas — de novo, ferramenta nova exigindo deploy.

*Alternativa considerada:* manter as rotas atuais e trocar de ferramenta por
um seletor global de contexto guardado em store. Menos mexida, porém o
endereço deixa de identificar a tela: dois usuários com o mesmo link veem
ferramentas diferentes, e não há como favoritar as execuções do DET.

O `/f/` no prefixo existe para não competir com as rotas transversais
(`/usuarios`, `/admin/*`) nem obrigar a reservar códigos de produto no
primeiro nível do caminho.

### O dashboard atual vira a visão geral do NFS-e; o hub é página nova

Tudo o que o `DashboardView` mostra hoje — notas por mês, alertas, ranking de
clientes, ranking de escritórios — é dado da coleta de NFS-e. Movê-lo para
`/f/nfse` mantém os requisitos de `dashboard-exibicao` valendo sem alterar
uma linha do que a tela apresenta; só o endereço muda, e `/dashboard` passa a
redirecionar para lá junto com as outras rotas antigas.

O hub em `/` é página nova e deliberadamente magra: card por ferramenta com
nome, descrição, estado e atalho. Número no card só para ferramenta cujo
resumo a API já sabe escopar — enquanto o resumo não for por produto, o card
do NFS-e mostra os números atuais e os demais mostram só o estado. Um hub que
inventa agregado de duas ferramentas com semânticas diferentes ("notas" e
"comunicados" somados) seria pior que um hub sem número.

O card da ferramenta não contratada é **só informativo**: nome, descrição e a
marca de não contratada, sem botão, sem link e sem contato comercial. Não há
autosserviço de contratação (está nos não-objetivos), então qualquer ação ali
levaria a lugar nenhum ou a um `mailto:` que ninguém acompanha — e o card
existe para o escritório saber que a ferramenta existe, não para vender por
conta própria. A contratação continua acontecendo fora do produto, e o admin
a registra em `EscritorioProduto`.

### O catálogo é carregado uma vez, no bootstrap da sessão

Novo store `produtos`, carregado no guard logo depois de a sessão ser
confirmada (`router/guards.ts` já é onde o bootstrap acontece), e limpo em
`auth.clearSession()`.

*Alternativa considerada:* carregar por rota, em cada página de ferramenta.
Evita o request no caminho crítico, mas o menu precisa do catálogo inteiro
para se desenhar — cairia em carregar tudo de qualquer jeito, só que mais
tarde e mais de uma vez.

Falha na carga não derruba a sessão: o layout mantém hub e itens
transversais, sinaliza e oferece nova tentativa. Derrubar a sessão por falha
de catálogo transformaria indisponibilidade de uma tela em logout geral.

### Ícone vem do domínio, com mapa de fallback no front

`Dominio.Icone` guarda o **nome** de um ícone; o front tem um mapa nome→SVG
e um ícone genérico para nome desconhecido. Ferramenta nova entra no ar com
o genérico e ganha o desenho no deploy seguinte — o cadastro nunca fica
bloqueado esperando arte, e o menu nunca renderiza um buraco.

Só o domínio tem ícone, não cada produto: hoje cada domínio tem exatamente
uma ferramenta, então a linha da ferramenta no menu e no hub reaproveita o
ícone do domínio dela. `Produto.Icone` fica para quando o primeiro domínio
ganhar uma segunda ferramenta e precisar distingui-las visualmente — não
antes.

### A explicação de página passa a ser indexada por ferramenta e página

`EXPLICACOES_PAGINA` é hoje indexado pelo `name` da rota. Com rota genérica a
chave passa a ser `${produto}.${pagina}`, com fallback para `${pagina}`.
Assim o texto de "Execuções" serve para todas as ferramentas e só se escreve
o específico onde o texto genérico mente.

## Risks / Trade-offs

- **Mudar todos os endereços quebra link salvo, favorito e a suíte
  Playwright** → redirect de cada rota antiga para o equivalente em
  `/f/nfse/`, preservando query string, mais atualização das specs em `e2e/`.
  Os redirects ficam: são baratos, e o custo de removê-los depois é maior que
  o de mantê-los.
- **Um request a mais antes do primeiro render útil** → o catálogo é pedido
  em paralelo à restauração da sessão, não depois dela, e o layout renderiza
  a moldura sem esperar. O menu aparece quando o catálogo chega.
- **Catálogo de um escritório vazar para a sessão seguinte na mesma aba** →
  o store é limpo no `clearSession()`, junto do resto da sessão, e o menu é
  renderizado só a partir do catálogo carregado, nunca de valor padrão.
- **Domínio "Contábil" sem nenhuma ferramenta pronta** → para o escritório o
  domínio some do menu; para o admin ele aparece com o catálogo. Ninguém vê
  seção vazia.
- **`Produto.Paginas` como conjunto fechado limita ferramenta com página
  exclusiva** → aceito por ora. Quando a primeira página exclusiva aparecer,
  a saída é uma rota registrada por ferramenta convivendo com a família
  genérica, não abrir o conjunto.

## Migration Plan

1. Migration cria `Dominio`, faz seed de `fiscal`, `dp` e `contabil`,
   acrescenta `Produto.DominioCodigo` e `Produto.Paginas`, e faz o backfill:
   NFS-e em `fiscal` com todas as páginas, DET em `dp` sem `configuracao`.
   A coluna entra anulável, o backfill roda, e só então vira obrigatória —
   sem janela em que cadastro existente fique inválido.
2. API passa a devolver os campos novos. São aditivos: o frontend em produção
   ignora o que não conhece, então API e front podem subir separados.
3. Frontend: store de catálogo, hub, rotas novas, redirects e menu gerado
   sobem juntos — é uma mudança visual só, e dividi-la deixaria o menu
   desalinhado das rotas.

Rollback: reverter o deploy do frontend restaura o menu e as rotas antigas,
que continuam existindo no banco e na API (os campos novos ficam ignorados).
A migration não precisa ser revertida.

## Open Questions

Nenhuma em aberto. As duas que existiam aqui foram decididas e estão em
Decisions: o domínio de Departamento Pessoal se chama "DP", com um nome só no
catálogo, e o card da ferramenta não contratada fica só informativo, sem
contato comercial.
