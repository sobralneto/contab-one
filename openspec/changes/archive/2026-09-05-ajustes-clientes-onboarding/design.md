## Context

Três ajustes pequenos que, juntos, tocam dois slices da API, o dashboard e a
listagem de clientes. O que exige desenho é o segundo e o terceiro: eles
compartilham uma noção — "cliente em fase de onboarding" — que não existe em
lugar nenhum do código hoje e que, se for escrita duas vezes, vai divergir.

Estado atual relevante:

- `Cliente.ModeloOnboardingId` é opcional. Sem modelo, o cliente não tem
  onboarding nenhum: a própria listagem já esconde a ação de checklist
  (`ClientesEndpoints.ListarAsync`).
- `ChecklistOnboardingCliente` só nasce quando alguém aciona "Adicionar
  checklist". No máximo um por cliente.
- `ChecklistOnboardingCliente.PercentualConclusao` é uma redundância deliberada
  (design.md da change de onboarding, D3): a verdade é derivável
  (concluídas ÷ total de tarefas do modelo), mas fica persistida para não exigir
  varredura de itens toda vez que o percentual aparece em outra tela. É gravado
  a cada alternância de tarefa e reconciliado na leitura do checklist.
- `ClientesEndpoints.AtualizarAsync` não copia `req.Codigo` para a entidade, e o
  campo vem `:disabled` no modal. O índice `(EscritorioId, Codigo)` é único.
- `AgentEndpoints` casa cliente por `(EscritorioId, Codigo)` — o agente só
  conhece o código, tirado do nome do arquivo `.pfx`.

Restrições que valem aqui: filtros globais de tenant fazem o escopo
(`AppDbContext`); predicado sobre propriedade computada quebra a tradução do EF
em tempo de execução (`TraducaoLinqTest`); enums e contratos com o Python não
são tocados.

## Goals / Non-Goals

**Goals:**

- Tornar o código do cliente editável sem abrir buraco na unicidade por
  escritório nem quebrar em silêncio a sincronização do agente.
- Uma definição só de "em onboarding", em um lugar só, consumida pelo filtro da
  listagem e pelo KPI do dashboard.
- Nada de migration, entidade nova, coluna nova ou enum novo.

**Non-Goals:**

- Não existe "concluir onboarding" como ato explícito — a conclusão continua
  sendo consequência de marcar a última tarefa. Nenhum campo de estado novo.
- Não filtrar por onboarding **concluído**, nem por faixa de percentual, nem
  ordenar a listagem por progresso.
- Não exibir o percentual de cada cliente na listagem (a coluna já mostra a ação
  de checklist; progresso por linha é outra discussão).
- Não mexer na sincronização do agente para acompanhar código renomeado.

## Decisions

### D1 — "Em onboarding" = tem modelo e ainda não fechou 100%

    ModeloOnboardingId != null
    && não existe checklist desse cliente com PercentualConclusao >= 100

Escrito com essa negação, os dois casos de "ainda em onboarding" caem no mesmo
ramo: **sem checklist** e **checklist abaixo de 100**. Uma condição só, sem
`OR`, e traduzível.

Alternativas descartadas:

- *Só quem tem checklist criado.* Deixaria de fora justamente o cliente recém
  cadastrado com modelo escolhido — que é o mais "em onboarding" de todos.
- *Todo cliente com modelo, concluído ou não.* Vira "clientes com modelo", que
  não responde à pergunta ("quantas implantações estão em curso?").
- *Um campo `OnboardingConcluidoEm` no cliente.* Estado novo para representar o
  que o percentual já representa, mais uma migration, mais um lugar para
  dessincronizar.

Efeito colateral aceito: cliente cujo modelo não tem tarefa nenhuma fica com
percentual 0 (a spec de onboarding manda ser 0, sem erro) e portanto conta como
"em onboarding" para sempre. É coerente — um modelo vazio é um onboarding que
ninguém terminou de montar — e o caminho de saída é povoar o modelo ou tirá-lo
do cliente.

