## Why

Múltiplos bugs foram identificados em todas as telas do frontend SaaS de NFS-e, afetando a experiência do usuário, a integridade dos dados exibidos e funcionalidades essenciais como criação de clientes, edição de escritórios e salvamento de configurações. A correção é necessária para viabilizar o uso produtivo da plataforma por administradores, escritórios e usuários finais.

## What Changes

- **Formatação de campos**: Aplicar máscara de CNPJ nos inputs de componentes e formatação monetária no campo de preço dos planos.
- **Dashboard por papel**:
  - Visão admin: gráfico de notas por mês deve exibir nome do escritório no eixo X (não a data); todos os dados agregados por escritório.
  - Visão escritório: gráfico deve exibir nome do cliente no eixo X; dados agregados por cliente.
  - Visão usuário: gráfico deve exibir nome do cliente no eixo X; dados agregados por cliente.
- **Gestão de clientes**:
  - Corrigir fluxo de cadastro de novo cliente.
  - Visão admin: exibir coluna do escritório responsável e filtro por escritório.
  - Visão escritório: filtro por dias até vencimento do certificado (1, 2, 3, 7, 15 dias).
- **Gestão de execuções**:
  - Visão admin: agrupar por escritório com detalhamento expansível.
  - Visão escritório: manter métricas por cliente.
- **Gestão de agentes**: Ao gerar nova chave (admin), abrir modal para selecionar o escritório; exibir nome do escritório na tabela.
- **Configuração**: Corrigir erro ao salvar configuração na visão admin.
- **Gestão de escritórios**:
  - Modal de edição deve carregar plano e status corretamente.
  - Tabela deve exibir nome do status (não o código numérico).
  - Operação de edição deve persistir os dados corretamente.

## Capabilities

### New Capabilities

- `formatacao-campos`: Aplicação de máscaras de entrada (CNPJ) e formatação monetária (preço de plano) nos formulários do frontend.
- `dashboard-exibicao`: Correção dos rótulos e escopo de dados dos gráficos do dashboard conforme o papel do usuário (admin, escritório, usuário).
- `gestao-clientes`: Correção do fluxo CRUD de clientes, coluna e filtro por escritório (admin) e filtro por vencimento de certificado (escritório).
- `gestao-execucoes`: Agrupamento e métricas por escritório (admin) e por cliente (escritório) na tela de execuções.
- `gestao-agentes`: Modal de seleção de escritório ao gerar chave de agente e exibição do nome do escritório na tabela.
- `configuracao-persistencia`: Correção do salvamento de configuração na visão admin.
- `gestao-escritorios`: Correção do modal de edição (carregamento de dados, exibição de status e persistência).

## Impact

- **Frontend** (`ContabOne.Frontend/src/`): Alterações em todos os componentes de formulário, views de Dashboard, Clientes, Execuções, Agentes, Configuração, Escritórios e Planos.
- **API** (`ContabOne.Api/`): Possíveis ajustes nos endpoints de Dashboard, Clientes, Execuções, Agentes, Configuração e Escritórios para garantir que os dados retornados correspondam ao esperado pelo frontend.
- **Sem breaking changes**: As correções mantêm compatibilidade com as interfaces existentes.
