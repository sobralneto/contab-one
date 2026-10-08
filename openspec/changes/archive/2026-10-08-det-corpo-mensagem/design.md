## Context

`Det.Agent` já captura o texto de cada mensagem não lida
(`caixa_postal._ler_corpo_mensagem`, campo `corpo` do JSON local), mas
`api_client._traduzir_mensagens` não o envia, e `MensagemDet` não tem onde
guardá-lo. A situação (`Situacao`) faz o caminho inverso: viaja, é gravada e
aparece numa coluna do painel, mas reflete só o instante da coleta.

## Goals / Non-Goals

**Goals:**

- O texto da mensagem chega ao painel.
- A situação some das três camadas.

**Non-Goals:**

- Mudar se ou quando o robô abre a mensagem no portal
  (`ler_corpo_mensagens` continua como está).
- Busca por texto, paginação da lista ou marcação de "tratada" no painel.
- Remover `situacao` do JSON local do agente: ele é a evidência crua do que
  a linha do portal mostrava e não vai para lugar nenhum.

## Decisions

### D1. `Corpo` é uma coluna `text` em `MensagensDet`, devolvida já na listagem

A lista é por escritório e pequena (dezenas de mensagens por execução), e o
texto é de poucos parágrafos. Devolver o texto junto evita um segundo
endpoint e um segundo pedido por clique. Se o volume crescer, separar o
detalhe é uma mudança local em `DetEndpoints`.

### D2. Limite de tamanho no servidor

O handler corta o texto em 20.000 caracteres. O agente é autenticado, mas é
entrada externa: sem teto, uma chave comprometida gravaria megabytes por
linha. Cortar é melhor que recusar, porque recusar perderia a mensagem
inteira por causa de um texto longo.

### D3. A coluna `Situacao` é removida, não só ignorada

Uma migration única adiciona `Corpo` e remove `Situacao`. Manter a coluna
"por via das dúvidas" deixaria dado morto que alguém voltaria a exibir. O
valor já gravado é descartado de propósito.

### D4. Compatibilidade com o agente já instalado

`MensagemDetRequest` perde a propriedade `Situacao`. O `System.Text.Json`
ignora propriedade desconhecida por padrão, então um `det.exe` antigo que
ainda mande `situacao` segue aceito, e um agente novo falando com uma API
antiga só não tem o `corpo` gravado. A ordem de deploy fica livre.

### D5. No painel, o texto abre num modal a partir de uma ação na linha

A tabela ganha a coluna de ações (`.col-actions`) com um botão "Ler
mensagem", e o texto abre no modal compartilhado (`.modal-overlay` /
`.modal-card`), com `white-space: pre-wrap` para preservar as quebras de
linha. Expandir a linha na própria tabela foi descartado: textos longos
empurrariam a lista e quebrariam a leitura das colunas.

## Risks / Trade-offs

- [O texto de mensagens trabalhistas passa a ficar no banco da plataforma.]
  → É a exceção que `MensagemDet` já declara, estendida ao texto; o
  isolamento por escritório (query filter global) cobre a coluna nova sem
  mudança, e `IsolamentoTest` continua sendo a guarda.
- [O texto pode conter dado pessoal de empregado.] → Mesmo tratamento do
  resto da entidade: só o escritório dono vê. Não entra em log da API.
- [Mensagens já gravadas ficam sem texto.] → A página diz "texto não
  capturado" para elas. Não há como recuperar: no portal já constam como
  lidas e o robô só lê as não lidas.
