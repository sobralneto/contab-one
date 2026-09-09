## Context

Hoje "exige segundo fator de autenticação" é uma propriedade da tarefa de
onboarding (`TarefaOnboarding.TemDoisFatores`), marcada por tarefa dentro de
cada modelo. Na prática isso obriga o escritório a repetir a marcação em cada
tarefa de cada modelo, quando o dado real é do cliente: "esse CNPJ tem 2FA
habilitado no GOV.br ou não". Esta change move o dado para o lugar certo
(`Cliente.Tem2FA`) e remove a flag antiga por completo — não é um
redirecionamento, é a correção de um entendimento errado do pedido original,
então não há mapeamento automático entre os dois conceitos (ver Riscos).

A change toca as duas pontas do monorepo (`ContabOne.Api` e
`ContabOne.Frontend`) e duas capabilities (`gestao-clientes` e
`checklist-onboarding`), com uma migration de schema em cada lado do dado
(adicionar coluna em `Clientes`, remover coluna em `TarefasOnboarding`) —
justifica um design.md por ser cross-cutting e mexer no modelo de dados.

## Goals / Non-Goals

**Goals:**
- Cliente ganha `Tem2FA` (bool, não-nulo, default `false`), editável no
  cadastro/edição, visível e filtrável na listagem.
- Tela de onboarding do cliente exibe um aviso fixo, condicionado a
  `cliente.tem2FA`, acima do primeiro grupo de tarefas.
- `TarefaOnboarding.TemDoisFatores` e toda referência a ela (modelo, checklist
  do cliente, PDF exportado, testes) deixam de existir.

**Non-Goals:**
- Nenhuma tentativa de inferir `Cliente.Tem2FA` a partir das marcações
  antigas por tarefa — os dois conceitos não são equivalentes o suficiente
  para migração automática (ver Riscos).
- Nenhuma mudança no fluxo de sincronização do agente (`Nfse.Agent` não lê nem
  escreve `Tem2FA`; é campo só do painel, como `RegimeTributario`).
- Nenhuma mudança em quem pode editar o cadastro do cliente — a flag segue a
  mesma autorização dos demais campos do formulário.

## Decisions

- **Nome e forma do campo**: `Tem2FA` (bool, `NOT NULL DEFAULT false`) em
  `Cliente`, seguindo a convenção já usada em booleans derivados do cliente
  (`TemChecklistOnboarding`, `Produto.TemAgente`). JSON/TS: `tem2FA`
  (camelCase, sem `JsonStringEnumConverter` envolvido — é bool puro, não
  enum).
- **Filtro na listagem**: parâmetro de query opcional `tem2FA` (bool?, sem
  valor = sem filtro), não um conjunto fechado de tokens como
  `regimeTributario`/`faixaCertificado` — não existe estado "não informado"
  aqui, só verdadeiro/falso/nenhum filtro escolhido, porque a coluna é
  não-nula com default.
- **Uma migration só, cobrindo os dois lados do dado**: adicionar `Tem2FA` em
  `Clientes` e remover `TemDoisFatores` de `TarefasOnboarding` na mesma
  migration EF Core, já que as duas alterações são publicadas juntas e
  revertidas juntas — duas migrations separadas não trazem benefício aqui e
  só multiplicam o histórico.
- **Aviso na tela de onboarding é somente leitura ali**: o aviso reflete
  `cliente.tem2FA`; não há edição inline na tela de onboarding, e sim no
  cadastro do cliente — evita duas fontes de escrita para o mesmo campo e
  mantém a tela de onboarding fiel ao padrão já usado por outros dados do
  cliente exibidos ali (ela só lê, não edita cadastro).
- **Remoção completa em vez de flag morta**: `TemDoisFatores` é removido da
  entidade, dos DTOs, das telas e do PDF — não fica como coluna ignorada nem
  como campo aceito e descartado, para não deixar rastro morto no contrato
  entre modelo/tarefa/checklist que alguém precise redescobrir depois.

## Risks / Trade-offs

- **[Risco] Perda da marcação existente por tarefa** → Escritórios que hoje
  marcam tarefas específicas como "exige 2FA" perdem essa marcação sem
  substituto automático. Mitigação: o próprio pedido classifica a flag antiga
  como fruto de confusão de entendimento — não há verdade a preservar; o
  re-trabalho do lado novo é pequeno (uma marcação por cliente, não por
  tarefa), e a proposta já é explícita sobre o **BREAKING**.
- **[Risco] Migration remove coluna não-nula em produção** → Se a aplicação
  antiga (sem o deploy do backend) ainda estiver servindo tráfego no momento
  da migration, ela quebra ao tentar ler/escrever `TemDoisFatores`. Mitigação:
  seguir a ordem padrão do projeto (migration roda automaticamente no boot da
  API; deploy do backend antes do frontend, como já é prática no repositório)
  — nenhuma mudança de processo é necessária, só atenção na hora do deploy.
- **[Trade-off] Sem estado "não informado" para 2FA** → Diferente do regime
  tributário, não existe filtro "não sei". Aceitável porque a flag nasce
  `false` e é binária por natureza (tem 2FA ou não tem); não é um dado que
  fique pendente de preenchimento como o regime.

## Migration Plan

1. Backend: adicionar `Tem2FA` a `Cliente`, remover `TemDoisFatores` de
   `TarefaOnboarding`, gerar uma única migration EF Core cobrindo as duas
   mudanças, atualizar `ClientesEndpoints.cs` (DTOs, request, validator,
   filtro em `ListarAsync`) e remover todo uso de `TemDoisFatores` em
   `OnboardingEndpoints.cs`.
2. Frontend: atualizar `api/types.ts` e `api/endpoints/clientes.ts`; atualizar
   `ClientesView.vue` (campo, coluna, filtro); atualizar
   `OnboardingClienteView.vue` (aviso novo, remoção do badge por tarefa);
   atualizar `OnboardingModeloDetalheView.vue` (remoção do campo/coluna/badge);
   atualizar `features/onboarding/exportacao/documento.ts` (remoção do badge
   no PDF).
3. Testes: ajustar fixtures/expectativas em `OnboardingTest.cs`,
   `ClientesView.spec.ts`, `OnboardingClienteView.spec.ts`,
   `documento.spec.ts`.
4. Deploy na ordem já praticada no projeto: API primeiro (migration roda no
   boot), depois frontend.
5. Rollback: reverter a migration (`dotnet ef database update <anterior>`)
   junto com o deploy do código anterior — como a migration é única, o
   rollback é uma operação só.

## Open Questions

Nenhuma — o pedido original já define nome do texto do aviso, posição na tela
e formato da coluna ("2FA" / "Sim" / "Não").
