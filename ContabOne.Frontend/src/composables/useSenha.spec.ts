import { describe, it, expect } from 'vitest'
import { useSenha } from './useSenha'

const { avaliarForca, gerarSenha } = useSenha()

describe('useSenha — avaliarForca', () => {
  it('senha vazia não tem rótulo nem pontuação', () => {
    const forca = avaliarForca('')
    expect(forca.pontuacao).toBe(0)
    expect(forca.rotulo).toBe('')
    expect(forca.valida).toBe(false)
  })

  it('aponta exatamente quais requisitos faltam', () => {
    const forca = avaliarForca('abc')
    expect(forca.requisitos).toEqual({
      comprimento: false,
      maiuscula: false,
      minuscula: true,
      numero: false,
    })
  })

  it('senha longa sem maiúscula nem número não passa de fraca', () => {
    // O caso que motiva o teto: sem ele, uma senha longa de minúsculas
    // apareceria como forte e seria recusada pela API depois da entrega.
    const forca = avaliarForca('abcdefghijklmnopqrst')
    expect(forca.valida).toBe(false)
    expect(forca.rotulo).toBe('Fraca')
    expect(forca.pontuacao).toBeLessThanOrEqual(2)
  })

  it('senha que atende o mínimo do Identity é média', () => {
    const forca = avaliarForca('Senha123')
    expect(forca.valida).toBe(true)
    expect(forca.rotulo).toBe('Média')
  })

  it('senha válida e longa é forte', () => {
    const forca = avaliarForca('SenhaMuitoLonga123')
    expect(forca.valida).toBe(true)
    expect(forca.rotulo).toBe('Forte')
    expect(forca.pontuacao).toBe(4)
  })

  it('exige os quatro requisitos para ser válida', () => {
    expect(avaliarForca('senha123').valida).toBe(false) // sem maiúscula
    expect(avaliarForca('SENHA123').valida).toBe(false) // sem minúscula
    expect(avaliarForca('SenhaSemNumero').valida).toBe(false) // sem número
    expect(avaliarForca('Senh12').valida).toBe(false) // curta demais
  })
})

describe('useSenha — gerarSenha', () => {
  it('gera senha do tamanho pedido', () => {
    expect(gerarSenha(16)).toHaveLength(16)
    expect(gerarSenha(24)).toHaveLength(24)
  })

  it('nunca gera abaixo do mínimo aceito pela API', () => {
    expect(gerarSenha(4).length).toBeGreaterThanOrEqual(8)
  })

  it('toda senha gerada passa na própria validação', () => {
    // Repetido porque o sorteio é aleatório: uma execução isolada poderia
    // passar por sorte mesmo com a garantia de classes quebrada.
    for (let i = 0; i < 200; i++) {
      const senha = gerarSenha()
      expect(avaliarForca(senha).valida, `senha gerada inválida: ${senha}`).toBe(true)
    }
  })

  it('não usa caracteres ambíguos (I, l, O, 0, 1)', () => {
    for (let i = 0; i < 100; i++) {
      expect(gerarSenha()).not.toMatch(/[IlO01]/)
    }
  })

  it('gera senhas diferentes a cada chamada', () => {
    const geradas = new Set(Array.from({ length: 50 }, () => gerarSenha()))
    expect(geradas.size).toBe(50)
  })
})
