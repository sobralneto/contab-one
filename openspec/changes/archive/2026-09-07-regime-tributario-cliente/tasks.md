## 1. Domínio e banco

- [x] 1.1 `Domain/Enums.cs`: enum `RegimeTributario` com `SimplesNacional`,
  `LucroPresumido`, `LucroReal`, `Mei`, `Outros`, nessa ordem (D1). Comentário
  XML com a invariante de sempre — persistido como inteiro, só acrescentar ao
  fim, nunca reordenar — porque a ordem de declaração é ao mesmo tempo o valor
  gravado e a ordem da coluna ordenada (D6).
- [x] 1.2 `Domain/Entities.cs`: `RegimeTributario? RegimeTributario` em
  `Cliente`, anulável. O comentário registra que `null` é "ninguém informou" e
  NÃO é `Outros` — a distinção é o requisito, não detalhe de implementação.
- [x] 1.3 `dotnet ef migrations add RegimeTributarioCliente --project ContabOne.Api`
  — coluna `integer NULL`, sem backfill e sem índice (D2). Conferir que a
  migration gerada não traz `UPDATE` nenhum e não encosta em
  `AppDbContextModelSnapshot.cs` à mão.

## 2. API

- [x] 2.1 `ClienteDto`: `string? RegimeTributario`, preenchido com
  `c.RegimeTributario.ToString()` nas **duas** projeções de
  `ClientesEndpoints` — `ListarAsync` e `ObterAsync`. Nome, não inteiro, pelo
  precedente do `Origem` no mesmo DTO (D3); esquecer a segunda projeção deixa a
  edição sem o valor atual.
- [x] 2.2 `ClienteRequest`: `string? RegimeTributario`, resolvido com
  `Enum.TryParse`. Vazio/ausente = sem regime.
- [x] 2.3 `ClienteRequestValidator`: aceita vazio ou um dos cinco nomes; qualquer
  outra coisa é erro de validação (D4). Comentário explicando por que aqui NÃO
  se faz o fallback que o `Origem` logo acima faz — regime errado gravado em
  silêncio é dado fiscal errado sem rastro.
- [x] 2.4 `CriarAsync`: grava o regime resolvido; sem valor, o cliente nasce sem
  regime.
- [x] 2.5 `AtualizarAsync`: grava o regime resolvido, **inclusive quando o
  resultado é `null`** — é assim que a edição limpa a escolha. Cuidado para não
  copiar o padrão "só atribui se veio preenchido" usado ali perto pelo CNPJ, que
  tornaria a limpeza impossível.
- [x] 2.6 `Ordenar`: ramo `"regime"` com `OrderBy(c => c.RegimeTributario == null)`
  antes do critério real e `ThenBy(c => c.Id)` no fim (D6) — nulos no fim nas
  duas direções, e desempate obrigatório, que com cinco valores possíveis é a
  regra e não a exceção.
- [x] 2.7 `TraducaoLinqTest`: provar que a ordenação por regime traduz, com o
  ramo de nulos — o mesmo cuidado que a de certificado já tem.

## 3. Frontend

- [x] 3.1 `api/types.ts`: `export type RegimeTributario = 'SimplesNacional' | ...`
  junto das demais unions, e o campo em `ClienteDto` (`string | null`) e em
  `ClienteRequest` (opcional, `null` limpa).
- [x] 3.2 `views/ClientesView.vue`: `REGIMES` como lista única de
  `{ valor, rotulo }` (D5), alimentando as `<option>` do modal e a célula da
  tabela. `Mei` → "MEI" é a única entrada cujo rótulo não é o nome com espaços.
- [x] 3.3 Modal: `<select>` de regime, com a primeira opção `null` rotulada de
  forma a deixar claro que não escolher é legítimo (não "Selecione..."), e
  `field-hint` curto. Entra no `form`, no `abrirCriar` (vazio), no `abrirEditar`
  (valor do cliente) e no payload de `salvar` — os quatro, senão o campo some
  em algum dos caminhos.
