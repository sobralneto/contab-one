## MODIFIED Requirements

### Requirement: Campo de valor monetário com formatação na digitação

O sistema DEVE (MUST) formatar como moeda brasileira (R$), com separador de
milhar e duas casas decimais, todo campo de entrada de valor monetário do
frontend, com a máscara aplicada **conforme o usuário digita** — não apenas na
saída do campo. Vale para qualquer campo de valor monetário, e não apenas para
o campo de preço dos planos.

A regra de digitação é a do sistema: **cada dígito digitado é um centavo**, e o
texto formatado volta como entrada a cada tecla. Digitar `1`→`5`→`0` produz
`R$ 0,01` → `R$ 0,15` → `R$ 1,50`. É a única regra compatível com um campo
ligado ao modelo: qualquer regra que dependa de onde está a vírgula se quebra
quando o próprio texto formatado retorna como entrada.

Valor zero é exibido como campo vazio — é o mesmo estado de "sem valor
preenchido", e é o que a simulação usa para marcar o mês.

#### Scenario: Digitação de valor inteiro

- **WHEN** o usuário digita `1`, `5` e `0` num campo de valor monetário
- **THEN** o campo exibe, a cada tecla, `R$ 0,01`, depois `R$ 0,15`, e
  depois `R$ 1,50`

#### Scenario: Digitação de valor com centavos

- **WHEN** o usuário digita `150,90` num campo de valor monetário
- **THEN** o campo exibe `R$ 150,90`, e a vírgula digitada não desloca os
  dígitos seguintes

#### Scenario: Valor grande agrupa milhar

- **WHEN** o usuário digita `123456` num campo de valor monetário
- **THEN** o campo exibe `R$ 1.234,56`

#### Scenario: Colagem de valor já formatado

- **WHEN** o usuário cola `160.000,00` num campo de valor monetário
- **THEN** o campo passa a valer R$ 160.000,00, com o ponto lido como
  separador de milhar e a vírgula como decimal

#### Scenario: Campo vazio

- **WHEN** o campo não tem valor, ou o usuário apaga o seu conteúdo
- **THEN** o campo é exibido vazio, e não como `R$ 0,00`

#### Scenario: Apagar um dígito

- **WHEN** o usuário apaga o último dígito de `R$ 1,50`
- **THEN** o campo passa a exibir `R$ 0,15`
