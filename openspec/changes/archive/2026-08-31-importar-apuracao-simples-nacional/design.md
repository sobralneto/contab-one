## Context

A ferramenta que entra é um arquivo HTML único de ~1.260 linhas, autônomo, que
já roda em produção informal nos dois escritórios. Ela faz três coisas bem
separadas:

1. **Lê o PDF** com `pdf.js`, reconstruindo as linhas por coordenada Y antes
   de aplicar as expressões regulares — e trata **dois leiautes diferentes**
   do mesmo documento: o *extrato* (tributos na seção "6) Informações sobre
   DAS", valor na mesma linha do rótulo) e a *declaração* (seção "2.8) Total
   Geral da Empresa", valor na linha seguinte ao cabeçalho). Cada campo tem
   dois ou três padrões de fallback.
2. **Oferece conferência editável** — a soma dos oito tributos contra o DAS
   informado, com tolerância de R$ 0,05, marcando a linha em vermelho quando
   não bate. É a rede de segurança contra mudança de leiaute da Receita, e é
   o que torna aceitável um parser acoplado a leiaute.
3. **Monta a dashboard** com Chart.js e exporta em PDF (html2canvas + jsPDF)
   ou em HTML autocontido que reconstrói os próprios gráficos.

Do lado da plataforma, três restrições atravessam qualquer desenho aqui:

- **Conteúdo fiscal não trafega.** É a regra que sustenta o modelo do agente
  ("o XML/PDF das notas nunca é enviado para a API") e não há razão para
  abrir exceção agora.
- **CNPJ completo nunca é persistido** — só `CnpjHash` (HMAC-SHA256, chave
  permanente) e `CnpjMascarado`.
- **Escopo de tenant nunca vem da query string** para usuário de escritório
  (`isolamento-multi-tenant`).

E uma quarta, específica desta mudança: **todo produto do catálogo hoje
pressupõe um binário em campo**. Este é o primeiro que não tem.

## Goals / Non-Goals

**Goals:**

- Gravar as competências lidas, por cliente, de forma que a dashboard possa
  ser reaberta meses depois sem nenhum PDF em mãos.
- Ligar o documento à carteira de clientes do escritório, cadastrando a
  empresa quando ela ainda não existir.
- Vestir os passos de carga e conferência com o layout da plataforma, e
  preservar a dashboard exatamente como está.
- Deixar o catálogo capaz de descrever uma ferramenta que não tem agente,
  sem gambiarra em quem consome o catálogo.

**Non-Goals:**

- **Reescrever o parser.** Ele é traduzido para TypeScript como está, regex
  por regex. O que ele ganha é suíte de testes, que hoje não tem.
- **Parser no servidor.** Ver Decisions.
- **Página de Configuração da ferramenta.** `ConfiguracaoView.vue` é hoje um
  componente único com os campos do NFS-e; declarar `configuracao` para o
  `pgdas` renderizaria formulário errado. É a mesma razão pela qual o DET não
  a declara. Quebrar essa tela em um formulário por produto é mudança
  própria.
- **Página de Execuções.** `Execucao.AgenteId` é não-anulável e a ferramenta
  não tem agente. Tornar a coluna anulável para acomodar "execução sem
  agente" é uma decisão sobre o modelo de execução da plataforma inteira, não
  um detalhe desta ferramenta.
- **Regra de vencimento com dia útil.** Continua dia 20 do mês seguinte,
  editável na conferência.
- **Alertas automáticos** (DAS em aberto, sublimite estourando). O
  `AlertaJob` é o lugar certo e a porta fica aberta, mas não nesta mudança.
- Cobrança ou autosserviço de contratação.

## Decisions

### O PDF continua sendo lido no navegador

A alternativa — subir o PDF e fazer o parsing em C# — daria duas coisas
reais: corrigir uma regex sem deploy de frontend, e um só lugar para o
leiaute. Mesmo assim fica de fora.

