## Why

O checklist de onboarding de um cliente só existe dentro do painel. Quando o
escritório precisa levar o andamento da implantação para fora dele — anexar ao
processo do cliente, mandar por e-mail a um sócio que não tem login, imprimir
para uma reunião de acompanhamento — não há saída: hoje resta o print de tela,
que corta a página, perde os grupos recolhidos e não registra data nem
responsáveis.

A dashboard do PGDAS-D já resolveu esse mesmo problema com "Baixar PDF"
(jsPDF + html2canvas). Falta o equivalente no onboarding, que é justamente o
documento que o cliente mais pede para ver.

## What Changes

- A página de onboarding do cliente ganha uma ação **Exportar PDF**, que gera e
  baixa um arquivo com o checklist inteiro daquele cliente.
- O PDF é montado a partir de um **documento de exportação próprio**, gerado dos
  dados do checklist — e não de uma foto da tela. Consequências diretas:
  - todos os grupos entram no PDF, inclusive os que estão recolhidos na tela;
  - o cromo interativo (checkbox clicável, `select` de responsáveis, `textarea`
    de observação, link "Editar", botão de voltar, banner de erro) não aparece;
    o que era campo editável vira texto impresso.
- **O conteúdo ocupa a largura inteira da página do PDF.** O documento é
  renderizado numa largura fixa conhecida e essa largura é mapeada na largura
  útil da página A4 — sem encolher-e-centralizar, sem faixas brancas laterais,
  em qualquer quantidade de conteúdo. Este é o ponto que o exportador do PGDAS-D
  não garante (ele centraliza o bloco quando o fator de redução fica acima de
  0,55) e que aqui vira requisito.
- Conteúdo mais alto que uma página é paginado por blocos: o cabeçalho com o
  progresso e cada grupo de tarefas são blocos, e a quebra cai entre blocos
  sempre que couber, em vez de partir uma tarefa ao meio.
- O PDF identifica o documento: código e nome do cliente, percentual de
  conclusão, contagem de tarefas concluídas/total e a data-hora da geração.
- Cada tarefa impressa carrega nome, status, indicação de 2FA, link, responsáveis,
  observação e o "concluída em/por" quando houver.
- Nenhuma mudança na API: o PDF é montado no navegador a partir do checklist já
  carregado pela página.

## Capabilities

### New Capabilities

Nenhuma. A exportação é uma nova forma de apresentar um checklist que já existe,
e pertence à capacidade que já define esse checklist.

### Modified Capabilities

- `checklist-onboarding`: passa a exigir que a página de onboarding de um cliente
  ofereça a exportação do checklist em PDF, define o conteúdo mínimo desse
  documento (independente do que está recolhido ou em edição na tela) e fixa o
  aproveitamento da largura da página como requisito de apresentação.

## Impact

- **Frontend** (única camada afetada):
  - `src/views/onboarding/OnboardingClienteView.vue` — botão de exportação,
    estado de "gerando", tratamento de falha.
  - `src/features/onboarding/exportacao/` (novo) — montagem do documento de
    exportação (HTML + CSS próprios) e o exportador para PDF, no mesmo espírito
    de `src/features/pgdas/dashboard/documento.ts`.
  - `src/views/onboarding/OnboardingClienteView.spec.ts` e testes novos do módulo
    de exportação.
- **Dependências**: nenhuma nova — `jspdf` e `html2canvas` já estão no
  `package.json` por causa do PGDAS-D.
- **API, banco, migrations, agentes Python**: nada muda.
- **Privacidade**: sem efeito sobre o contrato — o PDF é gerado e salvo na
  máquina do usuário, a partir de dados que a página já tinha; nada novo sobe
  para a API e nenhum conteúdo fiscal entra no documento.
