/**
 * Input masks for pt-BR fields.
 *
 * Moeda tem dois pares de funções, e a distinção importa:
 *
 * - **Digitação** (`moedaDigitada` + `moedaFormatada`): cada dígito digitado é
 *   um centavo. Digitar 1→5→0 dá R$ 0,01 → R$ 0,15 → R$ 1,50. É o que um campo
 *   ligado a v-model precisa, porque o valor exibido é reinterpretado a cada
 *   tecla: qualquer regra que dependa de onde está a vírgula quebra assim que o
 *   próprio texto formatado volta como entrada.
 *
 * - **Valor já formado** (`currencyMask` + `parseCurrency`): interpreta uma
 *   string completa (colada, vinda da API, digitada de uma vez) aplicando as
 *   regras pt-BR de vírgula decimal e ponto de milhar. NÃO usar em digitação.
 */
export function useInputMask() {
  function cnpjMask(value: string): string {
    const digits = value.replace(/\D/g, '').slice(0, 14)
    if (digits.length <= 2) return digits
    if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`
    if (digits.length <= 8) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`
    if (digits.length <= 12) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`
    return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`
  }

  function currencyMask(value: string): string {
    // With both separators, comma is the decimal; dots are thousands (strip)
    let cleaned = value.replace(/[^\d.,]/g, '')
    if (cleaned.includes(',')) cleaned = cleaned.replace(/\./g, '')
    cleaned = cleaned.replace(',', '.')
    const num = parseFloat(cleaned)
    if (isNaN(num)) return ''
    // Normalize the NBSP toLocaleString inserts after "R$" to a regular space
    return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }).replace(/ /g, ' ')
  }

  /**
   * Parse a masked/raw string back to a number (e.g. "R$ 1.234,56" → 1234.56).
   * pt-BR rules: comma is the decimal separator; dots group thousands — except
   * an ungrouped "99.90" typed mid-entry, where the final dot is the decimal.
   */
  function parseCurrency(value: string): number {
    const cleaned = value.replace(/[^\d.,-]/g, '')
    let normalized: string
    if (cleaned.includes(',')) {
      normalized = cleaned.replace(/\./g, '').replace(',', '.')
    } else if (/\.\d{2}$/.test(cleaned)) {
      const parts = cleaned.split('.')
      normalized = parts.slice(0, -1).join('') + '.' + parts[parts.length - 1]
    } else {
      normalized = cleaned.replace(/\./g, '')
    }
    const num = parseFloat(normalized)
    return isNaN(num) ? 0 : num
  }

  /**
   * Valor de um campo de moeda em digitação: só os dígitos contam, e o último
   * par são os centavos. "R$ 1,50" + tecla "0" chega aqui como "R$ 1,500" e
   * vira 15,00 — que é o comportamento de qualquer campo de valor bancário.
   *
   * Sem separador implícito, a alternativa seria reposicionar o cursor a cada
   * tecla para manter a vírgula no lugar; é aí que a versão anterior quebrava.
   */
  function moedaDigitada(value: string): number {
    const digitos = value.replace(/\D/g, '').slice(0, 15)
    if (digitos === '') return 0
    return parseInt(digitos, 10) / 100
  }

  /** Número → "R$ 1.234,56" (espaço normal, não NBSP, para facilitar teste e busca). */
  function moedaFormatada(num: number): string {
    if (!isFinite(num) || num === 0) return ''
    return num
      .toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
      .replace(/ /g, ' ')
  }

  return { cnpjMask, currencyMask, parseCurrency, moedaDigitada, moedaFormatada }
}
