## ADDED Requirements

### Requirement: O CNPJ completo é guardado legível no banco

O sistema DEVE (MUST) persistir o CNPJ completo do cliente em texto legível
(somente os 14 dígitos), sem cifrá-lo. O CNPJ completo NÃO DEVE (MUST NOT)
aparecer em listagem, busca, detalhe ou exportação CSV de clientes: essas
superfícies continuam expondo só a máscara e a indicação de que há CNPJ
completo.

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

#### Scenario: Listagem não expõe o CNPJ completo

- **WHEN** a listagem, a busca, o detalhe ou o CSV de clientes é gerado
- **THEN** o CNPJ completo não aparece em nenhum deles
