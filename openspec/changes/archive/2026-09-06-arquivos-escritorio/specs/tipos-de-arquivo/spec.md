## ADDED Requirements

### Requirement: O tipo de arquivo é cadastro do escritório

O sistema DEVE (MUST) permitir que o escritório cadastre, liste, edite e exclua
seus próprios tipos de arquivo. O tipo tem **nome obrigatório**; descrição é
opcional e PODE (MAY) ficar vazia.

O tipo pertence a um escritório e NÃO DEVE (MUST NOT) ser visível, editável nem
selecionável por outro escritório.

#### Scenario: Cadastro com o mínimo obrigatório

- **WHEN** um usuário cadastra um tipo informando apenas o nome
- **THEN** o tipo é criado ativo, sem descrição, disponível para classificar
  arquivos daquele escritório

#### Scenario: Cadastro sem nome

- **WHEN** um usuário tenta salvar um tipo com o nome vazio
- **THEN** o sistema recusa a operação e indica que o nome é obrigatório

#### Scenario: Tipo de outro escritório não aparece

- **WHEN** um usuário de um escritório lista os tipos de arquivo
- **THEN** aparecem apenas os tipos do escritório em foco, e nenhum tipo de outro
  escritório

### Requirement: O nome do tipo é único dentro do escritório

O sistema DEVE (MUST) recusar a criação ou a edição de um tipo cujo nome já
exista naquele escritório, comparando **sem diferenciar maiúsculas de minúsculas**
e ignorando espaços nas pontas.

Escritórios diferentes PODEM (MAY) ter tipos com o mesmo nome — a unicidade é por
escritório, não global.

#### Scenario: Nome repetido no mesmo escritório

- **WHEN** um usuário tenta cadastrar "Contrato social" e já existe "contrato
  social" naquele escritório
- **THEN** o sistema recusa a operação e indica que já existe um tipo com esse
  nome

#### Scenario: Mesmo nome em escritórios diferentes

- **WHEN** dois escritórios distintos cadastram, cada um, um tipo chamado
  "Procuração"
- **THEN** ambos os cadastros são aceitos, e cada escritório enxerga apenas o seu

#### Scenario: Edição que mantém o próprio nome

- **WHEN** um usuário edita apenas a descrição de um tipo, sem alterar o nome
- **THEN** a gravação é aceita, e o próprio tipo não é tratado como duplicata de
  si mesmo

### Requirement: O tipo inativo não classifica arquivo novo

O sistema DEVE (MUST) permitir marcar um tipo como inativo e DEVE (MUST) manter os
arquivos já classificados com ele exibindo esse tipo normalmente.

Um tipo inativo NÃO DEVE (MUST NOT) aparecer como opção ao enviar um arquivo novo
nem ser aceito na gravação de um arquivo novo.

#### Scenario: Envio de arquivo com tipo inativo

- **WHEN** um usuário tenta enviar um arquivo classificado com um tipo inativo
- **THEN** o sistema recusa a operação e indica que o tipo não está disponível

#### Scenario: Arquivo antigo de tipo inativado

- **WHEN** um tipo é inativado e existiam arquivos classificados com ele
- **THEN** esses arquivos continuam listados, exibindo o nome do tipo, e
  continuam podendo ser baixados e excluídos

### Requirement: Tipo em uso não é excluído

O sistema DEVE (MUST) recusar a exclusão de um tipo que tenha ao menos um arquivo
classificado com ele, e DEVE (MUST) informar quantos arquivos o usam e que a
alternativa é inativá-lo.

Um tipo **sem nenhum arquivo** PODE (MAY) ser excluído definitivamente.

#### Scenario: Exclusão de tipo com arquivos

- **WHEN** um usuário tenta excluir um tipo que classifica três arquivos
- **THEN** a exclusão é recusada, o sistema informa que o tipo está em uso, e nem
  o tipo nem os arquivos são alterados

#### Scenario: Exclusão de tipo sem arquivos

- **WHEN** um usuário exclui um tipo que não classifica arquivo algum
- **THEN** o tipo é removido e deixa de aparecer nas listagens

### Requirement: A administração dos tipos é do administrador do escritório

O sistema DEVE (MUST) exigir o papel `EscritorioAdmin` para criar, editar,
inativar ou excluir um tipo de arquivo, e DEVE (MUST) permitir que qualquer
`EscritorioUsuario` **leia** a lista de tipos — sem ela não há como classificar um
arquivo no envio.

#### Scenario: Usuário comum tenta cadastrar tipo

- **WHEN** um usuário sem papel de administrador tenta criar um tipo de arquivo
- **THEN** a operação é recusada por falta de autorização, e nada é gravado

#### Scenario: Usuário comum lista tipos para enviar arquivo

- **WHEN** um usuário sem papel de administrador abre o formulário de envio
- **THEN** ele enxerga os tipos ativos do escritório e consegue escolher um
