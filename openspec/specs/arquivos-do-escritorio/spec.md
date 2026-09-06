# arquivos-do-escritorio Specification

## Purpose

Define como o escritório guarda seus documentos administrativos — contrato
social, procuração, alvará — no painel: o que pode entrar, onde o conteúdo fica
e quem alcança o quê.

É a exceção estreita e deliberada ao contrato de privacidade da plataforma:
entra aqui apenas o que um humano do escritório enviou à mão, nada coletado por
agente, e a **lista fechada de formatos** é o que mantém o certificado digital e
o conteúdo fiscal de fora. Antes desta capacidade, isso era garantido por não
existir caminho; agora existe um, e o que o fecha é regra — por isso ela é
requisito com cenário próprio, e não consequência.

Cobre os formatos aceitos e a checagem do conteúdo real, o teto de tamanho, a
separação entre metadado no banco e conteúdo no armazenamento de objetos, o
isolamento por escritório tanto na consulta quanto na chave do objeto, o
download por URL assinada de curta duração e o comportamento quando o
armazenamento não está configurado.

## Requirements

### Requirement: Todo arquivo tem tipo

O sistema DEVE (MUST) exigir um tipo de arquivo — **ativo e do próprio
escritório** — em todo envio, e DEVE (MUST) recusar o envio sem tipo.

O arquivo guarda também um **nome de exibição**, que PODE (MAY) ser diferente do
nome do arquivo original; quando o usuário não informa um, o sistema DEVE (MUST)
usar o nome do arquivo enviado.

Nesta capacidade o arquivo pertence ao **escritório**; ele NÃO tem vínculo com
cliente.

#### Scenario: Envio sem tipo

- **WHEN** um usuário tenta enviar um arquivo sem escolher o tipo
- **THEN** o envio é recusado indicando que o tipo é obrigatório, e nada é
  gravado nem armazenado

#### Scenario: Envio com tipo de outro escritório

- **WHEN** um pedido de envio informa o identificador de um tipo pertencente a
  outro escritório
- **THEN** o envio é recusado como tipo inválido, sem revelar que o tipo existe

#### Scenario: Envio sem nome de exibição

- **WHEN** um usuário envia `contrato-social.pdf` sem preencher o nome de
  exibição
- **THEN** o arquivo é listado como `contrato-social.pdf`

### Requirement: Só os formatos declarados são aceitos

O sistema DEVE (MUST) aceitar exclusivamente arquivos nos formatos **xls, xlsx,
pdf, doc, docx, jpg e png**, tratando `jpeg` como o mesmo formato de `jpg`. Todo
outro formato DEVE (MUST) ser recusado com mensagem que informa a lista aceita.

A lista é **fechada**: formato ausente dela não é aceito, e isso inclui
explicitamente `pfx` e `p12` — o certificado digital do escritório continua fora
da plataforma.

A verificação DEVE (MUST) acontecer **no servidor**. A validação no navegador é
conveniência, e NÃO DEVE (MUST NOT) ser a única barreira.

#### Scenario: Formato fora da lista

- **WHEN** um usuário tenta enviar um arquivo `.txt`
- **THEN** o envio é recusado informando os formatos aceitos, e nada é armazenado

#### Scenario: Certificado digital

- **WHEN** um usuário tenta enviar um arquivo `.pfx`
- **THEN** o envio é recusado como formato não aceito

#### Scenario: Pedido montado fora do navegador

- **WHEN** um pedido de envio com formato não aceito chega direto à API, sem
  passar pela tela
- **THEN** a API recusa o pedido do mesmo jeito

### Requirement: O conteúdo real do arquivo tem de bater com a extensão

O sistema DEVE (MUST) verificar a **assinatura binária** do conteúdo enviado e
recusar o arquivo cujo conteúdo não corresponda ao formato declarado pela
extensão.

Renomear um arquivo para uma extensão aceita NÃO DEVE (MUST NOT) ser suficiente
para armazená-lo.

#### Scenario: Executável renomeado para PDF

- **WHEN** um usuário envia um executável renomeado como `relatorio.pdf`
- **THEN** o envio é recusado informando que o conteúdo não corresponde ao
  formato, e nada é armazenado

#### Scenario: Arquivo íntegro

- **WHEN** um usuário envia um PDF verdadeiro com extensão `.pdf`
- **THEN** o envio é aceito

#### Scenario: Arquivo vazio

- **WHEN** um usuário envia um arquivo de zero byte
- **THEN** o envio é recusado, porque não há conteúdo a verificar

### Requirement: O arquivo tem teto de tamanho

O sistema DEVE (MUST) impor um tamanho máximo por arquivo e DEVE (MUST) recusar,
informando o limite, o envio que o exceder.

