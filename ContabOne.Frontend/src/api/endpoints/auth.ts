import apiClient from '../client'
import type { LoginRequest, LoginResponse, TrocarSenhaRequest } from '../types'

export async function login(req: LoginRequest): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/api/auth/login', req)
  return data
}

/** Devolve um access token novo, já sem a exigência de troca de senha. */
export async function trocarSenha(req: TrocarSenhaRequest): Promise<{ accessToken: string }> {
  const { data } = await apiClient.post<{ accessToken: string }>('/api/auth/trocar-senha', req)
  return data
}

export async function logout(): Promise<void> {
  await apiClient.post('/api/auth/logout')
}