### D2 — O predicado mora no slice de onboarding, não é copiado

`Features/Onboarding/` passa a expor o predicado como
`Expression<Func<Cliente, bool>>`, e `ClientesEndpoints.ListarAsync` e
`DashboardEndpoints.KpisAsync` o consomem. É uma expressão, não um método com
`bool` de retorno: método com corpo em C# não é traduzível pelo EF e viraria
avaliação em memória — a listagem inteira materializada por página.

Por que ali e não em `Domain/`: o predicado precisa de um subselect sobre
`db.ChecklistsOnboardingCliente` (não há navegação de `Cliente` para o
checklist), então recebe o `AppDbContext` — e `Domain/` depender de `Infra/` é a
seta ao contrário.

Alternativas descartadas:

- *Copiar a condição nos dois handlers.* É exatamente o que a spec proíbe: dois
  lugares divergem, o card mostra um número e a lista mostra outro.
- *Criar a navegação `Cliente.ChecklistOnboarding`.* Deixaria o predicado
  autocontido, mas muda o modelo (e o snapshot) para um ganho de sintaxe; o
  padrão do arquivo hoje é o subselect correlacionado (`TemChecklistOnboarding`,
  D11 da change de onboarding).

### D3 — Ler o percentual persistido, não recalcular

O predicado lê `PercentualConclusao` da linha do checklist. Recalcular por
cliente (contar itens concluídos ÷ tarefas do modelo) dentro de um filtro de
listagem paginada seria um agregado por linha em toda página.

O preço é o do próprio D3 da change de onboarding: o percentual pode ficar
temporariamente defasado quando o **modelo** muda (uma tarefa nova entra e
todo mundo devia cair abaixo de 100), até que alguém abra o checklist e a
reconciliação da leitura o corrija. Assumido conscientemente: é o mesmo número
que já aparece em toda tela de onboarding — melhor defasar junto do que exibir
dois valores diferentes para o mesmo cliente.

### D4 — Edição de código: unicidade excluindo o próprio, 409 como no cadastro

`AtualizarAsync` valida antes de gravar:

    db.Clientes.Any(c => c.EscritorioId == cliente.EscritorioId
                      && c.Codigo == req.Codigo
                      && c.Id != id)

O `c.Id != id` é o que faz "salvar sem mexer no código" continuar funcionando.
O escritório vem da entidade carregada, nunca do request — `ClienteRequest` tem
`EscritorioId`, e usá-lo aqui deixaria mover cliente de escritório por PUT.

Resposta: `409 Conflict` com a mesma forma de `CriarAsync`
(`{ erro = "Código já existe para este escritório" }`), que o modal já sabe
exibir (`e?.response?.data?.erro`). Sem isso, a colisão sairia como 500 do
índice único.

`ClienteRequestValidator` já exige `Codigo` não vazio e ≤ 20 — vale para o PUT
sem mudança.

### D5 — Código editável também para cliente de origem agente, com aviso

O agente casa cliente por código. Renomear o código de um cliente
`Origem = Agente` sem renomear o `.pfx` na máquina do escritório faz a próxima
sincronização **cadastrar um cliente novo** sob o código antigo — o antigo fica
com todo o histórico e o novo nasce vazio.

Ainda assim o campo fica editável: renomear os dois lados é o caso de uso que
motiva a mudança, e travar o campo devolveria o usuário ao "excluir e recriar".
O modal exibe o aviso ao lado do campo quando `origem === 'Agente'`, no mesmo
espaço de `.field-hint` que CNPJ e validade já usam — a diferença é que ali o
campo fica desabilitado e aqui não.

Alternativa descartada: *desabilitar para origem agente*. Cobre o risco mas
deixa sem solução o cadastro errado que veio do próprio agente, que é o caso
mais provável de precisar de correção.

