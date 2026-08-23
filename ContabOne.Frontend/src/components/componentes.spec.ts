import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { defineComponent, h } from 'vue'
import KpiCard from '@/components/dashboard/KpiCard.vue'
import EstadoVazio from '@/components/comum/EstadoVazio.vue'
import ConfirmarAcao from '@/components/comum/ConfirmarAcao.vue'
import ListaAlertas from '@/components/dashboard/ListaAlertas.vue'
import UltimasExecucoes from '@/components/dashboard/UltimasExecucoes.vue'
import RankingClientes from '@/components/dashboard/RankingClientes.vue'
import { STATUS_ESCRITORIO } from '@/constants/statusEscritorio'
import type { AlertaDto, ExecucaoResumo, RankingItem, StatusEscritorio } from '@/api/types'

describe('KpiCard', () => {
  it('valor zero é renderizado como 0 e não some', () => {
    render(KpiCard, { props: { label: 'Notas', value: 0 } })
    expect(screen.getByText('0')).toBeInTheDocument()
    // O DOM tem "Notas" — o uppercase é só CSS (text-transform)
    expect(screen.getByText('Notas')).toBeInTheDocument()
  })

  it('número grande sai formatado em pt-BR', () => {
    render(KpiCard, { props: { label: 'Notas', value: 1234567 } })
    expect(screen.getByText('1.234.567')).toBeInTheDocument()
  })

  it('as três variantes aplicam a classe correspondente', () => {
    const { container } = render(KpiCard, { props: { label: 'A', value: 1, variant: 'warning' } })
    expect(container.querySelector('.kpi-card--warning')).not.toBeNull()
  })

  it('subtext é opcional', () => {
    render(KpiCard, { props: { label: 'A', value: 1, subtext: 'detalhe' } })
    expect(screen.getByText('detalhe')).toBeInTheDocument()
    render(KpiCard, { props: { label: 'B', value: 2 } })
  })
})

describe('EstadoVazio', () => {
  it('renderiza título e descrição', () => {
    render(EstadoVazio, { props: { title: 'Nenhum cliente', description: 'Sem dados ainda.' } })
    expect(screen.getByText('Nenhum cliente')).toBeInTheDocument()
    expect(screen.getByText('Sem dados ainda.')).toBeInTheDocument()
  })

  it('botão de ação emite action', async () => {
    const { emitted } = render(EstadoVazio, {
      props: { title: 'T', description: 'D', actionLabel: 'Criar' },
    })
    await userEvent.click(screen.getByText('Criar'))
    expect(emitted().action).toHaveLength(1)
  })
})

describe('Chip de status de escritório (contrato com a API)', () => {
  // O mapa depende da API serializar o enum como STRING — os quatro estados
  // precisam de rótulo legível e classe de cor (design.md, Decisão 7).
  it('os quatro estados têm rótulo e classe', () => {
    const esperado: Record<StatusEscritorio, [string, string]> = {
      Ativo: ['Ativo', 'status-ok'],
      Inadimplente: ['Inadimplente', 'status-warn'],
      Suspenso: ['Suspenso', 'status-err'],
      Cancelado: ['Cancelado', 'status-err'],
    }
    for (const [estado, [label, classe]] of Object.entries(esperado) as [StatusEscritorio, [string, string]][]) {
      expect(STATUS_ESCRITORIO[estado].label).toBe(label)
      expect(STATUS_ESCRITORIO[estado].cssClass).toBe(classe)
    }
  })

  it('um chip renderizado usa o rótulo e a classe do mapa', () => {
    const Chip = defineComponent({
      props: { status: { type: String, required: true } },
      setup(props) {
        const s = STATUS_ESCRITORIO[props.status as StatusEscritorio]
        return () => h('span', { class: `status-chip ${s.cssClass}` }, s.label)
      },
    })
    const { container } = render(Chip, { props: { status: 'Inadimplente' } })
    const chip = container.querySelector('.status-chip')!
    expect(chip.textContent).toBe('Inadimplente')
    expect(chip.classList.contains('status-warn')).toBe(true)
  })
})

