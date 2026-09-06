## 1. Infraestrutura do armazenamento

- [x] 1.1 Adicionar `AWSSDK.S3` ao `ContabOne.Api.csproj`
- [x] 1.2 Criar `Infra/IArmazenamentoArquivos.cs` com `GravarAsync`, `AssinarLeituraAsync` e `ExcluirAsync`, mais um `Configurado` booleano
- [x] 1.3 Implementar `Infra/ArmazenamentoArquivosS3.cs` sobre `AmazonS3Client` com `ServiceURL = ARQUIVOS_ENDPOINT`, `AuthenticationRegion = ARQUIVOS_REGION` e credenciais das variáveis de ambiente
- [x] 1.4 Implementar `Infra/ArmazenamentoArquivosIndisponivel.cs` — a variante "não configurado", que lança o erro traduzido em 503 pelos endpoints
- [x] 1.5 Registrar no `Program.cs` a escolha entre as duas implementações conforme a presença das cinco variáveis, com log de aviso no boot quando subir desligado
- [x] 1.6 Documentar `ARQUIVOS_BUCKET`, `ARQUIVOS_ENDPOINT`, `ARQUIVOS_REGION`, `ARQUIVOS_ACCESS_KEY_ID` e `ARQUIVOS_SECRET_ACCESS_KEY` em `ContabOne.Api/.env.example`, com nota de que no Railway são *variable references* para o bucket

## 2. Modelo de dados

- [x] 2.1 Adicionar `TipoArquivo` a `Domain/Entities.cs` (`Id`, `EscritorioId`, `Nome`, `NomeNormalizado`, `Descricao?`, `Ativo`, `CriadoEm`, `AtualizadoEm`)
- [x] 2.2 Adicionar `ArquivoEscritorio` a `Domain/Entities.cs` (`Id`, `EscritorioId`, `TipoArquivoId`, `NomeExibicao`, `Extensao`, `TamanhoBytes`, `ChaveObjeto`, `EnviadoPorUsuarioId`, `EnviadoEm`)
- [x] 2.3 Declarar os `DbSet`s e os filtros globais de tenant das duas entidades em `Infra/AppDbContext.cs`, no formato `VeTodosOsEscritorios || x.EscritorioId == ...`
- [x] 2.4 Configurar índice único `(EscritorioId, NomeNormalizado)` em `TipoArquivo`, índice `(EscritorioId, EnviadoEm)` em `ArquivoEscritorio` e a FK do tipo com `DeleteBehavior.Restrict`
- [x] 2.5 Gerar a migration (`dotnet ef migrations add AdicionarArquivosEscritorio --project ContabOne.Api`) e conferir que o snapshot não foi editado à mão

## 3. Validação de arquivo

- [x] 3.1 Criar `Features/Arquivos/ValidadorArquivo.cs` com a lista fechada de extensões (`xls, xlsx, pdf, doc, docx, jpg, jpeg, png`), normalizando `jpeg` para `jpg`
- [x] 3.2 Implementar a checagem de assinatura binária por formato (`%PDF`, PNG, `FF D8 FF`, ZIP `PK\x03\x04` para OOXML, OLE2 `D0 CF 11 E0…` para xls/doc), recusando arquivo vazio
- [x] 3.3 Implementar o teto de 25 MB e expor a mensagem de erro com o limite
- [x] 3.4 Testes unitários do validador: cada formato aceito, `.txt` recusado, `.pfx` recusado, executável renomeado para `.pdf` recusado, arquivo de zero byte recusado, arquivo exatamente no limite aceito

## 4. Endpoints de tipo de arquivo

- [x] 4.1 Criar `Features/Arquivos/TiposArquivoEndpoints.cs` com `GET /`, `POST /`, `PUT /{id}` e `DELETE /{id}`
- [x] 4.2 Aplicar `EscritorioAdmin` nas escritas e deixar a leitura em `EscritorioUsuario`, resolvendo o escopo sempre pelo `TenantContext`
- [x] 4.3 Implementar a unicidade case-insensitive por escritório via `NomeNormalizado`, com a edição não colidindo consigo mesma
- [x] 4.4 Implementar a recusa de exclusão de tipo em uso (409 com a contagem de arquivos) e a exclusão livre do tipo sem arquivos
- [x] 4.5 Validador FluentValidation para nome obrigatório e tamanhos máximos de nome e descrição

## 5. Endpoints de arquivo

