import apiClient from '../client'
import type { ProdutoDto } from '../types'

/**
 * Ferramentas que o escritório da sessão CONTRATOU — é o que alimenta o
 * seletor de nova chave de agente.
 *
 * `escritorioId` só tem efeito para admin da plataforma, que gera chave em
 * nome de outro escritório; para usuário de escritório o servidor ignora o
 * parâmetro e usa o escopo do token (passar id de terceiro seria IDOR).
 */
export async function listarProdutos(escritorioId?: string): Promise<ProdutoDto[]> {
  const { data } = await apiClient.get<ProdutoDto[]>('/api/produtos', {
    params: escritorioId ? { escritorioId } : undefined,
  })
  return data
}
