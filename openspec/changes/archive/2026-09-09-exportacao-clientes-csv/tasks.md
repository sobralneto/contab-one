## 1. Backend — builder de filtros compartilhado

- [x] 1.1 Extrair a cadeia de filtros inline de `ListarAsync`
      (`ContabOne.Api/Features/Clientes/ClientesEndpoints.cs`, hoje linhas
      214–263) para um helper privado estático `AplicarFiltros(db, tenant,
      busca, escritorioId, diasVencimentoCert, faixaCertificado,
      regimeTributario, emOnboarding, tem2FA)`, comentários inclusive
- [x] 1.2 Apontar `ListarAsync` para o helper — nenhum comportamento muda;
      conferir com `dotnet test --filter "Category!=Banco"` e depois a suíte
      de clientes (`ClientesTest`)

## 2. Backend — endpoint de exportação

- [x] 2.1 Adicionar `ExportarAsync` em `ClientesEndpoints.cs` com os mesmos
      parâmetros de `ListarAsync` menos `pagina`/`tamanho`, mais
      `ClaimsPrincipal`; aplicar `AplicarFiltros` + `Ordenar` e materializar
      o conjunto inteiro (projeção: Codigo, Nome, Escritorio.Nome,
      CnpjMascarado, RegimeTributario, CertificadoValidade, Tem2FA,
      AtualizadoEm)
- [x] 2.2 Construir o CSV na mão (`StringBuilder`, sem pacote novo): BOM
      (`﻿`), separador `;`, CRLF, cabeçalho com os rótulos da tabela
      (`Código;Nome;Escritório;CNPJ;Regime;2FA;Certificado;Atualizado`),
      escape RFC 4180 (cercar de aspas valor com `;`, `"` ou quebra, dobrando
      aspas internas), coluna `Escritório` apenas quando
      `user.IsInRole("PlatformAdmin")`, ausência como célula vazia, regime
      por extenso, 2FA como "Sim"/"Não", datas em dd/MM/aaaa
      (design.md, D3/D4)
- [x] 2.3 Devolver com `Results.File(bytes, "text/csv", "clientes.csv")` e
      mapear `GET /exportar` no bloco de `MapClientesEndpoints` (não conflita
      com `/{id:guid}` — mesmo caso de `/proximo-codigo`); nada a mudar no
      `Program.cs`

## 3. Frontend — API client e download

- [x] 3.1 Adicionar `exportarClientesCsv` a
      `ContabOne.Frontend/src/api/endpoints/clientes.ts`: `apiClient.get`
      com `responseType: 'blob'` e os parâmetros de filtro (sem
      `pagina`/`tamanho`), download via `URL.createObjectURL` com nome
      `clientes-AAAA-MM-DD.csv` e `revokeObjectURL` no fim
- [x] 3.2 Em `ClientesView.vue`, extrair `filtrosAtuais()` consumido por
      `carregar()` e pela exportação (filtro novo entra num lugar só);
      adicionar botão `btn-secondary` "Exportar CSV" na barra de filtros com
      ícone `Download` do `lucide-vue-next`, guarda `exportando`
      (`:disabled`, rótulo "Gerando..."), `catch` vazio como o resto da tela
      (interceptor avisa) e `finally` devolvendo o botão

## 4. Testes — backend

- [x] 4.1 `ContabOne.Api/tests/ClientesTest.cs`: exportar sem filtro traz
      todos os clientes criados no cenário; com filtro (busca e regime)
      traz apenas o conjunto que casa — nenhum cliente a mais
- [x] 4.2 `ClientesTest.cs`: formato — BOM presente na primeira linha,
      cabeçalho com `;`, valor com `;`/aspas no nome sai cercado de aspas
      com aspas internas dobradas, CNPJ sai mascarado em toda linha
- [x] 4.3 `ClientesTest.cs`: paridade — para os mesmos parâmetros, as linhas
      do arquivo são as mesmas (nomes, mesma ordem) que a listagem devolve
      paginada
- [x] 4.4 `ClientesTest.cs`: coluna `Escritório` presente para
      `PlatformAdmin` (helper `AuthHelpers.CriarUsuario(..., "PlatformAdmin",
      null)` + `escritorioId` no pedido) e ausente para `EscritorioUsuario`;
      conjunto filtrado vazio devolve arquivo só com cabeçalho, sem erro
- [x] 4.5 `IsolamentoTest.cs`: estender o bloco que já exerce
      `GET /api/clientes` — o arquivo exportado de um escritório não contém
      cliente do outro

## 5. Testes — frontend

- [x] 5.1 `ContabOne.Frontend/src/views/ClientesView.spec.ts`: handler MSW
      para `GET /api/clientes/exportar` (binário); stub de
      `URL.createObjectURL` (jsdom não tem); clique em "Exportar CSV" dispara
      o pedido com os filtros da tela; botão desabilita enquanto o pedido
      está em curso

## 6. Fechamento

- [x] 6.1 Rodar `npm test` a partir da raiz e revisar o que foi afetado —
      `ClientesTest`/`FocoEscritorioTest`/`IsolamentoTest`/`TokenIssuerTest`
      83/83 e a suíte Vitest afetada 111/111 (rodados diretamente; o wrapper
      `testes-afetados.mjs` reportou uma falha falsa de 0.0s numa execução em
      segundo plano, não reproduzida rodando os mesmos comandos em primeiro
      plano)
- [x] 6.2 Rodar `npm --prefix ContabOne.Frontend run build` (typecheck) após
      as mudanças de frontend — build limpo
- [ ] 6.3 Rodar `npm run test:tudo` antes de abrir o PR — não aplicável: sem
      PR, push direto na main a pedido do usuário; `Nfse.Agent`/`Det.Agent`
      intocados
