## Why

O painel nasceu para uma ferramenta só. `Clientes`, `Execuções`, `Agentes` e
`Configuração` são páginas globais que, na prática, significam "do NFS-e" — o
produto está implícito na tela inteira. Com a leitura do DET entrando e uma
terceira ferramenta contábil no horizonte, esse implícito quebra: não há onde
pendurar a segunda ferramenta sem duplicar item de menu, e o usuário não tem
como saber a qual produto o número na tela pertence.

O menu também é markup: cada `<router-link>` está escrito à mão em
`AppLayout.vue`. Ferramenta nova exige deploy do front — exatamente o
acoplamento que a mudança do catálogo de enum para tabela (`a4e32a2`) desfez
do lado da API. E não existe agrupamento: as três ferramentas atendem
departamentos diferentes do escritório contábil (Fiscal, DP, Contábil), e é
assim que o contador enxerga o próprio trabalho.

## What Changes

- O catálogo ganha **domínio**: nova tabela `Dominio` (`fiscal` → "Fiscal",
  `dp` → "DP", `contabil` → "Contábil") e `Produto.DominioCodigo`. Domínio é
  dado, não enum no código — cadastrar ferramenta em domínio novo não exige
  deploy.
- Cada produto declara também **quais páginas tem** (`paginas`:
  `visao-geral`, `execucoes`, `configuracao`). O submenu da ferramenta é
  gerado daí, então ferramenta cuja API ainda não está escopada simplesmente
  não declara a página. Clientes e Agentes ficam de fora desse conjunto —
  não são particionados por produto no banco, então não são "página de
  ferramenta".
- `GET /api/produtos` passa a devolver domínio, páginas e sempre o catálogo
  ativo **inteiro**, marcado por `contratado`, em vez de omitir o que não
  foi contratado — a navegação por domínio precisa saber que a ferramenta
  existe para mostrá-la como indisponível no hub. O seletor de nova chave de
  agente, que antes dependia dessa omissão, passa a filtrar por `contratado`
  no próprio frontend.
- Nova **página inicial (hub)** em `/`: cards de ferramenta agrupados por
  domínio, com os números-chave de cada uma.
- **BREAKING (rotas)**: as páginas de ferramenta passam a viver sob
  `/f/:produto/*` (`/f/nfse/execucoes`, `/f/det/execucoes`, …). `/dashboard`,
  `/execucoes` e `/configuracao` viram redirect permanente para o
  equivalente em `/f/nfse/`, então link salvo e suíte Playwright continuam
  chegando na tela certa. `/clientes` e `/agentes` **não entram nessa
  família**: continuam sendo o próprio endereço, sem `/f/:produto` — as duas
  telas mostram dado do escritório inteiro, não específico de uma
  ferramenta.
- Sidebar e submenu passam a ser **derivados do catálogo carregado na
  sessão**, não escritos no template.
- Visibilidade: `PlatformAdmin` vê todos os domínios e todo o catálogo;
  escritório vê só domínio que tenha ao menos uma ferramenta contratada, e a
  não contratada aparece apenas como card informativo no hub — sem ação
  alguma, nem navegação nem contato comercial.
- O guard de rota recusa `/f/:produto/*` de ferramenta não contratada,
  devolvendo ao hub — não a uma tela vazia.

## Capabilities

### New Capabilities
- `catalogo-dominios-ferramentas`: domínio e páginas como atributos do
  catálogo de produtos, e o que a API entrega de catálogo para cada papel.
- `navegacao-por-dominio`: hub inicial, agrupamento do menu por domínio,
  rotas por produto, redirects das rotas antigas e as regras de visibilidade
  por papel e por contratação.
- `isolamento-por-ferramenta`: configuração e execuções isoladas por
  ferramenta — descoberto e corrigido durante a implementação (ver Nota
  pós-implementação em Impact), não fazia parte do desenho original.

### Modified Capabilities
- `controle-exibicao-layout`: a navegação agora depende de dado carregado
  depois da autenticação. O layout não pode exibir menu de ferramentas
  enquanto o catálogo da sessão não resolveu — o estado intermediário não
  pode mostrar menu incompleto nem menu de outro escopo.

## Impact

**API** — `Domain/Entities.cs` (`Dominio`, `Produto.DominioCodigo`,
`Produto.Paginas`), migration com seed dos três domínios e backfill do NFS-e
e do DET, `Features/Produtos/ProdutosEndpoints.cs` (domínio, páginas, flag
`contratado` para admin), endpoints de admin de produtos (domínio no cadastro
e na edição), `ContabOne.Api.Tests`.

**Frontend** — `router/index.ts` (família `/f/:produto/*` e redirects),
`router/guards.ts` (catálogo no bootstrap, recusa de produto não
contratado), novo store de produtos, `layouts/AppLayout.vue` (menu gerado),
nova `views/HubView.vue`, `api/endpoints/produtos.ts` e `api/types.ts`,
`constants/explicacoesPagina.ts` (chave passa a ser `produto.pagina` com
fallback), specs em `e2e/`.

**Nota pós-implementação** — `Execucao` e `Configuracao` acabaram sendo
escopadas por produto ainda durante esta mudança (não estava no plano
original: `Cliente` nunca foi, porque não é um conceito por ferramenta, mas
Execução e Configuração são — só faltava a API filtrar). `ConfiguracaoEscritorio`
ganhou `ProdutoId` na chave, `GET /api/execucoes` ganhou `produtoCodigo`
opcional, e o handshake do agente só recebe a configuração da própria
ferramenta. `Cliente` continua global por escritório, de propósito (design.md).
