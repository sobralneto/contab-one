## Context

`MensagensDet.vue` (renderizado em `DetVisaoGeralView`, rota `/f/det`) carrega as mensagens via `listarMensagensDet(clienteId?)` e as exibe numa tabela plana, com modal de leitura. O DTO já traz `assunto`, `clienteId`, `dataEnvio`, `prazo`.

## Goals / Non-Goals

**Goals:**
- Visão agrupada por assunto como padrão; alternância de 2 botões para a lista plana atual.

**Non-Goals:**
- Mudança de API/banco/agente; agrupamento no servidor; paginação; persistir a escolha do modo; outros agrupamentos (por cliente, por remetente).

## Decisions

- **Agrupar no cliente.** A lista já está inteira em memória e o filtro por cliente já é server-side; um `computed` agrupa o resultado. Alternativa (endpoint de agregação) rejeitada: custo de contrato e testes sem ganho enquanto não há paginação.
- **Chave do grupo** = `assunto.trim().toLocaleLowerCase('pt-BR')`; rótulo exibido = assunto da primeira mensagem do grupo; vazio → "Sem assunto". Evita duplicar grupos por variação de caixa/espaço vinda do portal.
- **Ordem:** `dataEnvio` é texto do portal, então não se parseia a data: grupos e mensagens seguem a ordem em que a API devolve (primeira mensagem do grupo = a mais recente, usada como "envio mais recente"). Os grupos aparecem na ordem da primeira ocorrência.
- **Expansão** por linha clicável com `aria-expanded`, seguindo o padrão de `ExecucoesAgrupadas.vue` (`grupo-row`, `col-expand`); estado de expansão em `Set` local, reiniciado ao recarregar.
- **Alternância** como grupo de dois `<button>` com `aria-pressed` (segmentado), usando tokens de `tokens.css`/`components.css`; se não houver classe compartilhada equivalente, criar uma em `components.css` (não CSS por view). Padrão `'agrupado'`, sem persistência.
- Modal de leitura e filtro permanecem como estão; ambos os modos chamam o mesmo `abrirMensagem`. Ícones via `lucide-vue-next` (`ChevronRight`/`ChevronDown`, `Eye`).

## Risks / Trade-offs

- [Lista muito grande torna o agrupamento custoso] → hoje não há paginação e o volume é pequeno; revisitar junto com paginação.
- [Ordem depende da API] → coberta por teste com fixture ordenada.
