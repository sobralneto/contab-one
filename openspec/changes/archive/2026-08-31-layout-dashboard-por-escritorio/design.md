## Context

A ferramenta de apuração do Simples Nacional nasceu da fusão de duas
ferramentas autônomas de escritório (`conversor_dashboard_simples_v2.html`), e
trouxe as duas identidades visuais inteiras: `ContabOne.Frontend/src/features/pgdas/dashboard/temas.ts`
tem as paletas `lj` (vinho `#9c2b25` + dourado `#c99a2e`) e `mudahr` (roxo
`#430753` + verde `#04d795`) portadas verbatim daquele arquivo, mais uma
terceira, `contabone`, montada com os verdes de `tokens.css` para servir de
neutro.

O consumidor já existe e funciona:

- `PgdasDashboardView.vue:109` — `tema.value = temaPorCodigo(config?.valores.marca)`
- `documento.ts:330` — o `tema.logo` é estampado no cabeçalho do documento
- `documento.ts:395` e o `dashCss()` inteiro — todas as cores saem do `Tema`

O que não existe é o produtor. Não há tela, endpoint, seed ou migration que
grave a chave `marca` em `ConfiguracaoEscritorio` — `grep -rn "marca"
ContabOne.Api --include=*.cs` não devolve uma única escrita. Todo escritório cai
hoje no `return TEMAS.contabone` de `temaPorCodigo`, e as duas paletas de marca
nunca são renderizadas.

Restrições que moldam o desenho:

- **O CRUD de escritórios já é admin-only.** `Program.cs:332` monta
  `/api/admin` com `.RequireAuthorization("PlatformAdmin")`, e
  `EscritoriosView.vue` só é alcançável por esse perfil. A exigência de "somente
  admin" não pede autorização nova — pede que o campo more ali e em nenhum outro
  lugar.
- **O documento não pode depender do tema da plataforma.** Já é requisito de
  `apuracao-simples-nacional`: a dashboard sai igual na tela e no PDF, modo
  escuro incluso. O leiaute é do escritório, não do usuário.
- **`PUT /api/configuracao` é destrutivo.** `ConfiguracaoEndpoints.SalvarAsync`
  faz `RemoveRange` de todas as chaves do produto antes de inserir as recebidas.
  Qualquer escrita parcial por ali apaga o resto da configuração do PGDAS-D.

## Goals / Non-Goals

**Goals:**

- Dar ao admin da plataforma um campo, no cadastro do escritório, que escolha
  entre os três leiautes da dashboard de apuração.
- Fazer a criação nascer em `contabone` sem o admin precisar tocar no campo, e
  fazer todo escritório já existente ser lido como `contabone`.
- Ligar o leitor que já existe a uma fonte de verdade real, sem alterar
  nenhuma das três paletas.

**Non-Goals:**

- Cadastrar identidades novas — upload de logo, paleta customizada, editor de
  cores. Os três leiautes são fixos em código; um quarto cliente com marca
  própria é outra change.
- Aplicar o leiaute a qualquer outra tela. Ele governa exclusivamente o
  documento gerado em `/f/pgdas/dashboard` (tela, HTML exportado e PDF).
- Deixar o escritório escolher o próprio leiaute. É decisão comercial do admin,
  não autoatendimento.

## Decisions

### 1. Coluna em `Escritorio`, não chave em `ConfiguracaoEscritorio`

`Escritorio.LayoutDashboard`, coluna `NOT NULL DEFAULT 'contabone'`.

*Por quê.* O leiaute é atributo do escritório — vive no mesmo modal que nome,
CNPJ, plano e status, é escrito pelo mesmo `PUT /api/admin/escritorios/{id}` e
tem o mesmo dono (o admin). `ConfiguracaoEscritorio` é escopado por `(escritório,
produto)` e existe para configuração *da ferramenta* pelo próprio escritório.

