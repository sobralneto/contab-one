## MODIFIED Requirements

### Requirement: O CNPJ completo é guardado legível no banco

O sistema DEVE (MUST) persistir o CNPJ completo do cliente em texto legível
(somente os 14 dígitos), sem cifrá-lo. Onde o CNPJ do cliente é exibido —
listagem, detalhe, busca, exportação CSV —, vale o CNPJ completo, e não a
máscara (ver "O CNPJ completo é o que a plataforma exibe e busca").

Os CNPJs que já estavam guardados cifrados DEVEM (MUST) ser migrados para a
forma legível sem perda, e a migração DEVE (MUST) poder rodar mais de uma vez
sem efeito colateral.

#### Scenario: Cadastro informando o CNPJ

- **WHEN** um cliente é cadastrado ou editado com o CNPJ completo informado
- **THEN** o banco guarda os 14 dígitos legíveis, além de hash e máscara

#### Scenario: Cliente com CNPJ guardado cifrado antes desta mudança

- **WHEN** a API sobe com clientes que só têm o CNPJ cifrado
- **THEN** o CNPJ legível é preenchido a partir do valor cifrado, e uma nova
  subida não altera nada

#### Scenario: Valor cifrado que não pode ser decifrado

- **WHEN** um valor cifrado não autentica (chave diferente da original)
- **THEN** a API sobe normalmente e esse cliente fica sem CNPJ completo até
  alguém confirmá-lo pela tela

#### Scenario: Banco legível

- **WHEN** o CNPJ de um cliente é consultado diretamente no banco
- **THEN** a coluna do CNPJ completo traz os 14 dígitos, sem cifra

### Requirement: O CSV traz o que a tabela mostra

O arquivo DEVE (MUST) trazer as colunas que a tabela de clientes exibe para
aquele usuário, na mesma ordem em que a tabela as apresenta, com os mesmos
rótulos de cabeçalho. A coluna de escritório segue a regra da tabela: só para
quem a vê. Quem exporta deve reconhecer no arquivo a lista que estava
olhando — arquivo que pede tradução mental não é exportação, é segunda tela.

O CNPJ DEVE (MUST) aparecer no arquivo exatamente como a tabela o exibe:
completo e formatado quando o cliente o tem, e mascarado quando não tem. O
arquivo NÃO DEVE (MUST NOT) carregar o hash de identificação; o que não está
na tela não entra no arquivo.

Ausência de valor — regime não informado, certificado não registrado — DEVE
(MUST) sair como célula vazia, e NÃO DEVE (MUST NOT) sair como "—": o
travessão na tela existe para distinguir ausência de falha de carregamento,
distinção que num arquivo não faz sentido, e célula vazia é o que a planilha
entende como ausência.

Os valores DEVEM (MUST) sair com os rótulos que a tela usa: regime por
extenso, 2FA como "Sim" ou "Não".

#### Scenario: CNPJ completo

- **WHEN** o arquivo exportado contém um cliente com CNPJ completo gravado
- **THEN** a célula de CNPJ traz o CNPJ completo formatado, igual à tabela, e
  o hash não aparece em nenhuma coluna

#### Scenario: Cliente sem CNPJ completo

- **WHEN** o arquivo exportado contém um cliente que só tem hash e máscara
- **THEN** a célula de CNPJ traz a forma mascarada, igual à da tabela

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

### Requirement: A listagem de clientes filtra por situação, e por padrão mostra só ativos

A tela de clientes DEVE (MUST) oferecer um controle de situação com três
opções mutuamente exclusivas: **Ativos**, **Inativos** e **Todos**.

Sem escolha explícita do usuário, a listagem DEVE (MUST) se comportar como se
"Ativos" estivesse selecionado — cliente inativo NÃO DEVE (MUST NOT) aparecer
por padrão. Este é o único controle da tela cuja ausência de escolha já
restringe o resultado; os demais filtros (busca, escritório, certificado,
regime, onboarding, 2FA), sem escolha, não restringem nada.

O controle DEVE (MUST) combinar com os demais filtros da tela, restringindo o
resultado a quem atende a todos ao mesmo tempo, e DEVE (MUST) estar
disponível para todos os papéis que enxergam a listagem. A paginação e o
total exibido DEVEM (MUST) refletir o conjunto filtrado, e escolher uma opção
DEVE (MUST) levar de volta à primeira página.

#### Scenario: Listagem sem filtro de situação escolhido

- **WHEN** o usuário abre a tela de clientes sem tocar no controle de situação
- **THEN** a listagem exibe apenas clientes ativos, e o total exibido reflete
  só eles

#### Scenario: Filtrar por inativos

- **WHEN** o usuário seleciona "Inativos"
- **THEN** a listagem exibe apenas os clientes inativos

#### Scenario: Filtrar por todos

- **WHEN** o usuário seleciona "Todos"
- **THEN** a listagem exibe clientes ativos e inativos juntos

#### Scenario: Situação combinada com a busca

- **WHEN** o usuário digita um termo de busca com "Inativos" selecionado
- **THEN** a listagem exibe apenas os clientes inativos cujo nome, código ou
  CNPJ atendem ao termo

#### Scenario: Situação disponível para o administrador

- **WHEN** um administrador de plataforma abre a tela de clientes
- **THEN** o controle de situação está disponível para ele como para os
  demais papéis, e combina com o filtro de escritório

#### Scenario: Troca de situação volta à primeira página

- **WHEN** o usuário está numa página adiante e troca a opção de situação
- **THEN** a listagem volta para a primeira página do conjunto filtrado

## ADDED Requirements

### Requirement: O CNPJ completo é o que a plataforma exibe e busca

O sistema DEVE (MUST) exibir o CNPJ completo, formatado (`00.000.000/0000-00`),
em toda tela e documento que mostre o CNPJ de um cliente — listagem, edição,
sidebar e importação do PGDAS, onboarding e seu PDF, exportação CSV —, quando o
cliente o tem gravado. Quando não o tem (só hash e máscara), DEVE (MUST)
exibir a máscara, sem erro. A busca da listagem DEVE (MUST) também casar pelos
dígitos do CNPJ completo.

#### Scenario: Listagem de cliente com CNPJ completo

- **WHEN** a tela de clientes lista um cliente com CNPJ completo gravado
- **THEN** a coluna de CNPJ mostra o CNPJ completo formatado

#### Scenario: Listagem de cliente sem CNPJ completo

- **WHEN** a tela de clientes lista um cliente que só tem hash e máscara
- **THEN** a coluna de CNPJ mostra a máscara

#### Scenario: Busca pelo CNPJ

- **WHEN** o usuário digita parte do CNPJ completo no campo de busca
- **THEN** a listagem traz os clientes cujo CNPJ completo contém esses dígitos

#### Scenario: Edição abre com o CNPJ completo

- **WHEN** o usuário abre a edição de um cliente com CNPJ completo gravado
- **THEN** o campo de CNPJ vem preenchido com o CNPJ completo
