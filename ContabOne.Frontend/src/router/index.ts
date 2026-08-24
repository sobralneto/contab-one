import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import type { Papel, PaginaFerramenta } from '@/api/types'

// Extend vue-router meta types
declare module 'vue-router' {
  interface RouteMeta {
    layout?: 'auth' | 'app'
    public?: boolean
    papeis?: readonly Papel[]
    titulo?: string
    /** Só nas rotas de ferramenta (`/f/:produto/...`) — usado pelo guard e por ExplicacaoPagina. */
    pagina?: PaginaFerramenta
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { layout: 'auth', public: true, titulo: 'Entrar' },
  },
  {
    path: '/',
    name: 'hub',
    component: () => import('@/views/HubView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin', 'EscritorioAdmin', 'EscritorioUsuario'],
      titulo: 'Início',
    },
  },

  // ── Ferramentas: uma família de rotas por página, :produto identifica
  // qual ferramenta (o mesmo `codigo` do catálogo — "nfse", "det", …). O
  // guard (router/guards.ts) recusa produto fora do catálogo da sessão e
  // página que a ferramenta não declara.
  {
    path: '/f/:produto',
    name: 'ferramenta-visao-geral',
    // O dashboard nasceu como a única tela do sistema — hoje é a visão geral
    // de UMA ferramenta (NFS-e). Endereço novo, conteúdo intocado.
    component: () => import('@/views/DashboardView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin', 'EscritorioAdmin', 'EscritorioUsuario'],
      titulo: 'Visão geral',
      pagina: 'visao-geral',
    },
  },
  {
    path: '/f/:produto/execucoes',
    name: 'ferramenta-execucoes',
    component: () => import('@/views/ExecucoesView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin', 'EscritorioAdmin', 'EscritorioUsuario'],
      titulo: 'Execuções',
      pagina: 'execucoes',
    },
  },
  {
    path: '/f/:produto/configuracao',
    name: 'ferramenta-configuracao',
    component: () => import('@/views/ConfiguracaoView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin', 'EscritorioAdmin'],
      titulo: 'Configuração',
      pagina: 'configuracao',
    },
  },
  {
    // Cadastro do pacote de regras que os agentes baixam para o Portal
    // Nacional — só o NFS-e declara. Mais estrita que Configuração: só
    // PlatformAdmin, nunca EscritorioAdmin (publicar versão quebrada afeta
    // a coleta de todos os escritórios de uma vez).
    path: '/f/:produto/regras',
    name: 'ferramenta-regras',
    component: () => import('@/views/admin/RegrasView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin'],
      titulo: 'Regras de Coleta',
      pagina: 'regras',
    },
  },
  // ── Redirects — endereços antigos, de quando só existia o NFS-e.
  // Permanentes de propósito (design.md, Risks): link salvo, favorito e a
  // suíte Playwright continuam chegando na tela certa. `/clientes` e
  // `/agentes` NÃO entram aqui: já eram os endereços certos antes desta
  // família de rotas existir, e continuam sendo — as duas telas nunca
  // dependeram de qual ferramenta está na URL.
  { path: '/dashboard', redirect: (to) => ({ path: '/f/nfse', query: to.query }) },
  { path: '/execucoes', redirect: (to) => ({ path: '/f/nfse/execucoes', query: to.query }) },
  { path: '/configuracao', redirect: (to) => ({ path: '/f/nfse/configuracao', query: to.query }) },
  { path: '/admin/regras', redirect: (to) => ({ path: '/f/nfse/regras', query: to.query }) },

  // ── Transversais: Cliente e Agente não são particionados por produto no
  // banco — a mesma tela vale pra qualquer ferramenta, então não fazem
  // parte de /f/:produto/… (design.md).
  {
    path: '/clientes',
    name: 'clientes',
    component: () => import('@/views/ClientesView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin', 'EscritorioAdmin', 'EscritorioUsuario'],
      titulo: 'Clientes',
    },
  },
  {
    path: '/agentes',
    name: 'agentes',
    component: () => import('@/views/AgentesView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin', 'EscritorioAdmin'],
      titulo: 'Agentes',
    },
  },
  {
    path: '/usuarios',
    name: 'usuarios',
    component: () => import('@/views/UsuariosView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin', 'EscritorioAdmin'],
      titulo: 'Usuários',
    },
  },
  {
    // Exige sessão (não é `public`): quem chega aqui já autenticou, só está
    // preso pela flag deveTrocarSenha no guard.
    path: '/trocar-senha',
    name: 'trocar-senha',
    component: () => import('@/views/TrocarSenhaView.vue'),
    meta: { layout: 'auth', titulo: 'Trocar senha' },
  },
  {
    path: '/admin/escritorios',
    name: 'admin-escritorios',
    component: () => import('@/views/admin/EscritoriosView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin'],
      titulo: 'Escritórios',
    },
  },
  {
    path: '/admin/planos',
    name: 'admin-planos',
    component: () => import('@/views/admin/PlanosView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin'],
      titulo: 'Planos',
    },
  },
  {
    path: '/admin/produtos',
    name: 'admin-produtos',
    component: () => import('@/views/admin/ProdutosView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin'],
      titulo: 'Ferramentas',
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