### D6 — O filtro é um seletor próprio, visível para todos os papéis

A barra de ferramentas hoje é um `v-if/v-else`: admin vê o seletor de
escritório, os demais veem o de vencimento de certificado. O de onboarding entra
como um terceiro seletor, **fora** desse `v-if` — onboarding não é assunto de
papel. Fica com duas opções ("Todos os clientes" / "Em onboarding"), e o
parâmetro só vai para a API quando ligado (`emOnboarding: true | undefined`).

`bool?` no handler, e não `bool`: `emOnboarding=false` seria "só quem NÃO está
em onboarding", que ninguém pediu e a spec não descreve. Ausente é ausente.

### D7 — O indicador vai para o hub, não para a visão geral de uma ferramenta

Existem três telas que alguém chamaria de "dashboard", e a escolha entre elas
não é cosmética:

| Rota | Componente | O que é |
|---|---|---|
| `/` | `HubView.vue` | tiles das ferramentas + colunas do escritório |
| `/f/nfse` (destino do redirect de `/dashboard`) | `DashboardView.vue` | visão geral de UMA ferramenta, o NFS-e |
| `/f/pgdas` | `PgdasVisaoGeralView.vue` | visão geral do PGDAS-D |

O indicador vai para o **hub**. Onboarding é do cliente, não de ferramenta
alguma — o slice de Onboarding não é sequer particionado por produto. Em
`/f/nfse`, o escritório que só usa PGDAS-D nunca veria o número, o que
esvaziaria o requisito. O precedente está na mesma tela: `CertificadosVencimento`
mora no hub, com o comentário dizendo exatamente isto — "validade de certificado
é do cliente/escritório, não de uma ferramenta".

Arranjo final do hub: faixa de ferramentas (intocada), faixa com os três
contadores de certificado, e duas colunas — tarefas do dia e onboarding. Sem
custo de rede para os contadores: `HubView` já chamava `fetchKpis()` para os
números do card do NFS-e; por isso o `ref` deixou de se chamar `kpisNfse` e
passou a `kpis`, já que agora serve os dois.

`KpisAsync` ganha os quatro campos no objeto anônimo de retorno, e
`DashboardKpis` os correspondentes — acréscimo, nada renomeado, nada removido.

Alternativa descartada: *deixar nos dois lugares*. Duplicaria o mesmo número em
duas telas, com o risco clássico de uma delas envelhecer.

### D8 — As três faixas de certificado são contadas no servidor

Dava para derivar as três contagens no navegador, a partir de
`GET /dashboard/certificados`, que o hub já chamava. Não dá: aquela consulta tem
`Take(50)`. Escritório com mais de 50 certificados vencidos ou a vencer veria
contadores errados, e um contador errado é pior do que contador nenhum —
ninguém confere um número que parece plausível.

Então entram três `CountAsync` em `KpisAsync`, sobre a base inteira do escopo.
As faixas são contíguas e disjuntas:

| Faixa | Intervalo |
|---|---|
| vencidos | `validade < hoje` |
| até 3 dias | `hoje ≤ validade ≤ hoje+3` |
| de 4 a 30 dias | `hoje+3 < validade ≤ hoje+30` |

O horizonte de 30 dias não é arbitrário: é o mesmo já usado por
`certificadosVencendo30d`, por `CertificadosAsync` e pelo `AlertaJob`. Um
certificado que vence em 90 dias não entra em faixa nenhuma — não é notícia.
`vencendo3d + vencendoMais3d` reproduz exatamente `certificadosVencendo30d`, que
continua existindo para a visão geral do NFS-e; os vencidos ficam fora desse
total porque ele conta o que está *por* vencer.

Com isso a lista de certificados sai do hub: os contadores respondem "quantos", e
o detalhe já existe na tela de Clientes, com filtro por vencimento. Manter os
dois seria somar e listar os mesmos certificados na mesma tela.

