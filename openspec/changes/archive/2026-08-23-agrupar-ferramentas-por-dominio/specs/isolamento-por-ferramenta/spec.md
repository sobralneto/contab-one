## ADDED Requirements

### Requirement: A configuração é isolada por ferramenta

O sistema DEVE (MUST) manter a configuração de um escritório separada por
ferramenta. Salvar a configuração de uma ferramenta NÃO DEVE (MUST NOT)
alterar nem apagar a configuração salva de outra ferramenta do mesmo
escritório.

#### Scenario: Configurações diferentes por ferramenta

- **WHEN** um escritório salva um valor para uma chave de configuração da
  ferramenta A, e depois salva um valor diferente para a mesma chave na
  ferramenta B
- **THEN** consultar a configuração da ferramenta A continua devolvendo o
  valor salvo para A, sem interferência do que foi salvo para B

#### Scenario: Consulta ou gravação sem indicar a ferramenta

- **WHEN** o cliente da API pede ou tenta salvar configuração sem informar
  a qual ferramenta ela pertence
- **THEN** o sistema recusa o pedido com o motivo, sem adivinhar nem usar
  uma ferramenta padrão

### Requirement: O agente só recebe a configuração da própria ferramenta

O sistema DEVE (MUST), no handshake, entregar ao agente somente a
configuração salva para a ferramenta à qual a chave de API dele pertence.

#### Scenario: Agentes de ferramentas diferentes no mesmo escritório

- **WHEN** um escritório tem um agente da ferramenta A e um agente da
  ferramenta B, cada uma com configuração própria salva
- **THEN** o handshake do agente de A entrega a configuração de A, e o
  handshake do agente de B entrega a configuração de B

### Requirement: A lista de execuções pode ser filtrada por ferramenta

O sistema DEVE (MUST) permitir filtrar a listagem de execuções — plana ou
agrupada por escritório ou por cliente — pela ferramenta a que o agente
executor pertence. O filtro é opcional: sem ele, a listagem continua
trazendo execuções de todas as ferramentas do escopo, como antes de existir
mais de uma ferramenta.

#### Scenario: Tela de execuções de uma ferramenta

- **WHEN** a tela de execuções de uma ferramenta pede a listagem informando
  a ferramenta
- **THEN** a resposta traz somente execuções de agentes daquela ferramenta,
  em qualquer um dos três modos de listagem

#### Scenario: Consulta sem indicar a ferramenta

- **WHEN** um consumidor pede a listagem sem informar a ferramenta
- **THEN** a resposta traz execuções de todas as ferramentas do escopo,
  sem filtrar

#### Scenario: Ferramenta inexistente no filtro

- **WHEN** o filtro de ferramenta indica um código que não existe no
  catálogo
- **THEN** o sistema recusa o pedido com o motivo, em vez de devolver lista
  vazia silenciosamente
