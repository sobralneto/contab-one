## Why

A tela de regras (`/admin/regras`) permite publicar novas versões do bundle de regras de coleta, mas não oferece nenhuma forma de **visualizar o conteúdo de uma versão existente** nem de **carregar o conteúdo de uma versão anterior como ponto de partida para a edição**. O administrador é forçado a reescrever o JSON inteiro do zero a cada publicação, sem referência ao que está ativo ou ao que foi publicado antes — o que aumenta o risco de erro de digitação e dificulta ajustes pontuais (ex.: alterar apenas `maxDiasFiltro` ou uma URL).

## What Changes

- Expor endpoint `GET /api/admin/regras/{id}` na API para retornar uma regra individual incluindo seu `conteudo` completo
- Na tela de regras, permitir expandir uma linha do histórico de versões para visualizar o JSON daquela versão (modo somente leitura)
- Adicionar botão "Carregar no editor" ao visualizar uma versão existente, que copia o conteúdo para o editor de nova versão
- Adicionar botão "Copiar JSON" para copiar o conteúdo visível para a área de transferência

## Capabilities

### New Capabilities

- `visualizacao-edicao-regras`: Permitir que administradores da plataforma visualizem o conteúdo de versões existentes das regras de coleta e usem esse conteúdo como ponto de partida para novas versões

### Modified Capabilities

<!-- Nenhum spec existente é modificado — esta mudança adiciona comportamento novo sem alterar requisitos já especificados -->

## Impact

- **ContabOne.Api/Features/Admin/AdminEndpoints.cs**: Novo endpoint `GET /api/admin/regras/{id}`
- **ContabOne.Frontend/src/api/endpoints/admin.ts**: Nova função `obterRegra(id)` chamando o endpoint acima
- **ContabOne.Frontend/src/api/types.ts**: Novo tipo `RegraDetalheDto` (ou extensão de `RegraDto`) incluindo `conteudo`
- **ContabOne.Frontend/src/views/admin/RegrasView.vue**: Expansão de linha no histórico, visualização de JSON, botão "Carregar no editor" e "Copiar JSON"
