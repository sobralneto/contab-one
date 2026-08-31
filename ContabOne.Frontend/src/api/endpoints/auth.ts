import apiClient from '../client'
import type {
  LoginRequest,
  LoginResponse,
  TrocarSenhaRequest,
  EscritoriosDisponiveisResponse,
  TrocarEscritorioRequest,
  TrocarEscritorioResponse,
} from '../types'

export async function login(req: LoginRequest): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/api/auth/login', req)
  return data
}

/** Devolve um access token novo, já sem a exigência de troca de senha. */
export async function trocarSenha(req: TrocarSenhaRequest): Promise<{ accessToken: string }> {
  const { data } = await apiClient.post<{ accessToken: string }>('/api/auth/trocar-senha', req)
  return data
}

export async function listarEscritoriosDisponiveis(): Promise<EscritoriosDisponiveisResponse> {
  const { data } = await apiClient.get<EscritoriosDisponiveisResponse>(
    '/api/auth/escritorios-disponiveis',
  )
  return data
}

export async function trocarEscritorio(
  req: TrocarEscritorioRequest,
): Promise<TrocarEscritorioResponse> {
  const { data } = await apiClient.post<TrocarEscritorioResponse>('/api/auth/trocar-escritorio', req)
  return data
}

export async function logout(): Promise<void> {
  await apiClient.post('/api/auth/logout')
}
