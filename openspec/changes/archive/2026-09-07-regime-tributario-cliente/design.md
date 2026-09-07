## Context

`Cliente` (`ContabOne.Api/Domain/Entities.cs`) guarda hoje código, nome, CNPJ
mascarado + hash, validade e nome do arquivo do certificado, origem e o modelo
de onboarding. Nada sobre o enquadramento fiscal da empresa.

Três fatos do repositório moldam este change:

1. **Enums viajam como inteiro** (`AGENTS.md`) — nenhum `JsonStringEnumConverter`
   está registrado. Mas `ClienteDto.Origem` já contorna isso sendo tipado como
   `string` e preenchido com `c.Origem.ToString()`, e `ClienteRequest.Origem`
   entra como `string?`. Este endpoint já tem, portanto, um precedente próprio.
2. **A sincronização do agente atribui campo a campo** (`AgentEndpoints.cs`,
   ramo `existente != null`). Ela já não toca em `ModeloOnboardingId` — e por
   isso a escolha feita na tela sobrevive. O mesmo vale para o regime, mas por
   omissão, que é frágil.
3. **A ordenação é um conjunto fechado no servidor** (`ClientesEndpoints.Ordenar`),
   com `ThenBy(c => c.Id)` obrigatório em todo ramo e tratamento explícito de
   nulo no ramo do certificado.

O change é pequeno em superfície e quase inteiro sobre convenções já
estabelecidas — o que este documento decide é *qual* convenção vale em cada
ponto, porque duas delas se contradizem (item 1).

## Goals / Non-Goals

**Goals:**

- Guardar o regime tributário do cliente como dado de primeira classe, escolhido
  entre cinco valores fixos.
- Manter a escolha opcional e distinguível de "Outros".
- Deixar o regime visível na listagem sem obrigar a abrir a edição.
- Garantir que a sincronização do agente nunca apague a escolha — com teste, não
  com sorte.

**Non-Goals:**

- Usar o regime para decidir qualquer coisa: quais ferramentas o cliente vê,
  qual modelo de onboarding recebe, quais obrigações o painel cobra. Hoje o
  campo é descritivo, e só.
- Histórico de mudança de regime (empresa que migra de Simples para Presumido
  em 1º de janeiro). Guardamos o regime **atual**; versionar por competência é
  outro change, com outra tabela.
- Levar o regime até os agentes Python. Nenhum deles precisa dele, e o contrato
  `/api/agent` não muda.

## Decisions

### D1 — Enum novo, persistido como inteiro, append-only

`RegimeTributario` entra em `Domain/Enums.cs` na ordem em que o usuário a
enunciou: `SimplesNacional`, `LucroPresumido`, `LucroReal`, `Mei`, `Outros`.
Persistido como inteiro, como a maioria dos vizinhos daquele arquivo, com o
mesmo comentário de invariante que `OrigemCliente` carrega: **só acrescentar ao
fim; reordenar reescreve o significado das linhas já gravadas.**

*Alternativa considerada:* persistir como string, com `HasConversion<string>`,
como `LayoutDashboard`. Aquele caso se justifica por precisar de um `DEFAULT`
legível na coluna. Aqui a coluna é anulável e não tem default — o argumento não
se aplica, e o inteiro é o caminho batido.

*Alternativa considerada:* tabela de domínio (`RegimesTributarios`) com FK.
Rejeitada: o conjunto é fixo por lei, não por configuração de escritório, e uma
tabela abriria a porta para regime inventado por tenant — exatamente o que o
requisito de conjunto fechado proíbe. Nada aqui se parece com o catálogo de
produtos, que é editável de propósito.

### D2 — Coluna anulável, sem backfill

`public RegimeTributario? RegimeTributario { get; set; }` na entidade, coluna
`integer NULL` na migration, e **nenhum `UPDATE` de backfill**.

A base atual é majoritariamente de clientes cadastrados pelo agente. Ninguém
sabe o regime deles; marcar todos como `Outros` produziria uma base inteira
afirmando algo falso, e sem como distinguir depois quem foi realmente
classificado. `NULL` diz "ninguém informou", que é a verdade.

Isso obriga a UI a ter três estados no seletor (sem escolha / cinco opções) e a
tabela a saber exibir ausência — custo pequeno e pago uma vez.

### D3 — O regime cruza a API pelo **nome**, não pelo número

`ClienteDto.RegimeTributario` é `string?` (`c.RegimeTributario.ToString()`, que
devolve `null` para o nulo) e `ClienteRequest.RegimeTributario` é `string?`,
resolvido com `Enum.TryParse`. No frontend, `RegimeTributario` é uma union de
strings em `types.ts`, ao lado de `OrigemCliente`.