A recusa DEVE (MUST) acontecer **antes** de o conteúdo ser gravado no
armazenamento, para que um envio grande demais não consuma espaço.

#### Scenario: Arquivo acima do teto

- **WHEN** um usuário envia um arquivo maior que o tamanho máximo permitido
- **THEN** o envio é recusado informando o limite, e nada é armazenado

#### Scenario: Arquivo no limite

- **WHEN** um usuário envia um arquivo exatamente no tamanho máximo permitido
- **THEN** o envio é aceito

### Requirement: O conteúdo do arquivo fica fora do banco de dados

O sistema DEVE (MUST) guardar o conteúdo do arquivo em armazenamento de objetos
**privado**, e o banco de dados DEVE (MUST) guardar apenas metadado: nome de
exibição, tipo, formato, tamanho, quem enviou, quando, e a chave do objeto.

O conteúdo NÃO DEVE (MUST NOT) ser gravado em coluna do banco.

#### Scenario: Envio bem-sucedido

- **WHEN** um usuário envia um arquivo válido
- **THEN** o conteúdo vai para o armazenamento de objetos e o banco recebe apenas
  os metadados e a chave do objeto

#### Scenario: Falha ao armazenar o conteúdo

- **WHEN** a gravação no armazenamento de objetos falha
- **THEN** nenhum metadado é gravado, e o usuário recebe um erro de envio — não
  fica um arquivo listado sem conteúdo

### Requirement: A chave do objeto carrega o escritório

O sistema DEVE (MUST) derivar a chave do objeto armazenado a partir do
identificador do escritório e de um identificador gerado para o arquivo, e NÃO
DEVE (MUST NOT) usar o nome do arquivo enviado pelo usuário na composição da
chave.

Assim o isolamento entre escritórios não depende apenas da consulta: objetos de
escritórios diferentes ocupam espaços de nome diferentes, e um nome de arquivo
malicioso não consegue escapar do prefixo do escritório.

#### Scenario: Nome de arquivo com caminho

- **WHEN** um usuário envia um arquivo chamado `../../outro-escritorio/x.pdf`
- **THEN** o objeto é gravado sob o prefixo do escritório em foco, com chave
  gerada pelo sistema, e o nome informado aparece apenas como texto de exibição

#### Scenario: Dois escritórios enviam o mesmo arquivo

- **WHEN** dois escritórios enviam arquivos com o mesmo nome
- **THEN** cada um resulta em um objeto distinto, sob o prefixo do seu próprio
  escritório

### Requirement: O arquivo é visível apenas dentro do escritório

O sistema DEVE (MUST) restringir listagem, download e exclusão de um arquivo ao
escritório dono dele, resolvendo o escopo pela **sessão** — nunca por parâmetro do
pedido.

#### Scenario: Listagem

- **WHEN** um usuário lista os arquivos
- **THEN** aparecem apenas os arquivos do escritório em foco

#### Scenario: Download de arquivo alheio pelo identificador

- **WHEN** um usuário pede o download informando o identificador de um arquivo de
  outro escritório
- **THEN** o pedido é recusado como não encontrado, sem revelar que o arquivo
  existe

#### Scenario: Exclusão de arquivo alheio pelo identificador

- **WHEN** um usuário tenta excluir um arquivo de outro escritório pelo
  identificador
- **THEN** a exclusão é recusada como não encontrada, e o arquivo permanece
  intacto

### Requirement: O download acontece por URL assinada de curta duração

O sistema DEVE (MUST) responder ao pedido de download com uma **URL assinada e de
validade curta** para o objeto, em vez de transmitir os bytes pela API, e a URL
DEVE (MUST) fazer o navegador **baixar** o arquivo com o nome de exibição, e não
com a chave do objeto.

O sistema DEVE (MUST) autorizar o pedido **antes** de assinar: só quem pode ver o
arquivo recebe uma URL.

A URL assinada DEVE (MUST) expirar; uma URL vencida NÃO DEVE (MUST NOT) continuar
servindo o objeto.

#### Scenario: Download autorizado

- **WHEN** um usuário do escritório pede o download de um arquivo dele
- **THEN** recebe uma URL assinada válida por um período curto, e o navegador
  salva o arquivo com o nome de exibição

#### Scenario: URL vencida

- **WHEN** alguém usa uma URL assinada depois do prazo de validade
- **THEN** o armazenamento recusa o acesso ao objeto

#### Scenario: Acesso sem assinatura

- **WHEN** alguém tenta acessar o objeto diretamente no armazenamento, sem URL
  assinada
- **THEN** o acesso é recusado — o armazenamento é privado

### Requirement: A exclusão remove metadado e conteúdo

