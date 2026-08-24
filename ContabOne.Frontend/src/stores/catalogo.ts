import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { listarProdutos } from '@/api/endpoints/produtos'
import type { DominioDto, ProdutoDto } from '@/api/types'

export interface DominioComFerramentas {
  dominio: DominioDto
  produtos: ProdutoDto[]
}

/**
 * Catálogo de ferramentas da sessão — a fonte única para menu, hub e guard
 * de rota. Carregado uma vez no bootstrap (`router/guards.ts`), em paralelo
 * à restauração da sessão, e descartado no logout: nunca deve sobreviver de
 * uma sessão para a próxima na mesma aba.
 */
export const useCatalogoStore = defineStore('catalogo', () => {
  const produtos = ref<ProdutoDto[]>([])
  const carregando = ref(false)
  const falhou = ref(false)
  // Diferente de "produtos vazio": distingue "ainda não carregou" de
  // "carregou e não há nada" — o menu não deve piscar itens durante o
  // carregamento nem confundir os dois estados.
  const carregado = ref(false)

  const porDominio = computed<DominioComFerramentas[]>(() => {
    const grupos = new Map<string, DominioComFerramentas>()
    for (const produto of produtos.value) {
      let grupo = grupos.get(produto.dominio.codigo)
      if (!grupo) {
        grupo = { dominio: produto.dominio, produtos: [] }
        grupos.set(produto.dominio.codigo, grupo)
      }
      grupo.produtos.push(produto)
    }
    return [...grupos.values()].sort((a, b) => a.dominio.ordem - b.dominio.ordem)
  })

  function porCodigo(codigo: string): ProdutoDto | undefined {
    return produtos.value.find((p) => p.codigo === codigo)
  }

  // Duas chamadas concorrentes acontecem de verdade: o guard dispara a carga
  // sem esperar (carregarCatalogoEmParalelo) e, na mesma navegação, pode
  // precisar esperar o catálogo para validar produto/página de uma rota de
  // ferramenta. Sem memoizar a promessa em andamento, a segunda chamada
  // dispararia um request HTTP duplicado.
  let emAndamento: Promise<void> | null = null

  // Incrementada em cada limpar(): se um carregar() de uma sessão anterior
  // ainda estiver em voo quando o logout acontece, a resposta chega tarde
  // demais e não pode sobrescrever o catálogo (agora vazio, ou já da sessão
  // seguinte) — sem isso o menu do próximo login piscaria com dado de quem
  // saiu.
  let geracao = 0

  async function carregar(escritorioId?: string) {
    if (emAndamento) return emAndamento

    const minhaGeracao = geracao
    emAndamento = (async () => {
      carregando.value = true
      falhou.value = false
      try {
        const dados = await listarProdutos(escritorioId)
        if (minhaGeracao !== geracao) return
        produtos.value = dados
        carregado.value = true
      } catch {
        if (minhaGeracao === geracao) falhou.value = true
      } finally {
        if (minhaGeracao === geracao) carregando.value = false
        emAndamento = null
      }
    })()

    return emAndamento
  }

  function limpar() {
    geracao++
    emAndamento = null
    produtos.value = []
    carregando.value = false
    falhou.value = false
    carregado.value = false
  }

  return {
    produtos,
    carregando,
    falhou,
    carregado,
    porDominio,
    porCodigo,
    carregar,
    limpar,
  }
})
