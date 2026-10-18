## Context

`PgdasImportacaoView.vue` é um assistente de três passos (carga → conferência
→ cliente e gravação) que hoje guarda **uma** lista plana `competencias` e
deriva dela tudo o que é "da empresa":

- a mescla de documentos usa só o período: `competencias.findIndex(x => x._pa === c._pa)`
  — dois extratos de 03/2026 de CNPJs diferentes colidem e o segundo apaga o
  primeiro;
- `empresaExtraida` / `empresaEditada` vêm da primeira competência que trouxe
  `_nome`/`_cnpj`;
- `cnpjDoLote()` pega o primeiro CNPJ encontrado e a identificação roda uma vez;
- `gravar()` monta um único `GravarApuracoesRequest` com um único `clienteId`,
  uma série mensal e uma `competenciaDocumento`;
- `removerArquivo(i)` tira o arquivo da lista mas deixa as competências dele.

O parser (`features/pgdas/parser/`) já devolve `_cnpj`, `_nome`, `_mun`,
`_anexoTxt` **por bloco de apuração**, ou seja, a informação para agrupar já
existe — o que falta é o assistente usá-la.

Na API, `POST /api/pgdas/apuracoes` grava o lote de um cliente com um único
`SaveChangesAsync` (atômico por cliente) e devolve 409 com as competências em
conflito; `POST /api/pgdas/clientes/identificar` resolve o cliente pelo hash do
CNPJ. O grupo `/api/pgdas` não tem política de rate limit própria.

Restrições que não mudam: o PDF é lido só no navegador (pdf.js), a API recebe
apenas valores conferidos, e o CNPJ aparece mascarado na tela de importação.

## Goals / Non-Goals

**Goals:**

- Um lote pode misturar documentos de várias empresas; cada competência
  pertence a exatamente uma empresa.
- Conferência com um card por empresa: identificação no topo, tabela embaixo.
- Identificação, cadastro, conflito e gravação independentes por empresa, com
  retentativa só do que falhou.
- Lote de empresa única continua com a mesma experiência de hoje (um card, e ao
  final a dashboard do cliente).

**Non-Goals:**

- Endpoint de gravação em lote multi-cliente na API, ou transação que abranja
  várias empresas.
- Processar os PDFs em paralelo ou num Web Worker próprio — a leitura segue
  sequencial, como hoje.
- Persistir o lote em andamento (recarregar a página continua descartando-o).
- Mudar o parser ou o leiaute aceito do PGDAS-D.
- Mudar a visão geral ou a dashboard.

## Decisions

### D1. O estado do assistente passa a ser uma lista de empresas

```ts
interface EmpresaLote {
  chave: string                // cnpj só dígitos, ou `sem-cnpj:<idArquivo>`
  cnpj: string | null          // dígitos; null enquanto não identificada
  dados: { nome: string; municipio: string; anexo: string } // editáveis
  competencias: CompetenciaLote[]
  cliente: EstadoCliente       // 'pendente' | 'buscando' | encontrado | novo | erro
  gravacao: EstadoGravacao     // 'aguardando' | 'gravando' | 'gravada' | conflito | erro
}
interface CompetenciaLote extends Competencia { _arquivos: string[] } // ids de origem
```

Tudo o que hoje é escalar no componente (`empresaEditada`, `cnpjBusca`,
`clienteEncontrado`, `cadastro`, `conflito`, `erroGravar`…) vira campo da
`EmpresaLote`. **Alternativa considerada:** manter a lista plana e agrupar com
um `computed` por `_cnpj`. Rejeitada: o estado por empresa (cliente
identificado, conflito, gravada) e as edições de razão social não têm onde
morar numa lista derivada, e o `v-model` dos inputs da tabela precisa de
objetos estáveis.

### D2. A lógica de agrupamento é um módulo puro

`src/features/pgdas/importacao/lote.ts` concentra as operações sobre
`EmpresaLote[]`, sem Vue nem I/O:

- `adicionarCompetencias(lote, idArquivo, competencias)` — chave da empresa =
  `c._cnpj` do bloco; bloco sem CNPJ herda o CNPJ de outro bloco **do mesmo
  arquivo**; se nenhum bloco do arquivo trouxer CNPJ, a chave é
  `sem-cnpj:<idArquivo>`. Dentro da empresa, mescla por `_pa` com a regra atual
  (último documento lido prevalece) e acumula `_arquivos`.
- `removerArquivo(lote, idArquivo)` — tira o id de `_arquivos`; competência que
  fica sem arquivo de origem sai; empresa sem competências sai.
- `informarCnpj(lote, chave, cnpj)` — dá CNPJ a um grupo não identificado; se
  outro grupo já tem esse CNPJ, funde os dois (mesma mescla por `_pa`).
- `ordenar` — empresas por razão social; competências por período crescente.

Isso deixa o comportamento das specs testável em Vitest sem montar a view nem
mockar pdf.js, e a view fica só com orquestração. **Por que não inferir a
empresa pelo nome do arquivo ou pela razão social?** Nome de arquivo é
arbitrário e razão social varia entre extrato e declaração; o CNPJ é a única
chave confiável, e agrupar por suposição é exatamente o erro que a mudança
corrige.

`idArquivo` é um id gerado na carga (contador), não o nome — o usuário pode
carregar dois arquivos com o mesmo nome.

### D3. Card por empresa como componente próprio

