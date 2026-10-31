# apuracao-simples-nacional Specification

## Purpose

TBD

## Requirements

### Requirement: O documento do PGDAS-D não é enviado ao servidor

O sistema DEVE (MUST) extrair as competências do extrato ou da declaração do
PGDAS-D inteiramente no navegador do usuário. O arquivo PDF NÃO DEVE (MUST
NOT) ser transmitido à API, nem inteiro, nem em pedaços, nem como texto
bruto — a API recebe apenas os valores de apuração já conferidos.

É a mesma promessa que sustenta o agente: conteúdo fiscal de empresa de
terceiro não trafega para a plataforma.

#### Scenario: Usuário carrega um extrato

- **WHEN** o usuário seleciona ou arrasta um PDF do PGDAS-D na tela de
  importação
- **THEN** as competências são extraídas localmente e nenhuma requisição
  carrega o conteúdo do arquivo

#### Scenario: Documento ilegível

- **WHEN** o arquivo não é um documento do PGDAS-D reconhecível, ou nenhuma
  competência pôde ser extraída dele
- **THEN** o arquivo é marcado como não processado com o motivo, os demais
  arquivos do lote continuam sendo processados, e nada é enviado à API

### Requirement: A conferência precede a gravação

O sistema DEVE (MUST) exibir as competências extraídas em uma tela editável
antes de qualquer gravação, e DEVE (MUST) sinalizar cada competência em que a
soma dos oito tributos (IRPJ, CSLL, COFINS, PIS, INSS/CPP, ICMS, IPI, ISS)
divirja do DAS informado em mais de R$ 0,05.

A conferência é o único ponto de validação humana entre o documento e o
banco, e é o que torna aceitável um extrator acoplado a um leiaute que muda
sem aviso.

#### Scenario: Soma dos tributos diverge do DAS

- **WHEN** a soma dos oito tributos de uma competência difere do DAS
  informado em mais de R$ 0,05
- **THEN** a competência é sinalizada como divergente na tela de
  conferência, permanecendo editável

#### Scenario: Valor corrigido à mão

- **WHEN** o usuário altera um valor na conferência e a competência é gravada
- **THEN** a apuração fica registrada como editada manualmente

#### Scenario: Gravação sem passar pela conferência

- **WHEN** o usuário conclui a carga dos arquivos
- **THEN** nada é gravado até que ele confirme a conferência

### Requirement: Competência sem movimento é apuração válida

O sistema DEVE (MUST) tratar competência declarada sem receita e sem DAS a
recolher como uma apuração legítima, distinta de uma extração que falhou.
Competência sem movimento NÃO DEVE (MUST NOT) receber status de pagamento,
porque não há DAS a pagar.

#### Scenario: Mês sem receita

- **WHEN** o documento traz a linha da receita do período zerada e nenhum DAS
- **THEN** a competência aparece na conferência marcada como sem movimento,
  é gravada, e não recebe status de pagamento

#### Scenario: Extração incompleta

- **WHEN** o bloco não traz sequer a linha da receita do período de apuração
- **THEN** ele não vira competência, e o arquivo é reportado como não
  processado

### Requirement: Uma apuração por cliente e competência

O sistema DEVE (MUST) manter no máximo uma apuração por combinação de
escritório, cliente e competência. Gravação que colida com competência já
existente DEVE (MUST) ser recusada informando quais competências colidiram, e
só prosseguir mediante confirmação explícita de substituição.

Sobrescrever em silêncio apagaria correção feita à mão numa importação
anterior.

#### Scenario: Competência já gravada

- **WHEN** o usuário grava um lote que contém competência já existente para
  aquele cliente
- **THEN** a gravação é recusada, as competências em conflito são
  identificadas, e é indicado quais delas foram editadas manualmente

#### Scenario: Substituição confirmada

- **WHEN** o usuário confirma a substituição das competências em conflito
- **THEN** as apurações existentes são substituídas pelos valores do novo
  lote, junto com a segregação de receita correspondente

### Requirement: A dashboard é reconstruída a partir do banco

O sistema DEVE (MUST) permitir abrir a dashboard de apuração de um cliente
para um intervalo de competências usando apenas dados já gravados, sem exigir
que nenhum documento seja carregado de novo.

#### Scenario: Dashboard reaberta meses depois

- **WHEN** o usuário abre a dashboard de um cliente que teve competências
  gravadas em importações anteriores
- **THEN** o painel é montado com os valores gravados, sem pedir arquivo
  algum

#### Scenario: Cliente sem apuração no intervalo

- **WHEN** o intervalo pedido não tem nenhuma competência gravada
- **THEN** a tela informa a ausência de dados em vez de exibir um painel
  vazio ou com zeros

### Requirement: A visão geral lista uma apuração por cliente

A tela de visão geral do PGDAS-D DEVE (MUST) exibir a lista de apurações
agrupada por cliente: uma linha por cliente, com o nome do cliente e a
última competência importada dele, ordenada da competência mais recente
para a mais antiga. O ícone "Ver dashboard" DEVE (MUST) continuar
disponível na coluna de ações dessa tabela, comportando-se como hoje.