### D9 — Degradê e tinta andam em par, como token

Os três cartões carregam a informação na cor, então o contraste do texto sobre
degradê deixa de ser detalhe estético. Medido:

| Sobre | Branco |
|---|---|
| `#dc2626` (vermelho) | 4,83:1 |
| `#ea580c` (laranja) | 3,56:1 |
| `#fbbf24` (amarelo) | **1,67:1** |

Texto branco sobre amarelo só passa em 4,5:1 escurecendo até `#b45309` — que já
não é amarelo, e mataria a distinção entre o cartão de 3 dias e o de 30. Por
isso os três usam **degradê claro com tinta escura da mesma família**, e cada tom
publica o par em `tokens.css` (`--grad-erro` + `--grad-erro-texto`, e assim por
diante), como `--accent-gradient` já fazia com `--accent-gradient-texto`. Pior
caso medido: 5,28:1 no claro, 5,48:1 no escuro.

No tema escuro o par se inverte — pastel vira lanterna sobre página escura —,
com degradê translúcido sobre `--surface-card` e tinta clara, a mesma construção
dos `--*-suave` que já existem.

O componente nunca escreve cor: só escolhe `tom`. É o que garante que a medição
valha nos dois temas sem ninguém reconferir.

### D10 — A lista de onboarding ordena por progresso, no cliente

A API ordena clientes por nome. Para o hub isso é a ordem errada: quem interessa
é quem está quase pronto. Como o hub mostra poucos (5), pedir `tamanho=5` traria
os cinco primeiros do alfabeto, não os cinco mais adiantados — então o componente
pede uma página grande e ordena por percentual antes de cortar.

Isso vale enquanto "clientes em onboarding" for um conjunto pequeno, que é o caso
(são implantações simultâneas de um escritório, não a base inteira). Se um dia
não for, a ordenação vira parâmetro da API — e o sinal disso será o `total`
passar de uma página.

O percentual vem de `ClienteDto.PercentualOnboarding`, projetado com o mesmo
subselect correlacionado que já produzia `TemChecklistOnboarding` — sem N+1.
`FirstOrDefault()` sobre um cliente sem checklist devolve 0, que é exatamente o
percentual de quem tem modelo e não começou.

### D12 — A página inicial deixa de ser lançador de ferramentas

Os cards de ferramenta agrupados por domínio saem da página inicial. Hoje isso
são exatamente dois blocos — **Fiscal** (nfse, pgdas) e **DP** (det); o domínio
`contabil` está semeado mas sem produto algum, então não renderiza nada e não há
um terceiro bloco a preservar.

Nada fica inalcançável: `AppLayout` já monta o menu lateral a partir do mesmo
`catalogo.porDominio`, com o mesmo agrupamento por domínio. A navegação por
ferramenta simplesmente passa a ter **um** lugar em vez de dois, e a página
inicial passa a ser sobre o trabalho em aberto do escritório.

Duas consequências que não são cosméticas:

1. **O card informativo de ferramenta não contratada morre junto.** Era um
   requisito próprio — vitrine deliberadamente passiva, sem navegação e sem
   pedido de contratação. Com os cards fora, não sobra onde encaixá-lo: o menu
   lateral esconde domínio sem ferramenta contratada, de propósito, e reintroduzir
   a vitrine ali contrariaria esse outro requisito. A spec registra a remoção com
   o motivo, e a volta dela pede lugar próprio (uma página de catálogo), não o
   painel.
2. **O catálogo deixa de gatear a tela.** Antes, a página inteira ficava atrás de
   `carregando` / `falhou` / `sem ferramentas`, porque tudo que ela mostrava vinha
   do catálogo. Agora nada vem: contadores, tarefas e onboarding têm fontes
   próprias. Manter o gate esconderia um painel perfeitamente utilizável por causa
   de uma falha que só afeta o menu. Então o `carregando` e o estado vazio de
   "nenhuma ferramenta" saem, e a falha vira faixa estreita no topo — a spec de
   layout exige sinalizar e oferecer nova tentativa, e isso continua sendo feito.

