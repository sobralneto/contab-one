## Purpose

Permite que a plataforma corrija o protocolo de coleta do Portal Nacional NFS-e (URLs, limites de filtro, parâmetros de paginação e expressões de parsing) publicando uma nova versão do bundle de regras, sem redistribuir o executável instalado em cada escritório.

## Requirements

### Requirement: Toda instalação nasce com uma regra de coleta ativa

O sistema DEVE (MUST) garantir que exista uma versão ativa do bundle de regras a partir da primeira inicialização do banco, sem depender de publicação manual.

#### Scenario: Ambiente novo é inicializado

- **WHEN** o banco de dados de um ambiente novo é migrado pela primeira vez
- **THEN** existe uma `RegraColeta` versão 1 marcada como ativa, cujo conteúdo é aceito pela validação de schema do agente

#### Scenario: Agente consulta regras em ambiente recém-criado

- **WHEN** um agente faz handshake em um ambiente que nunca publicou regra manualmente
- **THEN** o handshake informa `regrasVersaoAtual` maior que zero e o agente consegue baixar o bundle

### Requirement: Publicação valida o schema do bundle

O sistema DEVE (MUST) rejeitar a publicação de um bundle que não satisfaça o schema esperado pelo agente, mesmo quando o conteúdo for JSON sintaticamente válido.

O schema exige: `portal.urlLogin`, `portal.urlNotas` e `portal.urlApiXml` como URLs `https://`; `portal.maxDiasFiltro` inteiro entre 1 e 366; `portal.paramPagina` string não-vazia; `portal.listagens.recebidas` e `portal.listagens.emitidas`, cada uma com `rota` não-vazia, `executar` booleano e `colunas` como lista não-vazia de strings; e `parsing.regexChave`, `parsing.regexLinha` e `parsing.regexTotalRegistros` como expressões regulares válidas e não-vazias.

#### Scenario: Admin publica bundle fora do schema

- **WHEN** o admin publica um conteúdo que é JSON válido mas viola o schema
- **THEN** a publicação é rejeitada com a lista de campos problemáticos, e a versão ativa anterior permanece intacta

#### Scenario: Admin publica bundle válido

- **WHEN** o admin publica um conteúdo que satisfaz o schema completo
- **THEN** a nova versão é criada como ativa e a versão anterior é marcada como inativa

#### Scenario: Bundle com expressão regular inválida

- **WHEN** o admin publica um bundle cujo `parsing.regexChave` não compila como expressão regular
- **THEN** a publicação é rejeitada identificando o campo e o erro de compilação

### Requirement: Numeração de versão nunca colide

O sistema DEVE (MUST) derivar o número da nova versão a partir de todas as versões já publicadas, e não apenas das ativas, de forma que a numeração seja sempre crescente e única.

#### Scenario: Publicação após rollback manual

- **WHEN** a regra ativa é desativada fora do fluxo de publicação e o admin publica uma nova versão
- **THEN** a nova versão recebe um número maior que o de qualquer versão já existente, sem violação de unicidade

#### Scenario: Número exibido na tela corresponde ao publicado

- **WHEN** o admin abre a tela de regras
- **THEN** o número de versão anunciado na tela é o mesmo que o servidor atribuirá à publicação

### Requirement: Editor de regras parte do bundle vigente

A tela de publicação DEVE (MUST) apresentar o conteúdo da versão ativa como ponto de partida editável, em vez de um campo vazio.

#### Scenario: Admin abre a tela de regras

- **WHEN** o admin acessa a tela de regras de coleta e existe uma versão ativa
- **THEN** o editor exibe o conteúdo dessa versão formatado, pronto para ser ajustado

#### Scenario: Admin edita o bundle para um estado inválido

- **WHEN** o admin altera o conteúdo do editor de forma que ele deixe de satisfazer o schema
- **THEN** a tela indica quais campos estão inválidos e o botão de publicar fica indisponível

### Requirement: Agente preserva a versão em uso diante de bundle ruim

O agente DEVE (MUST) manter a última versão válida conhecida quando o bundle recebido do servidor não passar na validação de schema, ou quando o download falhar.

#### Scenario: Servidor entrega bundle inválido

- **WHEN** o agente baixa um bundle que não satisfaz o schema
- **THEN** o agente registra o motivo em log, descarta o bundle recebido e continua a execução com a versão anterior
