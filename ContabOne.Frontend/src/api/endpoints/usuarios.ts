import apiClient from '../client'
import type {
  UsuarioListaDto,
  CriarUsuarioRequest,
  AtualizarUsuarioRequest,
  ResetarSenhaRequest,
} from '../types'

export async function listarUsuarios(): Promise<UsuarioListaDto[]> {
  const { data } = await apiClient.get<UsuarioListaDto[]>('/api/usuarios')
  return data
}

export async function criarUsuario(
  req: CriarUsuarioRequest,
): Promise<{ id: string; nome: string; email: string; papel: string }> {
  const { data } = await apiClient.post('/api/usuarios', req)
  return data
}

export async function atualizarUsuario(
  id: string,
  req: AtualizarUsuarioRequest,
): Promise<{ id: string; nome: string; papel: string }> {
  const { data } = await apiClient.put(`/api/usuarios/${id}`, req)
  return data
}

export async function resetarSenha(id: string, req: ResetarSenhaRequest): Promise<void> {
  await apiClient.post(`/api/usuarios/${id}/senha`, req)
}

export async function alterarAtivo(id: string, ativo: boolean): Promise<void> {
  await apiClient.patch(`/api/usuarios/${id}/ativo`, { ativo })
}
