## Why

Hoje a única forma de tirar um cliente de circulação é excluí-lo, o que apaga
também checklist de onboarding e histórico de execuções. Escritórios perdem
clientes (encerram contrato, saem da carteira) sem querer destruir esse
histórico — precisam de uma forma de tirar o cliente da operação do dia a dia
mantendo o registro.

## What Changes

- Novo campo `Ativo` (booleano) no cliente, com clientes existentes e novos
  nascendo ativos.
- Nova ação "Inativar" na coluna de ações da tela de busca/listagem de
  clientes, ao lado de editar e excluir, que marca o cliente como inativo sem
  apagar nada.
- Ação simétrica "Reativar" para um cliente inativo, na mesma coluna.
- A listagem de clientes passa a oferecer um controle de situação (Ativos /
  Inativos / Todos), combinável com os demais filtros da tela (busca,
  escritório, certificado, regime, onboarding, 2FA).
- Sem escolha no controle de situação, a listagem mostra **apenas ativos** —
  cliente inativo some da operação do dia a dia por padrão, sem precisar de
  filtro extra para continuar vendo só quem está em atividade.
- Cliente inativo continua contando para o limite de clientes do plano (não é
  exclusão), mas não aparece nos indicadores de onboarding/certificado do
  painel enquanto inativo.

## Capabilities

### Modified Capabilities

- `gestao-clientes`: adiciona o estado ativo/inativo ao cliente, a ação de
  inativar/reativar na listagem, o filtro por situação e a regra de a
  listagem, sem filtro escolhido, mostrar só ativos.

## Impact

- **Backend**: `ContabOne.Api/Domain/Entities.cs` (campo `Ativo` em
  `Cliente`), `ContabOne.Api/Features/Clientes/ClientesEndpoints.cs` (novos
  endpoints de inativar/reativar, filtro de situação no `ListarAsync`, DTO),
  nova migration EF Core.
- **Frontend**: `ContabOne.Frontend/src/views/ClientesView.vue` (ação de
  inativar/reativar, controle de situação), `src/api/clientes.ts` (novas
  chamadas), tipos do `ClienteDto`.
- Nenhum impacto no agente (`Nfse.Agent`): a sincronização não lê nem grava
  este campo.
