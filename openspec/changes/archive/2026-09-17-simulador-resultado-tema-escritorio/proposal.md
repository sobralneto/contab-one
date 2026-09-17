## Why

Hoje o Simulador Simples Nacional (`/simulador`) mostra os três cartões de
entrada (Identificação, Anexo, Faturamento) e o resultado inteiro — alerta,
indicadores, tabelas semestrais e gráfico — sempre visíveis e recalculados a
cada tecla; o botão "Calcular imposto estimado" só rola a tela até lá. No uso
real isso é cedo demais e visualmente pesado: o usuário quer preencher os
dados primeiro, numa tela enxuta, e só ver o resultado quando pedir.

Ao mesmo tempo, o resultado perdeu a identidade visual do documento original
(`formulario_simples_nacional.html`, com o cabeçalho "L&J Contabilidade" e o
acento vermelho-vinho) quando a simulação entrou no painel — hoje ele usa as
cores neutras do design system para todo escritório. A ferramenta de
apuração do PGDAS-D já resolve exatamente esse problema para a dashboard de
um cliente: a identidade visual (neutra, L&J ou MUDAHR) vem do cadastro do
escritório (`Escritorio.LayoutDashboard`), não do tema do painel. Esta
mudança aplica a mesma regra ao resultado do Simulador — que reaproveita o
mesmo leiaute que o formulário original tinha para o escritório L&J, mas
agora dirigido pelo cadastro, e disponível para os três leiautes.

## What Changes

- A página `/simulador` passa a mostrar, na abertura, **só** os três
  cartões de entrada (Identificação, Anexo da atividade, Faturamento) e a
  toolbar já existente (Limpar formulário, Repetir mês 1 em todos, Salvar
  simulação, Calcular imposto estimado). O bloco de resultado fica oculto.
- Clicar em **"Calcular imposto estimado"** revela o resultado pela primeira
  vez (e rola a tela até ele, como já acontece). Depois de revelado, o
  resultado continua acompanhando o preenchimento em tempo real — a
  visibilidade muda, o recálculo reativo não.
- Reabrir uma simulação salva pelo histórico (`?id=...`) também revela o
  resultado direto, sem exigir um clique a mais: já existe o que mostrar.
- O bloco de resultado, quando visível, DEVE reordenar-se conforme o
  documento original: identificação (nome/CNPJ) primeiro, dados do anexo
  logo abaixo, cartões totalizadores, rótulo **"1º Semestre — 1º ao 6º mês
  de atividade"** com a tabela do primeiro semestre, rótulo **"2º Semestre —
  7º ao 12º mês de atividade"** com a tabela do segundo, o gráfico, e por
  fim o aviso `<small>` centralizado: "Simulação de caráter estimativo ·
  valores em centavos, sem arredondamento · não substitui apuração oficial
  via PGDAS-D" — texto literal do documento original.
- O bloco de resultado passa a adotar a **identidade visual do escritório da
  sessão** (neutra/L&J/MUDAHR, `Escritorio.LayoutDashboard`) — mesma fonte
  de dado e mesmas três identidades já usadas pela dashboard de apuração do
  PGDAS-D (`apuracao-simples-nacional`), com a cor de fundo, a cor dos
  cartões, bordas e acento do leiaute escolhido. Diferente da dashboard de
  apuração (documento entregue ao cliente, exportado como HTML/PDF), aqui é
  navegação interna comum do painel: sem exportação, sem iframe, o resultado
  continua um bloco Vue normal, só que retemado.
- O módulo de paletas (`TEMAS`/`temaPorCodigo`), hoje só de
  `features/pgdas/dashboard/`, muda de lugar para uma pasta neutra
  compartilhada — a simulação não fala com o produto PGDAS-D (decisão já
  registrada na change anterior), então não pode importar de dentro da
  pasta dele para pegar cor.

## Capabilities

### Modified Capabilities

- `simulacao-simples-nacional`: o resultado passa a ficar oculto até o
  primeiro cálculo (ou até a reabertura de uma simulação salva), reordena a
  identificação para antes dos dados do anexo, ganha os rótulos de semestre
  e o aviso final, e adota a identidade visual do escritório da sessão em
  vez das cores neutras do painel.

`apuracao-simples-nacional` não muda de requisito — a dashboard de apuração
continua exatamente como está. O único ponto de contato é implementação: o
módulo de paletas que ela usa muda de pasta (ver Impact), sem alterar o
comportamento que aquela capability já documenta.

## Impact

- **API**: novo endpoint `GET /api/simulador/layout` (`Features/Simulador`),
  devolvendo o `LayoutDashboard` do escritório da sessão — sem isso o
  frontend não tem como saber a identidade do escritório fora do fluxo de
  apuração de um cliente específico. `RequireAuthorization
  ("EscritorioUsuario")`, mesmo grupo `/api/simulador` já existente.
- **Frontend**: `src/features/pgdas/dashboard/temas.ts` (+ spec) muda para
  `src/features/identidade-escritorio/temas.ts`, com `PgdasDashboardView.vue`
  ajustando o import — conteúdo idêntico, só de lugar.
  `src/api/endpoints/simulador.ts` ganha `obterLayoutSimulador()`.
  `SimuladorView.vue` ganha o estado de "resultado revelado", a
  reordenação do cabeçalho, os rótulos de semestre, o aviso final e a
  aplicação do tema via variáveis CSS locais ao bloco de resultado — sem
  tocar nos tokens globais (`tokens.css`) nem no modo escuro do painel.
- **Sem impacto** em `Cliente`, no cálculo (`calcular.ts`), na persistência
  (`SalvarSimulacaoRequest` não muda) nem no histórico.
