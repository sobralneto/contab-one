import type { Papel } from '@/api/types'

// Mapa enum → string legível. A API serializa o papel como string
// ("PlatformAdmin", "EscritorioAdmin", "EscritorioUsuario").
export const PAPEL_USUARIO: Record<Papel, { label: string; descricao: string }> = {
  PlatformAdmin: {
    label: 'Admin da Plataforma',
    descricao: 'Acesso total, inclusive a todos os escritórios',
  },
  EscritorioAdmin: {
    label: 'Admin do Escritório',
    descricao: 'Gerencia usuários, agentes e configuração do escritório',
  },
  EscritorioUsuario: {
    label: 'Usuário',
    descricao: 'Acompanha dashboard, clientes e execuções',
  },
}