### D11 — O atalho do hub leva à lista já filtrada

`ClientesView` passa a ler `?emOnboarding=true` da URL para nascer com o filtro
ligado. Sem isso, o atalho cairia na lista inteira e o usuário veria um número no
hub e outro na tela seguinte — exatamente a incoerência que a spec proíbe.

## Risks / Trade-offs

- **Código renomeado sem renomear o `.pfx` → cliente duplicado na próxima
  sincronização** → aviso no modal para cliente de origem agente (D5). Não há
  proteção técnica: o servidor não tem como saber o nome do arquivo na máquina
  do escritório. É o risco principal desta change.
- **Predicado novo não traduzível pelo EF** → é exatamente o defeito que já
  chegou à produção duas vezes; entra caso em `TraducaoLinqTest`, que prova a
  tradução com `ToQueryString()` sem banco. Só colunas mapeadas no predicado —
  nenhuma propriedade computada.
- **Percentual defasado depois de mexer no modelo** → aceito (D3); é o mesmo
  número já exibido em todas as telas de onboarding.
- **Modelo sem tarefas conta como onboarding eterno** → aceito e documentado
  (D1); coerente com a spec, que manda o percentual ser 0 nesse caso.
- **Filtro e contagem aplicam o mesmo predicado, mas a contagem ignora os demais
  filtros da listagem** (busca, escritório escolhido no seletor) → é o esperado:
  o hub fala do escopo da sessão, não do que o usuário digitou na outra tela. A
  spec cobra coerência *com o filtro de onboarding ligado*, não com busca
  aplicada.
- **A lista de certificados sai do hub** → quem usava aquela lista para varrer
  cliente a cliente perde o atalho e passa pela tela de Clientes. Foi a escolha
  explícita ao trocar detalhe por contagem; o caminho de volta é o filtro de
  vencimento que já existe lá.
- **Ordenação por progresso feita no navegador** (D10) → correto enquanto o
  conjunto couber numa página. Se `total` passar de 100, os cinco exibidos
  deixam de ser os cinco mais adiantados da base. Mitigação: o rodapé mostra
  `total`, então o próprio card denuncia quando esse dia chegar.

## Migration Plan

Nada a migrar: sem mudança de esquema, sem dado a converter, sem contrato de
agente alterado. Deploy normal da API e do frontend; rollback é reverter o
commit.

**Frontend antigo contra API nova**: continua funcionando — campos e parâmetros
novos são simplesmente ignorados.

**API antiga contra frontend novo** (a ordem de deploy errada, e também o estado
de quem esqueceu de reiniciar a API em desenvolvimento): todo campo novo chega
indefinido. Cada consumidor tem de degradar para zero, e não para tela quebrada:

- os quatro campos de `DashboardKpis` já entram como `?? 0` no template, então
  os contadores exibem 0;
- `percentualOnboarding` é normalizado ao carregar a lista (`?? 0`, com clamp em
  0–100). Sem isso o percentual sairia como `%` sem número, a barra com `width`
  inválido e a ordenação inteira em `NaN` — o campo é obrigatório no contrato
  atual, mas contrato não é garantia de qual versão está no ar do outro lado;
- `emOnboarding` seria ignorado pelo handler antigo, e a listagem viria inteira.

Nenhum desses estados é bonito, mas todos são legíveis e passam sozinhos quando
a API certa sobe.

## Open Questions

Nenhuma bloqueante. Fica registrado, para depois: se o escritório passar a pedir
"quem terminou o onboarding este mês", aí sim vale discutir um marco de
conclusão persistido (`OnboardingConcluidoEm`) — hoje não há como responder essa
pergunta, e esta change deliberadamente não a responde.
