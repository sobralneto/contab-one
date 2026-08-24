import apiClient from '../client'
import type { ProdutoDto } from '../types'

/**
 * Catálogo de ferramentas da sessão — alimenta o seletor de nova chave de
 * agente e, via `stores/catalogo.ts`, o menu e o hub.
 *
 * Sempre o catálogo ativo INTEIRO, marcado por `contratado` — a navegação
 * precisa saber da ferramenta não contratada para mostrá-la como
 * indisponível no hub. Quem quer só o contratado (o seletor de chave de
 * agente) filtra por essa flag no próprio componente.
 *
 * `escritorioId` só tem efeito para admin da plataforma, que enxerga o
 * catálogo em nome de outro escritório; para usuário de escritório o
 * servidor ignora o parâmetro e usa o escopo do token (passar id de
 * terceiro seria IDOR).
 */
export async function listarProdutos(escritorioId?: string): Promise<ProdutoDto[]> {
  const { data } = await apiClient.get<ProdutoDto[]>('/api/produtos', {
    params: escritorioId ? { escritorioId } : undefined,
  })
  return data
}
