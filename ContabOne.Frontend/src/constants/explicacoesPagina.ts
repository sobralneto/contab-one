import type { Papel } from '@/api/types'

/**
 * Texto que abre na primeira visita de cada página.
 *
 * Duas famílias de chave:
 * - Rota de ferramenta (`/f/:produto/...`): `${produtoCodigo}.${pagina}`
 *   (ex.: `nfse.clientes`), com fallback para `${pagina}` sozinho
 *   (`clientes`) quando não há texto específico daquela ferramenta — é
 *   assim que uma ferramenta nova (DET, e as que vierem depois) herda o
 *   texto genérico de "Clientes" sem precisar de entrada própria.
 * - Rota transversal (usuários, admin/*): o `name` da rota, como sempre foi.
 *
 * `visao-geral` é o texto genérico do dashboard — a chave era `dashboard`
 * antes da rota virar `/f/:produto`.
 *
 * O componente ExplicacaoPagina lê deste mapa e é montado uma única vez no
 * AppLayout, então nenhuma view precisa ser alterada para ganhar explicação.
 *
 * Rotas do layout de autenticação (login, troca de senha) ficam de fora de
 * propósito: não são "a aplicação" e o layout delas nem monta o componente.
 */
export interface ExplicacaoPagina {
  titulo: string
  paragrafos: string[]
  /** Complemento mostrado só para o papel indicado. */
  notaPorPapel?: Partial<Record<Papel, string>>
}

export const EXPLICACOES_PAGINA: Record<string, ExplicacaoPagina> = {
  'visao-geral': {
    titulo: 'Visão geral',
    paragrafos: [
      'A visão geral do que o agente coletou: quantas notas foram baixadas no mês, quantos clientes estão cadastrados e quantos agentes estão ativos.',
      'Os alertas avisam sobre certificado perto de vencer, execução que falhou e agente que parou de dar sinal. Vale olhar aqui primeiro no começo do dia.',
    ],
    notaPorPapel: {
      PlatformAdmin: 'Como admin da plataforma, os números somam todos os escritórios.',
    },
  },

  clientes: {
    titulo: 'Clientes',
    paragrafos: [
      'As empresas cujas notas o agente baixa — os clientes do seu escritório, cada uma com seu próprio certificado digital.',
      'Um cliente pode aparecer aqui sozinho: quando o agente encontra um certificado novo na máquina, ele cadastra a empresa automaticamente. A coluna de origem mostra se veio do agente ou de cadastro manual.',
      'Fique de olho na validade do certificado: vencido, a coleta daquela empresa para.',
    ],
  },

  execucoes: {
    titulo: 'Execuções',
    paragrafos: [
      'Cada rodada do agente vira uma linha aqui: quando começou, quanto tempo levou, quantas notas baixou e o que falhou.',
      'Abrir uma execução mostra o detalhe por cliente e por competência — é onde você descobre qual empresa especificamente deu problema.',
    ],
  },

  agentes: {
    titulo: 'Agentes',
    paragrafos: [
      'O agente é o programa que roda na máquina do escritório e faz a coleta. Cada máquina precisa da própria chave.',
      'A chave aparece uma única vez, no momento em que é gerada. Se ela se perder, o caminho é revogar e gerar outra.',
      'Revogar bloqueia aquela máquina no próximo contato com o servidor.',
    ],
  },

  configuracao: {
    titulo: 'Configuração',
    paragrafos: [
      'Ajustes que valem para todo o escritório, como o período padrão de busca das notas.',
      'O que você muda aqui chega ao agente no próximo contato dele com o servidor — não é preciso mexer na máquina.',
    ],
  },

  usuarios: {
    titulo: 'Usuários',
    paragrafos: [
      'Quem tem acesso a este painel. O papel define o que a pessoa enxerga: quem é usuário acompanha, quem é admin também configura.',
      'A senha que você define ao cadastrar é provisória e aparece uma única vez — anote e entregue. A própria pessoa escolhe a definitiva no primeiro acesso.',
      'Para tirar o acesso de alguém, desative em vez de apagar: o histórico do que a pessoa fez continua de pé.',
    ],
  },

  'admin-escritorios': {
    titulo: 'Escritórios',
    paragrafos: [
      'Os escritórios de contabilidade que assinam a plataforma. Cada um é um cliente pagante, isolado dos demais.',
      'Cuidado com o status: marcar como inadimplente ou suspenso bloqueia os agentes daquele escritório no próximo contato com o servidor, e a coleta para.',
    ],
  },

  'admin-planos': {
    titulo: 'Planos',
    paragrafos: [
      'Os limites que cada plano impõe: quantos clientes e quantos agentes o escritório pode ter, e se ele pode coletar notas emitidas além das recebidas.',
      'Os limites são checados na hora de cadastrar — reduzir um plano não apaga o que já existe acima do teto.',
    ],
  },

  regras: {
    titulo: 'Regras de coleta',
    paragrafos: [
      'O pacote de regras que todos os agentes baixam para saber como conversar com o Portal Nacional.',
      'Esta é a tela de maior risco do sistema: publicar uma versão quebrada afeta a coleta de todos os escritórios de uma vez. Confira o conteúdo antes de publicar.',
      'Publicar cria uma versão nova e desativa a anterior, então dá para voltar atrás republicando o conteúdo antigo.',
    ],
  },

  // Genérico: qualquer ferramenta sem agente que precise de um assistente de
  // carga e conferência de documento herda este texto por padrão.
  importacao: {
    titulo: 'Importar extratos',
    paragrafos: [
      'Carregue o PDF do documento — a leitura acontece no seu navegador, nenhum arquivo sobe para o servidor.',
      'Confira os valores extraídos antes de gravar: é a única checagem entre o documento e o banco, então vale revisar as linhas marcadas em vermelho.',
      'Depois de gravado, o painel fica disponível na visão geral sem precisar carregar o PDF de novo.',
    ],
  },

  // pgdas.visao-geral sobrepõe o texto genérico de "visao-geral" (que fala de
  // agente e notas — não se aplica: PGDAS-D é a primeira ferramenta sem
  // agente do catálogo).
  'pgdas.visao-geral': {
    titulo: 'PGDAS-D — Apuração do Simples Nacional',
    paragrafos: [
      'As competências já gravadas, por cliente — faturamento, DAS e se o pagamento foi reconhecido.',
      'Pendências aparecem em destaque: DAS em aberto, linha em que a soma dos tributos não bate com o DAS informado, e sublimite estadual acima de 80%.',
      'O ícone de gráfico abre o painel completo daquele cliente, reconstruído a partir do que já está gravado — sem pedir arquivo nenhum.',
    ],
  },
}
