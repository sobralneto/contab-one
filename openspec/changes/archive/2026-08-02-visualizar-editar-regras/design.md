## Context

A tela de regras atual (`RegrasView.vue`) possui dois blocos: um editor de JSON para publicar novas versões e uma tabela de histórico que exibe versão, data, status e tamanho. A API lista regras via `GET /api/admin/regras` retornando `RegraDto[]` sem o campo `conteudo` (o JSON em si é um `jsonb` potencialmente grande no banco). Não existe endpoint para obter uma regra individual com seu conteúdo, nem mecanismo no frontend para expandir uma linha do histórico e ver o que foi publicado.

Ver [proposal.md](proposal.md) para motivação completa.

## Goals / Non-Goals

**Goals:**
- Expor endpoint `GET /api/admin/regras/{id}` que retorna a regra com seu `conteudo` completo
- Permitir expansão de uma linha do histórico para visualizar o JSON formatado (somente leitura)
- Permitir carregar o JSON de uma versão existente no editor de nova versão
- Permitir copiar o JSON de uma versão existente para a área de transferência

**Non-Goals:**
- Editar uma regra já publicada (regras são imutáveis — publica-se uma nova versão)
- Excluir ou desativar regras existentes
- Diferença visual entre duas versões (diff)
- Alterar o fluxo de publicação de regras (validação, modal de confirmação)

## Decisions

### Decisão 1: Novo endpoint `GET /api/admin/regras/{id}` em vez de incluir `conteudo` na listagem

**Escolha:** Criar um endpoint dedicado para retornar uma regra individual com seu `conteudo`. O endpoint de listagem (`GET /api/admin/regras`) continua retornando apenas metadados (sem `conteudo`).

**Alternativa considerada:** Adicionar `conteudo` ao `RegraDto` da listagem. Descartada porque o campo `conteudo` é um `jsonb` que pode ter vários KB — trazer o conteúdo de todas as versões na listagem seria desperdício de banda e aumentaria o tempo de carregamento da tela. O conteúdo só é necessário quando o admin expande uma linha específica.

### Decisão 2: Expansão inline na tabela em vez de modal

**Escolha:** Ao clicar em uma linha do histórico, o conteúdo JSON expande inline abaixo da linha (como um accordion), com um `<pre>` formatado e botões "Carregar no editor" e "Copiar JSON".

**Alternativa considerada:** Modal/diálogo com o conteúdo. Descartada porque adiciona um clique extra para fechar e interrompe o fluxo de comparar versões diferentes (abrir e fechar modais sequencialmente é mais lento que expandir/recolher linhas).

### Decisão 3: Confirmação antes de sobrescrever o editor

**Escolha:** Se o editor de nova versão já contém texto (não publicado), o botão "Carregar no editor" deve confirmar com o usuário antes de sobrescrever. A confirmação usa o componente `ConfirmarAcao` já existente.

**Alternativa considerada:** Sobrescrever silenciosamente. Descartada — o admin pode ter passado minutos escrevendo um JSON novo e perder o trabalho com um clique acidental.

### Decisão 4: JSON formatado com `JSON.stringify(..., null, 2)` no próprio componente

**Escolha:** Exibir o JSON formatado com indentação de 2 espaços em um bloco `<pre>` com syntax highlighting mínimo (sem biblioteca externa). O conteúdo vem como string da API e é parseado + stringify para garantir formatação consistente.

**Alternativa considerada:** Usar uma biblioteca de JSON viewer (ex.: `vue-json-pretty`). Descartada — adiciona uma dependência para uma necessidade simples. Um `<pre>` com fonte monoespaçada resolve.

### Decisão 5: `GET /api/admin/regras/{id}` autorizado apenas para `PlatformAdmin`

**Escolha:** O novo endpoint segue a mesma política de autorização dos endpoints admin existentes: requer role `PlatformAdmin`.

**Alternativa considerada:** Endpoint público ou com autorização mais ampla. Descartada — o conteúdo das regras inclui URLs internas do portal e padrões de parsing que são detalhes operacionais da plataforma.

## Risks / Trade-offs

- **[Risk] Conteúdo de regra muito grande pode deixar a expansão inline pesada** → Mitigação: O `jsonb` típico de regras tem < 5 KB. Se um dia crescer muito, a expansão inline ainda é mais leve que um modal com o mesmo conteúdo. O `<pre>` tem `max-height` com scroll.
- **[Risk] Duas chamadas de API (lista + detalhe) em vez de uma** → Trade-off aceitável: a listagem sem `conteudo` é rápida e leve. O detalhe só é buscado sob demanda, quando o admin clica em uma linha.
- **[Trade-off] Conteúdo da regra trafega em texto plano na resposta da API** → Já é o comportamento atual do `POST /api/admin/regras` (envia o JSON no body) e do `GET /api/agent/regras` (retorna o bundle para os agentes). O endpoint admin já exige autenticação + role PlatformAdmin.
