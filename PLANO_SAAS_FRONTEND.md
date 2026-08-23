# Plano — Front-end Vue 3 (Railway)

Status: **plano, nada implementado**. Escrito para ser executado numa sessão
futura.

Documentos irmãos: [PLANO_SAAS_API.md](PLANO_SAAS_API.md) ·
[PLANO_SAAS_AGENTE.md](PLANO_SAAS_AGENTE.md)

O vocabulário (Plataforma / Escritório / Cliente / Agente) está definido em
[PLANO_SAAS_API.md §1](PLANO_SAAS_API.md) — vale ler antes.

---

## 1. Stack

| Item | Escolha | Por quê |
|---|---|---|
| Framework | **Vue 3** + `<script setup>` + Composition API | pedido |
| Linguagem | **TypeScript** | os contratos da API são o coração do app; tipo estático evita quebra silenciosa quando o backend mudar |
| Build | **Vite** | padrão do ecossistema Vue |
| Roteamento | Vue Router 4 | guards por papel |
| Estado | **Pinia** | store de sessão + config; o resto é estado local |
| UI | **PrimeVue 4**, preset **Nora** | traz `DataTable` com paginação/filtro/ordenação e `Chart` prontos — economiza semanas num app que é essencialmente tabelas + gráficos. Nora é o preset de cara corporativa (mais angular e compacto); Aura é mais arredondado/consumer — ver §2 |
| Gráficos | `Chart.js` via PrimeVue `Chart` | já vem junto; não adiciona dependência nova |
| HTTP | Axios com interceptors | refresh de token automático no 401 |
| Formulários | vee-validate + zod | validação declarativa, e o schema zod dobra como tipo TS |
| Testes | Vitest + Testing Library; Playwright p/ e2e | |

**Alternativas consideradas:** Nuxt (SSR desnecessário — é app autenticado
atrás de login, sem SEO); Vuetify (bom, mas PrimeVue tem DataTable superior
para o volume de dados aqui); Tailwind puro + headless (mais controle, muito
mais tempo até a primeira tela útil).

> **Reaproveitar o que já existe:** o `dashboard.html` local já tem a paleta de
> **séries de dados** validada (azul `#2a78d6` recebidas, laranja `#eb6834`
> emitidas) e as decisões de gráfico. Ela continua valendo — mas só para os
> gráficos, não para a interface. A distinção está em §2.3 e é o que evita o
> app virar um arco-íris.
>
> *(09/08/2026: o `dashboard.html` local foi removido do agente. As demais
> menções a ele neste plano são referência histórica — os valores citados já
> vivem nos tokens do frontend, não há mais arquivo para consultar.)*

---

## 2. Identidade visual — clean e empresarial

O público é contador, usando a ferramenta várias horas por dia, muitas vezes
ao lado de um ERP e de um sistema contábil. Nesse contexto **familiaridade
vale mais que originalidade**: a tela tem que parecer óbvia no primeiro uso e
não cansar no centésimo.

### 2.1 O que "clean e empresarial" significa em decisão concreta

| Aspecto | Sim | Não |
|---|---|---|
| Cor | neutros dominam; cor só quando carrega significado (status, série) | gradiente decorativo, roxo de startup, cor de marca espalhada pela tela |
| Elevação | borda *hairline* de 1px sobre fundo branco | sombra pesada, card flutuante, glassmorphism |
| Raio de canto | 4–6px | pílula, 16px+ |
| Densidade | confortável-densa — o contador quer ver ~20 linhas sem rolar | espaçamento de landing page |
| Movimento | 120–150ms em hover/foco, ou nada | animação de entrada, parallax, skeleton pulsante |
| Tipografia | uma família, pesos 400/500/600 | fonte display, peso 300 em texto pequeno |
| Ilustração | nenhuma, exceto em estado vazio | mascote, ícone 3D, foto de banco de imagem |

A coluna da direita não é enfeite: é onde a maioria dos dashboards moderninhos
erra e vira cansativo para uso diário.

### 2.2 Tokens (modo claro — o primário)

```
--surface-page      #f6f7f9    fundo da aplicação
--surface-card      #ffffff    card, tabela, painel
--surface-sidebar   #101828    navegação (escura, ancora a tela)
--border            #e3e6ea    hairline, o separador padrão
--border-forte      #cdd3da    divisor de seção

--text-primary      #14171a
--text-secondary    #5a6472
--text-muted        #667085    rótulo de eixo, placeholder

--accent            #1e5aa8    ação primária, item ativo, link
--accent-hover      #17497f
--accent-suave      #eef3fa    fundo de linha selecionada

--sucesso           #0f7a3d
--atencao           #b45309
--erro              #b42318
```

