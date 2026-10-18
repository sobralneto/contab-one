## 1. Módulo de agrupamento do lote (puro, sem Vue)

- [ ] 1.1 Criar `ContabOne.Frontend/src/features/pgdas/importacao/lote.ts` com os tipos `EmpresaLote`, `CompetenciaLote` (com `_arquivos`), `EstadoCliente` e `EstadoGravacao` (design D1)
- [ ] 1.2 Implementar `adicionarCompetencias(lote, idArquivo, competencias)`: chave por `_cnpj` do bloco, herança do CNPJ dentro do mesmo arquivo, `sem-cnpj:<idArquivo>` quando o arquivo não traz nenhum; mescla por `_pa` só dentro da mesma empresa (design D2)
- [ ] 1.3 Implementar `removerArquivo(lote, idArquivo)`: remove competências sem outra origem e empresas que fiquem vazias
- [ ] 1.4 Implementar `informarCnpj(lote, chave, cnpj)`: identifica o grupo não identificado e o funde a uma empresa do lote com o mesmo CNPJ
- [ ] 1.5 Implementar ordenação (empresas por razão social, competências por período) e os helpers por empresa `montarSerieMensal(competencias)`, `competenciaDocumentoMaisRecente(competencias)` e `montarRequisicao(empresa, substituir)`, movidos da view
- [ ] 1.6 Testes Vitest em `lote.spec.ts`: duas empresas no mesmo lote; mesmo mês em empresas diferentes não colide; extrato + declaração da mesma empresa viram uma linha; documento sem CNPJ vira grupo próprio; remoção de arquivo; fusão ao informar CNPJ; requisição montada só com as competências da empresa

## 2. Card por empresa

- [ ] 2.1 Criar `ContabOne.Frontend/src/components/pgdas/CardEmpresaLote.vue` com moldura `.card-painel*` (cabeçalho com razão social, badge de competências, ação "retirar empresa") e prop `modo: 'conferencia' | 'gravacao'` (design D3)
- [ ] 2.2 Bloco de identificação no topo do card: razão social, município/UF e anexo editáveis, CNPJ mascarado (ou campo para informar o CNPJ quando não identificada), situação do cliente (buscando / já cadastrado / não cadastrado / erro)
- [ ] 2.3 Mover a tabela de conferência da view para o card (inputs, `confere`/`somaTributos`, Pago/Aberto, sem movimento, remover linha), junto com o CSS scoped dela; ícones via `lucide-vue-next`, cores só por token
- [ ] 2.4 Modo `gravacao`: cadastro de cliente novo (código sugerido + razão social), aviso de conflito com competências e indicação de edição manual, botão "Substituir e gravar" da empresa, estado gravada/erro, link "Ver dashboard" quando gravada

## 3. Reestruturar `PgdasImportacaoView.vue`

- [ ] 3.1 Trocar o estado `competencias` + escalares da empresa por `lote: EmpresaLote[]`; arquivos ganham `id` gerado na carga; `processarArquivos` passa a chamar `adicionarCompetencias`
- [ ] 3.2 Corrigir `removerArquivo` para usar `removerArquivo(lote, id)` do módulo
- [ ] 3.3 Passo 1: botão "Conferir dados (E empresa(s), N competência(s))" e dica de mescla "por empresa" (design D7)
- [ ] 3.4 Passo 2: renderizar um `CardEmpresaLote` por empresa em modo conferência; só avançar quando toda empresa restante tiver CNPJ
- [ ] 3.5 Identificação por empresa ao abrir o passo 2, com no máximo 3 chamadas simultâneas; identificar de novo só empresas novas ou com CNPJ recém-informado (design D4)
- [ ] 3.6 Passo 3: cards em modo gravação; "Gravar todas" sequencial só das empresas prontas, com progresso "gravando X de Y"; tratamento 200/409/erro por empresa e retentativa sem regravar as já gravadas (design D5)
- [ ] 3.7 Conclusão: empresa única navega para a dashboard do cliente; várias empresas exibem o resumo com link para cada dashboard e para a visão geral (design D6)
- [ ] 3.8 Remover da view o código que ficou órfão (`empresaExtraida`, `empresaEditada`, `cnpjDoLote`, `cnpjBusca` global etc.)

## 4. Testes da view

- [ ] 4.1 Ajustar `PgdasImportacaoView.spec.ts` para o caso de empresa única (divergência, cliente já cadastrado na etapa 2, edição de razão social, 409 com substituição, cadastro de cliente novo, erro de identificação) continuar passando
- [ ] 4.2 Novo teste: lote com duas empresas exibe dois cards, cada um com a identificação acima e a tabela das próprias competências abaixo
- [ ] 4.3 Novo teste: 409 em uma empresa não impede a gravação da outra, e "Substituir e gravar" reenvia só a empresa em conflito
- [ ] 4.4 Novo teste: falha de rede em uma empresa permite regravar só ela
- [ ] 4.5 Novo teste: lote com várias empresas termina no resumo; lote com uma empresa navega para a dashboard

## 5. Verificação

- [ ] 5.1 `npm --prefix ContabOne.Frontend run build` (vue-tsc + vite) sem erros
- [ ] 5.2 `npm test` na raiz (testes afetados) verde
- [ ] 5.3 Teste manual no navegador com extratos reais de ao menos três empresas, incluindo o mesmo mês em duas delas, uma empresa não cadastrada e uma com competência já gravada; confirmar no DevTools que nenhuma requisição carrega o conteúdo do PDF
- [ ] 5.4 Avaliar com um lote grande (~30 empresas) se os cards precisam começar recolhidos (Open Question do design) e registrar a decisão no design.md