- [x] 5.1 Criar `Features/Arquivos/ArquivosEndpoints.cs` com `GET /` (filtros por tipo e por texto, ordem por envio decrescente), `POST /` (multipart), `GET /{id}/download` e `DELETE /{id}`
- [x] 5.2 No `POST`: validar o tipo (existe, é do escritório, está ativo), rodar o `ValidadorArquivo`, gravar o objeto em `escritorios/{escritorioId}/arquivos/{arquivoId}{ext}` e só então gravar a linha — removendo o objeto no `catch` se a gravação falhar
- [x] 5.3 Definir `EnviadoEm` e `EnviadoPorUsuarioId` no servidor, ignorando o que vier no corpo; usar o nome do arquivo enviado como `NomeExibicao` quando não houver um informado
- [x] 5.4 No `GET /{id}/download`: autorizar pelo tenant **antes** de assinar, e devolver presigned GET de 5 minutos com `response-content-disposition: attachment; filename="<NomeExibicao>"`
- [x] 5.5 No `DELETE`: remover a linha e depois o objeto, logando a chave se a remoção do objeto falhar
- [x] 5.6 Traduzir "armazenamento não configurado" em 503 com mensagem explícita no envio e no download, mantendo `GET /` funcionando
- [x] 5.7 Registrar os grupos `/api/arquivos` e `/api/arquivos/tipos` em `Program.cs` sob `EscritorioUsuario`, com `RequestSizeLimit`/`MultipartBodyLengthLimit` no endpoint de envio
- [x] 5.8 Adicionar a política de rate limit `arquivos` (fixed window, ~30/min, particionada pela sessão) e aplicá-la só ao `POST` de envio

## 6. Testes de API

- [x] 6.1 Implementação em memória de `IArmazenamentoArquivos` para os testes, sem rede
- [x] 6.2 Estender `IsolamentoTest.cs` com `TipoArquivo` e `ArquivoEscritorio`
- [x] 6.3 Estender `TraducaoLinqTest.cs` com as consultas novas (listagem com filtros)
- [x] 6.4 Testes dos tipos: nome obrigatório, unicidade case-insensitive por escritório, mesmo nome em escritórios distintos aceito, tipo em uso não excluído, usuário comum recusado nas escritas e aceito na leitura
- [x] 6.5 Testes dos arquivos: envio sem tipo recusado, tipo de outro escritório recusado, tipo inativo recusado, formato fora da lista recusado, `.pfx` recusado, conteúdo incompatível recusado, acima do teto recusado
- [x] 6.6 Testes de isolamento por identificador: download e exclusão de arquivo de outro escritório respondem "não encontrado"
- [x] 6.7 Teste da chave do objeto: nome com `../` não escapa do prefixo do escritório, e dois escritórios com o mesmo nome de arquivo geram objetos distintos
- [x] 6.8 Teste de 503 nos endpoints de envio/download com armazenamento não configurado, e de que `GET /` continua respondendo

## 7. Frontend

- [x] 7.1 Tipos de `TipoArquivo` e `ArquivoEscritorio` em `api/types.ts` e cliente em `api/endpoints/arquivos.ts` (envio multipart, listagem, download, exclusão, CRUD de tipo)
- [x] 7.2 Rota transversal `/arquivos` em `router/index.ts`, fora da família `/f/:produto`
- [x] 7.3 Item "Arquivos" na seção "Escritório" de `layouts/AppLayout.vue`, ao lado de Clientes, Tarefas e Agentes
- [x] 7.4 `views/ArquivosView.vue`: listagem com tipo, formato, tamanho, quem enviou e data; filtros por tipo e por texto; usando `.card-painel` e as classes de `components.css` (incluindo `.col-actions`)
- [x] 7.5 `components/arquivos/EnvioArquivo.vue`: seleção de arquivo com `accept` restrito, seletor de tipo listando só os ativos, nome de exibição opcional e checagem de tamanho antes de subir
- [x] 7.6 `components/arquivos/FormularioTipoArquivo.vue` e a tela de gerenciamento dos tipos, visível só para `EscritorioAdmin`
- [x] 7.7 Download: pedir a URL assinada à API e navegar até ela, sem passar os bytes pelo painel
- [x] 7.8 Estado de armazenamento indisponível: quando a API responde 503, desabilitar envio e download com aviso, mantendo a listagem
- [x] 7.9 Vitest da validação de formato e tamanho no cliente, do agrupamento/filtro da listagem e do estado indisponível (MSW com `onUnhandledRequest: 'error'`)
- [x] 7.10 Playwright: cadastrar tipo → enviar arquivo → aparecer na lista → baixar

## 8. Fechamento

- [x] 8.1 `npm --prefix ContabOne.Frontend run build` (typecheck) e `dotnet test` limpos, sem `DATABASE_URL` no ambiente
- [ ] 8.2 Configurar as cinco variáveis no serviço da API no Railway como *variable references* para o bucket, no ambiente `production`
- [x] 8.3 Atualizar `README.md` com a funcionalidade e as variáveis novas
- [x] 8.4 Registrar em `AGENTS.md` a fronteira de privacidade desta exceção: documento administrativo do escritório, enviado à mão; certificado e conteúdo fiscal continuam fora