Contraste conferido por cálculo, não no olho — todos passam **WCAG AA (4.5:1)**
para texto normal, medidos contra `--surface-card` e `--surface-page`:

| Par | Razão |
|---|---|
| `text-primary` / card | 17.99 |
| `text-secondary` / card | 6.00 |
| `text-muted` / card · page | 4.97 · 4.64 |
| `accent` / card *(link)* | 6.81 |
| branco / `accent` *(botão)* | 6.81 |
| `sucesso` · `atencao` · `erro` / card | 5.42 · 5.02 · 6.57 |
| branco / sidebar | 17.75 |

> O `--text-muted` era `#8a929c` no primeiro rascunho e **reprovava** (3.15 no
> card, 2.94 na página). `#667085` é o cinza mais claro dessa família que ainda
> passa nas duas superfícies. Ao trocar qualquer token, **recalcule** — cinza
> claro sobre fundo claro é onde isso quebra, e é justamente o que mais some
> na tela do usuário com visão cansada no fim do dia.

Os semânticos aparecem em *chip* e alerta (validade de certificado, status de
execução) — sempre com **ícone + texto junto**, nunca só a cor. Um dos usuários
pode ter daltonismo, e "vermelho = vencido" sozinho não comunica.

### 2.3 Duas paletas, com papéis diferentes — não misturar

Este é o ponto que, se ignorado, estraga o dashboard:

- **Interface** (nav, botão, borda, fundo): escala neutra + um acento
  discreto. É moldura, tem que sumir.
- **Séries de dados** (barras, linhas): a paleta do `dashboard.html`, que é
  vibrante **de propósito** — precisa distinguir categoria à primeira vista.

Por isso o acento da UI (`#1e5aa8`) é um azul **mais escuro e dessaturado** que
o azul das séries (`#2a78d6`). Se fossem o mesmo, o olho não distinguiria "isto
é dado" de "isto é interface", e o gráfico perderia leitura no meio da própria
tela.

### 2.4 Tipografia

**Inter**, auto-hospedada (não via CDN do Google — evita dependência externa e
questão de privacidade), com `system-ui` de fallback. Escala curta:

```
32/600  número de KPI        14/400  corpo, célula de tabela
20/600  título de página     13/500  rótulo de coluna
16/500  título de seção      12/400  auxiliar, timestamp
```

**`font-variant-numeric: tabular-nums` é obrigatório** em toda coluna numérica,
KPI e eixo. Sem isso os dígitos têm larguras diferentes e uma coluna de valores
fica visualmente desalinhada — em software fiscal isso passa impressão de
desleixo mais rápido que qualquer outro detalhe.

Valores em R$ e contagens sempre **alinhados à direita**; texto à esquerda.

### 2.5 Componentes — o que define o caráter

- **Tabela** (a tela mais usada): sem zebra; separador *hairline* entre linhas;
  cabeçalho em 500 com fundo `#f6f7f9` e fixo ao rolar; hover de linha em
  `--accent-suave`; densidade compacta via token do PrimeVue.
- **Botão**: primário sólido no acento; secundário *outline*; terciário só
  texto. Sem sombra, sem gradiente. Ação destrutiva em `--erro` e sempre com
  confirmação.
- **Card de KPI**: borda hairline, sem sombra, rótulo pequeno em maiúscula
  discreta, número grande em tabular-nums, variação abaixo.
- **Sidebar escura** (`--surface-sidebar`): ancora visualmente e é o padrão que
  o público já reconhece de ERP. Item ativo = barra de 3px no acento + fundo
  sutil, **não** pílula colorida.
- **Estado vazio**: uma frase explicando e um botão com o próximo passo. É o
  único lugar onde cabe uma ilustração — discreta, monocromática.

### 2.6 Modo escuro

Secundário, não corte de escopo do MVP. Construa com *design tokens* desde o
início (o PrimeVue 4 já é baseado neles) para que o modo escuro seja uma troca
de valores, não uma refatoração. O `dashboard.html` já tem os valores escuros
validados para os gráficos — reaproveitar.

### 2.7 Referências de linguagem visual

Para alinhar expectativa sem precisar de mockup: Linear, Stripe Dashboard,
Vercel e Sentry acertam o registro "clean + empresarial" — neutro, denso,
tipografia forte, cor com parcimônia. Serve de norte; não copiar layout.

---

## 3. Estrutura