Isto contraria a linha geral do `AGENTS.md` ("enums cross the wire as
integers") e segue o precedente **do próprio DTO**: `Origem` já viaja como nome
neste mesmo objeto, e `types.ts` já declara `OrigemCliente` como union de
strings. Ter dois enums do mesmo DTO com codificações diferentes seria pior que
a inconsistência com a regra geral — e a regra geral existe por causa do
contrato com os agentes Python (`api_client.TIPO_NOTA`/`STATUS_EXECUCAO`), que
não passam por aqui.

Ganho concreto: acrescentar um membro ao enum não relabela linha nenhuma no
painel. Com inteiro, o frontend precisaria de um vetor posicional `0..4`, e uma
divergência de ordem entre C# e TS mudaria em silêncio o regime exibido de todo
mundo — um erro de dado fiscal que ninguém percebe. Com nome, a divergência é um
valor desconhecido, visível.

### D4 — Valor desconhecido é 400, não fallback

O `ClienteRequestValidator` recusa qualquer string que não seja vazia nem um dos
cinco nomes. `null` e `""` significam "sem regime".

Note o contraste deliberado com `Origem`, ali ao lado, que faz *fallback* para
`Manual` quando não reconhece o valor. São coisas diferentes: origem é
proveniência interna, e errar para `Manual` é inócuo; regime é o enquadramento
fiscal da empresa, e gravar em silêncio um valor diferente do que o caller pediu
é dado fiscal errado sem rastro. Um comentário no validador registra o porquê,
senão a assimetria parece descuido e alguém "corrige".

### D5 — Rótulos em um lugar só, no frontend

Um `const REGIMES: { valor: RegimeTributario; rotulo: string }[]` alimenta ao
mesmo tempo as `<option>` do modal e a célula da tabela. O `<select>` e a coluna
não podem discordar sobre como se escreve "Simples Nacional".

*Alternativa considerada:* endpoint de catálogo (`GET /api/regimes`). Rejeitada:
cinco valores fixos por lei não justificam uma chamada de rede no bootstrap, e o
catálogo dinâmico do repo (`/api/produtos`) existe porque publicar ferramenta é
trabalho de dado — aqui não é.

O mapeamento nome → rótulo mora no frontend, não no C#, porque é decisão de
apresentação e o backend nunca precisa dele. `Mei` → "MEI" é a única entrada
onde o rótulo não é o nome com espaços.

### D6 — Ordenação por regime segue a regra de nulo do certificado

Novo ramo `"regime"` no `switch` de `Ordenar`, com a mesma forma do ramo
`"certificado"`:

```
query.OrderBy(c => c.RegimeTributario == null)
     .ThenBy(c => c.RegimeTributario)   // ou ThenByDescending
     .ThenBy(c => c.Id)
```

O `== null` primeiro empurra os sem regime para o fim **nas duas direções**; sem
ele, o Postgres abriria a lista decrescente com quem não tem regime nenhum. Duas
colunas vizinhas tratando ausência de formas opostas é uma pegadinha que o
usuário teria de decorar.

O `ThenBy(c => c.Id)` não é enfeite, pelo mesmo motivo já documentado no método:
com cinco valores possíveis e centenas de clientes, **o empate é a regra, não a
exceção**, e `Skip`/`Take` sobre ordenação empatada faz cliente aparecer em duas
páginas e sumir de outra.

Ordena-se pelo inteiro, ou seja, pela ordem de declaração do enum — Simples,
Presumido, Real, MEI, Outros. É uma ordem fiscal razoável e melhor que a
alfabética (que colocaria "Lucro Presumido" antes de "MEI" e "Simples Nacional"
por último, sem significado nenhum). Fica registrado que a ordem exibida depende
da ordem de declaração, que D1 já congelou.

### D7 — Agente: nenhuma linha nova, um teste novo

`AgentEndpoints` não muda. O comportamento correto — não escrever no regime — já
é o que acontece, porque o bloco de atualização lista os campos um a um.

O risco é de manutenção: o próximo a ler aquele bloco vê uma lista de campos do
`Cliente` que parece incompleta e "completa". Um teste que sincroniza um cliente
com regime informado e verifica que ele continua lá transforma essa omissão
intencional em contrato verificado. É o mesmo padrão de `IsolamentoTest` e
`TraducaoLinqTest`: o teste existe para o defeito que ainda não aconteceu.

### D8 — Filtro por token, com "não informado" como sexta opção

`ListarAsync` ganha `string? regimeTributario`, resolvido por um helper que
devolve `Expression<Func<Cliente, bool>>?` — a mesma forma de
`CertificadoFiltros.PorToken`. Seis tokens: os cinco nomes do enum mais
`naoInformado`.

**Por que "não informado" é opção do filtro, e não uma ausência de opção.** D2
deixou a base inteira sem regime de propósito, e a pergunta que o escritório vai
fazer no dia seguinte é "quem falta classificar?". Sem esse token, os clientes
que mais precisam de atenção seriam exatamente os únicos inalcançáveis pelo
filtro — o campo nasceria com um buraco no lugar onde ele é mais útil. Não
colide com nada: `naoInformado` não é nome de membro do enum.

**Token desconhecido não filtra, e não é erro** — ao contrário do 400 do
cadastro (D4). A assimetria é a mesma que o repositório já pratica em
`CertificadoFiltros.PorToken` e no `switch` de `Ordenar`: escrita ruim vira dado
ruim e tem de ser barrada; leitura ruim só precisa mostrar uma lista. Endereço
velho ou colado errado abre a tela, não uma falha.

*Alternativa considerada:* criar `RegimeFiltros`, espelhando `CertificadoFiltros`.
Rejeitada por ora — aquela classe existe porque **contador do painel e filtro
compartilham o predicado**, e um número que não bate com a lista aberta é o
defeito que ela previne. Aqui não há contador. Um helper privado em
`ClientesEndpoints` diz o mesmo sem inventar um ponto de compartilhamento que
não tem segundo lado. Se um indicador de regime aparecer no painel, extrair a
classe é o passo óbvio.

## Risks / Trade-offs

**Reordenar o enum reescreve dado fiscal já gravado** → Comentário XML no enum
com a invariante, no mesmo formato de `OrigemCliente`; D1 explícito neste
documento; e o novo membro futuro entra ao fim por regra, não por lembrança.

**A tabela de clientes chega a oito colunas na visão admin** (código, nome,
escritório, CNPJ, regime, certificado, atualizado, ações) → Os rótulos são
curtos e a coluna usa as classes compartilhadas de `components.css`; nada de CSS
por-view (`AGENTS.md`). Se a densidade incomodar em telas estreitas, a saída é
tratar a responsividade da tabela inteira, não esconder esta coluna — o problema
já existia com sete.

**"Outros" vai virar depósito** — o usuário com pressa escolhe "Outros" em vez
de deixar em branco, e o campo perde poder de segmentação → Aceito. O rótulo do
estado vazio no seletor deixa claro que não escolher é uma opção legítima. Não
há como impedir sem tornar o campo obrigatório, o que só empurraria mais gente
para "Outros".

**O regime fica desatualizado** — empresa migra de regime na virada do ano e
ninguém edita o cadastro → Aceito neste change. É o mesmo risco de qualquer
cadastro manual, e a alternativa (histórico por competência) é o Non-Goal
declarado acima. Vale registrar como candidato a change futuro se o campo passar
a alimentar apuração.

**Divergência entre a union de strings do TS e o enum do C#** → O valor
desconhecido aparece como texto estranho na coluna, visivelmente, em vez de
relabelar linhas em silêncio (que é o que o inteiro faria). É exatamente o
trade-off que D3 comprou.

## Migration Plan

1. Enum + propriedade na entidade.
2. `dotnet ef migrations add RegimeTributarioCliente --project ContabOne.Api` —
   uma coluna `integer NULL` em `Clientes`, sem `UPDATE`. **Sem índice**, mesmo
   com o filtro de D8: a listagem já é escopada por escritório e paginada, e o
   conjunto tem cinco valores — seletividade baixa demais para o Postgres
   preferir um índice ao seq scan da partição do tenant. Se algum escritório
   grande mostrar plano ruim, aí sim é caso de índice, medido.
3. API (DTO, request, validador, projeções, `Ordenar`), depois frontend.
4. As migrations rodam sozinhas no startup e dentro do Testcontainers a cada
   `dotnet test` — uma migration quebrada derruba a suíte, que é o gate.

**Rollback:** a coluna é anulável e nada a lê fora do slice de clientes;
reverter a migration só descarta os regimes informados no intervalo. Nenhum
outro dado depende dela.

## Open Questions

- **Regime como pré-requisito de ferramenta** — oferecer o PGDAS-D só a quem é
  Simples Nacional é tentador e mudaria a natureza do campo, de descritivo para
  normativo. Precisa de proposta própria: hoje o gate comercial é
  `EscritorioProdutos`, e misturar enquadramento fiscal com liberação de produto
  merece decisão consciente.