O documento do PGDAS-D traz faturamento, tributos, CNPJ e a receita mês a mês
dos últimos doze meses de uma empresa de terceiro. Recebê-lo no servidor
transforma a plataforma em custodiante de documento fiscal — exatamente o
que o desenho do agente evita de propósito. O ganho operacional não paga
essa troca.

A consequência prática é que **a API nunca vê o documento**: recebe um JSON
de competências que o usuário já viu e conferiu na tela. Isso também explica
por que a conferência é obrigatória no fluxo e não um passo opcional — é o
único ponto de validação humana entre o PDF e o banco.

### `TemAgente` no catálogo, e não um `codigo` especial

O seletor de nova chave em `AgentesView.vue` filtra o catálogo apenas por
`contratado`. Sem mais nada, o `pgdas` apareceria como opção de gerar uma
chave de API que nenhum binário vai usar.

Três saídas foram consideradas: (a) o front esconder o `pgdas` por código
literal; (b) inferir de `paginas` — ferramenta sem `execucoes` não tem
agente; (c) um atributo explícito no catálogo.

(a) é o acoplamento que a mudança do catálogo para tabela desfez, e volta a
exigir deploy a cada ferramenta nova. (b) amarra duas coisas que não têm
relação necessária — uma ferramenta com agente pode não declarar Execuções, e
o DET é quase isso hoje. Fica (c): **`Produto.TemAgente`**, com default
`true` na migration para não mexer no que já existe.

O atributo não entra no caminho de autenticação — o handshake continua
comparando o código da chave com o `Produto.Codigo` do próprio agente, sem
consultar o catálogo (`catalogo-dominios-ferramentas`). `TemAgente` só
governa a **oferta** de chave nova, da mesma família que `Produto.Ativo`.

### Uma página nova no conjunto fechado: `importacao`

O conjunto (`visao-geral`, `execucoes`, `configuracao`, `regras`) é fechado
porque cada valor corresponde a um componente que existe no frontend —
aceitar valor arbitrário produziria item de menu que leva a lugar nenhum.
A ferramenta precisa de um lugar para o assistente de carga, e nenhum dos
quatro serve: não é visão geral (é ação, não painel), não é execução (não há
agente), não é configuração.

`pgdas` declara então `['visao-geral', 'importacao']`:

- `/f/pgdas` — as apurações gravadas, por cliente e competência, com as
  pendências em destaque: DAS em aberto, linha que não confere, sublimite
  acima de 80%.
- `/f/pgdas/importacao` — os passos de carga e conferência.

### A dashboard é rota de detalhe, não página declarada

A dashboard é de **um cliente e um intervalo** — `/f/pgdas/dashboard/:clienteId`
— e se chega nela a partir de uma linha da lista. Não é item de menu.

O guard já suporta isso sem alteração: ele valida `meta.pagina` só quando a
rota declara uma, e valida produto e contratação para **qualquer** rota sob
`/f/:produto`. Uma rota sem `meta.pagina` fica fora do menu e continua
protegida pelo gate de contratação. É esse comportamento que o delta de
`navegacao-por-dominio` escreve — hoje ele existe no código mas não na spec, e
a redação atual ("página não declarada não é alcançável pelo endereço") leria
como se a proibisse.

### A dashboard renderiza dentro de um `iframe srcdoc`

O CSS da dashboard define `:root` e usa nomes genéricos (`.card`, `.kpi`,
`h3`), e o gerador produz HTML como string. Montar isso dentro do DOM da
aplicação obrigaria a prefixar cada seletor e ainda assim brigaria com o tema
escuro da plataforma — num documento que precisa sair idêntico no PDF
entregue ao cliente.

Um `iframe` de mesma origem com `srcdoc` resolve os três problemas de uma vez:

- isolamento de CSS completo, sem tocar em uma linha do estilo existente;
- **o mesmo gerador serve preview e exportação** — é literalmente o documento
  que o botão "Baixar HTML" já monta hoje;
- `html2canvas` alcança `iframe.contentDocument` normalmente (mesma origem),
  então a exportação em PDF por blocos (`dashPart1` / `dashPart2`, que existe
  para a quebra de página cair acima do "Detalhamento mensal") continua
  valendo sem alteração.

