## 1. Backend — Novo endpoint de detalhe de regra

- [x] 1.1 Adicionar `RegraDetalheDto` (record com `Id`, `Versao`, `PublicadaEm`, `Ativa`, `TamanhoConteudo`, `Conteudo`) em `ContabOne.Api/Features/Admin/AdminEndpoints.cs`
- [x] 1.2 Adicionar endpoint `GET /api/admin/regras/{id}` que busca a `RegraColeta` por id, retorna `200` com `RegraDetalheDto` se encontrada, ou `404` se não existir
- [x] 1.3 Verificar que o endpoint exige autenticação e role `PlatformAdmin` (seguir o padrão dos endpoints admin existentes)
- [x] 1.4 Buildar o projeto .NET (`dotnet build`) sem erros

## 2. Frontend — Camada de API

- [x] 2.1 Adicionar interface `RegraDetalheDto` em `ContabOne.Frontend/src/api/types.ts` estendendo os campos de `RegraDto` com `conteudo: string`
- [x] 2.2 Adicionar função `obterRegra(id: string)` em `ContabOne.Frontend/src/api/endpoints/admin.ts` que chama `GET /api/admin/regras/{id}` e retorna `RegraDetalheDto`

## 3. Frontend — Visualização de regra existente

- [x] 3.1 Adicionar estado reativo `expandedId: string | null` e `expandedContent: string | null` em `RegrasView.vue` para controlar qual linha está expandida
- [x] 3.2 Adicionar evento `@click` nas linhas do `<tbody>` que alterna a expansão: ao clicar, chama `obterRegra(id)` e exibe o conteúdo JSON formatado abaixo da linha
- [x] 3.3 Renderizar o conteúdo expandido como bloco `<pre>` com JSON formatado (`JSON.stringify(JSON.parse(conteudo), null, 2)`), fonte monoespaçada, `max-height` com scroll, dentro de uma nova linha `<tr>` abaixo da linha clicada
- [x] 3.4 Adicionar indicador visual de expansão (seta ou ícone) na coluna "Versão" da linha ativa
- [x] 3.5 Adicionar `loading` local (spinner pequeno) enquanto o conteúdo é carregado da API

## 4. Frontend — Botões de ação na visualização

- [x] 4.1 Adicionar botão "Copiar JSON" que copia o conteúdo formatado para a área de transferência via `navigator.clipboard.writeText()` e exibe feedback visual temporário ("Copiado!")
- [x] 4.2 Adicionar botão "Carregar no editor" que copia o JSON (string original da API, não formatado) para `novoJson` e rola a tela até o editor (`scrollIntoView`)
- [x] 4.3 Implementar confirmação via `ConfirmarAcao` antes de sobrescrever o editor se `novoJson` já contiver texto não publicado

## 5. Verificação

- [x] 5.1 Testar fluxo completo: acessar `/admin/regras` como PlatformAdmin, clicar em uma versão do histórico, verificar que o JSON é exibido formatado
- [x] 5.2 Testar "Copiar JSON": verificar que o conteúdo é copiado corretamente para o clipboard
- [x] 5.3 Testar "Carregar no editor": verificar que o JSON aparece no textarea, editar um campo, publicar nova versão, e confirmar que a nova versão aparece no histórico
- [x] 5.4 Testar confirmação de sobrescrita: digitar algo no editor, carregar outra versão, verificar que o modal de confirmação aparece
- [x] 5.5 Testar que a rota `/admin/regras` não é acessível para papéis não-PlatformAdmin
- [x] 5.6 Rodar `npm run build` no frontend sem erros