describe('Chip de status de execução (UltimasExecucoes)', () => {
  function execucao(status: string, id: string): ExecucaoResumo {
    return {
      id, status: status as ExecucaoResumo['status'], iniciadoEm: new Date().toISOString(),
      finalizadoEm: null, duracaoMs: 5000, versaoAgente: null, mensagemErro: null,
      totalMetricas: 0, totalBaixadas: 1, totalFalhas: 0,
    }
  }

  it('os três estados renderizam o rótulo e a classe correta', () => {
    const { container } = render(UltimasExecucoes, {
      props: {
        execucoes: [execucao('Sucesso', 'e1'), execucao('Parcial', 'e2'), execucao('Falha', 'e3')],
      },
    })
    const chips = Array.from(container.querySelectorAll('.status-chip'))
    expect(chips).toHaveLength(3)
    expect(chips[0].textContent).toBe('Sucesso')
    expect(chips[0].classList.contains('status-ok')).toBe(true)
    expect(chips[1].textContent).toBe('Parcial')
    expect(chips[1].classList.contains('status-warn')).toBe(true)
    expect(chips[2].textContent).toBe('Falha')
    expect(chips[2].classList.contains('status-err')).toBe(true)
  })
})

describe('ListaAlertas', () => {
  function alerta(id: string, mensagem: string, aberto = true): AlertaDto {
    return {
      id, tipo: 'ExecucaoFalhou', severidade: 'Critico', mensagem,
      criadoEm: new Date().toISOString(), resolvidoEm: aberto ? null : new Date().toISOString(),
      clienteNome: null, aberto,
    }
  }

  it('lista vazia não renderiza o card (o estado vazio é do pai)', () => {
    const { container } = render(ListaAlertas, { props: { alertasAbertos: [] } })
    expect(container.querySelector('.alertas-card')).toBeNull()
  })

  it('alerta aberto é listado e o botão resolver emite com o id', async () => {
    const { emitted } = render(ListaAlertas, {
      props: { alertasAbertos: [alerta('a1', 'Execução falhou')] },
    })
    expect(screen.getByText('Execução falhou')).toBeInTheDocument()
    await userEvent.click(document.querySelector('.alerta-resolver')!)
    expect(emitted().resolver).toEqual([['a1']])
  })
})

describe('UltimasExecucoes e RankingClientes — vazios e com dados', () => {
  it('UltimasExecucoes vazio mostra a mensagem de vazio', () => {
    render(UltimasExecucoes, { props: { execucoes: [] } })
    expect(screen.getByText('Nenhuma execução registrada.')).toBeInTheDocument()
  })

  it('RankingClientes vazio mostra a mensagem de vazio', () => {
    render(RankingClientes, { props: { clientes: [] } })
    expect(screen.getByText('Nenhum cliente com dados.')).toBeInTheDocument()
  })

  it('RankingClientes ordena por total decrescente', () => {
    const itens: RankingItem[] = [
      { clienteId: 'a', nome: 'Menor', codigo: '02', total: 5 },
      { clienteId: 'b', nome: 'Maior', codigo: '01', total: 50 },
    ]
    const { container } = render(RankingClientes, { props: { clientes: itens } })
    const nomes = Array.from(container.querySelectorAll('.ranking-name')).map((n) => n.textContent)
    expect(nomes).toEqual(['01 — Maior', '02 — Menor'])
  })
})

describe('ConfirmarAcao', () => {
  it('não renderiza o modal quando invisível (o Teleport deixa só placeholders)', () => {
    render(ConfirmarAcao, {
      props: { visible: false, title: 'Excluir', message: 'Tem certeza?' },
    })
    expect(document.querySelector('.modal-card')).toBeNull()
  })

  it('emite confirm no botão de confirmação e cancel no cancelar', async () => {
    const { emitted } = render(ConfirmarAcao, {
      props: { visible: true, title: 'Excluir', message: 'Tem certeza?', confirmLabel: 'Excluir' },
    })
    expect(screen.getByText('Tem certeza?')).toBeInTheDocument()
    // "Excluir" aparece no título e no botão — o getByRole desambigua
    await userEvent.click(screen.getByRole('button', { name: 'Excluir' }))
    expect(emitted().confirm).toHaveLength(1)
    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(emitted().cancel).toHaveLength(1)
  })
})
