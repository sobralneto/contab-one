## ADDED Requirements

### Requirement: O demonstrativo reproduz o leiaute do modelo do escritório

A sidebar de detalhe do cliente na visão geral do PGDAS-D DEVE (MUST) exibir o
documento "Demonstrativo Mensal de Faturamento". Os blocos DEVEM (MUST)
aparecer nesta ordem, reproduzindo o modelo `Relatorio_Faturamento_2025_2026.pdf`:

1. o título `DEMONSTRATIVO MENSAL DE FATURAMENTO`, em caixa alta e negrito,
   seguido de um filete horizontal escuro na largura do documento;
2. um quadro de identificação com fundo cinza-claro e cantos arredondados. Na
   primeira linha, o rótulo `RAZÃO SOCIAL` e o nome do cliente. Na segunda,
   três colunas de mesma largura: `CNPJ`, `DATA DE ABERTURA` e `REGIME
   TRIBUTÁRIO`. Os rótulos ficam em caixa alta, pequenos e acinzentados, com
   o valor logo abaixo, em negrito;
3. a tabela de faturamento mensal (ver "A tabela compara dois anos-calendário
   mês a mês");
4. a nota sobre a base de cálculo (ver "A nota cita a declaração entregue à
   Receita Federal");
5. a linha de local e data (ver "Local fica em branco e a data é a da
   emissão");
6. o bloco de assinaturas (ver "O documento termina com o bloco de
   assinaturas").

O documento DEVE (MUST) ter aparência de papel: fundo branco e texto escuro,
nos dois temas do painel, claro e escuro.

#### Scenario: Abrir o detalhe de um cliente

- **WHEN** o usuário aciona o ícone de detalhe de uma linha da visão geral do
  PGDAS-D
- **THEN** a sidebar exibe o título, o quadro de identificação, a tabela, a
  nota, a linha de local e data e o bloco de assinaturas, nessa ordem

#### Scenario: Painel em tema escuro

- **WHEN** o usuário abre o detalhe com o painel em tema escuro
- **THEN** o documento continua com fundo branco e texto escuro, igual ao
  modelo, e só a moldura da sidebar segue o tema

### Requirement: A identificação usa os dados gravados do cliente

O quadro de identificação DEVE (MUST) mostrar:

- **Razão social:** o nome do cliente;
- **CNPJ:** o CNPJ completo formatado (`00.000.000/0000-00`) quando o cliente
  o tem, e a versão mascarada quando não tem;
- **Data de abertura:** a data de abertura do cliente no formato
  `dd/mm/aaaa`, ou `—` quando ela não é conhecida;
- **Regime tributário:** o texto fixo `Simples Nacional`. Só empresas do
  Simples entregam o PGDAS-D.

#### Scenario: Cliente com todos os dados

- **WHEN** o cliente tem CNPJ completo e data de abertura gravados
- **THEN** o quadro exibe o nome, o CNPJ formatado, a data de abertura em
  `dd/mm/aaaa` e `Simples Nacional`

#### Scenario: Cliente sem data de abertura nem CNPJ completo

- **WHEN** o cliente só tem a máscara do CNPJ e nenhuma data de abertura
  gravada
- **THEN** o quadro exibe o CNPJ mascarado e `—` em Data de abertura, sem erro

### Requirement: A tabela compara dois anos-calendário mês a mês

A tabela DEVE (MUST) ter três colunas: `MÊS`, `FATURAMENTO <A-1>` e
`FATURAMENTO <A>`. `A` é o ano da competência mais recente gravada para o
cliente. A tabela DEVE (MUST) ter exatamente doze linhas, de Janeiro a
Dezembro, com o nome do mês por extenso e só a inicial maiúscula.

Cada célula de valor DEVE (MUST) mostrar o faturamento da competência
`<ano>-<mês>` no formato `R$ 0.000,00`. Uma competência sem apuração gravada,
ou gravada como sem movimento, DEVE (MUST) aparecer como `R$ 0,00`. Os valores
ficam alinhados à direita.

Depois de Dezembro e de um filete escuro, a linha `TOTAL GERAL` DEVE (MUST)
mostrar, em negrito, a soma das doze células de cada coluna.

O cabeçalho da tabela fica em caixa alta, pequeno e acinzentado, sobre um
filete escuro. As linhas de mês alternam fundo branco e cinza-claríssimo e
são separadas por um filete claro.

#### Scenario: Cliente com competências em dois anos

- **WHEN** a competência mais recente do cliente é 2026-08 e há apurações de
  2025-01 a 2026-08
- **THEN** as colunas são `FATURAMENTO 2025` e `FATURAMENTO 2026`, os meses de
  setembro a dezembro de 2026 mostram `R$ 0,00`, e cada `TOTAL GERAL` é a soma
  da sua coluna

#### Scenario: Competência sem movimento

- **WHEN** uma competência do período foi gravada como sem movimento
- **THEN** a célula correspondente mostra `R$ 0,00`

#### Scenario: Competências fora dos dois anos

- **WHEN** o cliente tem apurações anteriores ao ano `A-1`
- **THEN** elas não aparecem na tabela nem entram no `TOTAL GERAL`

### Requirement: A nota cita a declaração entregue à Receita Federal

Abaixo da tabela, o documento DEVE (MUST) exibir o texto: "Ressalta-se que os
valores informados neste demonstrativo têm como base de cálculo os dados
declarados à Receita Federal do Brasil, conforme Nº da Declaração:
**<número>**.", com o número em negrito.

O número DEVE (MUST) ser o Nº da Declaração da competência mais recente do
cliente que tenha um gravado. Quando nenhuma competência dos dois anos tem
número gravado, o trecho ", conforme Nº da Declaração: <número>" DEVE (MUST)
ser omitido e a frase termina em "Receita Federal do Brasil.".

#### Scenario: Declaração conhecida

- **WHEN** a competência mais recente com número gravado é 2026-08, com o
  número `48992503202608001`
- **THEN** a nota termina em "conforme Nº da Declaração:
  **48992503202608001**."

#### Scenario: Nenhuma declaração conhecida

- **WHEN** nenhuma competência dos dois anos tem Nº da Declaração gravado
- **THEN** a nota termina em "Receita Federal do Brasil.", sem o trecho do
  número

### Requirement: Local fica em branco e a data é a da emissão

Abaixo da nota, na mesma linha, o documento DEVE (MUST) exibir, à esquerda,
`Local:` seguido de um traço em branco para preenchimento à mão e, à direita,
`Data: <dia> de <Mês> de <ano>`. A data é a do dia em que o documento é
exibido ou exportado, com o mês por extenso e só a inicial maiúscula (por
exemplo, `Data: 14 de Outubro de 2026`).

#### Scenario: Emissão do documento

- **WHEN** o usuário abre o demonstrativo em 14/10/2026
- **THEN** a linha mostra `Local:` com o traço vazio à esquerda e
  `Data: 14 de Outubro de 2026` à direita

### Requirement: O documento termina com o bloco de assinaturas

Depois de um espaço livre para as assinaturas, o documento DEVE (MUST) exibir
duas linhas de assinatura lado a lado, cada uma centrada na sua metade. Abaixo
de cada linha fica o rótulo centralizado, em caixa alta e acinzentado:
`SÓCIO-ADMINISTRADOR` à esquerda e `CONTADOR` à direita.

#### Scenario: Bloco de assinaturas presente

- **WHEN** o demonstrativo é exibido, exportado ou impresso
- **THEN** o final do documento traz as duas linhas de assinatura com os
  rótulos `SÓCIO-ADMINISTRADOR` e `CONTADOR`

### Requirement: O demonstrativo pode ser exportado em PDF ou impresso

O topo da sidebar, fora do documento, DEVE (MUST) oferecer duas ações:
**Exportar PDF** e **Imprimir**.

- **Exportar PDF** DEVE (MUST) baixar um arquivo PDF A4 retrato, de uma
  página, com o documento inteiro, do título ao bloco de assinaturas, em fundo
  branco. O nome do arquivo segue o padrão
  `demonstrativo_faturamento_<codigo>_<nome-normalizado>.pdf`.
- **Imprimir** DEVE (MUST) abrir a caixa de impressão do navegador com
  apenas o documento na página. Menu, lista, KPIs, moldura da sidebar e os
  próprios botões ficam fora.
- O arquivo e a impressão DEVEM (MUST) ter o mesmo conteúdo da tela, inclusive
  a data de emissão e o bloco de assinaturas.
- As duas ações DEVEM (MUST) ficar desabilitadas enquanto as competências do
  cliente estão carregando. **Exportar PDF** fica desabilitada também enquanto
  um PDF está sendo gerado.

Nem o documento nem o PDF gerado DEVEM (MUST) ser enviados à API. A geração é
inteira no navegador.

#### Scenario: Exportar em PDF

- **WHEN** o usuário aciona "Exportar PDF" com o demonstrativo carregado
- **THEN** o navegador baixa um PDF A4 retrato de uma página com o
  demonstrativo completo, e nenhuma requisição carrega o arquivo

#### Scenario: Imprimir

- **WHEN** o usuário aciona "Imprimir"
- **THEN** a caixa de impressão do navegador abre e a pré-visualização mostra
  só o demonstrativo, sem o painel ao redor

#### Scenario: Ações durante o carregamento

- **WHEN** as competências do cliente ainda estão carregando
- **THEN** "Exportar PDF" e "Imprimir" estão desabilitadas
