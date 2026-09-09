## Context

`Cliente` hoje só tem um jeito de sair da listagem: `ExcluirAsync` (DELETE),
que remove a linha do banco e leva junto `ChecklistOnboardingCliente` e
`ExecucaoMetrica` referenciados por FK. Não há nenhum conceito de estado no
cliente — ele existe ou não existe.

O padrão mais próximo no código já existente é `Escritorio.Status`
(`StatusEscritorio.Ativo`/`Suspenso`, ver `AdminEndpoints.cs`) e
`Produto.Ativo` (bool simples, editado via `req.Ativo.HasValue` no mesmo
endpoint de atualização). Nenhum dos dois é acionado como ação isolada de
linha de tabela — ambos são um campo do formulário de edição.

Aqui o pedido é o oposto: uma ação rápida na **linha da listagem/busca**, ao
lado de excluir, sem abrir o formulário de edição — o mesmo padrão de UX que
`ExcluirAsync` já usa.

## Goals / Non-Goals

**Goals:**
- Cliente pode ser tirado da operação do dia a dia sem perder checklist,
  execuções ou histórico.
- A ação é acessível diretamente da linha da listagem, como excluir.
- O padrão (sincronização do agente nunca grava sobre escolha humana) que já
  vale para `RegimeTributario`/`ModeloOnboardingId` se estende a `Ativo`.

**Non-Goals:**
- Não é um soft-delete genérico para outras entidades — só `Cliente`.
- Não introduz um terceiro estado (ex.: "arquivado"): é binário, ativo ou
  inativo.
- Não bloqueia login, execução do agente ou API key do escritório — isso é
  `Escritorio.Status`, uma camada acima, e continua intacto.

## Decisions

**D1 — Campo `bool Ativo` na entidade, default `true`.**
Alternativa considerada: enum `SituacaoCliente` (Ativo/Inativo) espelhando
`StatusEscritorio`. Rejeitada por não haver hoje nenhum terceiro estado
plausível para cliente, e um enum de dois valores só adiciona conversão
string↔enum sem ganho (ao contrário de `StatusEscritorio`, que já nasceu
pensando em `Suspenso` por inadimplência, um motivo de negócio distinto).

**D2 — Endpoint dedicado `PATCH /api/clientes/{id}/situacao`, corpo
`{ ativo: bool }`, em vez de passar por `AtualizarAsync` (PUT).**
A ação sai da listagem/busca, não do formulário de edição, e não deve exigir
os campos obrigatórios do `ClienteRequest` (código, nome) nem rodar o
`ClienteRequestValidator` inteiro para uma mudança de um bit. Mesmo padrão de
independência que `ExcluirAsync` já tem em relação a `AtualizarAsync`.
Retorna `{ id, ativo }`.

**D3 — Sem filtro escolhido, a listagem mostra só ativos.**
Alternativa considerada: manter o comportamento atual (mostrar todos) e só
oferecer inativos como opção adicional. Rejeitada: cliente inativo existe
justamente para sair da visão do dia a dia — se o padrão continuasse
mostrando todo mundo, a ação de inativar não mudaria nada que o usuário veja
sem tocar em outro controle, e a maior parte do valor da feature (turma
inativa parar de poluir a lista, a paginação e os indicadores) se perderia.
Filtro de situação vira, então, o único controle desta tela cujo valor
"não escolhido" não é "sem restrição" — é `ativo=true` implícito. Escolher
"Todos" explicitamente é o jeito de voltar a ver tudo.

**D4 — Indicadores do painel (`DashboardEndpoints`) e os contadores de
certificado/onboarding que a listagem reaproveita (`CertificadoFiltros`,
`OnboardingFiltros`) passam a contar só clientes ativos.**
Cliente inativo não é mais operação corrente; contar o certificado vencido
dele como pendência ativa no painel produziria um número que não corresponde
a nada que alguém vá agir. Como a listagem, sem filtro, já mostra só ativos
(D3), os contadores do painel batem com o tamanho da lista que abre ao
clicar neles — a mesma garantia que `CertificadoFiltros`/`OnboardingFiltros`
já dão hoje entre painel e listagem.

**D5 — Cliente inativo continua contando para `plano.MaxClientes`.**
Inativar não é excluir; o registro (e o espaço que ele ocupa no plano)
continua existindo. Tratar diferente exigiria decidir uma regra comercial
nova (o plano "libera vaga" ao inativar?) que ninguém pediu — fora do escopo
desta mudança. Quem quiser liberar a vaga usa exclusão, que já existe.

**D6 — Sincronização do agente (`AgentEndpoints.cs`) nunca lê nem grava
`Ativo`.**
Mesma régua que já protege `RegimeTributario` e `ModeloOnboardingId`: o
agente deriva o que sabe do nome/conteúdo dos certificados na máquina do
escritório, e "ativo/inativo" não é informação que exista lá. Se a
sincronização reativasse um cliente automaticamente ao ver o certificado de
novo, inativar deixaria de ser confiável — o cliente reapareceria sozinho na
próxima execução do robô, sem ninguém ter pedido.

## Risks / Trade-offs

- [Cliente inativo com onboarding em andamento pode confundir quem está no
  meio do checklist] → a tela de onboarding do cliente (acessada por link
  direto, não pela listagem) continua funcionando normalmente para cliente
  inativo; só a listagem/busca e os indicadores do painel deixam de trazê-lo
  por padrão.
- [Migration adiciona coluna `NOT NULL DEFAULT true` numa tabela em produção]
  → `ALTER TABLE` com default é operação segura no Postgres usado aqui
  (18-alpine, sem necessidade de rewrite de tabela para adicionar coluna com
  default constante); mesmo padrão já usado para `Tem2FA`.

## Migration Plan

1. Migration EF Core adiciona `Ativo boolean NOT NULL DEFAULT true` —
   clientes existentes nascem ativos, sem mudança de comportamento visível
   até alguém inativar o primeiro.
2. Deploy do backend (endpoint novo + filtro na listagem + contadores do
   painel).
3. Deploy do frontend (ação de inativar/reativar + controle de situação).
Nenhum passo exige coordenação especial: o campo com default `true`
mantém a listagem idêntica à de hoje enquanto o frontend novo não é
publicado. Rollback é reverter os três deploys em ordem inversa; a coluna
pode ficar (não quebra nada ser ignorada).

## Open Questions

Nenhuma em aberto — payload e comportamento padrão (D1–D6) cobrem o pedido.