```
src/
├── main.ts
├── App.vue
├── router/
│   ├── index.ts
│   └── guards.ts              autenticação + papel
├── stores/
│   ├── auth.ts                usuário, token, papel
│   └── ui.ts                  tema, sidebar
├── api/
│   ├── client.ts              instância axios + interceptors
│   ├── types.ts               contratos (espelham a API)
│   └── endpoints/             auth.ts, dashboard.ts, clientes.ts, admin.ts…
├── layouts/
│   ├── AuthLayout.vue         só o login
│   └── AppLayout.vue          sidebar + topbar
├── views/
│   ├── LoginView.vue
│   ├── DashboardView.vue
│   ├── ClientesView.vue
│   ├── ConfiguracaoView.vue
│   ├── AgentesView.vue
│   ├── ExecucoesView.vue
│   └── admin/
│       ├── EscritoriosView.vue
│       ├── PlanosView.vue
│       └── RegrasView.vue
├── components/
│   ├── dashboard/  KpiCard, GraficoMensal, RankingClientes, ListaAlertas
│   └── comum/      TabelaPadrao, EstadoVazio, ConfirmarAcao
└── composables/
    ├── useApi.ts              loading/erro padronizados
    └── useFormatters.ts       CNPJ, data pt-BR, número
```

---

## 4. Telas

### 3.1 Login

E-mail + senha, mensagem de erro genérica ("e-mail ou senha inválidos" — nunca
"usuário não existe", que entrega quais e-mails estão cadastrados). Guarda o
access token **em memória** (Pinia), nunca em `localStorage`; o refresh vive em
cookie `httpOnly` que o JS não lê. Isso reduz o estrago de um XSS.

Redireciona por papel: `PlatformAdmin` → `/admin`, demais → `/dashboard`.

### 3.2 Dashboard

Estrutura herdada do `dashboard.html` local, agora multi-cliente e com filtro:

1. **Linha de KPIs** — total de clientes ativos, notas baixadas no mês,
   certificados vencendo em 30 dias (destacado se >0), última execução (com
   status e "há X horas")
2. **Alertas** — no topo, não no rodapé: certificado vencido, agente sem dar
   sinal, execução falhada. É o que exige ação.
3. **Notas por mês** — barras empilhadas (recebidas/emitidas), com filtro de
   período e de cliente
4. **Ranking de clientes** — barra horizontal por volume
5. **Últimas execuções** — tabela compacta com status, duração, quantidades

Filtros ficam numa linha só acima do conteúdo (período + cliente), e o estado
vai na query string — assim o usuário consegue compartilhar/favoritar a visão.

**Estado vazio importa:** escritório recém-cadastrado, sem nenhuma execução,
não pode ver gráficos zerados e achar que quebrou. Mostrar um guia curto:
"Nenhum dado ainda — instale o agente e gere sua primeira chave em Agentes".

### 3.3 Meus Clientes

`DataTable` com busca, ordenação e paginação server-side. Colunas: código,
nome, CNPJ mascarado, validade do certificado (com *chip* colorido: verde OK,
âmbar <30 dias, vermelho vencido), total de notas, última atualização.

Cadastro manual + edição. **A validade e o CNPJ chegam do agente** — na tela
de edição esses campos são somente leitura, com a indicação "atualizado
automaticamente pelo agente em …". Deixar editável dá a falsa impressão de que
alterar ali muda alguma coisa no certificado.

### 3.4 Configuração da ferramenta

Formulário dos parâmetros que o agente lê no próximo handshake:
tipos (recebidas/emitidas), `primeira_busca_desde`, gerar PDF, pasta de saída
padrão sugerida.

Deixar explícito na tela que **a mudança vale a partir da próxima execução do
agente** — sem isso o usuário troca a opção, olha o dashboard e acha que não
funcionou.

### 3.5 Agentes

Lista das máquinas do escritório: nome, versão, último contato, status. Botão
"Gerar nova chave" abre modal exibindo a chave **uma única vez**, com aviso
claro e botão de copiar. Revogar pede confirmação digitando o nome do agente
(ação destrutiva: revogar a chave errada para a coleta do escritório).

### 3.6 Admin da plataforma

Fora do menu normal, só para `PlatformAdmin`:

- **Escritórios** — CRUD, mudança de plano e, principalmente, o seletor de
  `Status` (Ativo / Inadimplente / Suspenso). É a alavanca comercial: mudar
  para Inadimplente faz o agente parar no próximo handshake. Ação com
  confirmação e registro de auditoria.
