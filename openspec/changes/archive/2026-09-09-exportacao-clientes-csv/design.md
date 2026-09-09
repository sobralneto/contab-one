# Design — exportação de clientes em CSV

## Context

A tela de clientes (`ContabOne.Frontend/src/views/ClientesView.vue`) monta os
filtros em `carregar()` e chama `listarClientes` (`src/api/endpoints/clientes.ts`),
que faz `GET /api/clientes` paginado (tamanho travado em 20 na tela, clamp 1–100
no servidor). No servidor, `ListarAsync`
(`ContabOne.Api/Features/Clientes/ClientesEndpoints.cs:198`) constrói a cadeia
de filtros inline — busca, escritório, `diasVencimentoCert`, faixa de
certificado, regime, onboarding, 2FA — e já possui um método `Ordenar` separado
(resolvido por conjunto fechado, com desempate por `Id`).

A API hoje só devolve JSON: nenhum endpoint usa `Results.File`, nenhum
`text/csv`. No painel, o único precedente de exportação é o PDF do checklist
(`exportacao-pdf-onboarding`), 100% frontend. Aquele precedente **não** serve
aqui: o PDF renderiza uma tela; o CSV precisa do conjunto inteiro filtrado, e
a tela só tem páginas de 20.

## Goals / Non-Goals

**Goals:**

- Baixar, um clique, o conjunto inteiro que passou pelos filtros ativos, na
  ordem da tabela, como CSV que abre em planilha pt-BR sem configuração.
- Listagem e exportação filtrarem **pela mesma construção de código** — não por
  duas cópias que coincidem.
- Manter o contrato de privacidade: o arquivo só carrega o que a tela carrega
  (CNPJ mascarado; nem CNPJ completo — que não existe no servidor — nem hash).

**Non-Goals:**

- XLSX, seletor de colunas, exportação de outras telas, agendamento/envio.
- Streaming para conjuntos gigantes: escritório real tem centenas, no máximo
  poucos milhares de clientes; materializar em `StringBuilder` na memória é
  suficiente e mais simples.
- Rate limit novo: o grupo `/api/clientes` não tem um hoje e a exportação custa
  o mesmo que a listagem sem paginação; introduzir política só aqui seria
  exceção sem motivo.
- Paginação no endpoint de exportação.

## Decisions

### D1 — Exportação no servidor, endpoint novo `GET /api/clientes/exportar`

Alternativa considerada: gerar o CSV no navegador, paginando `GET /api/clientes`
até esgotar `total`. Rejeitada — N pedidos por exportação, dados podem mudar
entre páginas, e o construtor de CSV viveria no frontend com uma segunda visão
das regras de formato. No servidor, um pedido devolve o conjunto inteiro e os
filtros são os do servidor.

O endpoint aceita **os mesmos parâmetros de filtro e ordenação da listagem,
menos `pagina`/`tamanho`**: `busca`, `escritorioId`, `diasVencimentoCert`,
`faixaCertificado`, `regimeTributario`, `emOnboarding`, `tem2FA`, `ordenarPor`,
`direcao`. Como `/exportar` não é GUID, não conflita com `/{id:guid}` — mesmo
padrão de `/proximo-codigo`. Entra no mesmo grupo `/api/clientes` já montado no
`Program.cs`, herdando `EscritorioUsuario` sem tocar no arquivo.

É a primeira resposta não-JSON da API: `Results.File(bytes, "text/csv",
"clientes.csv")`, que já produz `Content-Disposition: attachment`. Nenhuma
mudança no pipeline de serialização — o endpoint simplesmente não passa pelo
JSON.

### D2 — Builder de filtros compartilhado, extraído de `ListarAsync`

A cadeia inline (hoje linhas 214–263 de `ListarAsync`) sai para um helper
privado estático, algo como `AplicarFiltros(db, tenant, busca, escritorioId,
diasVencimentoCert, faixaCertificado, regimeTributario, emOnboarding, tem2FA)`.
`ListarAsync` chama e segue com `CountAsync` + paginação + projeção exatamente
como hoje; `ExportarAsync` chama, aplica `Ordenar` (já existe, já é fechado,
já tem o desempate por `Id`) e materializa tudo.

Filtro novo adicionado no helper vale para listagem e exportação de uma vez —
o oposto de duplicar a cadeia, onde todo filtro novo é uma chance de o arquivo
e a tela divergirem silenciosamente.

### D3 — Formato do arquivo: convenções de planilha pt-BR

- Separador `;` — o que o Excel pt-BR espera ao clicar duas vezes no arquivo.
- UTF-8 **com BOM**: sem a marca, Excel abre acentuação quebrada.
- Quebras de linha CRLF, conforme RFC 4180.
- Cabeçalho na primeira linha, rótulos iguais aos da tabela.
- Escape RFC 4180: valor que contenha `;`, `"`, quebra de linha sai cercado de
  aspas, com aspas internas dobradas; valor limpo sai sem aspas.

CSV construído à mão com `StringBuilder` — nenhum pacote CsvHelper; escape são
dez linhas e a suíte tem teste próprio para ele.

### D4 — Colunas espelham a tabela; coluna de escritório decide por papel

