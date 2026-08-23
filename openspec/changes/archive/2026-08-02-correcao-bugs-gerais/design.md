## Context

O frontend é uma SPA Vue 3 com PrimeVue (unstyled) + Tailwind CSS, comunicando-se com uma API .NET. Todos os bugs listados são correções pontuais em componentes e views existentes — não há nova arquitetura ou dependências externas. Ver `proposal.md` para motivação e escopo completo.

Principais constraints:

- PrimeVue unstyled + Tailwind: sem dependência de temas prontos do PrimeVue
- API .NET com endpoints já existentes; eventuais ajustes devem ser mínimos
- Multi-tenancy: os papéis (admin, escritório, usuário) determinam escopo de dados

## Goals / Non-Goals

**Goals:**

- Corrigir TODOS os bugs listados no proposal sem introduzir regressões
- Garantir que máscaras de input (CNPJ, preço) funcionem em qualquer navegador
- Alinhar dados do dashboard com o papel do usuário logado
- Tornar CRUD de clientes e escritórios funcional

**Non-Goals:**

- Refatoração ampla de components ou stores
- Redesign visual das telas
- Migração de bibliotecas (manter PrimeVue + Chart.js)
- Alteração de regras de negócio existentes

## Decisions

### D1: Máscaras de input — abordagem com composable Vue

**Decisão**: Criar um composable `useInputMask.ts` com funções `cnpjMask` e `currencyMask` que retornam handlers de `@input` para aplicar formatação durante digitação. Não usar biblioteca externa (ex: vue-the-mask) para evitar nova dependência.

**Alternativa considerada**: `vue-the-mask` — rejeitada por adicionar dependência desnecessária para apenas 2 campos.

**Implementação**:

- `cnpjMask`: no evento `input`, remove não-dígitos, limita a 14 caracteres, insere `.`, `/`, `-` nas posições corretas
- `currencyMask`: no evento `input`, armazena valor numérico internamente, exibe formatado como `R$ X.XXX,XX`

### D2: Gráfico do dashboard — incluir nome da entidade na resposta da API

**Decisão**: Modificar o endpoint de dashboard (`/api/dashboard/series`) para incluir o campo `label` (nome do escritório ou cliente) na resposta, além da `competencia`. O frontend usará `label` no eixo X, com fallback para `competencia` formatada.

**Alternativa considerada**: Fazer join no frontend com dados de escritórios/clientes — rejeitada por complexidade e performance desnecessárias quando a API já tem acesso aos dados relacionais.

**Impacto**: Mudança no DTO `SerieItem` do frontend (`api/types.ts`) e no endpoint correspondente da API.

### D3: Filtro de vencimento de certificado — parâmetro de query na API

**Decisão**: Adicionar parâmetro `diasVencimentoCert` ao endpoint `GET /api/clientes`. Quando presente, a API filtra clientes cujo certificado vence em até N dias. O frontend renderiza um `<select>` com as opções (1, 2, 3, 7, 15 dias).

### D4: Agrupamento em execuções — dois endpoints distintos

**Decisão**:

- Admin: novo endpoint ou parâmetro `agruparPor=escritorio` no endpoint existente, retornando dados aninhados (escritório → execuções)
- Escritório: endpoint existente já retorna por cliente, apenas garantir que as métricas estejam corretas

**Alternativa considerada**: Agrupar no frontend — rejeitada para grandes volumes de dados.

### D5: Status de escritório — mapeamento enum → string

**Decisão**: Criar mapa constante `STATUS_ESCRITORIO` no frontend e usar em tabela e modal.

**Implementação — descoberta importante**: a recomendação original ("API já retorna o nome do status") estava errada — **nenhum `JsonStringEnumConverter` está registrado**, então todos os enums serializavam como **número** (0/1/2) enquanto o frontend espera strings (`'Ativo'`, `'Sucesso'`). O `JsonStringEnumConverter` global foi **descartado** porque o agente Python envia enums como inteiros de propósito (coberto por testes próprios). A correção foi cirúrgica: `.ToString()` nas projeções dos endpoints do frontend (dashboard, execuções, admin) e `Status` como string nos DTOs de request do admin (PUT/POST escritórios).

### D6: Filtro do dashboard por papel — escritório (admin) vs cliente (demais)

**Decisão**: O filtro do dashboard é condicionado ao papel: admin seleciona um **escritório** (`escritorioId`), escritório/usuário selecionam um **cliente** (`clienteId`). O endpoint `/api/dashboard/series` aceita ambos os parâmetros; o query filter global mantém a isolação de tenancy (um `escritorioId` alheio não vaza dados).

**Implementação — correção de filtragem duplicada**: o frontend filtrou as séries uma segunda vez por `competencia`, mas desde o D2 a série agregada por entidade tem `competencia` vazio — qualquer filtro de data zerava o gráfico. A filtragem passou a ser **exclusiva da API** (de/ate/escritorioId/clienteId).

**Ranking**: componente dedicado `RankingEscritorios.vue` para a visão admin (agregação por escritório já retornada pela API); `RankingClientes.vue` ficou restrito aos demais papéis.

## Risks / Trade-offs

- **[Baixo] Alteração de DTO da API**: Mudanças nos endpoints de dashboard e clientes podem quebrar compatibilidade com versões anteriores do frontend. → Mitigação: deploy conjunto frontend + API; campos adicionais são aditivos (não removemos campos existentes).
- **[Baixo] Máscara de CNPJ**: Comportamento pode variar entre navegadores no evento `input` vs `keydown`. → Mitigação: testar em Chrome, Firefox e Edge; usar `input` + `v-model` com getter/setter computado.
- **[Médio] Correção de CRUD**: Bugs de salvamento podem ter causa raiz em validação do backend ou em mapeamento de DTOs. → Mitigação: verificar network tab e logs da API antes de alterar código; corrigir na camada correta.

## Open Questions

- ~~Confirmar o enum de status de escritório na API (valores exatos e nomes) para o mapeamento do D5~~ — **resolvido**: `StatusEscritorio` = Ativo, Inadimplente, Suspenso, Cancelado (D5).