`src/components/pgdas/CardEmpresaLote.vue` recebe uma `EmpresaLote` e emite
eventos (`remover-empresa`, `remover-competencia`, `informar-cnpj`,
`cadastrar`, `gravar`). O card usa a família `.card-painel*` de
`components.css` para a moldura (cabeçalho com razão social, contagem de
competências como badge, ação de retirar a empresa) e mantém **scoped** só o que
é dele: o grid de identificação e a tabela de conferência (as classes
`.conf-table`, `.num-input` etc. migram da view para o card). A tabela segue em
`.table-card` com `overflow-x: auto`, como hoje.

O mesmo card serve aos passos 2 e 3 com uma prop `modo: 'conferencia' |
'gravacao'`: na conferência mostra identificação + tabela editável; na gravação
mostra identificação + situação do cliente (cadastro, conflito, resultado) e um
resumo das competências, sem a tabela editável. **Alternativa:** dois
componentes. Rejeitada por duplicar o bloco de identificação, que precisa ser
idêntico nos dois passos.

### D4. Identificação: uma chamada por empresa, com concorrência limitada

Ao abrir o passo 2, cada empresa com CNPJ e `cliente === 'pendente'` dispara
`identificarClientePgdas`. As chamadas rodam com no máximo **3 em paralelo**
(fila simples no próprio módulo da view), para não despejar dezenas de
requisições de uma vez num lote grande. Empresa não identificada só é buscada
quando o usuário informa o CNPJ (`informarCnpj` → identificar). Voltar ao passo
1 e adicionar arquivos identifica só as empresas novas.

### D5. Gravação: uma requisição por empresa, sequencial

"Gravar todas" percorre as empresas prontas (cliente identificado, gravação em
`aguardando` ou `erro`) **uma de cada vez** e chama o `POST /api/pgdas/apuracoes`
existente com o `GravarApuracoesRequest` daquela empresa — `montarSerieMensal`
e `competenciaDocumentoMaisRecente` passam a receber a lista de competências da
empresa em vez de ler o estado global. Resultado por empresa:

- 200 → `gravada` (não entra mais em "Gravar todas");
- 409 → `conflito` com a resposta; o card mostra as competências e o botão
  "Substituir e gravar", que reenvia **só aquela empresa** com `substituir: true`;
- outro erro → `erro`, retentável.

**Por que não um endpoint multi-cliente?** A API já é atômica por cliente, a
confirmação de substituição é por cliente, e um endpoint novo duplicaria
validação e tenant check sem ganho para o usuário — falha parcial por empresa é
o comportamento desejado, não um problema a esconder numa transação maior.
**Por que sequencial e não paralelo?** Lote típico é de dezenas de empresas;
sequencial dá progresso legível ("gravando 4 de 12") e não compete com o
connection pool da API. Se ficar lento, paralelizar com o mesmo limite do D4 é
mudança local.

### D6. Conclusão

Com uma empresa no lote, a gravação bem-sucedida navega para
`/f/pgdas/dashboard/{clienteId}`, como hoje. Com várias, o passo 3 vira o
resumo: cada card em `modo: 'gravacao'` exibe "N competências gravadas" e o link
"Ver dashboard"; um botão leva à visão geral do PGDAS-D. Nada navega
sozinho enquanto houver empresa com conflito ou erro.

### D7. Passos e textos

Os três passos continuam. O botão do passo 1 passa a dizer "Conferir dados (E
empresa(s), N competência(s))" e a dica de mescla explica que ela ocorre "por
empresa". O passo 2 só avança se toda empresa restante tiver CNPJ (as não
identificadas precisam ser resolvidas ou retiradas); o passo 3 lista as empresas
na mesma ordem do passo 2.

## Risks / Trade-offs

- [Lote grande deixa a página pesada: dezenas de cards com tabelas de 12+
  linhas de inputs] → Cards a partir do segundo podem começar recolhidos com um
  resumo (competências, divergências) e expandir ao clicar; divergência expande
  o card automaticamente. Avaliar com um lote real de ~30 empresas antes de
  decidir se é necessário.
- [Leitura sequencial de muitos PDFs demora] → Fora do escopo (Non-Goals); a
  lista de arquivos já mostra o status por arquivo, e o timeout de 30 s por
  arquivo continua impedindo que um PDF trave o lote.
- [Gravação parcial deixa o lote "meio gravado" se o usuário fechar a aba] →
  Cada empresa gravada é atômica e idempotente do ponto de vista do usuário:
  reimportar o lote leva ao 409 nas que já foram, com a substituição explícita
  de sempre. Nada fica corrompido.
- [Bloco sem CNPJ herdando o CNPJ de outro bloco do mesmo arquivo pode errar se
  um PDF misturar empresas] → O PGDAS-D emite um documento por CNPJ; a herança
  vale só dentro do arquivo e só para bloco sem CNPJ algum. Bloco com CNPJ
  próprio sempre vai para a própria empresa.
- [Identificação em massa grava o CNPJ completo no cliente
  (`IdentificarClienteAsync` já faz isso hoje)] → Comportamento inalterado,
  apenas executado N vezes; o CNPJ completo é o que a spec "O CNPJ completo é
  persistido" já prevê.
- [Refatoração grande de uma view com testes existentes] → O módulo puro (D2)
  chega primeiro com testes próprios; a view é refeita em cima dele e o
  `PgdasImportacaoView.spec.ts` existente continua passando para o caso de
  empresa única antes de ganhar os casos de lote.

## Migration Plan

Mudança só de frontend, sem migração de banco nem de contrato. Deploy normal do
painel; rollback é reverter o build. Não há dado gravado em formato novo.

## Open Questions

- Cards recolhidos por padrão a partir de quantas empresas? (Risco 1 — decidir
  na implementação com um lote real.)
- O resumo do lote deve oferecer exportar/baixar algo (ex.: lista de empresas
  com divergência)? Fora do pedido atual; anotar se surgir no uso.