*Alternativa considerada:* manter a chave `marca` em `ConfiguracaoEscritorio`,
que dispensaria migration porque o leitor já aponta pra lá. Descartada por dois
motivos concretos. Primeiro, o único endpoint de escrita que existe é
destrutivo por produto (`SalvarAsync` faz `RemoveRange` antes do insert), então
o CRUD de escritórios precisaria de um endpoint novo só para gravar uma chave
sem apagar as outras — mais código do que a coluna. Segundo, amarraria o
cadastro de escritórios a uma configuração escopada pelo produto `pgdas`:
salvar um escritório passaria a depender de a ferramenta PGDAS-D existir no
catálogo.

*Consequência:* a chave `marca` deixa de ser lida. Como nunca foi escrita, não
há dado a migrar e nenhum escritório muda de aparência.

### 2. Enum C# persistido como string, seguindo `StatusEscritorio` na fronteira

`enum LayoutDashboard { ContabOne, Lj, Mudahr }` em `Domain/Enums.cs`, mapeado
com `.HasConversion<string>()` no `AppDbContext`.

*Por quê a string na coluna.* O default da migration precisa ser legível e
estável (`DEFAULT 'contabone'`), e este enum é um conjunto fechado de
identidades visuais que só cresce por acréscimo. Uma coluna de texto sobrevive a
reordenação do enum; uma coluna inteira não.

