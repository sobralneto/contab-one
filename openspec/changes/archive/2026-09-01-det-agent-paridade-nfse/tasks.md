## 1. API — dado e endpoints

- [x] 1.1 Adicionar entidade `MensagemDet` em `Domain/Entities.cs`
      (`Id, ExecucaoId, ClienteId, IdMensagemPortal, Numero, DataEnvio,
      DataLeitura, Prazo, Remetente, Tipo, Assunto, Situacao, Link,
      RecebidaEm`), com FK para `Execucao` e `Cliente`.
- [x] 1.2 Mapear `MensagemDet` em `AppDbContext` com o filtro global de
      tenant no mesmo formato de todo entidade tenant-scoped (via
      `Cliente.EscritorioId`), índice único em
      `(ExecucaoId, ClienteId, IdMensagemPortal)` para o upsert por chave.
- [x] 1.3 Gerar migration (`dotnet ef migrations add AdicionarMensagensDet
      --project ContabOne.Api`) e conferir a snapshot gerada.
- [x] 1.4 Adicionar `POST /api/agent/execucoes/{id}/mensagens-det` em
      `AgentEndpoints.cs`, espelhando `EnviarMetricasAsync`: filtra por
      `clientesDoTenant`, faz upsert por `(ExecucaoId, ClienteId,
      IdMensagemPortal)`.
- [x] 1.5 Criar `Features/Det/DetEndpoints.cs` com
      `GET /api/det/mensagens?clienteId=` (JWT, escopado por
      `TenantContext`, filtro opcional por cliente), mapeado a partir de
      `Program.cs`.
- [x] 1.6 Cobrir isolamento multi-tenant de `MensagemDet` em
      `IsolamentoTest.cs`.
- [x] 1.7 Testar tradutibilidade de qualquer predicado LINQ novo sobre
      `MensagemDet` em `TraducaoLinqTest.cs`, se houver propriedade
      computada.
- [x] 1.8 Testes de integração para o endpoint agente (upsert, descarte de
      cliente de outro tenant) e para o endpoint do painel (sem filtro, com
      filtro por cliente).

## 2. `Det.Agent` — configuração e cliente de API

- [x] 2.1 Criar `config.exemplo.toml` no formato de
      `Nfse.Agent/config.exemplo.toml` (`[api] url`/`chave`, `senha_padrao`,
      `[senhas]`), documentando a migração do `.env` atual.
- [x] 2.2 Criar `api_client.py` em `Det.Agent/src/det_bot/`, modelado no de
      `Nfse.Agent`: leitura de `config.toml`, handshake, hash/mascaramento
      de CNPJ, upsert de clientes, abertura/finalização de execução, envio
      de mensagens, fila de pendências local com descarte após 30 dias.
- [x] 2.3 Ajustar `settings.py` para carregar `[api]` de `config.toml` e
      recusar rodar sem `url`/`chave` (código de saída `3`, mesmo padrão já
      documentado no README para erro de configuração).
- [x] 2.4 Migrar a resolução de senha do certificado de `DET_PFX_SENHA`
      (`.env`) para a ordem padrão: senha no nome do arquivo → `[senhas]`
      pelo nome do arquivo → `senha_padrao` → `DET_PFX_SENHA` como
      fallback.
- [x] 2.5 Atualizar `README.md` (seção 3, Configuração) substituindo a
      referência a `.env`/`DET_PFX_SENHA` por `config.toml`.

## 3. `Det.Agent` — envio do relatório e remoção do CSV automático

- [x] 3.1 Em `runner.py`, ao final da varredura, mapear as mensagens
      coletadas de cada empresa para o payload de
      `POST /api/agent/execucoes/{id}/mensagens-det`, usando o
      `Cliente.Id` retornado pelo upsert (fonte: `id_mensagem`, `numero`,
      `data_envio_iso`, `data_leitura`, `prazo`, `remetente`, `tipo`,
      `assunto`, `situacao`, `link`).
- [x] 3.2 Abrir a execução no início da varredura e finalizá-la no fim,
      reportando o status agregado (sucesso/parcial/falha) da mesma forma
      que os códigos de saída já expressam.
- [x] 3.3 Remover a chamada automática a `relatorio.py` (geração de CSV) do
      fluxo principal de `runner.py` quando `[api]` estiver configurada;
      manter `tools/exportar_csv.py` funcionando sobre o JSON salvo.
- [x] 3.4 Sem `[api]` configurada, a ferramenta recusa rodar (código de
      saída `3`) — decisão do usuário em 2026-09-01, alinhando com o spec
      `agente-det-integracao-api` (o texto original de "preservar CSV local"
      do design.md ficou obsoleto).
- [x] 3.5 Testes offline (fake HTTP server nos moldes de
      `Nfse.Agent/testes/_fake_api.py`) cobrindo: recusa sem `[api]`, 401
      bloqueia imediatamente, upsert de cliente, envio de mensagens,
      fila de pendências e reenvio.

## 4. Catálogo e frontend

- [x] 4.1 Definir o id da nova página em `PaginaFerramenta` (backend) e
      registrar o texto associado em `explicacoesPagina.ts` (frontend).
- [x] 4.2 Criar a view `DetMensagensView.vue`, seguindo o padrão de
      `ExecucoesView.vue`: tabela com os campos de `MensagemDet`, filtro de
      cliente, uso das classes compartilhadas de `components.css`.
- [x] 4.3 Adicionar o endpoint ao cliente HTTP do frontend
      (`src/api/endpoints/`) e os tipos correspondentes em `types.ts`.
- [x] 4.4 Registrar a rota `/f/det/mensagens` (ou id equivalente) em
      `router/index.ts`, respeitando `router/guards.ts` (só navegável se o
      produto declarar a página).
- [x] 4.5 Testes: Vitest da view/store e, se aplicável, um cenário de E2E
      cobrindo a navegação até a página quando o produto DET está
      habilitado.

## 5. Dados de catálogo (fora do deploy de código)

- [ ] 5.1 Cadastrar/atualizar o `Produto` de código `det` no catálogo
      (admin), incluindo a nova página em `Paginas` — trabalho de dados,
      feito após o deploy, por escritório, conforme `design.md`.
