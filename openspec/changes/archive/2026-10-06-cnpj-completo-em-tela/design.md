## Context

A API passou a devolver `cnpj` (14 dígitos, nulo se ausente) ao lado de
`cnpjMascarado` em clientes, apurações e identificação do PGDAS. O frontend
formata `cnpj` com `formatarCnpj` e cai para a máscara. O CSV formata no
servidor.

## Decisions

- Exibição: `cnpj` formatado, senão máscara. Alternativa (substituir a
  máscara no DTO) rejeitada: quebraria quem depende do campo e esconderia o
  fallback.
- Busca: dígitos digitados contra `Cliente.Cnpj`, além de nome, código e
  máscara.
- Specs corrigidos só nos requisitos que contradiziam o comportamento; a
  ordenação por CNPJ não muda (o texto do motivo, "valor mascarado", fica
  imprecisa mas o comportamento segue valendo).

## Risks

Quem exporta o CSV passa a levar CNPJ completo no arquivo — decisão assumida
do produto.