#### Scenario: Cliente com várias competências

- **WHEN** a lista é carregada e um cliente tem apurações de mais de uma
  competência
- **THEN** ele aparece em exatamente uma linha, com a última competência
  importada dele

#### Scenario: Ver dashboard permanece acessível

- **WHEN** o usuário clica no ícone "Ver dashboard" de uma linha
- **THEN** a navegação para a dashboard do cliente ocorre como antes da
  mudança

### Requirement: A sidebar mostra a identidade do cliente e o histórico de competências

Cada linha da lista DEVE (MUST) ter um ícone que, ao ser acionado, abre uma
sidebar à direita. A sidebar DEVE (MUST) exibir o "Demonstrativo Mensal de
Faturamento" do cliente, definido na capability `demonstrativo-faturamento`:
identificação do cliente (razão social, CNPJ, data de abertura e regime
tributário), faturamento mês a mês de dois anos-calendário com o total de
cada ano, nota sobre a declaração, local e data, e bloco de assinaturas. O
CNPJ DEVE (MUST) aparecer completo quando o cliente o tem, e mascarado quando
não tem.

A sidebar NÃO DEVE (MUST NOT) exibir mais a tabela operacional de competências
(DAS, vencimento, situação pago/aberto e pendências). Esses dados continuam na
lista principal e na dashboard do cliente.

A sidebar DEVE (MUST) carregar todas as competências do cliente, sem os
filtros de competência da lista principal. O demonstrativo cobre anos
inteiros, independentemente do intervalo filtrado na lista.

#### Scenario: Abrir a sidebar de um cliente

- **WHEN** o usuário aciona o ícone de detalhe de uma linha da lista
- **THEN** uma sidebar se abre à direita com o demonstrativo de faturamento do
  cliente e, no topo, as ações "Exportar PDF" e "Imprimir"

#### Scenario: Filtro da lista não recorta o demonstrativo

- **WHEN** a lista principal está filtrada de 2026-06 a 2026-08 e o usuário
  abre o detalhe de um cliente com apurações desde 2025-01
- **THEN** o demonstrativo mostra todos os meses gravados de 2025 e 2026

#### Scenario: Fechamento da sidebar

- **WHEN** o usuário fecha a sidebar ou aciona o detalhe de outro cliente
- **THEN** a sidebar fecha (ou muda para o novo cliente) e a lista principal
  permanece com os mesmos dados

### Requirement: A listagem carrega a identidade do cliente

A resposta de `GET /api/pgdas/apuracoes` DEVE (MUST) incluir, em cada
apuração:

- o código do cliente, o CNPJ mascarado dele e, quando existir, o CNPJ
  completo (`clienteCodigo`, `clienteCnpjMascarado`, `clienteCnpj`),
  provenientes das colunas já gravadas de `Cliente`;
- a data de abertura do cliente (`clienteDataAbertura`, `AAAA-MM-DD`), ou
  `null` quando não é conhecida;
- o Nº da Declaração da apuração (`numeroDeclaracao`), ou `null` quando não
  foi gravado.

#### Scenario: Listagem expõe a identidade

- **WHEN** o endpoint de listagem responde a uma requisição autenticada
- **THEN** cada item da resposta carrega `clienteCodigo` e
  `clienteCnpjMascarado`, mais `clienteCnpj` quando o cliente tem CNPJ
  completo gravado

#### Scenario: Listagem expõe data de abertura e nº da declaração

- **WHEN** o cliente tem data de abertura gravada e a apuração tem Nº da
  Declaração gravado
- **THEN** o item da resposta carrega `clienteDataAbertura` e
  `numeroDeclaracao` preenchidos

#### Scenario: Dados anteriores à mudança

- **WHEN** a apuração foi gravada antes desta mudança
- **THEN** o item da resposta traz `numeroDeclaracao` nulo (e
  `clienteDataAbertura` nulo se o cliente nunca recebeu essa data), sem erro

### Requirement: A extração captura a data de abertura e o Nº da Declaração

O extrator do PGDAS-D, no navegador, DEVE (MUST) ler de cada documento,
extrato ou declaração, quando presentes:

- a **data de abertura no CNPJ** da empresa (`dd/mm/aaaa`);
- o **Nº da Declaração** da competência (sequência de dígitos).

A ausência de um desses campos NÃO DEVE (MUST NOT) marcar o documento como
não processado nem bloquear a gravação. Os dois são opcionais.

#### Scenario: Documento com os dois campos

- **WHEN** o documento traz "Data de abertura no CNPJ: 28/12/2022" e
  "Nº da Declaração: 48992503202608001"
- **THEN** a competência extraída carrega a data de abertura `2022-12-28` e o
  número `48992503202608001`

#### Scenario: Documento sem os campos

- **WHEN** o documento não traz nem a data de abertura nem o Nº da Declaração
- **THEN** a competência é extraída normalmente, com os dois campos vazios

### Requirement: A gravação persiste a data de abertura e o Nº da Declaração