O sistema DEVE (MUST) remover, ao excluir um arquivo, tanto o registro do banco
quanto o objeto armazenado, e NÃO DEVE (MUST NOT) deixar objeto órfão ocupando
espaço.

Se a remoção do objeto falhar, o sistema DEVE (MUST) registrar a falha de forma
recuperável em vez de mentir que excluiu tudo.

#### Scenario: Exclusão bem-sucedida

- **WHEN** um usuário exclui um arquivo
- **THEN** ele some da listagem e o objeto correspondente é removido do
  armazenamento

#### Scenario: Falha ao remover o objeto

- **WHEN** a remoção do objeto falha depois de o registro ser removido
- **THEN** a falha é registrada com a chave do objeto, para que a limpeza possa
  ser refeita

### Requirement: A lista de arquivos mostra quem enviou e quando

O sistema DEVE (MUST) registrar, em cada arquivo, o usuário que o enviou e o
instante do envio, e DEVE (MUST) exibir essas informações na listagem junto do
tipo, do formato e do tamanho.

O instante do envio DEVE (MUST) ser definido pelo servidor, e NÃO DEVE (MUST NOT)
vir do corpo do pedido.

#### Scenario: Arquivo recém-enviado

- **WHEN** um usuário envia um arquivo
- **THEN** a listagem mostra o nome de exibição, o tipo, o formato, o tamanho, o
  nome de quem enviou e a data do envio

#### Scenario: Data forjada no pedido

- **WHEN** um pedido de envio traz uma data de envio no corpo
- **THEN** o valor é ignorado, e o instante gravado é o do servidor

### Requirement: A listagem filtra por tipo e por texto

O sistema DEVE (MUST) permitir filtrar a listagem de arquivos por **tipo** e por
**texto do nome de exibição**, e DEVE (MUST) apresentar os arquivos do mais
recente para o mais antigo por padrão.

#### Scenario: Filtro por tipo

- **WHEN** um usuário filtra a listagem por um tipo
- **THEN** aparecem apenas os arquivos daquele tipo

#### Scenario: Busca por nome

- **WHEN** um usuário digita parte do nome de exibição no campo de busca
- **THEN** aparecem apenas os arquivos cujo nome de exibição contém aquele texto

#### Scenario: Ordem padrão

- **WHEN** um usuário abre a listagem sem filtro algum
- **THEN** os arquivos aparecem do envio mais recente para o mais antigo

### Requirement: Sem armazenamento configurado, a funcionalidade se recusa em voz alta

O sistema DEVE (MUST) subir normalmente quando as credenciais do armazenamento de
objetos não estiverem configuradas — as demais funcionalidades da API não podem
depender disso — e DEVE (MUST) responder aos pedidos de envio e de download com
um erro explícito de **armazenamento não configurado**.

A configuração ausente NÃO DEVE (MUST NOT) se manifestar como erro genérico nem
como envio que parece dar certo e não guarda nada.

#### Scenario: API sem credenciais de armazenamento

- **WHEN** a API sobe sem as credenciais do armazenamento e um usuário tenta
  enviar um arquivo
- **THEN** o sistema responde que o armazenamento não está configurado, e o resto
  da API continua funcionando

#### Scenario: Listagem sem credenciais

- **WHEN** a API está sem credenciais e um usuário abre a página de arquivos
- **THEN** a listagem dos arquivos já registrados funciona, e a tela informa que o
  envio e o download estão indisponíveis

### Requirement: O envio tem limite de frequência

O sistema DEVE (MUST) limitar a frequência de envios por sessão, para que um laço
de envio não encha o armazenamento nem monopolize a API.

#### Scenario: Envios em rajada

- **WHEN** uma mesma sessão dispara envios acima do limite de frequência
- **THEN** os pedidos excedentes são recusados com indicação de limite atingido, e
  os já aceitos permanecem gravados

### Requirement: Os arquivos ficam na seção Escritório do painel

O sistema DEVE (MUST) oferecer a página de arquivos em uma rota transversal,
listada na seção **"Escritório"** do menu lateral, ao lado de Clientes, Tarefas e
Agentes.

A página NÃO DEVE (MUST NOT) fazer parte do catálogo de produtos: não depende de
ferramenta contratada, não tem agente e não aparece sob `/f/:produto`.

#### Scenario: Item de menu

- **WHEN** um usuário de escritório abre o painel
- **THEN** vê "Arquivos" na seção "Escritório" do menu, e o item leva à página de
  arquivos

#### Scenario: Escritório sem ferramenta contratada

- **WHEN** um escritório sem nenhuma ferramenta contratada abre o painel
- **THEN** "Arquivos" continua disponível, porque não depende do catálogo
