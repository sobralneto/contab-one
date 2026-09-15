## 1. Rota transversal — a página é do escritório, não de ferramenta

> Primeira versão: slug `simulacao` no conjunto fechado de páginas de
> ferramenta + migration declarando no produto `pgdas`. Revertida quando o
> usuário rejeitou o enquadramento ("o simulador não é um produto do
> PGDAS") — a página é calculadora do escritório, como Arquivos.

- [x] 1.1 ~~Membro em `PaginaFerramenta` + migration~~ Revertido: a API não muda, `PaginaFerramenta` e o produto `pgdas` ficam como estavam (`Paginas = ['visao-geral','importacao']`)
- [x] 1.2 ~~`'simulacao'` na união de `types.ts` e em `PAGINAS_DISPONIVEIS`~~ Revertido junto — a simulação não é página declarável de ferramenta
- [x] 1.3 Reverter o delta da spec `catalogo-dominios-ferramentas` (o conjunto fechado não cresce)
- [x] 1.4 Limpar o dev local da primeira versão: remover `'simulacao'` da linha do `pgdas`, apagar a migration e a entrada de histórico dela

## 2. Cálculo — módulo puro, portado do HTML

- [x] 2.1 Criar `src/features/simulacao/anexos.ts` com a tabela dos Anexos I a V (6 faixas cada: limite, alíquota nominal, parcela dedutível) e a descrição de cada anexo, transcritas de `formulario_simples_nacional.html`
- [x] 2.2 Criar `src/features/simulacao/calcular.ts` com `calcular(anexo, faturamentos)` devolvendo as 12 linhas (faturamento, RBT12, alíquota nominal, dedutível, alíquota efetiva, imposto, excedeu o limite, sem histórico), preservando a regra do original: primeiro mês sem histórico usa a alíquota mínima, meses seguintes proporcionalizam pelo acumulado, RBT12 é comparado com R$ 4.800.000,00
- [x] 2.3 Criar `calcular.spec.ts` cobrindo: as seis faixas, proporcionalização a partir do 2º mês, primeiro mês sem histórico, mês com faturamento zero no meio da série, extrapolação do limite, e série totalmente vazia sem divisão por zero
- [x] 2.4 Conferir a paridade com o HTML original: rodar os mesmos 12 valores nos dois e comparar as 12 linhas de saída

## 3. Rota e menu

- [x] 3.1 Criar `src/views/SimuladorView.vue` com o esqueleto das telas do painel: `div.simulador-view.animate-fade-in` + `.view-header` com `<h1>`, contêiner de largura limitada scoped
- [x] 3.2 Acrescentar a rota transversal `/simulador` em `src/router/index.ts` (name `simulador`, `meta.titulo: "Simulador Simples Nacional"`, sem `meta.pagina`) apontando para a view
- [x] 3.3 Acrescentar o item **Simulador Simples Nacional** na área Escritório do menu (`src/layouts/AppLayout.vue`), ao lado de Arquivos, para todo usuário de escritório
- [x] 3.4 Acrescentar o texto de primeira visita em `src/constants/explicacoesPagina.ts` (chave `simulador`, o name da rota, como as transversais), explicando que é estimativa local e não substitui a apuração
- [x] 3.5 No E2E, nada de lista manual: as chaves transversais de `e2e/global-setup.ts` saem de `EXPLICACOES_PAGINA`, então a entrada nova é coberta sozinha

## 4. Layout — duas colunas no topo

- [x] 4.1 Montar a coluna à esquerda com o bloco de identificação (nome empresarial + CNPJ) e, abaixo, o cartão de seleção do Anexo I a V
- [x] 4.2 Montar a coluna à direita com a grade dos 12 cartões de faturamento
- [x] 4.3 Garantir o empilhamento em tela estreita (identificação e anexo antes do faturamento), sem rolagem horizontal
- [x] 4.4 Usar as classes globais de `components.css` (`.form-field`/`.req`, `.btn-primary`/`.btn-secondary`, `.table-card`/`.data-table`) e os tokens de `tokens.css`, sem portar a folha de estilo, as fontes, o logo, a marca d'água nem o rodapé do HTML original

## 5. Identificação e anexo

- [x] 5.1 Aplicar `cnpjMask` (`useInputMask`) ao campo de CNPJ, no lugar da máscara própria do HTML
- [x] 5.2 Manter nome e CNPJ opcionais, sem exigir nem consultar cliente cadastrado, e sem nenhuma chamada à API
- [x] 5.3 Implementar a seleção do anexo com um selecionado por vez e refazer o cálculo ao trocar, preservando o faturamento já digitado de cada anexo

## 6. Faturamento — máscara de moeda e marcação de mês vazio

- [x] 6.1 Ligar cada um dos 12 campos a um `computed` gravável sobre `moedaDigitada`/`moedaFormatada`, com `bloquearNaoDigito` no `@beforeinput` (padrão de `PlanosView.vue`)
- [x] 6.2 Exibir o prefixo `R$` em cada cartão e iniciar os 12 meses sem valor, sem o preenchimento de R$ 160.000,00 do original
- [x] 6.3 Aplicar a borda esquerda em `--erro` somente no mês sem valor, derivada do próprio valor do mês (`meses[i] === 0`), e removê-la assim que o mês receber valor — nunca o `--gold` do arquivo original
- [x] 6.4 ~~Acrescentar sinal textual de "sem valor preenchido" por cartão (`aria-describedby`)~~ Removido a pedido do usuário no uso real — a marcação de mês vazio é exclusivamente a borda em `--erro` (ver design.md, decisão 6)
- [x] 6.5 Portar a toolbar: "Limpar formulário" e "Repetir mês 1 em todos" como `.btn-secondary`, com a segunda desabilitada enquanto o mês 1 não tiver valor, e "Calcular imposto estimado" como `.btn-primary`

## 7. Resultado da simulação

- [x] 7.1 Exibir os 4 indicadores de 12 meses (faturamento, imposto estimado, alíquota efetiva média, RBT12 do 12º mês) com os componentes do design system, sem declarar chrome próprio
- [x] 7.2 Exibir o aviso de extrapolação do limite de R$ 4.800.000,00, e sinalizar em `--erro` os meses excedidos na tabela
- [x] 7.3 Montar as duas tabelas semestrais com as 6 linhas (faturamento, RBT12, alíquota nominal, parcela dedutível, alíquota efetiva, imposto) e subtotal por semestre, com a indicação de alíquota mínima nos meses sem histórico
- [x] 7.4 Trocar as barras CSS por Chart.js via PrimeVue dentro de `.card-painel`, com as séries faturamento e imposto num único eixo rotulado comum — a pedido do usuário no uso real; dois eixos independentes reproduziam a distorção do original (ver design.md, decisão 8) — com legenda, tooltip e cores lidas dos tokens
- [x] 7.5 Recalcular indicadores, tabelas e gráfico a cada alteração de mês ou troca de anexo

## 8. Testes e verificação

- [x] 8.1 Criar `SimuladorView.spec.ts`: arranjo de duas colunas, 12 meses vazios na abertura com as 12 marcações, a marcação sumindo ao preencher o mês e voltando ao apagá-lo, e os 12 cartões sem nenhuma requisição à API
- [x] 8.2 ~~`guards.spec.ts` com a página nova~~ Revertido: rota transversal não passa pelo guard de produto — o fixture do pgdas e os casos da simulação saíram
- [x] 8.3 ~~`CatalogoDominiosTest.cs` com o membro novo~~ Revertido: a API não muda nesta change
- [x] 8.4 Rodar `npm --prefix ContabOne.Frontend run build` (único gate de tipos) e `npm test`

## 9. Persistência — entidade e migration (API)

- [x] 9.1 Criar `SimulacaoSimplesNacional` em `ContabOne.Api/Domain/Entities.cs`: `Id`, `EscritorioId` (+ nav `Escritorio`), `Nome`, `Cnpj` (texto puro, sem hash e sem máscara — design.md, decisão 11), `Anexo`, `Faturamentos` (`decimal[]`, 12 posições), `CriadoEm` — sem FK para `Cliente` (design.md, decisão 13)
- [x] 9.2 Registrar `DbSet<SimulacaoSimplesNacional>` em `AppDbContext` e o filtro de tenant fail-closed (`_tenantContext.VeTodosOsEscritorios || s.EscritorioId == _tenantContext.EscritorioId`), no mesmo padrão de `Cliente`/`ArquivoEscritorio`
- [x] 9.3 Criar a migration (`dotnet ef migrations add CriarSimulacaoSimplesNacional --project ContabOne.Api`): só `CREATE TABLE`, sem tocar em `Produto`, `Paginas` ou qualquer migration de catálogo

## 10. Persistência — endpoints (API)

- [x] 10.1 Criar `ContabOne.Api/Features/Simulador/SimulacoesEndpoints.cs` com `MapSimulacoesEndpoints()`: `POST /` (salvar), `GET /` (listar, paginado, ordenado por `CriadoEm` desc), `GET /{id:guid}` (obter uma, para reabrir), `DELETE /{id:guid}` (excluir) — escopo sempre do `TenantContext.EscritorioId`, nunca de parâmetro do pedido
- [x] 10.2 Mapear o grupo `app.MapGroup("/api/simulador").MapSimulacoesEndpoints().RequireAuthorization("EscritorioUsuario")` em `Program.cs`
- [x] 10.3 Validar a gravação: `Anexo` precisa estar em `{I, II, III, IV, V}`, `Faturamentos` precisa ter exatamente 12 posições não-negativas, `Nome` respeita o `maxlength` de 120 já usado na view — `Cnpj` grava como recebido, sem validação de formato ou checksum (design.md, decisão 11)

## 11. Persistência — botão salvar e reabrir (frontend)

- [x] 11.1 Criar `src/api/endpoints/simulador.ts` com as chamadas às 4 rotas (`salvarSimulacao`, `listarSimulacoes`, `obterSimulacao`, `excluirSimulacao`)
- [x] 11.2 Acrescentar o botão **"Salvar simulação"** em `SimuladorView.vue` (toolbar, `.btn-secondary` ou `.btn-primary` conforme hierarquia visual da tela) chamando `salvarSimulacao` com nome, CNPJ (texto puro, sem `cnpjMask` aplicado no valor enviado), anexo ativo e os 12 valores do anexo atual, com feedback de sucesso/erro
- [x] 11.3 Suportar reabrir: rota `/simulador` aceita um identificador (query param `?id=`) que, presente, busca a simulação via `obterSimulacao` e preenche nome, CNPJ, anexo e os 12 meses antes de qualquer interação do usuário

## 12. Histórico (frontend)

- [x] 12.1 Criar `src/views/HistoricoSimuladorView.vue`: `.view-header` com `<h1>` e ação de voltar ao Simulador, listagem em `.data-table` (nome, CNPJ, anexo, data), ação de abrir (navega para `/simulador?id=...`) e ação de excluir (confirmação + `excluirSimulacao`), `EstadoVazio` quando não há simulações salvas
- [x] 12.2 Acrescentar a rota `/simulador/historico` em `src/router/index.ts` (name `simulador-historico`, `meta.titulo`, sem `meta.pagina` — transversal como `/simulador`)
- [x] 12.3 Acrescentar um botão/link "Histórico" no `.view-header` de `SimuladorView.vue`, apontando para `/simulador/historico` — sem entrada própria no menu do escritório (design.md, decisão 12)
- [x] 12.4 Acrescentar o texto de primeira visita para `simulador-historico` em `src/constants/explicacoesPagina.ts`

## 13. Testes da persistência

- [x] 13.1 Testes de endpoint da API: salvar grava só os 4 campos, listar retorna só as simulações do escritório da sessão, obter por id recusa id de outro escritório (404, nunca dado de outro tenant), excluir remove definitivamente
- [x] 13.2 Teste de isolamento multi-tenant (`IsolamentoTest.cs` ou equivalente): duas simulações de escritórios diferentes, uma sessão não vê a da outra
- [x] 13.3 Atualizar `SimuladorView.spec.ts`: clicar em "Salvar simulação" chama a API com nome/CNPJ/anexo/faturamento e nenhum resultado calculado no corpo; reabrir via `?id=` preenche os 4 campos e recalcula
- [x] 13.4 Criar `HistoricoSimuladorView.spec.ts`: listagem, estado vazio, abrir leva ao simulador preenchido, excluir remove da lista
- [x] 13.5 Rodar `npm --prefix ContabOne.Frontend run build`, `dotnet test` (ou `dotnet test --filter "Category!=Banco"` durante iteração) e `npm test` antes de commitar — build ok, 351/351 testes da API, 98/98 do frontend afetado

## 14. Correção pós-implementação: campo de CNPJ virou componente reutilizável

> No uso real, o CNPJ do Simulador não respeitava a máscara ao digitar. Em
> vez de depurar essa implementação, a implementação que já funciona
> (`ClientesView.vue`) foi extraída para um componente compartilhado
> (design.md, decisão 14).

- [x] 14.1 Criar `src/components/comum/CampoCnpj.vue`: `v-model` carrega o valor mascarado (`00.000.000/0000-00`), reaplica `cnpjMask` a cada tecla — o mesmo padrão de `ClientesView.vue`, sem bloquear caractere na origem
- [x] 14.2 Refatorar `ClientesView.vue` para usar `CampoCnpj`, removendo o `computed` local e o import de `useInputMask` que ficou sem outro uso
- [x] 14.3 Refatorar `SimuladorView.vue` para usar `CampoCnpj`: o par `cnpj` (dígitos) + `cnpjExibicao` (computed) vira um único `cnpjMascarado`; o texto puro enviado ao salvar (decisão 11) passa a ser derivado do valor mascarado (`replace(/\D/g, '')`) no momento de montar o payload; a reabertura (`?id=`) aplica `cnpjMask` ao dígito vindo do servidor antes de preencher o campo
- [x] 14.4 Criar `CampoCnpj.spec.ts` cobrindo a máscara ao digitar, dígitos com pontuação misturada, limite de 14 dígitos e o valor inicial já mascarado vindo do v-model
- [x] 14.5 Rodar `npm --prefix ContabOne.Frontend run build` e os specs afetados (`CampoCnpj`, `ClientesView`, `SimuladorView`) — todos verdes
