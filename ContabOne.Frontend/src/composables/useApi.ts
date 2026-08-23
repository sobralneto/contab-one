import { ref, type Ref } from 'vue'

/**
 * Wraps an API call with standardized loading/error/data state.
 *
 * Usage:
 *   const { data, loading, error, execute } = useApi<ClienteDto[]>()
 *   await execute(listarClientes({ busca: 'silva' }))
 */
export function useApi<T>() {
  const loading: Ref<boolean> = ref(false)
  const error: Ref<string | null> = ref(null)
  const data: Ref<T | null> = ref(null) as Ref<T | null>

  async function execute(promise: Promise<T>): Promise<T | undefined> {
    loading.value = true
    error.value = null
    try {
      data.value = await promise
      return data.value
    } catch (e: unknown) {
      const err = e as { response?: { data?: { erro?: string } }; message?: string }
      error.value = err?.response?.data?.erro ?? err?.message ?? 'Erro desconhecido'
      return undefined
    } finally {
      loading.value = false
    }
  }

  return { loading, error, data, execute }
}