`POST /api/pgdas/apuracoes` DEVE (MUST) aceitar, opcionalmente:

- a data de abertura do cliente (`dataAberturaCliente`). Quando informada, é
  gravada em `Cliente.DataAbertura`, substituindo o valor anterior;
- o Nº da Declaração de cada apuração (`numeroDeclaracao`). É gravado em
  `ApuracaoSimples.NumeroDeclaracao` na criação e na substituição da
  competência.

Quando a data não é informada, a data já gravada no cliente DEVE (MUST) ser
mantida. O Nº da Declaração, se informado, DEVE (MUST) conter só dígitos, com
no máximo 30 caracteres. Fora disso, o pedido é recusado com erro de
validação.

#### Scenario: Gravação com os dois campos

- **WHEN** o lote é gravado com `dataAberturaCliente = 2022-12-28` e uma
  apuração com `numeroDeclaracao = 48992503202608001`
- **THEN** o cliente passa a ter data de abertura 28/12/2022 e a apuração
  passa a ter aquele número

#### Scenario: Gravação sem data de abertura

- **WHEN** o lote é gravado sem `dataAberturaCliente` para um cliente que já
  tem data de abertura
- **THEN** a data de abertura do cliente permanece a mesma

#### Scenario: Número da declaração inválido

- **WHEN** uma apuração chega com `numeroDeclaracao` contendo letras
- **THEN** a API responde com erro de validação e nada é gravado

### Requirement: A série mensal do documento alimenta a evolução de 12 meses

O sistema DEVE (MUST) persistir a série de receita bruta mensal que o próprio
documento traz, por cliente e competência, de modo que o gráfico de evolução
cubra também meses cujo documento nunca foi carregado.

O valor de um mês na série DEVE (MUST) seguir esta precedência:

- **Mês declarado pelo documento** (uma competência gravada como apuração no
  mesmo pedido): a receita declarada DEVE (MUST) sobrescrever o valor da
  série daquele mês, mesmo que ele tenha sido gravado antes pelo histórico de
  um documento de competência mais recente. É o caso da retificadora de uma
  competência antiga.
- **Mês que chega só pelo histórico de outro documento:** NÃO DEVE (MUST NOT)
  sobrescrever mês que tenha apuração gravada para o cliente. Para mês sem
  apuração gravada, quando o mesmo mês aparecer em documentos diferentes,
  prevalece o do documento de competência mais recente.

Assim, para todo mês com apuração gravada, a série mensal DEVE (MUST) ter a
mesma receita que o faturamento da apuração. A dashboard não pode mostrar um
valor nos cards e outro no gráfico de evolução para o mesmo mês.

#### Scenario: Mês sem documento carregado

- **WHEN** a dashboard de um cliente é montada e um dos doze meses da série
  não tem apuração gravada, mas aparece na série de um documento carregado
- **THEN** o gráfico de evolução exibe o faturamento daquele mês

#### Scenario: Mesmo mês em dois documentos

- **WHEN** dois documentos de competências diferentes trazem, só no histórico,
  o mesmo mês com valores distintos, e esse mês não tem apuração gravada
- **THEN** prevalece o valor do documento da competência mais recente

#### Scenario: Retificadora de competência antiga

- **WHEN** a série de março/2026 foi gravada pelo histórico do documento de
  08/2026, e depois o usuário importa a retificadora de 03/2026 e confirma a
  substituição da competência
- **THEN** a série de março/2026 passa a ter a receita declarada na
  retificadora, igual ao faturamento da apuração substituída

#### Scenario: Histórico de documento mais novo não desfaz a apuração

- **WHEN** março/2026 tem apuração gravada, e depois é importado um documento
  de 09/2026 cujo histórico traz março/2026 com outro valor
- **THEN** a série de março/2026 mantém o faturamento da apuração gravada

#### Scenario: Dados gravados antes da mudança

- **WHEN** a mudança é implantada, e um cliente tem um mês em que a série
  mensal e o faturamento da apuração divergem
- **THEN** a série daquele mês passa a ter o faturamento da apuração, sem que
  nenhum documento precise ser reimportado

### Requirement: A identidade visual da dashboard vem do escritório

O sistema DEVE (MUST) montar a dashboard com o leiaute escolhido para o
escritório da sessão no cadastro daquele escritório, entre três identidades
fixas: a neutra da plataforma, a da L&J e a da MUDAHR. Cada identidade define ao
mesmo tempo a paleta do documento e o logotipo estampado no cabeçalho.

O sistema DEVE (MUST) usar a identidade neutra da plataforma para escritório
cujo leiaute não esteja definido ou não seja reconhecido — nunca a identidade de
outro escritório.

O leiaute escolhido DEVE (MUST) valer igualmente para a dashboard exibida na
tela, para o HTML exportado e para o PDF, que são o mesmo documento. A
identidade visual DEVE (MUST) estar disponível junto com os dados que ela pinta,
sem estado intermediário em que o painel já apareceu e ainda vai trocar de
cores.

