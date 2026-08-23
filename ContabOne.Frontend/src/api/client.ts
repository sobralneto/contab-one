import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'

// Augment axios types to support _retry flag
declare module 'axios' {
  interface InternalAxiosRequestConfig {
    _retry?: boolean
  }
}

const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL as string,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Chama /api/auth/refresh usando um axios "cru" (sem os interceptors do apiClient).
 * Usado tanto pelo interceptor de resposta abaixo quanto pelo bootstrap de sessão
 * em router/guards.ts — nenhum dos dois pode passar pelo apiClient, senão uma falha
 * de refresh dispara o interceptor de 401 de novo (refresh chamando refresh).
 */
export async function refreshAccessToken(): Promise<{ accessToken: string }> {
  const { data } = await axios.post<{ accessToken: string }>(
    `${import.meta.env.VITE_API_URL}/api/auth/refresh`,
    {},
    { withCredentials: true },
  )
  return data
}

// ── Request interceptor: attach access token ──
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const auth = useAuthStore()
    if (auth.accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${auth.accessToken}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ── Response interceptor: 401 → refresh → retry ──
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (error: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach((p) => {
    if (error) {
      p.reject(error)
    } else {
      p.resolve(token!)
    }
  })
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig

    // Only attempt refresh on 401, once per request
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    // 401 de uma requisição SEM token (ex.: POST /api/auth/login com
    // credenciais erradas) é "credenciais inválidas", não "sessão expirada" —
    // tentar refresh aqui redirecionaria para /login e engoliria a mensagem
    // de erro do formulário. Refresh só faz sentido quando o 401 respondeu a
    // uma requisição que carregava um access token.
    if (!originalRequest.headers?.Authorization) {
      return Promise.reject(error)
    }

    // If we're already refreshing, queue this request
    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      })
        .then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`
          }
          return apiClient(originalRequest)
        })
        .catch((err) => Promise.reject(err))
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      const data = await refreshAccessToken()

      const auth = useAuthStore()
      auth.setAccessToken(data.accessToken)

      // Update the original request with new token
      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${data.accessToken}`
      }

      // Retry all queued requests with new token
      processQueue(null, data.accessToken)

      return apiClient(originalRequest)
    } catch (refreshError) {
      // Refresh failed — clear session and redirect to login
      processQueue(refreshError, null)
      useAuthStore().clearSession()
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)

export default apiClient
