## Why

A Caixa Postal DET repete o mesmo aviso (mesmo assunto) para dezenas de clientes; a lista plana em `/f/det` vira um bloco longo onde o escritório não enxerga *quais tipos* de comunicado chegaram nem quantos clientes cada um atingiu. Agrupar por assunto responde isso de relance.

## What Changes

- Na seção "Mensagens" de `/f/det`, a visualização padrão passa a ser **agrupada por assunto**: uma linha por assunto, com quantidade de mensagens, quantidade de clientes e envio mais recente, expansível para as mensagens do grupo.
- Novo controle de 2 botões (segmentado) para alternar entre **Agrupado** (padrão) e **Lista** (a tabela plana atual, inalterada).
- Leitura do texto da mensagem (modal) e filtro por cliente continuam funcionando nos dois modos.
- Somente frontend: agrupamento feito no cliente sobre o que a consulta de mensagens já devolve. Sem mudança de API, banco ou agente.

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `visualizacao-mensagens-det`: a lista de mensagens passa a ter dois modos de visão, com o agrupado por assunto como padrão.

## Impact

- `ContabOne.Frontend/src/components/det/MensagensDet.vue` (e, se extraído, um componente de alternância de visão reutilizável).
- Testes Vitest do componente. Sem impacto em `ContabOne.Api`, agentes ou contratos C#/Python.
