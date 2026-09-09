## ADDED Requirements

### Requirement: A listagem de clientes exporta o conjunto filtrado em CSV

A tela de clientes DEVE (MUST) oferecer uma ação de exportação que baixe um
arquivo CSV com os clientes do escopo corrente. A ação DEVE (MUST) estar
disponível para **todos os papéis que enxergam a listagem** — exportar a
própria lista não é ato de administração — e NÃO DEVE (MUST NOT) exigir
filtro escolhido: sem filtro, o arquivo traz o escopo inteiro.

O arquivo DEVE (MUST) conter **o conjunto inteiro que passou pelos filtros
ativos** — busca por texto, escritório, regime tributário, situação do
certificado, 2FA e onboarding, combinados como na listagem — e NÃO DEVE
(MUST NOT) se limitar à página visível: quem exporta quer o conjunto, e a
paginação é conveniência de leitura da tela, não propriedade do conjunto. A
ordem das linhas DEVE (MUST) ser a mesma que a tabela exibe no momento da
exportação, inclusive a ordenação escolhida pelo usuário.

O conjunto filtrado vazio é um resultado válido: o arquivo sai com a linha de
cabeçalho e nenhuma linha de dados, sem erro.

#### Scenario: Exportar sem filtro algum

- **WHEN** o usuário abre a tela sem escolher filtro e aciona a exportação
- **THEN** o arquivo baixado contém todos os clientes do escopo, não só a
  página em exibição

#### Scenario: Exportar com filtro ativo

- **WHEN** o usuário escolhe, por exemplo, a faixa de certificados vencidos e
  aciona a exportação
- **THEN** o arquivo contém apenas os clientes que a tabela exibe com aquele
  filtro, e nenhum cliente fora do conjunto filtrado

#### Scenario: Filtros combinados

- **WHEN** o usuário digita um termo de busca E escolhe um regime
- **THEN** o arquivo contém apenas os clientes que atendem aos dois critérios,
  como a tabela exibe

#### Scenario: Conjunto além da página

- **WHEN** o conjunto filtrado ocupa várias páginas e o usuário exporta
- **THEN** o arquivo contém todos os clientes do conjunto, inclusive os que
  não estão na página corrente

#### Scenario: Ordem da tela preservada

- **WHEN** a tabela está ordenada por uma coluna e o usuário exporta
- **THEN** as linhas do arquivo vêm nessa mesma ordem

#### Scenario: Conjunto vazio

- **WHEN** os filtros ativos não casam com nenhum cliente e o usuário exporta
- **THEN** o arquivo é baixado com a linha de cabeçalho e nenhuma linha de
  dados, sem erro

#### Scenario: Usuário comum exporta

- **WHEN** um `EscritorioUsuario` aciona a exportação
- **THEN** o arquivo é gerado normalmente, sem exigir papel de administrador

### Requirement: O CSV traz o que a tabela mostra

O arquivo DEVE (MUST) trazer as colunas que a tabela de clientes exibe para
aquele usuário, na mesma ordem em que a tabela as apresenta, com os mesmos
rótulos de cabeçalho. A coluna de escritório segue a regra da tabela: só para
quem a vê. Quem exporta deve reconhecer no arquivo a lista que estava
olhando — arquivo que pede tradução mental não é exportação, é segunda tela.

O CNPJ DEVE (MUST) aparecer no arquivo exatamente como a tabela o exibe:
mascarado. O arquivo viaja — e-mail, pasta compartilhada, mesa do cliente —
e NÃO DEVE (MUST NOT) carregar nem o CNPJ completo nem o hash de
identificação; o que não está na tela não entra no arquivo.

Ausência de valor — regime não informado, certificado não registrado — DEVE
(MUST) sair como célula vazia, e NÃO DEVE (MUST NOT) sair como "—": o
travessão na tela existe para distinguir ausência de falha de carregamento,
distinção que num arquivo não faz sentido, e célula vazia é o que a planilha
entende como ausência.

Os valores DEVEM (MUST) sair com os rótulos que a tela usa: regime por
extenso, 2FA como "Sim" ou "Não".

#### Scenario: CNPJ mascarado

- **WHEN** o arquivo exportado contém um cliente com CNPJ registrado
- **THEN** a célula de CNPJ traz a forma mascarada, igual à da tabela, e nem
  o CNPJ completo nem o hash aparecem em qualquer coluna

#### Scenario: Coluna de escritório para o admin