O leiaute da dashboard NÃO DEVE (MUST NOT) ser afetado pelo tema da
plataforma — inclusive o modo escuro —, porque é documento entregue ao
cliente final e precisa sair igual na tela e no PDF.

#### Scenario: Escritório com identidade própria

- **WHEN** o escritório tem o leiaute de uma das duas marcas escolhido no seu
  cadastro
- **THEN** a dashboard usa as cores e o logotipo dessa identidade

#### Scenario: Escritório sem identidade configurada

- **WHEN** o escritório está no leiaute neutro, ou seu leiaute não é reconhecido
- **THEN** a dashboard é montada com a identidade neutra da plataforma, sem
  erro e sem logotipo de outro escritório

#### Scenario: Plataforma em modo escuro

- **WHEN** o usuário está com a plataforma em modo escuro e abre a dashboard
- **THEN** a dashboard é exibida com as próprias cores, idêntica ao que será
  exportado

#### Scenario: Exportação mantém o leiaute

- **WHEN** o usuário exporta a dashboard de um escritório em leiaute de marca,
  em HTML ou em PDF
- **THEN** o arquivo sai com as mesmas cores e o mesmo logotipo vistos na tela

#### Scenario: Abertura sem piscar de identidade

- **WHEN** o usuário abre a dashboard de um cliente com apurações gravadas
- **THEN** o painel aparece já no leiaute do escritório, sem passar antes pelo
  neutro

#### Scenario: Tela de ausência de dados

- **WHEN** a dashboard é aberta para um cliente sem nenhuma apuração no
  intervalo
- **THEN** a tela que informa a ausência de dados também respeita o leiaute do
  escritório, em vez de cair no neutro por falta de apurações

### Requirement: O CNPJ completo é persistido e a dashboard o exibe quando disponível

Ao gravar uma competência a partir de um documento, o sistema DEVE (MUST)
persistir o CNPJ completo lido do documento no cliente correspondente, junto
com o hash de identificação e a versão mascarada.

A dashboard do cliente (`/f/pgdas/dashboard/{clienteId}`) DEVE (MUST) exibir
o CNPJ completo do cliente quando ele estiver disponível, e DEVE (MUST) cair
de volta para a versão mascarada quando não estiver. Nem todo cliente tem o
CNPJ completo disponível: os cadastrados antes desta mudança, e os só
sincronizados por um agente que ainda não envia o CNPJ completo, continuam
apenas com hash e máscara — não há como completá-los retroativamente.

A exportação em HTML e em PDF, por serem o mesmo documento que a tela (ver
"A identidade visual da dashboard vem do escritório"), seguem a mesma regra:
CNPJ completo quando disponível, máscara como fallback.

#### Scenario: Documento gravado para cliente com CNPJ completo disponível

- **WHEN** uma competência é gravada a partir de um documento cujo cliente já
  tem o CNPJ completo persistido
- **THEN** a dashboard desse cliente exibe o CNPJ completo

#### Scenario: Documento traz o CNPJ completo pela primeira vez

- **WHEN** uma competência é gravada a partir de um documento, e o CNPJ lido
  bate com um cliente que ainda não tinha o CNPJ completo persistido
- **THEN** o CNPJ completo passa a ser persistido nesse cliente

#### Scenario: Cliente sem CNPJ completo disponível

- **WHEN** a dashboard é montada para um cliente que só tem hash e máscara
  gravados, sem o CNPJ completo
- **THEN** a dashboard exibe a versão mascarada, sem erro

#### Scenario: Exportação segue a mesma regra de exibição

- **WHEN** o usuário exporta em HTML ou em PDF a dashboard de um cliente com
  CNPJ completo disponível
- **THEN** o arquivo exportado exibe o CNPJ completo, igual à tela

### Requirement: Apuração pertence ao escritório da sessão

O sistema DEVE (MUST) escopar apuração, segregação e série mensal ao
escritório da sessão, e NÃO DEVE (MUST NOT) aceitar escopo indicado no
pedido para usuário de escritório.

#### Scenario: Leitura de apuração de outro escritório

- **WHEN** um usuário de escritório pede apurações indicando outro escritório
- **THEN** ele recebe apenas as apurações do próprio escritório

#### Scenario: Gravação para cliente de outro escritório

- **WHEN** a gravação aponta para um cliente que não pertence ao escritório
  da sessão
- **THEN** a gravação é recusada e nenhuma apuração é criada

### Requirement: A visão geral filtra por cliente escolhido numa lista

A visão geral do PGDAS-D (`/f/pgdas`) DEVE (MUST) oferecer o filtro "Cliente"
como um campo de seleção (select), e NÃO DEVE (MUST NOT) mais oferecer um
campo de texto livre para buscar cliente. As opções DEVEM (MUST) ser:

- "Todos os clientes", selecionada por padrão, que não restringe a lista;
- um item por cliente do escritório da sessão que tenha ao menos uma
  apuração gravada, exibido como "código — nome" e ordenado por nome.

