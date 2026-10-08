## Why

Depois de `cnpj-completo-texto-puro`, o CNPJ completo fica legível em
`Cliente.Cnpj`, mas as telas ainda exibiam e buscavam pela máscara. O dono do
produto decidiu que a plataforma usa o CNPJ completo em tudo. A implementação
já foi mergeada (ContabOne.Api#14, ContabOne.Frontend#15); os specs principais
ainda dizem que listagem, busca, CSV e sidebar do PGDAS só mostram a máscara.

## What Changes

- Listagem, detalhe, busca, edição, CSV, sidebar e importação do PGDAS,
  onboarding e seu PDF passam a usar o CNPJ completo formatado quando o cliente
  o tem; a máscara fica como fallback.
- A busca de clientes também casa pelos dígitos do CNPJ completo.
- O CSV continua sem o hash de identificação.
- A ordenação por CNPJ continua indisponível (fora de escopo).

## Capabilities

### New Capabilities

### Modified Capabilities

- `gestao-clientes`: exibição e busca pelo CNPJ completo; CSV com CNPJ
  completo; requisito do banco deixa de proibir o CNPJ completo nas telas.
- `apuracao-simples-nacional`: sidebar e listagem de apurações carregam o CNPJ
  completo quando existe.

## Impact

Só specs: o código já foi entregue nos PRs citados.
