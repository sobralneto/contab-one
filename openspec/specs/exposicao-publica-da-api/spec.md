# exposicao-publica-da-api Specification

## Purpose

Define o que a plataforma entrega a quem chega sem credencial em produção — documentação, cabeçalhos de resposta e hosts atendidos — e como ela identifica o cliente real atrás do proxy para que os limites por origem funcionem.

## Requirements

### Requirement: A documentação da API não é pública em produção

O sistema NÃO DEVE (MUST NOT) servir, em produção, o documento de descrição da API nem a interface interativa de documentação. Ambos DEVEM (MUST) existir apenas fora de produção, junto dos demais recursos de desenvolvimento.

#### Scenario: Documento de descrição em produção

- **WHEN** alguém acessa a rota do documento de descrição da API em produção
- **THEN** a resposta é 404

#### Scenario: Interface de documentação em produção

- **WHEN** alguém acessa a rota da interface interativa de documentação em produção
- **THEN** a resposta é 404

#### Scenario: Documentação em desenvolvimento

- **WHEN** a API roda em ambiente de desenvolvimento
- **THEN** o documento de descrição e a interface interativa continuam disponíveis

### Requirement: Os limites por origem contam o cliente real

O sistema DEVE (MUST) identificar a origem de um pedido pelo endereço do cliente informado pelo proxy de borda confiável, e NÃO DEVE (MUST NOT) usar o endereço da conexão quando a API está atrás de proxy — sob pena de todos os clientes dividirem uma cota só.

O sistema DEVE (MUST) aceitar esse cabeçalho apenas de proxies conhecidos, para que a origem não seja forjável por quem chama.

#### Scenario: Dois clientes distintos atrás do mesmo proxy

- **WHEN** dois clientes de endereços diferentes fazem pedidos pela borda
- **THEN** cada um consome sua própria cota, e o esgotamento da cota de um não recusa os pedidos do outro

#### Scenario: Cliente forja o cabeçalho de origem

- **WHEN** um cliente envia diretamente um cabeçalho de origem alegando outro endereço, sem passar pelo proxy confiável
- **THEN** o cabeçalho é ignorado e o endereço real da conexão é usado

### Requirement: As respostas trazem os cabeçalhos de segurança do navegador

As respostas do frontend publicado e da API DEVEM (MUST) instruir o navegador a: exigir HTTPS em acessos seguintes, recusar a exibição da aplicação dentro de moldura de outro site, não adivinhar o tipo do conteúdo, limitar as origens de onde script, estilo e conexões podem vir, e limitar o que é enviado no cabeçalho de referência.

#### Scenario: Tentativa de embutir a aplicação em outro site

- **WHEN** outro site tenta carregar a aplicação dentro de uma moldura
- **THEN** o navegador recusa a exibição

#### Scenario: Resposta do frontend publicado

- **WHEN** um navegador carrega qualquer página do frontend publicado
- **THEN** a resposta traz política de conteúdo, política de referência, exigência de HTTPS e recusa de adivinhação de tipo

#### Scenario: Script de origem não prevista

- **WHEN** um script de uma origem fora da política tenta executar na página
- **THEN** o navegador bloqueia a execução

### Requirement: A API atende apenas os hosts previstos

O sistema DEVE (MUST) atender apenas pedidos endereçados aos hosts configurados para o ambiente, e NÃO DEVE (MUST NOT) aceitar qualquer host.

#### Scenario: Pedido endereçado a host não previsto

- **WHEN** chega um pedido cujo host não está entre os configurados
- **THEN** a API recusa o pedido

#### Scenario: Pedido endereçado ao host de produção

- **WHEN** chega um pedido endereçado ao host configurado da API
- **THEN** o pedido é atendido normalmente