Escolher um cliente DEVE (MUST) recarregar a lista principal a partir do
servidor restrita a esse cliente (`GET /api/pgdas/apuracoes?clienteId=…`),
combinando com os filtros de competência inicial e final. O filtro de cliente
NÃO DEVE (MUST NOT) depender das apurações já carregadas em memória: um
cliente cujas apurações ficaram fora da amostra truncada da lista geral DEVE
(MUST) aparecer no select e, quando escolhido, ter suas apurações listadas.

Os indicadores do topo (KPIs do resumo) continuam refletindo o escritório
inteiro, independentemente do cliente escolhido. A sidebar de detalhe continua
carregando todas as competências do cliente, como definido em "A sidebar
mostra a identidade do cliente e o histórico de competências".

#### Scenario: Select lista os clientes com apuração

- **WHEN** o escritório tem os clientes "ALFA" e "BETA" com apurações gravadas
  e o cliente "GAMA" sem nenhuma apuração, e o usuário abre a visão geral
- **THEN** o filtro "Cliente" é um select com "Todos os clientes", "ALFA" e
  "BETA", nessa ordem, e não lista "GAMA"

#### Scenario: Padrão mostra todos

- **WHEN** o usuário abre a visão geral sem mexer no filtro
- **THEN** o select está em "Todos os clientes" e a lista mostra uma linha por
  cliente com apuração

#### Scenario: Escolher um cliente restringe a lista

- **WHEN** o usuário escolhe "ALFA" no select
- **THEN** a lista é recarregada do servidor com `clienteId` de ALFA e mostra
  só a linha de ALFA

#### Scenario: Cliente combinado com competência

- **WHEN** o usuário escolhe "ALFA" e define a competência de 2026-06 a 2026-08
- **THEN** a lista considera só as apurações de ALFA nesse intervalo, e mostra
  o estado vazio se ALFA não tem apuração nele

#### Scenario: Voltar para todos

- **WHEN** com "ALFA" escolhido, o usuário volta o select para "Todos os
  clientes"
- **THEN** a lista volta a mostrar uma linha por cliente com apuração

#### Scenario: Cliente fora da amostra truncada

- **WHEN** a lista geral está truncada e o cliente "ZETA" só tem apurações
  antigas que ficaram fora da amostra
- **THEN** "ZETA" aparece no select e, quando escolhido, suas apurações são
  listadas

#### Scenario: KPIs não seguem o filtro de cliente

- **WHEN** o usuário escolhe um cliente no select
- **THEN** os indicadores do topo continuam mostrando os totais do escritório

### Requirement: A API lista os clientes com apuração do escritório

O sistema DEVE (MUST) expor `GET /api/pgdas/clientes`, que devolve os clientes
do escritório da sessão com ao menos uma apuração gravada, cada um com `id`,
`codigo` e `nome`, ordenados por nome, sem paginação e sem repetição. O
escopo DEVE (MUST) vir sempre do escritório da sessão, nunca de parâmetro do
pedido; sem escritório na sessão, o endpoint DEVE (MUST) responder 403, como
os demais endpoints da ferramenta. A resposta NÃO DEVE (MUST NOT) incluir CNPJ
nem qualquer valor fiscal.

#### Scenario: Lista sem repetição e ordenada

- **WHEN** o escritório tem "BETA" com três competências e "ALFA" com uma
- **THEN** a resposta traz exatamente dois itens, "ALFA" antes de "BETA"

#### Scenario: Cliente sem apuração fica de fora

- **WHEN** o escritório tem um cliente sem nenhuma apuração gravada
- **THEN** esse cliente não aparece na resposta

#### Scenario: Isolamento por escritório

- **WHEN** um usuário do escritório A chama o endpoint e o escritório B tem
  clientes com apuração
- **THEN** a resposta não contém nenhum cliente do escritório B

#### Scenario: Sessão sem escritório

- **WHEN** um administrador da plataforma sem escritório em foco chama o
  endpoint
- **THEN** a resposta é 403

### Requirement: O lote de importação pode conter várias empresas

O sistema DEVE (MUST) aceitar, numa mesma importação, documentos do PGDAS-D de
empresas diferentes, e DEVE (MUST) atribuir cada competência extraída à empresa
do CNPJ lido no próprio documento. A mescla de documentos do mesmo período
(extrato e declaração do mesmo mês) DEVE (MUST) ocorrer apenas entre documentos
da **mesma** empresa: competências de mesmo período e empresas diferentes NÃO
DEVEM (MUST NOT) ser mescladas, sobrescritas nem gravadas no mesmo cliente.

Quando um documento não trouxer CNPJ reconhecível, suas competências DEVEM
(MUST) formar um grupo próprio, marcado como empresa não identificada, e NÃO
DEVEM (MUST NOT) ser atribuídas por suposição a outra empresa do lote.

Remover um arquivo do lote DEVE (MUST) remover também as competências que
vieram exclusivamente dele.

A data de abertura no CNPJ e o Nº da Declaração lidos de um documento DEVEM
(MUST) ficar com a empresa daquele documento, e NÃO DEVEM (MUST NOT) ser
atribuídos a outra empresa do lote.

#### Scenario: Lote com extratos de duas empresas