- [x] 3.4 Tabela: entrada `{ rotulo: 'Regime', chave: 'regime' }` em `colunas` e
  a `<td>` correspondente na mesma posição do `<tbody>`. O `<thead>` sai da
  lista e o corpo não — sair do compasso aqui é o erro clássico desta tela.
- [x] 3.5 Célula exibe `—` para quem não tem regime, e nunca cai em "Outros" nem
  em célula vazia. Usar as classes compartilhadas de `components.css`; nada de
  CSS por-view para a coluna nova.

## 4. Agente

- [x] 4.1 Nenhuma mudança em `AgentEndpoints.cs` — confirmar, lendo o bloco de
  atualização, que o regime continua fora da lista de campos atribuídos (D7).
  A tarefa é a leitura: o campo estar ausente é o comportamento correto.

## 5. Testes

- [x] 5.1 `tests/ClientesTest.cs`: cadastro com regime grava o valor; cadastro
  sem regime grava `null` (e não `Outros`).
- [x] 5.2 `tests/ClientesTest.cs`: edição troca o regime; edição com regime
  ausente/vazio **limpa** a escolha — o caso que 2.5 pode quebrar.
- [x] 5.3 `tests/ClientesTest.cs`: regime fora do conjunto devolve erro de
  validação e não grava nada.
- [x] 5.4 `tests/ClientesTest.cs`: ordenação por regime nas duas direções, com
  clientes sem regime no fim em ambas.
- [x] 5.5 `tests/ContratoAgenteTest.cs` (ou `ClientesTest.cs`, onde a
  sincronização já for exercitada): cliente com regime informado é
  sincronizado pelo agente com nome/CNPJ/validade novos e **continua com o
  mesmo regime**. É o teste que transforma a omissão de 4.1 em contrato.
- [x] 5.6 `views/ClientesView.spec.ts`: o modal oferece os cinco regimes mais a
  opção vazia; a coluna mostra o rótulo por extenso de quem tem regime e `—` de
  quem não tem.

## 6. Fechamento

- [x] 6.1 `dotnet test --filter "Category!=Banco"` e depois `dotnet test`
  completo (a migration roda dentro do Testcontainers — migration quebrada
  derruba a suíte).
- [x] 6.2 `npm --prefix ContabOne.Frontend run build` — é o único gate de
  typecheck do repo, e este change mexe em `types.ts`.
- [x] 6.3 `npm --prefix ContabOne.Frontend test`.

## 7. Filtro por regime na listagem

- [x] 7.1 `ClientesEndpoints`: helper `FiltroPorRegime(string?)` devolvendo
  `Expression<Func<Cliente, bool>>?`, com os cinco nomes mais `naoInformado`
  (D8). Token desconhecido devolve `null` e a listagem não filtra — mesma regra
  de `CertificadoFiltros.PorToken`, e o oposto do 400 do cadastro (D4).
- [x] 7.2 `ListarAsync`: parâmetro `string? regimeTributario` e o `Where`
  correspondente, junto dos demais filtros. Combina com busca, escritório,
  certificado e onboarding; `total` e paginação saem do conjunto já filtrado.
- [x] 7.3 `api/endpoints/clientes.ts`: `regimeTributario` nos parâmetros de
  `listarClientes`, só enviado quando escolhido.
- [x] 7.4 `ClientesView.vue`: seletor na barra de filtros, entre escritório e
  certificado — a mesma ordem em que a coluna aparece na tabela. Opções vindas
  do `REGIMES` já existente (D5), mais "Todos os regimes" e "Não informado".
  `@change="aplicarFiltros"`, que já volta para a primeira página.
- [x] 7.5 `tests/ClientesTest.cs`: filtra por um regime; `naoInformado` traz só
  os sem regime (e nenhum "Outros"); token desconhecido não filtra e não erra;
  combina com a busca.
- [x] 7.6 `ClientesView.spec.ts`: escolher um regime manda o parâmetro na
  query; o seletor oferece "Todos os regimes" + os cinco + "Não informado".
- [x] 7.7 Rodar de novo os gates de fechamento (6.1–6.3).
