## 1. API — modelo e migration

- [x] 1.1 Adicionar `Cliente.DataAbertura` (`DateOnly?`) e `ApuracaoSimples.NumeroDeclaracao` (`string?`) em `Domain/Entities.cs`, com comentário XML no estilo das propriedades vizinhas
- [x] 1.2 Configurar `NumeroDeclaracao` com `HasMaxLength(30)` em `Infra/AppDbContext.cs`
- [x] 1.3 Gerar a migration `AddDemonstrativoFaturamento` com `dotnet ef migrations add` e conferir que ela só adiciona as duas colunas nulas, sem backfill

## 2. API — gravação e listagem

- [x] 2.1 Adicionar `DataAberturaCliente` (`DateOnly?`) em `GravarApuracoesRequest` e `NumeroDeclaracao` (`string?`) em `ApuracaoRequest`
- [x] 2.2 No `GravarApuracoesRequestValidator`, exigir que `NumeroDeclaracao`, quando presente, tenha só dígitos e no máximo 30 caracteres
- [x] 2.3 Em `GravarApuracoesAsync`, gravar `Cliente.DataAbertura` quando `DataAberturaCliente` vier preenchida, e mantê-la quando vier nula. Passar `NumeroDeclaracao` por `AplicarValores`, na criação e na substituição
- [x] 2.4 Incluir `ClienteDataAbertura` e `NumeroDeclaracao` na projeção de `ListarApuracoesAsync`
- [x] 2.5 Testes xUnit (`Category=Banco`): a gravação com os dois campos persiste; a gravação sem data mantém a data anterior; um número com letras dá 400 e nada é gravado; a listagem devolve os dois campos, ou nulos quando ausentes
- [x] 2.6 Conferir `TraducaoLinqTest`/`ToQueryString()` na projeção nova da listagem, se ela usar algo além de colunas diretas

## 3. Frontend — extração e tipos

- [x] 3.1 Em `src/api/types.ts`, adicionar `clienteDataAbertura?: string | null` e `numeroDeclaracao?: string | null` em `ApuracaoListaDto`, `numeroDeclaracao?` em `ApuracaoPgdasRequest` e `dataAberturaCliente?` no request de gravação
- [x] 3.2 Em `parser/tipos.ts`, adicionar `numeroDeclaracao?: string` e `_abertura?: string` (ISO `AAAA-MM-DD`) em `Competencia`
- [x] 3.3 Em `parser/parseApuracao.ts`, capturar "Data de abertura no CNPJ" e "Nº da Declaração" (tolerando `Nº`/`No`/`N°`). Antes, conferir os rótulos exatos num extrato e numa declaração reais
- [x] 3.4 Acrescentar as duas linhas às fixtures `extratoUmMes` e `declaracaoUmMes` e cobrir em `parser.spec.ts`: os dois campos extraídos, e um documento sem eles extraído normalmente com os campos vazios
- [x] 3.5 Na importação (`PgdasImportacaoView.vue`), enviar `numeroDeclaracao` por apuração e `dataAberturaCliente` (o primeiro `_abertura` do lote) no `POST /api/pgdas/apuracoes`

## 4. Frontend — montagem do demonstrativo

- [x] 4.1 Criar `src/features/pgdas/demonstrativo/montar.ts` com `montarDemonstrativo(apuracoes, identidade, hoje)`. A função devolve os anos `[A-1, A]` (A = ano da competência mais recente), 12 linhas Janeiro–Dezembro, `R$ 0,00` para mês ausente ou sem movimento, os totais por coluna, o Nº da Declaração da competência mais recente que tiver um, e a data por extenso ("14 de Outubro de 2026")
- [x] 4.2 Criar `montar.spec.ts` cobrindo cada cenário da spec `demonstrativo-faturamento`: dois anos, sem movimento, competências fora do intervalo ignoradas, número presente e ausente, data por extenso, cliente com uma única competência e lista vazia

## 5. Frontend — documento e estilos

- [x] 5.1 Adicionar os tokens `--papel-*` em `tokens.css` (fundo, texto, texto suave, rótulo, quadro, zebra, filete, filete forte, assinatura), sem redefinição no tema escuro, com um comentário explicando por quê
- [x] 5.2 Criar `src/components/pgdas/DemonstrativoFaturamento.vue`: uma folha de 794 px com proporção A4 e classe `.imprimivel`, com título e filete, quadro de identificação, tabela com zebra e `TOTAL GERAL`, nota com o número em negrito (ou a frase sem o trecho), linha `Local:`/`Data:` e o bloco de assinaturas `SÓCIO-ADMINISTRADOR`/`CONTADOR`. Medidas conforme o Context do design.md e cores só por tokens
- [x] 5.3 Escalar a folha com `transform: scale()` para caber na largura da sidebar, sem reflow, e anular a escala em `@media print`
- [x] 5.4 Criar `src/assets/styles/impressao.css`, que, sob `body:has(.imprimivel)`, esconde tudo menos a folha e define `@page { size: A4 portrait; margin: 0 }`. Importá-lo em `src/style.css`

## 6. Frontend — sidebar, exportação e impressão

- [x] 6.1 Criar `src/features/pgdas/demonstrativo/pdf.ts` com `exportarDemonstrativoPdf(el, nomeArquivo, rasterizar?)`. A função clona a folha num contêiner fora de tela sem `transform`, roda `html2canvas` (`scale: 2`, fundo resolvido de `--papel-fundo`) e `jsPDF('p','mm','a4').addImage(…, 0, 0, 210, 297)`, e remove o contêiner no `finally`. O rasterizador é injetável para teste. Nome do arquivo: `demonstrativo_faturamento_<codigo>_<nome-normalizado>.pdf`
- [x] 6.2 Em `PgdasVisaoGeralView.vue`, substituir o cabeçalho e a tabela da sidebar por uma barra com "Demonstrativo de faturamento", "Exportar PDF" (`FileDown`), "Imprimir" (`Printer`) e fechar (`X`), seguida de `<DemonstrativoFaturamento>`. Remover o CSS e o markup que não são mais usados
- [x] 6.3 Desabilitar as duas ações durante `sidebarLoading`, e "Exportar PDF" também enquanto o PDF é gerado. Manter o foco inicial no fechar, o Esc e a troca de cliente com a sidebar aberta
- [x] 6.4 Atualizar `PgdasVisaoGeralView.spec.ts`: a sidebar mostra o título do documento, o nome, o CNPJ, `FATURAMENTO <A-1>`/`<A>`, `TOTAL GERAL`, `SÓCIO-ADMINISTRADOR` e `CONTADOR`; "Imprimir" chama `window.print`; "Exportar PDF" chama o exportador; as duas ficam desabilitadas durante o carregamento; os mocks MSW da listagem incluem os campos novos
- [x] 6.5 Criar `pdf.spec.ts`, com rasterizador falso, verificando uma página A4, `addImage` em `0,0,210,297`, o nome do arquivo e a remoção do contêiner mesmo com falha

## 7. Verificação

- [x] 7.1 Rodar `npm --prefix ContabOne.Frontend run build` (typecheck)
- [x] 7.2 Rodar `npm test` na raiz (o runner seletivo)
- [x] 7.3 Conferência visual: abrir `/f/pgdas`, abrir o detalhe de um cliente com dois anos de apurações, exportar o PDF e comparar lado a lado com `Relatorio_Faturamento_2025_2026.pdf`, nos temas claro e escuro. Conferir também a pré-visualização de impressão