- **WHEN** o usuário carrega, no mesmo lote, extratos de duas empresas com
  CNPJs diferentes
- **THEN** as competências de cada uma ficam agrupadas sob a sua empresa, e o
  lote informa quantas empresas e quantas competências foram lidas

#### Scenario: Mesmo mês em empresas diferentes

- **WHEN** o lote traz a competência 03/2026 de duas empresas diferentes
- **THEN** cada empresa mantém a sua competência 03/2026, com os próprios
  valores, sem que uma substitua a outra

#### Scenario: Extrato e declaração do mesmo mês da mesma empresa

- **WHEN** o lote traz extrato e declaração da mesma competência de uma mesma
  empresa
- **THEN** eles resultam em uma única linha de competência naquela empresa,
  como numa importação de empresa única

#### Scenario: Data de abertura não passa de uma empresa para outra

- **WHEN** o lote traz documentos de duas empresas e só os de uma delas trazem
  a data de abertura no CNPJ
- **THEN** a data de abertura fica associada apenas a essa empresa, e a outra
  segue sem data de abertura lida

#### Scenario: Documento sem CNPJ reconhecível

- **WHEN** um documento é lido com competências válidas mas sem CNPJ
  reconhecível
- **THEN** suas competências aparecem num grupo de empresa não identificada,
  separado das demais empresas do lote

#### Scenario: Arquivo removido do lote

- **WHEN** o usuário remove do lote um arquivo já processado
- **THEN** as competências que só esse arquivo trouxe deixam de aparecer na
  empresa correspondente, e uma empresa que fique sem competências sai do lote

### Requirement: A conferência exibe um card por empresa

A etapa de conferência DEVE (MUST) exibir um card para cada empresa do lote.
Cada card DEVE (MUST) mostrar, no topo, a identificação da empresa — razão
social editável, CNPJ mascarado, município/UF e anexo/atividade editáveis, a
data de abertura no CNPJ quando lida dos documentos (só leitura, porque a
gravação a grava no cadastro do cliente), e a situação do cliente no
escritório (já cadastrado ou ainda não cadastrado) — e, abaixo dela, a tabela
editável com as competências importadas daquela empresa.

A sinalização de divergência entre a soma dos tributos e o DAS, a alternância
Pago/Aberto, a marcação de sem movimento e a remoção de linha DEVEM (MUST)
continuar valendo dentro da tabela de cada card, afetando apenas a empresa
daquele card. O usuário DEVE (MUST) poder retirar uma empresa inteira do lote
sem afetar as demais.

O CNPJ DEVE (MUST) continuar aparecendo mascarado nesta etapa.

#### Scenario: Conferência de um lote com três empresas

- **WHEN** o usuário avança para a conferência com documentos de três empresas
- **THEN** a tela exibe três cards, cada um com a identificação da empresa
  acima e a tabela das competências dela abaixo

#### Scenario: Lote de uma única empresa

- **WHEN** o lote contém documentos de uma única empresa
- **THEN** a conferência exibe um único card, com a identificação da empresa
  acima e a tabela das competências abaixo, no mesmo card

#### Scenario: Divergência sinalizada dentro do card da empresa

- **WHEN** uma competência de uma das empresas tem soma de tributos diferente
  do DAS em mais de R$ 0,05
- **THEN** a linha é sinalizada como divergente na tabela do card daquela
  empresa, e os cards das demais empresas não são afetados

#### Scenario: Situação do cliente já visível na conferência

- **WHEN** a conferência é aberta
- **THEN** cada card informa, a partir do CNPJ do documento, se a empresa já é
  cliente cadastrado do escritório, sem esperar a etapa seguinte

#### Scenario: CNPJ informado para empresa não identificada

- **WHEN** o usuário informa o CNPJ no card de empresa não identificada e esse
  CNPJ é de outra empresa já presente no lote
- **THEN** as competências do card passam para o card dessa empresa, com a mesma
  regra de mescla por período da mesma empresa, e o card não identificado deixa
  de existir

#### Scenario: Empresa retirada do lote

- **WHEN** o usuário retira uma empresa do lote na conferência
- **THEN** o card dela some, nada dela é gravado, e as demais empresas
  continuam na conferência com os valores editados até ali

### Requirement: Identificação e gravação são resolvidas por empresa

O sistema DEVE (MUST) identificar o cliente, permitir o cadastro de cliente
novo, tratar o conflito com competência já gravada e gravar as apurações
**separadamente para cada empresa** do lote, cada empresa no seu próprio
cliente. A gravação de uma empresa NÃO DEVE (MUST NOT) depender do sucesso da
gravação das demais, e uma empresa já gravada com sucesso NÃO DEVE (MUST NOT)
ser regravada ao se tentar de novo as que falharam.

O pedido de gravação de cada empresa DEVE (MUST) levar a data de abertura do
cliente e o Nº da Declaração de cada competência lidos dos documentos **daquela
empresa**, e apenas deles. Empresa cujos documentos não trouxeram data de
abertura DEVE (MUST) ser gravada sem ela, mantendo a data já existente no
cadastro do cliente.