Colunas, na ordem da tabela (`colunas` em `ClientesView.vue:362`):
`Código; Nome; [Escritório;] CNPJ; Regime; 2FA; Certificado; Atualizado`.

- **CNPJ**: `CnpjMascarado` como está — mascarado por construção, pois é o que
  a entidade guarda.
- **Regime**: por extenso (`RegimeTributario.ToString()`), célula vazia quando
  nulo — **não** "—" (o travessão é convenção de tela para distinguir ausência
  de falha de carregamento; arquivo é dado, e célula vazia é o que a planilha
  entende).
- **2FA**: "Sim"/"Não", como a coluna da tela.
- **Certificado**: a data da validade em `dd/MM/aaaa`, célula vazia sem
  certificado — não o rótulo efêmero da tela ("Vence em N dias"), que apodrece
  no dia seguinte; a data é o dado por trás do rótulo.
- **Escritório**: só quando o papel é `PlatformAdmin`. O handler recebe
  `ClaimsPrincipal` e decide por `user.IsInRole("PlatformAdmin")` — o mesmo
  critério do `auth.isPlatformAdmin` (`stores/auth.ts:56`) que decide a coluna
  na tela. Não usar `tenant.VeTodosOsEscritorios`: admin **com foco** em um
  escritório tem essa flag falsa mas a tabela dele continua mostrando a coluna,
  e o arquivo divergiria da tela — duas verdades para a mesma decisão.

### D5 — Download no frontend via Blob; o nome do arquivo é do lado cliente

O JWT viaja no header `Authorization`, então link direto `<a href>` não se
autentica — o download precisa passar pelo `apiClient`. `exportarClientesCsv`
em `src/api/endpoints/clientes.ts` faz `apiClient.get('/api/clientes/exportar',
{ params, responseType: 'blob' })`, cria `URL.createObjectURL`, aciona um
`<a download>` efêmero e revoga a URL.

O nome do arquivo é montado no frontend (`clientes-AAAA-MM-DD.csv`), sem ler o
`Content-Disposition` — lê-lo cruzando origem exigiria `Access-Control-Expose-
Headers` no CORS da API. O servidor continua setando o header (correto para
consumo direto da API), mas o painel não depende dele.

Em `ClientesView.vue`, o botão segue o padrão já estabelecido pelo exportar PDF
(`OnboardingClienteView.vue:66`): `btn-secondary`, `:disabled="exportando"`,
rótulo trocando para "Gerando..." durante a geração. Ícone `Download` do
`lucide-vue-next`, `aria-hidden`. Os parâmetros saem de um helper único de
filtros (`filtrosAtuais()`), consumido por `carregar()` e pela exportação —
mesma dedução de D2, agora no frontend: filtro novo entra num lugar só.
Falha: `catch` vazio como o resto da tela (o interceptor avisa), `finally`
devolve o botão — a listagem nunca é derrubada.

### D6 — Guardas de teste

- **Backend** (`ContabOne.Api/tests/ClientesTest.cs`, mesma categoria `Banco`
  e o mesmo `CenarioAsync`): exportar sem filtro traz todos os criados; com
  filtro traz só o conjunto; valor com `;` sai cercado de aspas; BOM presente;
  cabeçalho com `;`. Um teste de paridade compara, para os mesmos parâmetros,
  as linhas do arquivo com o que a listagem devolve paginada — é o teste que
  prende listagem e exportação na mesma verdade.
- **Isolamento** (`IsolamentoTest.cs`, que já exerce `GET /api/clientes`):
  acrescentar a exportação à verificação — arquivo de um escritório não
  contém cliente do outro.
- **Frontend** (`ClientesView.spec.ts`, MSW): handler para o endpoint novo
  (`onUnhandledRequest: 'error'` falha o teste sem ele), clique dispara o
  pedido com os filtros da tela, botão desabilita durante a geração. O jsdom
  não tem `URL.createObjectURL` — stub global no teste.

## Risks / Trade-offs

- [Primeira resposta binária/não-JSON da API] → o endpoint não passa pelo
  caminho que os testes e o frontend já conhecem. Mitigado por `Results.File`
  (nada de middleware novo) e pelos testes de formato; o axios lida com
  `responseType: 'blob'` sem mudança no interceptor (401→refresh continua
  valendo normalmente, a resposta de erro segue JSON).
- [Alguém estende a listagem sem estender a exportação] → impossível por
  construção no backend (D2) e no frontend (D5); o teste de paridade é o
  detector caso alguém contorne o helper.
- [Excel de outro locale abre `;` em coluna única] → é o preço de otimizar
  para pt-BR, o mercado do produto; Google Sheets e LibreOffice detectam o
  separador. Não é meta suportar importação manual em locale não-pt-BR.
- [Admin com foco recebe coluna Escritório repetida] → escolhido de propósito
  (D4): espelha a tabela; a coluna não mente, só não acrescenta.

## Migration Plan

Nenhuma. Endpoint e botão são aditivos; nenhuma migração, nenhuma dependência
nova, nenhum contrato existente muda. Rollback é reverter o commit.

## Open Questions

Nenhuma — as decisões de formato e de colunas ficaram registradas em D3/D4 e
os requisitos correspondentes no delta de `gestao-clientes`.