import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import type { Papel } from '@/api/types'

// Extend vue-router meta types
declare module 'vue-router' {
  interface RouteMeta {
    layout?: 'auth' | 'app'
    public?: boolean
    papeis?: readonly Papel[]
    titulo?: string
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
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin', 'EscritorioAdmin', 'EscritorioUsuario'],
      titulo: 'Dashboard',
    },
  },
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
    path: '/execucoes',
    name: 'execucoes',
    component: () => import('@/views/ExecucoesView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin', 'EscritorioAdmin', 'EscritorioUsuario'],
      titulo: 'Execuções',
    },
  },
  {
    path: '/configuracao',
    name: 'configuracao',
    component: () => import('@/views/ConfiguracaoView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin', 'EscritorioAdmin'],
      titulo: 'Configuração',
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
    path: '/admin/regras',
    name: 'admin-regras',
    component: () => import('@/views/admin/RegrasView.vue'),
    meta: {
      layout: 'app',
      papeis: ['PlatformAdmin'],
      titulo: 'Regras de Coleta',
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
