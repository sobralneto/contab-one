/**
 * Validação de schema do bundle de regras de coleta no cliente — espelho do
 * servidor (ContabOne.Api/Domain/RegraColetaValidator.cs) e do agente
 * (Nfse.Agent/regras.validar_bundle). As três validações são mantidas
 * alinhadas pelo corpus compartilhado (testes/fixtures/bundles/manifest.json);
 * este espelho existe para o editor avisar o admin ANTES de publicar.
 *
 * Devolve a lista de mensagens de problema (vazia = válido). Nunca lança.
 */

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}

export function validarBundle(conteudo: string): string[] {
  const erros: string[] = []

  let raiz: unknown
  try {
    raiz = JSON.parse(conteudo)
  } catch {
    return ['conteúdo não é um objeto JSON']
  }
  if (!isRecord(raiz)) return ['conteúdo não é um objeto JSON']

  // ── portal ──
  const portal = raiz.portal
  if (!isRecord(portal)) {
    erros.push("'portal' ausente ou não é um objeto")
  } else {
    for (const campo of ['urlLogin', 'urlNotas', 'urlApiXml']) {
      const valor = portal[campo]
      if (typeof valor !== 'string' || !valor.startsWith('https://')) {
        erros.push(`portal.${campo} ausente ou não é uma URL https`)
      }
    }

    const maxDias = portal.maxDiasFiltro
    if (
      typeof maxDias !== 'number' ||
      !Number.isInteger(maxDias) ||
      maxDias <= 0 ||
      maxDias > 366
    ) {
      erros.push('portal.maxDiasFiltro ausente ou fora da faixa esperada (1-366)')
    }

    if (typeof portal.paramPagina !== 'string' || portal.paramPagina === '') {
      erros.push('portal.paramPagina ausente ou vazio')
    }

    const listagens = portal.listagens
    if (!isRecord(listagens)) {
      erros.push('portal.listagens ausente ou não é um objeto')
    } else {
      for (const tipo of ['recebidas', 'emitidas']) {
        const lst = listagens[tipo]
        if (!isRecord(lst)) {
          erros.push(`portal.listagens.${tipo} ausente ou não é um objeto`)
          continue
        }
        if (typeof lst.rota !== 'string' || lst.rota === '') {
          erros.push(`portal.listagens.${tipo}.rota ausente ou vazia`)
        }
        if (typeof lst.executar !== 'boolean') {
          erros.push(`portal.listagens.${tipo}.executar ausente ou não é booleano`)
        }
        if (
          !Array.isArray(lst.colunas) ||
          lst.colunas.length === 0 ||
          lst.colunas.some((c) => typeof c !== 'string')
        ) {
          erros.push(`portal.listagens.${tipo}.colunas ausente ou inválida`)
        }
      }
    }
  }

  // ── parsing ──
  const parsing = raiz.parsing
  if (!isRecord(parsing)) {
    erros.push("'parsing' ausente ou não é um objeto")
  } else {
    for (const campo of ['regexChave', 'regexLinha', 'regexTotalRegistros']) {
      const padrao = parsing[campo]
      if (typeof padrao !== 'string' || padrao === '') {
        erros.push(`parsing.${campo} ausente ou vazio`)
        continue
      }
      try {
        // eslint-disable-next-line no-new
        new RegExp(padrao)
      } catch {
        erros.push(`parsing.${campo} não é uma expressão regular válida`)
      }
    }
  }

  return erros
}