O custo é ter que aguardar `load` do iframe antes de desenhar os gráficos e
antes de exportar. É um custo pequeno e local.

### Marca por escritório, com um terceiro tema neutro

Os dois temas (`lj` e `mudahr`) entram inteiros, com os logos saindo do
base64 para `assets/marcas/`. A escolha deixa de ser um botão no passo 1 e
vira configuração do escritório — `ConfiguracaoEscritorio`, que já é escopado
por `ProdutoId`, chave `marca`.

Mas a plataforma é multi-tenant e um terceiro escritório não tem tema. Por
isso entra um terceiro, **`contabone`**, montado com os verdes de
`tokens.css`, como default de quem não for L&J nem MUDAHR. Sem ele a
ferramenta só serviria a dois clientes — e o próximo escritório exigiria
deploy.

### Uma linha por cliente × competência, e a série mensal em tabela própria

`ApuracaoSimples` tem chave única `(EscritorioId, ClienteId, Competencia)`.
Competência como string `"2026-03"`, no mesmo formato de
`ExecucaoMetrica.Competencia`.

**Não há coluna `Confere`.** A validação é a soma dos oito tributos contra o
DAS, com tolerância de R$ 0,05 — derivável a qualquer momento, e guardá-la
criaria um segundo lugar para a verdade. ⚠️ Filtrar por "não confere" exige
escrever a aritmética na query: propriedade computada em C# **não é
traduzível** e explode em runtime, o defeito que `Alerta.Aberto` já causou
duas vezes em produção.

A série mensal (seção 2.2.1 do documento) vai para **`ReceitaMensalCliente`**,
com chave `(EscritorioId, ClienteId, Competencia)` e upsert — não para uma
tabela filha da apuração. A razão é que o mesmo mês aparece na série de até
doze documentos diferentes; guardar por apuração multiplicaria a linha por
doze e ainda exigiria escolher qual vale na hora de montar o gráfico. Com
upsert, o documento mais recente sobrescreve, e o gráfico de evolução
funciona **mesmo para meses cujo PDF nunca foi carregado** — que é o dado
mais valioso que a ferramenta hoje joga fora.

`ApuracaoSegregacao` fica como tabela filha de verdade (PK
`(ApuracaoId, Categoria)`, cascade): a segregação é da apuração daquele mês,
não tem vida própria.

**Sem tabela de lote de importação.** `ImportadoEm` e `ImportadoPorUsuarioId`
na própria apuração já dão a auditoria; lote só se aparecer a necessidade de
desfazer uma importação inteira.

### Competência já gravada: recusar e perguntar

`POST /api/pgdas/apuracoes` com uma competência que já existe devolve **409
listando quais**, e a tela pergunta se substitui. Reenviar com
`substituir: true` sobrescreve.

Sobrescrever calado seria pior num caso concreto e provável: o usuário abre a
conferência, corrige um valor à mão, grava — e semanas depois recarrega o
mesmo PDF por engano, apagando a correção. A flag `EditadoManualmente` existe
para que a tela consiga avisar exatamente isso antes de substituir.

### `POST /api/clientes` passa a aceitar CNPJ cru

O documento traz o CNPJ inteiro e a plataforma precisa dele para achar o
cliente — o `CnpjHash` é HMAC com chave que só o servidor tem, então o
navegador não consegue calcular o hash sozinho.

A saída é o servidor receber o CNPJ cru, derivar hash e máscara **em
memória** e descartar. Isso já era necessário para a identificação; estender
o mesmo campo ao cadastro conserta um defeito existente de graça: hoje o
cadastro pela tela envia apenas `cnpjMascarado`, e o cliente vai para o banco
com `CnpjHash` vazio — nunca casando com o cliente que o agente cadastrou
para a mesma empresa.

Por isso a identificação também tem **fallback por máscara**: não achando
pelo hash, procura por `CnpjMascarado` e, casando, **preenche o hash que
faltava**. A carteira vai se consertando sozinha conforme os documentos
passam.