- **WHEN** um administrador de plataforma exporta a listagem
- **THEN** o arquivo traz a coluna de escritório, como a tabela que ele vê

#### Scenario: Sem coluna de escritório para o escritório

- **WHEN** um usuário de escritório exporta a listagem
- **THEN** o arquivo não traz coluna de escritório — a tabela dele não tem,
  e todas as linhas seriam do mesmo escritório

#### Scenario: Valor ausente

- **WHEN** um cliente exportado não tem regime informado
- **THEN** a célula de regime sai vazia, sem "—" e sem "Outros"

#### Scenario: Rótulos como na tela

- **WHEN** o arquivo traz um cliente com 2FA habilitado e regime Lucro
  Presumido
- **THEN** as células dizem "Sim" e "Lucro Presumido", como as colunas da
  tabela

### Requirement: O arquivo abre em planilha com acentos e colunas intactos

O arquivo DEVE (MUST) abrir em planilha — Excel, LibreOffice, Google Sheets —
sem configuração manual: acentuação legível e cada campo em sua coluna. Para
isso ele DEVE (MUST) vir em UTF-8 com marca de ordem de byte, usar o
separador `;` — o que a planilha pt-BR espera —, trazer os cabeçalhos na
primeira linha, e cercar com aspas qualquer valor que contenha separador,
aspas ou quebra de linha, no formato CSV padrão (RFC 4180).

Nome de empresa com ponto e vírgula que parte a linha em duas células é o
defeito que este requisito existe para impedir.

#### Scenario: Nome com ponto e vírgula

- **WHEN** um cliente exportado tem `;` no nome
- **THEN** a linha do arquivo mantém o nome inteiro em uma só célula

#### Scenario: Nome com vírgula e aspas

- **WHEN** um cliente exportado tem vírgula ou aspas no nome
- **THEN** a célula preserva o valor, com aspas internas escapadas

#### Scenario: Acentuação

- **WHEN** o arquivo exportado é aberto em planilha
- **THEN** os acentos aparecem corretamente, sem importação manual de
  codificação

#### Scenario: Cabeçalho

- **WHEN** o arquivo exportado é aberto
- **THEN** a primeira linha traz os cabeçalhos das colunas

### Requirement: A exportação não dispara duas vezes nem derruba a tela

Enquanto o arquivo é gerado, a ação DEVE (MUST) sinalizar que está em curso e
NÃO DEVE (MUST NOT) aceitar um segundo acionamento — acionar duas vezes em
paralelo só produz dois downloads iguais.

Falhando a exportação, o sistema DEVE (MUST) sinalizar a falha ao usuário e
DEVE (MUST) deixar a tela intacta e operável: a listagem carregada continua
na tela, e a ação volta a ficar disponível para nova tentativa.

#### Scenario: Acionamento durante a geração

- **WHEN** o usuário aciona a exportação e volta a acionar antes de o arquivo
  ficar pronto
- **THEN** o segundo acionamento é ignorado, e um único arquivo é produzido

#### Scenario: Erro durante a exportação

- **WHEN** a geração do arquivo falha
- **THEN** o usuário é avisado da falha, a listagem continua na tela como
  estava, e a ação de exportar pode ser acionada de novo

### Requirement: A exportação não sai do escopo do escritório

O arquivo DEVE (MUST) conter apenas os clientes que a sessão enxerga na
listagem, conforme o isolamento multi-tenant de [[isolamento-multi-tenant]]:
usuário de escritório exporta só clientes do próprio escritório;
administrador exporta o conjunto que a tela dele mostra, respeitando o filtro
de escritório quando escolhido.

O arquivo é lido fora do painel, onde nenhum outro controle protege os dados
— a exportação NÃO DEVE (MUST NOT) incluir cliente de escritório algum que a
tela daquele usuário não exibiria.

#### Scenario: Usuário de escritório exporta

- **WHEN** existem clientes no próprio escritório do usuário e em outro
  escritório, e o usuário de escritório exporta a listagem
- **THEN** o arquivo contém apenas os clientes do próprio escritório

#### Scenario: Admin com filtro de escritório

- **WHEN** um administrador escolhe um escritório no filtro e exporta
- **THEN** o arquivo contém apenas clientes daquele escritório

#### Scenario: Cliente de mesmo nome em outro escritório

- **WHEN** dois escritórios têm clientes com o mesmo nome e o usuário de um
  deles exporta
- **THEN** o arquivo traz apenas o cliente do próprio escritório, em uma só
  linha