## Purpose

Garante que campos de CNPJ e valores monetários nos formulários do frontend apliquem máscara de formatação durante a digitação, melhorando a experiência do usuário e reduzindo erros de entrada.

## Requirements

### Requirement: Campo de CNPJ com máscara

O sistema DEVE (MUST) aplicar automaticamente a máscara `XX.XXX.XXX/XXXX-XX` conforme o usuário digita em qualquer campo de CNPJ nos formulários do frontend.

#### Scenario: Digitação de CNPJ válido

- **WHEN** o usuário digita os 14 dígitos de um CNPJ em um campo de CNPJ
- **THEN** o campo exibe o valor formatado como `XX.XXX.XXX/XXXX-XX`

#### Scenario: Colagem de CNPJ sem formatação

- **WHEN** o usuário cola uma string de 14 dígitos sem formatação no campo de CNPJ
- **THEN** o campo aplica a máscara e exibe o valor como `XX.XXX.XXX/XXXX-XX`

### Requirement: Campo de preço com formatação monetária

O sistema DEVE (MUST) formatar automaticamente o valor digitado no campo de preço dos planos como moeda brasileira (R$), com separador de milhar e duas casas decimais.

#### Scenario: Digitação de valor inteiro

- **WHEN** o usuário digita `100` no campo de preço
- **THEN** o campo exibe `R$ 100,00`

#### Scenario: Digitação de valor com centavos

- **WHEN** o usuário digita `99.90` no campo de preço
- **THEN** o campo exibe `R$ 99,90`
