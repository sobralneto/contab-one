## 1. Formatação de campos (CNPJ e preço)

- [x] 1.1 Criar composable `useInputMask.ts` com funções `cnpjMask` e `currencyMask`
- [x] 1.2 Aplicar máscara de CNPJ em todos os campos de CNPJ nos formulários (componentes de cliente, escritório, etc.)
- [x] 1.3 Aplicar formatação monetária no campo de preço do modal de plano (`PlanosView.vue`)
- [x] 1.4 Testar máscara de CNPJ com digitação e colagem (Ctrl+V)
- [x] 1.5 Testar formatação de preço com valores inteiros e decimais

## 2. Dashboard — correção de gráficos e escopo de dados

- [x] 2.1 Adicionar campo `label` ao DTO `SerieItem` em `ContabOne.Frontend/src/api/types.ts`
- [x] 2.2 Ajustar endpoint `/api/dashboard/series` para retornar `label` (nome do escritório ou cliente) conforme papel do usuário
- [x] 2.3 Alterar `GraficoMensal.vue` para usar `label` no eixo X em vez de `competencia` formatada
- [x] 2.4 Verificar e corrigir escopo de dados nos cards KPI (`KpiCard.vue`) e ranking (`RankingClientes.vue`) para cada papel
- [x] 2.5 Testar dashboard nos 3 papéis: admin (por escritório), escritório (por cliente), usuário (por cliente)

## 3. Clientes — correções de CRUD e filtros

- [x] 3.1 Diagnosticar e corrigir fluxo de cadastro de novo cliente (verificar chamada API, validação e feedback)
- [x] 3.2 Adicionar coluna "Escritório" na tabela de clientes da visão admin (`ClientesView.vue`)
- [x] 3.3 Adicionar filtro dropdown de escritório na visão admin
- [x] 3.4 Adicionar filtro por dias até vencimento do certificado (select: 1, 2, 3, 7, 15 dias) na visão escritório
- [x] 3.5 Ajustar endpoint `GET /api/clientes` para aceitar parâmetros `escritorioId` e `diasVencimentoCert`
- [x] 3.6 Testar CRUD completo (criar, listar, editar, excluir) em ambas as visões

## 4. Execuções — agrupamento e métricas

- [x] 4.1 Criar/se ajustar endpoint de execuções para retornar dados agrupados por escritório (admin) e por cliente (escritório)
- [x] 4.2 Implementar agrupamento visual com expansão na visão admin (`ExecucoesView.vue`)
- [x] 4.3 Garantir que métricas (total, sucesso, falha) estejam agregadas por cliente na visão escritório
- [x] 4.4 Testar ambas as visões com dados reais

## 5. Agentes — modal de escritório e exibição

- [x] 5.1 Criar componente modal de seleção de escritório para geração de nova chave
- [x] 5.2 Integrar modal ao fluxo "Nova Chave" na visão admin (`AgentesView.vue`)
- [x] 5.3 Adicionar coluna "Escritório" na tabela de agentes da visão admin
- [x] 5.4 Ajustar endpoint de criação de chave para aceitar `escritorioId`
- [x] 5.5 Testar geração de chave com seleção de escritório e visualização na tabela

## 6. Configuração — correção de salvamento

- [x] 6.1 Diagnosticar erro ao salvar configuração na visão admin (verificar network, console e logs da API)
- [x] 6.2 Corrigir causa raiz (validação, mapeamento de DTO, ou lógica no endpoint)
- [x] 6.3 Adicionar feedback visual de sucesso/erro ao salvar (`ConfiguracaoView.vue`)
- [x] 6.4 Testar salvamento com valores válidos e inválidos

## 7. Escritórios — correções do CRUD

- [x] 7.1 Verificar endpoint `GET /api/admin/escritorios/{id}` e garantir que retorna `planoId` e `status`
- [x] 7.2 Corrigir modal de edição para carregar plano e status do escritório (`EscritoriosView.vue`)
- [x] 7.3 Criar mapa de status (enum → string) e aplicar na coluna de status da tabela
- [x] 7.4 Corrigir fluxo de salvamento da edição (verificar endpoint PUT e payload)
- [x] 7.5 Testar edição completa: abrir modal → dados carregados → alterar → salvar → tabela atualizada

## 8. Verificação final

- [x] 8.1 Smoke test completo: percorrer todas as telas nos 3 papéis (admin, escritório, usuário)
- [x] 8.2 Verificar console do navegador para erros residuais
- [x] 8.3 Rodar lint e build do frontend sem erros
