/**
 * Avaliação de força e geração de senha, compartilhadas pela tela de cadastro
 * de usuários e pela tela de troca obrigatória.
 *
 * Os requisitos espelham o Identity configurado em Program.cs (mínimo 8,
 * maiúscula, minúscula e número; caractere especial não é exigido). Ficam
 * duplicados aqui só para dar retorno imediato ao usuário — a API continua
 * sendo a autoridade e rejeita de novo no servidor.
 */

export interface RequisitosSenha {
  comprimento: boolean
  maiuscula: boolean
  minuscula: boolean
  numero: boolean
}

export interface ForcaSenha {
  /** 0 = vazia, 1–2 = fraca, 3 = média, 4 = forte. */
  pontuacao: number
  rotulo: '' | 'Fraca' | 'Média' | 'Forte'
  cssClass: '' | 'forca-fraca' | 'forca-media' | 'forca-forte'
  requisitos: RequisitosSenha
  /** True quando a senha passa em todos os requisitos da API. */
  valida: boolean
}

// Alfabetos sem caracteres ambíguos (I, l, O, 0, 1): a senha gerada é lida em
// voz alta ou digitada à mão na entrega para o usuário.
const MAIUSCULAS = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
const MINUSCULAS = 'abcdefghijkmnopqrstuvwxyz'
const NUMEROS = '23456789'

function inteiroAleatorio(limite: number): number {
  const buffer = new Uint32Array(1)
  crypto.getRandomValues(buffer)
  return buffer[0] % limite
}

export function useSenha() {
  function avaliarForca(senha: string): ForcaSenha {
    const requisitos: RequisitosSenha = {
      comprimento: senha.length >= 8,
      maiuscula: /[A-Z]/.test(senha),
      minuscula: /[a-z]/.test(senha),
      numero: /[0-9]/.test(senha),
    }

    const atendidos = Object.values(requisitos).filter(Boolean).length
    const valida = atendidos === 4

    let pontuacao = 0
    if (senha.length > 0) {
      // Enquanto falta requisito, a barra não passa de "fraca" — senão uma
      // senha longa só de minúsculas apareceria como forte e seria recusada
      // pela API depois de o admin já tê-la entregue.
      pontuacao = valida ? (senha.length >= 14 ? 4 : 3) : Math.min(atendidos, 2)
    }

    const rotulo = pontuacao === 0 ? '' : pontuacao <= 2 ? 'Fraca' : pontuacao === 3 ? 'Média' : 'Forte'
    const cssClass =
      pontuacao === 0 ? '' : pontuacao <= 2 ? 'forca-fraca' : pontuacao === 3 ? 'forca-media' : 'forca-forte'

    return { pontuacao, rotulo, cssClass, requisitos, valida }
  }

  /** Gera uma senha que já satisfaz todos os requisitos da API. */
  function gerarSenha(tamanho = 16): string {
    const efetivo = Math.max(tamanho, 8)
    const todos = MAIUSCULAS + MINUSCULAS + NUMEROS

    // Um de cada classe obrigatória primeiro; o sorteio livre do resto poderia
    // (com azar) não produzir nenhum número e gerar uma senha inválida.
    const caracteres = [
      MAIUSCULAS[inteiroAleatorio(MAIUSCULAS.length)],
      MINUSCULAS[inteiroAleatorio(MINUSCULAS.length)],
      NUMEROS[inteiroAleatorio(NUMEROS.length)],
    ]
    while (caracteres.length < efetivo) {
      caracteres.push(todos[inteiroAleatorio(todos.length)])
    }

    // Embaralha (Fisher-Yates) para as três primeiras posições não terem
    // sempre a mesma classe de caractere.
    for (let i = caracteres.length - 1; i > 0; i--) {
      const j = inteiroAleatorio(i + 1)
      ;[caracteres[i], caracteres[j]] = [caracteres[j], caracteres[i]]
    }

    return caracteres.join('')
  }

  return { avaliarForca, gerarSenha }
}
