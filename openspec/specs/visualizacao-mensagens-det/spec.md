## Purpose

Cobre a página do painel onde o escritório visualiza as mensagens da Caixa
Postal DET coletadas pelo agente, publicada de forma catálogo-driven como
qualquer outra ferramenta.

## Requirements

### Requirement: O produto DET declara uma página de mensagens no catálogo

O produto DET DEVE (MUST) declarar a nova página de mensagens em
`Produto.Paginas`, seguindo o mesmo mecanismo catálogo-driven que já governa
o menu e as rotas `/f/:produto/:pagina` de toda ferramenta — sem item de
menu hard-coded no frontend.

#### Scenario: Escritório contratou o produto DET

- **WHEN** um escritório com o produto DET habilitado carrega o catálogo
  (`GET /api/produtos`)
- **THEN** a página de mensagens DET aparece no menu desse produto

#### Scenario: Escritório sem o produto DET

- **WHEN** um escritório não tem o produto DET habilitado
- **THEN** a página de mensagens DET não aparece no menu nem é alcançável
  pela rota

### Requirement: A página lista mensagens DET filtráveis por cliente

A página de mensagens DET DEVE (MUST) listar as mensagens recebidas do
escritório em foco e DEVE (MUST) oferecer um filtro por cliente, usando o
endpoint de consulta de `registro-mensagens-det`.

#### Scenario: Usuário abre a página sem filtro

- **WHEN** o usuário abre a página de mensagens DET sem selecionar um
  cliente
- **THEN** a lista mostra as mensagens de todos os clientes do escritório
  em foco

#### Scenario: Usuário filtra por cliente

- **WHEN** o usuário seleciona um cliente no filtro
- **THEN** a lista é restrita às mensagens desse cliente