A regra de recusa e confirmação explícita de substituição ("Uma apuração por
cliente e competência") DEVE (MUST) valer por empresa: o conflito de uma
empresa é exibido e confirmado no card dela, sem bloquear nem substituir nada
nas outras.

O sistema DEVE (MUST) oferecer a gravação de todas as empresas prontas de uma
vez, e DEVE (MUST) deixar de fora dessa ação as empresas que ainda não têm
cliente identificado ou que estão com conflito pendente de confirmação.

#### Scenario: Gravação de lote com todas as empresas cadastradas

- **WHEN** todas as empresas do lote já são clientes do escritório e o usuário
  grava o lote
- **THEN** as competências de cada empresa são gravadas no cliente
  correspondente, e o resultado de cada empresa é exibido

#### Scenario: Data de abertura gravada só no cliente certo

- **WHEN** um lote com as empresas A e B é gravado, e só os documentos de A
  trouxeram data de abertura
- **THEN** a data de abertura é gravada no cliente de A, e o cliente de B
  mantém a data de abertura que já tinha (ou continua sem nenhuma)

#### Scenario: Empresa nova no meio do lote

- **WHEN** uma das empresas do lote ainda não é cliente do escritório
- **THEN** o card dela oferece o cadastro com razão social e código sugerido,
  e as empresas já cadastradas podem ser gravadas sem esperar esse cadastro

#### Scenario: Conflito em uma das empresas

- **WHEN** o lote é gravado e uma das empresas tem competência já gravada
- **THEN** apenas essa empresa é recusada, com as competências em conflito e a
  indicação de edição manual exibidas no card dela, enquanto as demais
  empresas são gravadas normalmente

#### Scenario: Substituição confirmada em uma empresa

- **WHEN** o usuário confirma a substituição no card da empresa em conflito
- **THEN** só as apurações dessa empresa são substituídas, e nenhuma outra
  empresa do lote é regravada

#### Scenario: Falha de gravação em uma empresa

- **WHEN** a gravação de uma das empresas falha por erro de rede ou do servidor
- **THEN** essa empresa é marcada com o erro e pode ser gravada de novo, sem
  reenviar as empresas que já foram gravadas

#### Scenario: Conclusão de lote com uma empresa

- **WHEN** o lote tinha uma única empresa e ela foi gravada
- **THEN** o usuário é levado à dashboard desse cliente, como numa importação
  de empresa única

#### Scenario: Conclusão de lote com várias empresas

- **WHEN** todas as empresas de um lote com várias empresas foram gravadas
- **THEN** a tela exibe o resumo do lote, com cada empresa, quantas
  competências foram gravadas e o acesso à dashboard de cada cliente

### Requirement: A visão geral permite selecionar clientes para exportação

A tabela da visão geral do PGDAS-D DEVE (MUST) oferecer, em cada linha, uma
caixa de seleção do cliente, e no cabeçalho uma caixa que seleciona ou limpa
todos os clientes listados, indicando quando a seleção é parcial.

Com ao menos um cliente selecionado, a tela DEVE (MUST) exibir quantos estão
selecionados, a ação "Exportar PDFs" e a ação de limpar a seleção. Sem seleção,
essas ações NÃO DEVEM (MUST NOT) aparecer.

#### Scenario: Selecionar alguns clientes

- **WHEN** o usuário marca dois clientes de uma lista de cinco
- **THEN** a tela informa dois clientes selecionados, oferece "Exportar PDFs",
  e a caixa do cabeçalho indica seleção parcial

#### Scenario: Selecionar todos os listados

- **WHEN** o usuário marca a caixa do cabeçalho
- **THEN** todos os clientes listados ficam selecionados

### Requirement: A seleção contém apenas clientes visíveis na lista

A seleção DEVE (MUST) conter apenas clientes visíveis na lista: ao mudar um
filtro, os clientes que saírem da lista DEVEM (MUST) sair da seleção. O sistema
NÃO DEVE (MUST NOT) exportar cliente que o usuário não esteja vendo.

#### Scenario: Filtro tira cliente da seleção

- **WHEN** há clientes selecionados e o usuário muda um filtro de forma que um
  deles deixa de aparecer na lista
- **THEN** esse cliente sai da seleção, e os que continuam na lista permanecem
  selecionados

#### Scenario: Lista truncada

- **WHEN** a lista está truncada pelo teto da listagem e o usuário marca a caixa
  do cabeçalho
- **THEN** a seleção cobre apenas os clientes listados, e o aviso de lista
  truncada continua visível

### Requirement: A exportação em lote gera um PDF da dashboard por cliente

Ao acionar "Exportar PDFs", o sistema DEVE (MUST) gerar um PDF para cada cliente
selecionado e entregar um único download: um arquivo ZIP com um PDF por cliente.

O PDF de cada cliente DEVE (MUST) ser o mesmo documento do "Baixar PDF" da
dashboard daquele cliente, com o leiaute do escritório, a mesma regra de exibição
do CNPJ e os gráficos desenhados por completo.

#### Scenario: Exportação de três clientes

- **WHEN** o usuário seleciona três clientes e aciona "Exportar PDFs"
- **THEN** um único ZIP é baixado, com três PDFs, cada um com os dados do próprio
  cliente

#### Scenario: Mesmo documento da dashboard

- **WHEN** o ZIP é gerado para um cliente e o usuário compara o PDF com o "Baixar
  PDF" da dashboard desse cliente
- **THEN** os dois trazem as mesmas seções, valores e leiaute, com os gráficos
  completos

### Requirement: O filtro de competência define o período do PDF exportado

Quando a visão geral tiver filtro de competência, o PDF de cada cliente DEVE
(MUST) se limitar a esse período. Sem filtro, DEVE (MUST) trazer as mesmas
competências da dashboard do cliente.

#### Scenario: Filtro de competência aplicado

- **WHEN** a visão geral está filtrada de 01/2026 a 03/2026 e o usuário exporta
  os clientes selecionados
- **THEN** o PDF de cada cliente traz apenas as competências desse período

#### Scenario: Sem filtro de competência

- **WHEN** a visão geral não tem filtro de competência e o usuário exporta os
  clientes selecionados
- **THEN** o PDF de cada cliente traz as mesmas competências da dashboard dele

### Requirement: Cada PDF do lote tem nome próprio

O nome de cada PDF DEVE (MUST) identificar o cliente pelo código e pelo nome, e
dois clientes do lote NÃO DEVEM (MUST NOT) resultar em arquivos com o mesmo nome.

#### Scenario: Clientes com nomes parecidos

- **WHEN** dois clientes selecionados têm o mesmo nome
- **THEN** o ZIP traz dois arquivos com nomes diferentes, e nenhum sobrescreve o
  outro

### Requirement: Cada exportação aceita até 100 clientes

Cada exportação DEVE (MUST) aceitar até 100 clientes. Acima disso, o sistema
DEVE (MUST) explicar o limite e NÃO DEVE (MUST NOT) iniciar a geração.

#### Scenario: Seleção acima do limite

- **WHEN** o usuário seleciona 101 clientes
- **THEN** a tela informa o limite de 100 clientes por exportação, e a geração
  não pode ser iniciada

### Requirement: A exportação em lote mostra o progresso

Durante a geração, a tela DEVE (MUST) mostrar quantos clientes já foram
processados do total, e DEVE (MUST) impedir mudar a seleção, mudar os filtros ou
iniciar outra exportação. A informação de progresso DEVE (MUST) ser anunciada a
tecnologias assistivas.

#### Scenario: Progresso visível

- **WHEN** a exportação de doze clientes está em andamento e três já terminaram
- **THEN** a tela indica três de doze, e a seleção não pode ser alterada

### Requirement: A falha de um cliente não interrompe o lote

A falha na geração de um cliente NÃO DEVE (MUST NOT) interromper os demais. Ao
final, o ZIP DEVE (MUST) trazer os PDFs gerados, e a tela DEVE (MUST) informar
quantos foram gerados e quais clientes ficaram de fora. A seleção DEVE (MUST)
passar a conter apenas os que falharam, para que o usuário possa gerar só esses
de novo. Se nenhum PDF for gerado, nenhum arquivo DEVE (MUST) ser baixado.

#### Scenario: Falha em um cliente

- **WHEN** a geração falha para um de três clientes
- **THEN** o ZIP é baixado com dois PDFs, a tela nomeia o cliente que ficou de
  fora, e a seleção passa a conter só esse cliente

#### Scenario: Todos falham

- **WHEN** a geração falha para todos os clientes selecionados
- **THEN** nenhum arquivo é baixado, e a tela informa a falha

### Requirement: A exportação em lote pode ser cancelada

O usuário DEVE (MUST) poder cancelar a exportação em andamento. Cancelada a
exportação, ou deixada a tela, a geração DEVE (MUST) parar e nenhum arquivo DEVE
(MUST) ser baixado.

#### Scenario: Cancelamento

- **WHEN** o usuário cancela a exportação depois de alguns clientes
- **THEN** a geração para, nenhum ZIP é baixado, e a seleção permanece como estava

#### Scenario: Usuário deixa a tela

- **WHEN** o usuário sai da visão geral durante a exportação
- **THEN** a geração para, e nenhum ZIP é baixado

### Requirement: A exportação em lote acontece inteira no navegador

Os PDFs e o ZIP DEVEM (MUST) ser gerados no navegador do usuário, a partir das
leituras que a dashboard já faz. Nenhum PDF, ZIP ou conteúdo gerado DEVE (MUST)
ser enviado ao servidor, e a exportação NÃO DEVE (MUST NOT) gravar nada no
servidor. Cada leitura DEVE (MUST) respeitar o escopo do escritório da sessão.

#### Scenario: Requisições durante a exportação

- **WHEN** o usuário exporta um lote com as ferramentas do navegador abertas
- **THEN** as únicas requisições do lote são leituras da dashboard de cada
  cliente, sem corpo com arquivo
