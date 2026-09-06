## Why

A listagem de clientes sempre volta ordenada por nome. Para achar quem foi
mexido por último, quem tem o certificado mais próximo de vencer ou o cliente de
código mais alto, só resta paginar até encontrar — e com 100 clientes por página
isso é folhear, não consultar.

A tela já tem busca e três filtros; o que falta é escolher **por onde** olhar o
que sobrou do filtro.

## What Changes

- Os cabeçalhos da tabela de clientes viram controles de ordenação: código,
  nome, certificado e última atualização — mais escritório, na visão do
  administrador. Clicar alterna entre crescente e decrescente; clicar em outra
  coluna começa crescente.
- `GET /api/clientes` aceita `ordenarPor` e `direcao`. O padrão continua sendo
  **nome crescente**, então quem não tocar em nada vê o que via antes.
- A coluna aceita é resolvida por uma lista fechada no servidor. Valor
  desconhecido cai no padrão, sem erro.
- **Toda ordenação termina com um desempate estável.** Sem isso, ordenar por uma
  coluna com valores repetidos (nome igual, certificado nulo) e paginar faz o
  banco escolher a ordem livremente dentro do empate, e a mesma linha pode
  aparecer em duas páginas enquanto outra some.
- Cliente **sem certificado** fica no fim da ordenação por certificado nas duas
  direções. O padrão do banco jogaria os nulos para o topo na direção
  decrescente, abrindo a lista com quem não tem certificado nenhum — ruído no
  lugar da informação.
- A **CNPJ não é ordenável**: o valor guardado é mascarado (`54.283.***/**26`),
  então ordenar por ele ordena por um texto meio escondido. Pareceria um recurso
  e não seria.
- Trocar a ordenação volta para a primeira página.

Sem mudança de banco: nenhuma entidade, coluna ou enum novo.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `gestao-clientes`: a listagem ganha ordenação escolhida pelo usuário, com o
  requisito de estabilidade entre páginas e o tratamento de cliente sem
  certificado.

## Impact

**API** (`ContabOne.Api`)

- `Features/Clientes/ClientesEndpoints.cs` — `ListarAsync` aceita `ordenarPor` e
  `direcao` e resolve a ordenação por lista fechada.

**Frontend** (`ContabOne.Frontend`)

- `views/ClientesView.vue` — cabeçalhos clicáveis, estado da ordenação, reset de
  página.
- `assets/styles/components.css` — o estilo do cabeçalho ordenável entra no
  padrão de tabela compartilhado, não em CSS scoped da view.
- `api/endpoints/clientes.ts` — parâmetros novos.

**Não muda**: banco, contratos com os agentes Python, o contrato de privacidade.