O cadastro reusa `POST /api/clientes` inteiro — limite `MaxClientes` do
plano, conflito de código, tenancy — em vez de um endpoint paralelo dentro da
slice `pgdas`.

### `Cliente.Codigo` é sugerido, não inventado

`Codigo` é obrigatório e único por escritório, e o documento do PGDAS-D não
tem esse conceito. Gerar um código silenciosamente criaria divergência com a
pasta de certificados que o agente usa (`0001`, `0002`, …).

`GET /api/clientes/proximo-codigo` sugere o próximo numérico livre de quatro
dígitos e a tela deixa editar antes de confirmar. Quem sabe o código certo
digita o código certo; quem não sabe aceita a sugestão.

### `OrigemCliente.Importacao` acrescentado ao fim do enum

O enum é persistido como inteiro. O valor novo entra **no fim**
(`Manual = 0`, `Agente = 1`, `Importacao = 2`) — reordenar reescreveria o
significado das linhas já gravadas.

### Bibliotecas por npm, carregadas sob demanda

`pdfjs-dist`, `jspdf` e `html2canvas` entram como dependências, não por CDN:
o arquivo autônomo depende de `cdnjs` e não abre sem internet, e num SaaS isso
vira dependência de terceiro no caminho crítico. Somadas passam de 1,5 MB,
então são importadas por `import()` dinâmico dentro das telas da ferramenta —
quem nunca abre o `pgdas` não paga nada. O worker do `pdf.js` é resolvido pelo
Vite (`?url`), não por URL remota.

## Risks / Trade-offs

**O parser está acoplado ao leiaute PGDAS-D 2018.** Mudança de leiaute da
Receita quebra a extração. Mitigação em três camadas, todas já presentes ou
previstas: os fallbacks de regex por campo; a conferência humana obrigatória
antes de gravar; e a suíte de testes que esta mudança acrescenta, com
fixtures de texto extraído. Sem os testes, cada ajuste de regex é uma aposta.

**Fixtures são dado fiscal real.** As fixtures do parser precisam ser
**anonimizadas** — CNPJ, razão social e valores alterados —, no mesmo espírito
do aviso sobre `Nfse.Agent/certificados/`. Um extrato real commitado é
vazamento de dado de cliente de contabilidade.

**Regex fica no frontend, então corrigir exige deploy do front.** É o preço
consciente de não receber o documento no servidor. Aceito.

**A dashboard passa a mostrar o CNPJ mascarado.** A ferramenta autônoma
mostra o CNPJ inteiro no cabeçalho; a plataforma só guarda a máscara. Optou-se
por mascarar **também durante a importação**, quando o CNPJ inteiro ainda está
em memória — mostrar inteiro na primeira geração e mascarado ao reabrir o
mesmo relatório seria pior do que mascarar sempre. Está listado em Open
Questions porque muda a aparência de um documento entregue a cliente.

**`iframe` complica teste de componente.** Assertar sobre o conteúdo da
dashboard em Vitest fica difícil. Mitigação: o gerador de HTML é função pura
(`dashHTML`, `dashCss`, `rebuildChartsScript`) e é testado como string, sem
montar o iframe; o teste de componente cobre só a moldura.

**Cliente errado grava competência no cliente errado.** A identificação é
automática pelo CNPJ, mas o cadastro é confirmado por humano. A tela mostra
razão social e CNPJ mascarado do cliente identificado **antes** de gravar, e o
lote inteiro é de um cliente só — não há gravação parcial em dois clientes.

## Migration Plan

Uma migration só, na ordem:

1. Cria `ApuracaoSimples`, `ApuracaoSegregacao` e `ReceitaMensalCliente`.
2. Acrescenta `Produto.TemAgente` como `NOT NULL DEFAULT TRUE` — `nfse` e
   `det` continuam exatamente como estão.
3. Semeia o produto `pgdas` (domínio `fiscal`, ordem 3, páginas
   `visao-geral` e `importacao`, `TemAgente = FALSE`).
