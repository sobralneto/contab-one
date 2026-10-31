## 1. Separar a geração do PDF da dashboard

- [x] 1.1 Criar `ContabOne.Frontend/src/features/pgdas/dashboard/pdf.ts` com `desenharGraficos(doc, dados, tema, { animar })` e `montarPdfDashboard(doc, fundo, rasterizar?)`, movendo `addBlocoPdf` da view (design D1)
- [x] 1.2 Ajustar `PgdasDashboardView.vue` para usar o módulo, levando `triggerDownload` para um helper compartilhado, sem mudar a tela nem o "Baixar PDF"
- [x] 1.3 Testes Vitest em `pdf.spec.ts` com `rasterizar` injetado: dois blocos geram páginas separadas, bloco alto é escalado ou dividido como hoje, e sem `dashPart1`/`dashPart2` cai em `dashRoot`

## 2. Geração fora de tela

- [x] 2.1 Implementar `gerarPdfDashboardForaDeTela(dados, tema)`: `iframe` fora de tela com largura de 1160 px, espera do `load` e do `decode()` das imagens, gráficos com `animation: false`, captura e devolução dos bytes (design D2)
- [x] 2.2 Garantir no `finally` a destruição dos gráficos e a remoção do `iframe`, inclusive em falha, com teste que confirma que nenhum `iframe` sobra no documento

## 3. Orquestrador do lote

- [x] 3.1 Adicionar `fflate` como dependência direta (`npm install fflate`, sem `--legacy-peer-deps`)
- [x] 3.2 Criar `src/features/pgdas/dashboard/exportacaoLote.ts` com `LIMITE_LOTE`, `exportarLote(clientes, deps, { signal, aoProgredir })` sequencial, cedendo a thread entre clientes (design D3)
- [x] 3.3 Implementar `nomesUnicos` (`dashboard_<codigo>_<slug>.pdf`, com sufixo em colisão) e a montagem do ZIP com `zipSync` em `level: 0` e o nome `dashboards_pgdas_AAAA-MM-DD.zip` (design D4)
- [x] 3.4 Testes Vitest em `exportacaoLote.spec.ts`: ordem sequencial, progresso, falha de um cliente não interrompe, `montarDadosDashboard` nulo conta como falha, cancelamento para antes do cliente seguinte e não devolve arquivos, período repassado à leitura, nomes sem colisão, ZIP com um arquivo por cliente lido de volta com `unzipSync`

## 4. Seleção na visão geral

- [x] 4.1 Adicionar a coluna de seleção e o `Set` de `clienteId`, com caixas nomeadas por `aria-label` e o estado `indeterminate` no cabeçalho, usando tokens e sem `display:flex` em `<td>` (design D5)
- [x] 4.2 Intersectar a seleção com a lista ao fim de cada `carregar()`
- [x] 4.3 Adicionar a barra de seleção com contagem, "Exportar PDFs" e "Limpar seleção", ícones de `lucide-vue-next`, e o aviso quando passar de `LIMITE_LOTE`

## 5. Exportação na visão geral

- [x] 5.1 Ligar "Exportar PDFs" ao orquestrador com `import()` dinâmico (design D8), guardando o período no início e passando o `tema` de cada payload
- [x] 5.2 Mostrar o progresso em região `aria-live="polite"`, com "Cancelar", e bloquear seleção, filtros e nova exportação enquanto roda
- [x] 5.3 Tratar o fim da exportação: baixar o ZIP quando houver PDF, informar gerados e falhas, reduzir a seleção às falhas ou limpá-la, e não baixar nada se todos falharem ou se cancelar (design D9)
- [x] 5.4 Abortar pelo `signal` no `onBeforeUnmount`
- [x] 5.5 Testes em `PgdasVisaoGeralView.spec.ts`: seleção parcial e total, filtro tirando cliente da seleção, limite de 100, progresso e bloqueio, falha reduzindo a seleção, todos falhando sem download, cancelamento mantendo a seleção

## 6. Verificação

- [x] 6.1 Atualizar `ContabOne.Frontend/e2e/pgdas.spec.ts` com o fluxo de selecionar dois clientes e baixar o ZIP, conferindo os dois PDFs, e rodá-lo à mão com `npm --prefix ContabOne.Frontend run test:e2e`
- [x] 6.2 `npm --prefix ContabOne.Frontend run build` (vue-tsc + vite) sem erros
- [x] 6.3 `npm test` na raiz (testes afetados) verde
- [x] 6.4 Teste manual no navegador com dados reais: comparar o PDF do lote com o "Baixar PDF" do mesmo cliente (gráficos completos, logo, paginação), com leiaute de marca e com a aba em segundo plano; confirmar no DevTools que só há leituras da dashboard
- [ ] 6.5 Medir tempo por cliente, tamanho do ZIP e memória num lote de cerca de 30 clientes, confirmar ou ajustar `LIMITE_LOTE` e registrar o resultado em design.md
