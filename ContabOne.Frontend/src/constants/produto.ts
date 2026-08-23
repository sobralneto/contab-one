import type { Produto } from '@/api/types'

// Mapa enum → rótulo. A API serializa o produto como string ("Nfse", "Det"),
// e `prefixo` é o mesmo nome em minúsculas que abre a chave de API — espelha
// ApiKeyHasher.PrefixoDe no servidor.
export const PRODUTO: Record<Produto, { label: string; descricao: string; prefixo: string }> = {
  Nfse: {
    label: 'NFS-e',
    descricao: 'Coleta de NFS-e no Portal Nacional',
    prefixo: 'nfse',
  },
  Det: {
    label: 'DET',
    descricao: 'Domicílio Eletrônico Trabalhista',
    prefixo: 'det',
  },
}

export const PRODUTOS = Object.keys(PRODUTO) as Produto[]
