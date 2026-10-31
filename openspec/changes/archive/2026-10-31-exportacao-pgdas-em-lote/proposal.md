## Why

Hoje o PDF da dashboard do PGDAS-D sai um cliente por vez: o usuário abre a
dashboard, baixa e volta. No fechamento do mês, um escritório repete isso para
dezenas de clientes. A importação já aceita várias empresas de uma vez, mas a
saída ainda não acompanha.

## What Changes

- A tabela da visão geral do PGDAS-D ganha uma coluna de seleção, com a opção de
  selecionar todos os clientes listados.
- Com clientes selecionados, aparece a ação "Exportar PDFs", que gera o PDF da
  dashboard de cada cliente e entrega um único arquivo ZIP, com um PDF por
  cliente.
- O PDF de cada cliente é o mesmo documento do "Baixar PDF" da dashboard, com o
  leiaute do escritório e o CNPJ que a tela exibe. Quando há filtro de
  competência na visão geral, o documento se limita a esse período.
- A geração mostra o progresso, pode ser cancelada e não para quando um cliente
  falha: o ZIP sai com os demais, e a tela informa quais ficaram de fora e
  permite gerar de novo só esses.
- Cada exportação aceita até 100 clientes.
- Toda a geração, inclusive a do ZIP, acontece no navegador. A API não recebe
  nenhum arquivo e não ganha endpoint novo.
- O "Exportar PDF" do demonstrativo de faturamento não muda e fica fora do lote.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `apuracao-simples-nacional`: novos requisitos de seleção de clientes na visão
  geral e de exportação em lote da dashboard em PDF.

## Impact

- **ContabOne.Frontend:**
  - `src/views/pgdas/PgdasVisaoGeralView.vue`: seleção, barra de ações, progresso
    e resultado.
  - `src/views/pgdas/PgdasDashboardView.vue`: a geração do PDF sai da view e passa
    a ser compartilhada, sem mudar o que o usuário vê.
  - Novos módulos em `src/features/pgdas/dashboard/` para gerar o PDF fora da tela
    e orquestrar o lote.
  - `e2e/pgdas.spec.ts`: novo fluxo de exportação.
- **Dependência:** `fflate` passa a ser dependência direta. Ela já está instalada
  como dependência do `jspdf`.
- **ContabOne.Api:** sem mudança. O lote usa o
  `GET /api/pgdas/clientes/{clienteId}/dashboard` que já existe.
- **Contrato de privacidade:** mantido. A exportação só lê o que já está gravado,
  e os PDFs e o ZIP nascem e ficam no navegador do usuário.