4. **Backfill de `EscritorioProdutos`**: habilita `pgdas` para todos os
   escritórios existentes, no mesmo padrão de
   `20260823052601_EscritorioProdutoContratado` — escritório existente nasce
   com toda ferramenta ativa habilitada, restringir é ação deliberada.

O passo 4 é o motivo de semear por migration em vez de cadastrar pela tela
`/admin/produtos`: o cadastro pela tela **não cria vínculo de contratação**,
e a ferramenta ficaria invisível para todo mundo até um admin habilitá-la
escritório por escritório. E como a ferramenta exige deploy de qualquer forma
(as telas são código), não há ganho em cadastrá-la por fora.

Sem passo de rollback de dado: as tabelas nascem vazias e `Down` as remove.

## Open Questions

1. **CNPJ mascarado na dashboard** — ✅ decidido e implementado: `dashHTML`
   só recebe `cliente.cnpjMascarado` (nunca o CNPJ inteiro); testado em
   `documento.spec.ts` ("nunca imprime o CNPJ inteiro, só a máscara").
2. **Terceiro tema `contabone`** — ✅ implementado em
   `src/features/pgdas/dashboard/temas.ts`, derivado dos verdes de
   `tokens.css` (`--accent`, `--accent-hover`, `--atencao` como terceira cor
   de contraste nos gráficos). É o fallback de `temaPorCodigo` para qualquer
   valor de `marca` que não seja `lj`/`mudahr`.
3. **Substituir competência já gravada** — ✅ implementado: `POST
   /api/pgdas/apuracoes` devolve 409 com as competências em conflito e a
   flag `editadoManualmente`; `substituir: true` sobrescreve. Fluxo completo
   testado em `PgdasTest.cs` (API) e `PgdasImportacaoView.spec.ts` (tela).
4. **Vencimento do DAS** — ✅ mantida a regra atual (dia 20 do mês seguinte),
   gravada em `ApuracaoSimples.Vencimento` e editável na conferência.
5. **Números no card do hub** — não incluído nesta mudança, como já previsto
   aqui. O card do `pgdas` aparece no hub sem número, comportamento existente
   para qualquer ferramenta que não seja o `nfse`.

### Decisões tomadas durante a implementação (não previstas acima)

- **`ApuracaoSimples` ganhou `Rba`, `Sublimite` e `Impedido`** (nullable),
  além dos campos já listados na seção "Uma linha por cliente ×
  competência". Sem eles o painel de sublimite estadual — citado no `Why`
  como uma das coisas que a ferramenta autônoma já mostra — não seria
  reconstruível a partir do banco, o que contradiria o objetivo central da
  mudança. Faltou nomear esses três campos explicitamente na primeira
  redação deste documento.
- **RBT12 não é persistido, e a dashboard reconstruída do banco não mostra
  mais o card de RBT12** que a ferramenta autônoma tinha. Ele nunca apareceu
  na lista de dados preservados no `Why` ("faturamento, DAS, carga efetiva,
  sublimite estadual, segregação da receita") — diferente do sublimite, essa
  omissão foi deliberada desde a primeira redação, só não estava registrada
  aqui. Ficou documentado como comentário em `documento.ts`.
- **Município, anexo e sigla da empresa** (campos que a ferramenta autônoma
  extraía e mostrava no cabeçalho da dashboard) também saem da versão
  reconstruída do banco: não fazem parte do `Cliente` da plataforma, e
  persisti-los exigiria colunas novas sem requisito correspondente em
  nenhuma spec. O cabeçalho da dashboard mostra nome do cliente e CNPJ
  mascarado apenas.
- **`Pago` como `bool` não anulável** (não `bool?`): a ferramenta autônoma
  tinha um terceiro estado ("—", desconhecido — principalmente para
  declarações, que não informam pagamento). Persistir esse tri-estado exigia
  tornar a coluna anulável. Optou-se por manter `bool` simples e resolver a
  ambiguidade na própria tela de conferência, onde o usuário confirma o
  status antes de gravar — consistente com o princípio geral desta mudança
  de que a conferência é o único ponto de validação humana entre o
  documento e o banco.