- **Planos** — limites e preço
- **Regras de coleta** — editor JSON com validação de schema, histórico de
  versões e botão de publicar. **Tela de alto risco:** publicar um JSON quebrado
  para em todos os agentes de todos os clientes. Exigir preview do diff contra
  a versão atual e confirmação explícita antes de publicar.
- **Visão geral** — saúde de todos os escritórios numa tabela

---

## 5. Papéis e rotas

```ts
PlatformAdmin    → tudo, inclusive /admin/*
EscritorioAdmin  → dashboard, clientes, configuração, agentes, execuções
EscritorioUsuario→ dashboard, clientes (leitura), execuções
```

Guard no router bloqueia por `meta.papeis`. **Isso é conveniência de UI, não
segurança** — o back precisa validar o papel em todo endpoint de novo. Um
usuário pode chamar a API direto, sem passar pelo front.

---

## 6. Camada de API

`client.ts` centraliza:
- `baseURL` de `import.meta.env.VITE_API_URL`
- `Authorization: Bearer` a cada request
- interceptor de **401 → tenta refresh uma vez → repete a request**; se o
  refresh falhar, limpa a sessão e manda para o login. Cuidado com o laço
  infinito quando o próprio refresh der 401 (flag de "já tentei")
- erro tratado num formato só, para o `useApi` mostrar toast sem cada tela
  reimplementar tratamento

`types.ts` espelha os contratos da API. Se o backend expõe OpenAPI (e expõe,
pelo plano da API), vale gerar esses tipos automaticamente com
`openapi-typescript` — elimina a classe inteira de bug "o back renomeou um
campo e o front só descobre em produção".

---

## 7. Fases

**Fase 1 — Esqueleto.** Vite + TS + Router + Pinia + PrimeVue, layouts, tema
com os tokens do `dashboard.html`, deploy vazio no Railway funcionando.

**Fase 2 — Auth.** Login, store de sessão, interceptors, guards, refresh.
Testar expiração de verdade (token curto em dev).

**Fase 3 — Dashboard.** KPIs, gráficos, alertas, filtros. Casa com a Fase 4 da API.

**Fase 4 — Clientes, Agentes, Execuções.** As telas do dia a dia.

**Fase 5 — Configuração e Admin.** Inclui o editor de regras com validação.

**Fase 6 — Acabamento.** Estados vazios, tratamento de erro, responsivo,
acessibilidade (foco, contraste, navegação por teclado nas tabelas).

---

## 8. Testes

- **Vitest** — composables (`useFormatters`: CNPJ mascarado, datas), lógica das
  stores, interceptor de refresh (o laço infinito citado em §6 é exatamente o
  tipo de bug que só teste pega)
- **Testing Library** — componentes com regra de negócio visível: `KpiCard` com
  zero, tabela vazia, chip de validade nos três estados
- **Playwright** — 4 caminhos que não podem quebrar: login→dashboard,
  cadastrar cliente, gerar chave de agente, admin suspender escritório
- **MSW** para mockar a API nos testes de componente

---

## 9. Deploy no Railway

Build estático servido por Caddy (o Railway tem guia próprio para Caddy) ou
Nginx:

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM caddy:alpine
COPY --from=build /app/dist /usr/share/caddy
COPY Caddyfile /etc/caddy/Caddyfile
```

Dois pontos que costumam morder:

1. **SPA fallback.** Sem `try_files`, atualizar a página em `/clientes` dá 404 —
   o servidor procura um arquivo que não existe. O `Caddyfile` precisa cair no
   `index.html`.
2. **`VITE_API_URL` é embutida no build, não lida em runtime.** Trocar a
   variável no Railway **não** muda o bundle já compilado; exige rebuild. Se
   isso incomodar, a saída é servir um `config.json` carregado no boot da app.

O Caddy também precisa escutar em `$PORT`.

---

## 10. Perguntas em aberto

1. Domínio próprio ou subdomínio do Railway? Afeta CORS e cookie de refresh
   (`SameSite=Strict` só funciona bem se front e API compartilham domínio —
   com domínios diferentes, avaliar `SameSite=None; Secure` e o impacto).
2. O escritório precisa de **múltiplos usuários** desde o MVP, ou um login por
   escritório basta no início? Modelei múltiplos, mas simplificar acelera.
3. Precisa de tela de **auto-cadastro** (trial) ou você cadastra os escritórios
   manualmente no começo? Manual é bem mais simples e é o normal nos primeiros
   clientes.
4. Onde o escritório **baixa o instalador do agente**? Sugestão: um card no
   dashboard com o link da versão atual e a chave já gerada — reduz o atrito
   do onboarding, que é onde se perde cliente.