Isso é uma exceção deliberada ao "enums são inteiros no banco" do resto do
modelo, e ela é segura porque **nenhum agente Python lê este campo**. O aviso do
AGENTS.md ("Enums cross the wire as integers... o agente Python traduz em
`api_client`") vale para o contrato com os robôs; `LayoutDashboard` nunca sai
por `/api/agent`.

*Na fronteira HTTP* o campo vai como string, exatamente como `Status` já vai:
`AdminEndpoints` monta os DTOs anônimos com `Status = escritorio.Status.ToString()`
e volta com `Enum.TryParse<StatusEscritorio>(req.Status, true, out …)`. O novo
campo usa o mesmo par, inclusive o `ignoreCase: true`.

*Consequência para o frontend:* o valor chega em PascalCase (`"ContabOne"`,
`"Lj"`, `"Mudahr"`) enquanto as chaves de `TEMAS` são minúsculas. `temaPorCodigo`
normaliza com `codigo?.toLowerCase()` antes de comparar — uma linha, que de
quebra segue aceitando os valores minúsculos que a assinatura já documentava.

### 3. Valor inválido no PUT é recusado, não silenciosamente ignorado

O validator de `AtualizarEscritorioRequest` rejeita string que não seja um dos
três valores, com 400.

*Por quê.* O padrão atual de `Status` é `Enum.TryParse` sem validator: string
inválida simplesmente não altera nada, e o admin recebe 200 achando que salvou.
Para `Status` isso é tolerável porque a tela é um `<select>` fechado; a
tolerância vira armadilha quando o campo é novo e o admin pode estar chamando a
API direto. O validator torna a falha visível. Não mexemos no comportamento de
`Status` — mudar aquilo é outra change.

*Na criação* o campo é opcional: ausente ou nulo vira `ContabOne`, que é o
mesmo default do banco. É o que faz "por padrão a criação já recebe contab-one"
valer tanto pela tela quanto pela API.

### 4. O leiaute viaja no payload da dashboard, não numa segunda requisição

`GET /api/pgdas/clientes/{id}/dashboard` passa a devolver
`layoutDashboard: "<valor>"` ao lado de `cliente`, `apuracoes` e `serieMensal`.

*Por quê.* Hoje `PgdasDashboardView.carregar()` dispara duas chamadas em
paralelo — a dashboard e `obterConfiguracao('pgdas')` — sendo que a segunda
existe só para descobrir a marca. Movendo o valor para o payload, a view perde
uma dependência e uma requisição, e o tema chega junto com os dados que ele
pinta, sem janela em que `dados` já existe e `tema` ainda não.

O handler já resolve o escritório: `EscopoOuNull(tenant)` devolve
`tenant.EscritorioId`, o escritório em foco. O leiaute sai de
`db.Escritorios.Where(e => e.Id == escritorioId)`, sujeito ao mesmo filtro
global de tenancy do resto.

*Cuidado de implementação:* `DashboardAsync` tem um **early return** quando
`apuracoes.Count == 0`, com formato próprio. O campo tem de entrar nos dois
retornos — esquecer o primeiro deixa a tela de "sem apurações" fora do tema.

*Alternativa considerada:* expor o leiaute em `GET /api/configuracao` junto com
`valores` e `plano`. Manteria a view como está, mas conservaria a segunda
requisição e colocaria um atributo do escritório dentro da resposta escopada
por produto — a mesma confusão de camadas que a decisão 1 evita.

### 5. Logotipo acompanha o leiaute (decidido com o usuário)

Escolher `Lj` ou `Mudahr` traz cores **e** o logotipo daquela marca para o
cabeçalho do documento, que é como `temas.ts` já se comporta (`Tema.logo`,
consumido em `documento.ts:330`).

*Consequência operacional, que precisa estar escrita:* os leiautes `Lj` e
`Mudahr` são identidades completas de dois escritórios reais. Atribuir um deles
a um terceiro escritório estampa a marca alheia no documento entregue ao cliente
final desse terceiro. O leiaute neutro `ContabOne` é a resposta correta para
todo escritório que não seja dono da marca — e é por isso que ele é o default e
não uma das outras duas opções.

Isso é reforçado na tela pelo rótulo de cada opção, que nomeia o escritório dono
(`L&J Contabilidade (laranja)`, `MUDAHR Contabilidade (roxo)`), em vez de vender
"laranja" e "roxo" como paletas genéricas escolhíveis à vontade.

*Alternativa considerada:* trocar só as cores e manter sempre o logo Contab One.
Isolaria o risco acima, mas descaracterizaria o documento das duas ferramentas
originais, cujo cabeçalho com a marca do escritório é justamente o que faz o PDF
servir como entrega ao cliente.

## Risks / Trade-offs

- **Admin atribui `Lj`/`Mudahr` ao escritório errado e o logo alheio vai parar
  num PDF entregue a cliente final** → é o risco central da decisão 5. Mitigado
  em três camadas: default `ContabOne` na criação, rótulos que nomeiam o
  escritório dono da marca em vez da cor, e nota na tela dizendo que os dois
  leiautes de marca incluem o logotipo. Não é mitigável por código além disso —
  o sistema não tem como saber que um escritório *não* é a L&J.

- **Divergência de caixa entre o enum C# e as chaves de `TEMAS`** → um
  `.toLowerCase()` em `temaPorCodigo`, coberto por teste com os três valores em
  PascalCase e os três em minúsculo. Sem isso, todo escritório voltaria
  silenciosamente ao fallback neutro — falha que não quebra nada e por isso
  passa despercebida.

- **Esquecer o early return de `DashboardAsync`** → cliente sem apuração
  renderiza fora do tema. Coberto por teste do payload vazio, listado nas
  tasks.

- **Coluna string aceita lixo por escrita direta no banco** → `temaPorCodigo`
  já cai no neutro para qualquer valor desconhecido, e o parse no C# também. O
  fallback é seguro por construção: o pior caso é a identidade neutra, nunca a
  de outro escritório.

- **Trade-off aceito: três leiautes fixos em código.** O quarto cliente com
  marca própria exige deploy do frontend, não só dado. É proporcional enquanto
  os leiautes forem três; vira problema se a lista crescer, e aí a resposta é
  paleta em dado, que é change própria.

## Migration Plan

1. Migration adiciona `LayoutDashboard text NOT NULL DEFAULT 'contabone'` em
   `Escritorios`. O backfill é o próprio default — nenhum `UPDATE` explícito, e
   como a chave `marca` nunca foi gravada, não há dado antigo a converter.
2. API e frontend sobem juntos. Se o frontend subir antes, o campo chega
   `undefined` e `temaPorCodigo` devolve o neutro — que é o comportamento de
   hoje.
3. **Rollback:** reverter os dois deploys. A coluna pode ficar no banco sem
   efeito; ninguém a lê. Só derrubar a coluna se o rollback for definitivo.
