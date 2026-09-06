## Why

O painel mostra três contagens de certificado — vencidos, vencendo em até 3
dias, vencendo de 4 a 30 dias — e o usuário não tem o que fazer com elas. Ler
"7 vencidos" e não conseguir chegar aos sete obriga a abrir Clientes e refazer o
filtro na mão, torcendo para acertar a mesma faixa.

Só que hoje não dá para acertar: o filtro de vencimento da tela de Clientes é
`diasVencimentoCert`, que sempre filtra `>= hoje && <= hoje+N`. Ele expressa
"até 3 dias" (N=3), mas **não expressa** as outras duas — não alcança certificado
já vencido (`< hoje`) nem uma faixa com piso (`hoje+4` a `hoje+30`). Tornar os
cards clicáveis sem resolver isso levaria a uma lista que não bate com o número
clicado, que é pior do que não ter link.

## What Changes

- Os três cards de certificado do painel viram **links** para a tela de Clientes
  com a faixa correspondente já aplicada.
- `GET /api/clientes` ganha `faixaCertificado`, com as duas faixas que
  `diasVencimentoCert` não alcança: `vencidos` e `vencendoMais3d`. O card de 3
  dias continua usando `diasVencimentoCert=3`, que já é exatamente aquela faixa.
- **As faixas passam a ter uma definição única**, extraída dos três `CountAsync`
  hoje escritos dentro de `KpisAsync`. Contador e filtro leem o mesmo predicado —
  mesma razão de `OnboardingFiltros`: escritos em separado, o número do card
  deixa de bater com o tamanho da lista que o usuário abre ao clicar nele.
- O seletor de certificado da tela de Clientes ganha as duas opções novas
  ("Vencidos" e "Vencendo de 4 a 30 dias"), junto das que já existem.
- **O seletor de certificado sai do `v-if` de papel.** Hoje só aparece para quem
  não é admin de plataforma, e a listagem descarta o parâmetro para admin. Como
  os cards do painel são vistos por todos, um admin que clicasse cairia numa
  lista sem filtro — o número não bateria. Vencimento de certificado não é
  assunto de papel, como onboarding já não era.

Sem mudança de banco: nenhuma entidade, coluna ou enum novo.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `gestao-clientes`: o filtro de vencimento passa a valer para todos os papéis
  (hoje a spec o descreve como "na visão escritório") e ganha as faixas de
  vencidos e de 4 a 30 dias.
- `navegacao-por-dominio`: as três contagens do cartão de certificados passam a
  levar à listagem filtrada, e o requisito fixa que o conjunto aberto é o mesmo
  que foi contado.

## Impact

**API** (`ContabOne.Api`)

- `Features/Clientes/CertificadoFiltros.cs` (novo) — as três faixas como
  `Expression<Func<Cliente, bool>>`.
- `Features/Clientes/ClientesEndpoints.cs` — `ListarAsync` aceita
  `faixaCertificado`.
- `Features/Dashboard/DashboardEndpoints.cs` — `KpisAsync` passa a contar pelo
  predicado compartilhado em vez das condições inline.

**Frontend** (`ContabOne.Frontend`)

- `views/HubView.vue` — `para` nos três `CartaoContador`.
- `views/ClientesView.vue` — seletor fora do `v-if` de papel, duas opções novas,
  leitura da faixa pela URL.
- `api/endpoints/clientes.ts` e `api/types.ts` — parâmetro novo.

**Não muda**: banco, contratos com os agentes Python, o contrato de privacidade.
