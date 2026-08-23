import { describe, it, expect } from 'vitest'
import { useInputMask } from './useInputMask'

const { cnpjMask, parseCurrency, currencyMask } = useInputMask()

describe('useInputMask.cnpjMask', () => {
  it('mascara progressivamente em cada faixa de tamanho', () => {
    expect(cnpjMask('12')).toBe('12')
    expect(cnpjMask('123')).toBe('12.3')
    expect(cnpjMask('12345')).toBe('12.345')
    expect(cnpjMask('123456')).toBe('12.345.6')
    expect(cnpjMask('12345678')).toBe('12.345.678')
    expect(cnpjMask('123456789')).toBe('12.345.678/9')
    expect(cnpjMask('123456789012')).toBe('12.345.678/9012')
    expect(cnpjMask('12345678901234')).toBe('12.345.678/9012-34')
  })

  it('descarta não-dígitos e limita a 14 dígitos', () => {
    expect(cnpjMask('12.345.678/9012-34')).toBe('12.345.678/9012-34')
    expect(cnpjMask('12345678901234567890')).toBe('12.345.678/9012-34')
    expect(cnpjMask('a1b2c3')).toBe('12.3')
  })
})

describe('useInputMask.parseCurrency', () => {
  it('com vírgula decimal, pontos são milhares', () => {
    expect(parseCurrency('R$ 1.234,56')).toBe(1234.56)
    expect(parseCurrency('1.234,56')).toBe(1234.56)
  })

  it('sem vírgula, um ponto com duas casas decimais é decimal (99.90)', () => {
    expect(parseCurrency('99.90')).toBe(99.9)
  })

  it('sem vírgula e sem decimal final, pontos são milhares', () => {
    expect(parseCurrency('1234')).toBe(1234)
    expect(parseCurrency('1.234')).toBe(1234)
    expect(parseCurrency('R$ 10')).toBe(10)
  })

  it('entrada vazia ou sem número devolve 0 em vez de NaN', () => {
    expect(parseCurrency('')).toBe(0)
    expect(parseCurrency('abc')).toBe(0)
    expect(parseCurrency('R$')).toBe(0)
  })
})

describe('useInputMask.currencyMask', () => {
  it('normaliza o espaço não-separável que toLocaleString insere após R$', () => {
    const resultado = currencyMask('1234.56')
    expect(resultado).toBe('R$ 1.234,56') // NBSP vira espaço normal
    expect(resultado).not.toContain(' ')
  })

  it('entrada sem número devolve string vazia', () => {
    expect(currencyMask('abc')).toBe('')
  })
})

describe('useInputMask — moeda em digitação', () => {
  const { moedaDigitada, moedaFormatada } = useInputMask()

  /** Simula o v-model: o texto exibido volta como entrada a cada tecla. */
  function digitar(teclas: string): string[] {
    let campo = ''
    const passos: string[] = []
    for (const tecla of teclas) {
      campo = moedaFormatada(moedaDigitada(campo + tecla))
      passos.push(campo)
    }
    return passos
  }

  it('cada dígito digitado é um centavo', () => {
    expect(digitar('150')).toEqual(['R$ 0,01', 'R$ 0,15', 'R$ 1,50'])
  })

  it('digitar 150,90 chega em R$ 150,90 — a vírgula digitada é ignorada', () => {
    // O defeito anterior produzia "R$ 1,010,90" aqui: a máscara formatava como
    // moeda completa a cada tecla e o dígito seguinte caía depois da vírgula.
    const passos = digitar('150,90')
    expect(passos[passos.length - 1]).toBe('R$ 150,90')
  })

  it('valor grande agrupa milhar', () => {
    expect(moedaFormatada(moedaDigitada('123456'))).toBe('R$ 1.234,56')
  })

  it('apagar dígito reduz o valor de forma previsível', () => {
    // "R$ 1,50" com o último caractere apagado → dígitos "15" → R$ 0,15
    expect(moedaFormatada(moedaDigitada('R$ 1,5'))).toBe('R$ 0,15')
  })

  it('campo vazio e entrada sem dígito devolvem vazio', () => {
    expect(moedaFormatada(moedaDigitada(''))).toBe('')
    expect(moedaFormatada(moedaDigitada('R$'))).toBe('')
  })

  it('formatação é estável: reformatar o próprio resultado não muda o valor', () => {
    const uma = moedaFormatada(moedaDigitada('150'))
    expect(moedaFormatada(moedaDigitada(uma))).toBe(uma)
  })
})
