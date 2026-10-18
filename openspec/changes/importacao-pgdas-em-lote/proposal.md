## Why

A importação do PGDAS-D aceita vários PDFs de uma vez, mas trata o lote como
se fosse sempre de **uma única empresa**: as competências são mescladas só pela
chave do período (`_pa`), a identificação do cliente usa o CNPJ do primeiro
documento que trouxe um, e a gravação vai para um único `clienteId`. Na
prática, quem fecha o Simples de uma carteira inteira precisa repetir o fluxo
inteiro empresa por empresa — e, se arrastar extratos de duas empresas juntos,
o março de uma sobrescreve o março da outra em silêncio e tudo acaba gravado no
cliente errado.

Permitir a importação em lote, com os documentos agrupados por empresa já na
conferência, transforma dezenas de rodadas do assistente em uma só, e fecha o
risco de misturar apurações de CNPJs diferentes.

## What Changes

- O passo 1 (carga) passa a aceitar PDFs de **várias empresas diferentes** no
  mesmo lote. Cada competência extraída é atribuída à empresa do CNPJ lido no
  documento; extrato e declaração do mesmo mês **da mesma empresa** continuam
  sendo mesclados numa linha, mas meses iguais de empresas diferentes nunca se
  misturam.
- Ao avançar, o passo 2 (conferência) exibe **um card por empresa**. Dentro de
  cada card: a identificação da empresa no topo (razão social, CNPJ mascarado,
  município/UF, anexo, e se o cliente já está cadastrado no escritório) e, logo
  abaixo, a tabela editável das competências importadas daquela empresa. Isso
  substitui o leiaute atual de dois cards soltos (empresa em cima, tabela
  embaixo) que só comporta uma empresa.
- Documento sem CNPJ reconhecível forma um card próprio, marcado como "empresa
  não identificada", onde o usuário informa o CNPJ; se o CNPJ informado for de
  uma empresa já presente no lote, os dois cards se juntam.
- A identificação do cliente (`POST /api/pgdas/clientes/identificar`) passa a
  rodar **para cada empresa** do lote assim que o passo 2 abre.
- O passo 3 (cliente e gravação) passa a tratar cada empresa separadamente:
  cadastro de cliente novo, conflito de competência já gravada e confirmação de
  substituição são resolvidos **por empresa**, e a gravação de uma empresa não
  depende das demais. Um botão grava de uma vez todas as empresas prontas.
- Remover um arquivo no passo 1 remove também as competências que vieram dele
  (hoje só some da lista de arquivos).
- Ao final, com uma única empresa o fluxo segue para a dashboard dela, como hoje;
  com várias, mostra o resumo do lote com o resultado de cada empresa.
- **Sem mudança na API**: cada empresa continua sendo gravada pela chamada
  existente `POST /api/pgdas/apuracoes`, um `clienteId` por requisição. O PDF
  continua sendo processado só no navegador.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `apuracao-simples-nacional`: a importação passa a aceitar lote com várias
  empresas — as competências são agrupadas por empresa (CNPJ do documento), a
  conferência exibe um card por empresa com a identificação acima e a tabela
  abaixo, e identificação, conflito e gravação passam a ser resolvidos por
  empresa, de forma independente.

## Impact

- **Frontend**:
  - `ContabOne.Frontend/src/views/pgdas/PgdasImportacaoView.vue` — estado do
    assistente reorganizado de "uma lista de competências" para "uma lista de
    empresas, cada uma com suas competências"; passos 2 e 3 refeitos.
  - Novo módulo puro de agrupamento em `src/features/pgdas/importacao/`
    (atribuição de competência a empresa, mescla por empresa + período, junção
    de cards ao informar CNPJ), testável sem montar a view.
  - Provável extração de um componente de card por empresa
    (`src/components/pgdas/`) para manter a view legível.
  - `PgdasImportacaoView.spec.ts` atualizado e novos testes do agrupamento.
- **API**: nenhuma alteração de contrato. `IdentificarClienteAsync` e
  `GravarApuracoesAsync` passam a ser chamados N vezes por lote, um por empresa.
- **Privacidade**: inalterada — o documento continua no navegador, a API só
  recebe valores conferidos e o CNPJ segue mascarado na tela de importação.
