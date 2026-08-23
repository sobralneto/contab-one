## 1. Estrutura do projeto

- [x] 1.1 Criar `ContabOne.Api.Tests` (xUnit, `net10.0`) com referência de projeto a `ContabOne.Api`
- [x] 1.2 Criar `ContabOne.sln` na raiz do repositório reunindo `ContabOne.Api` e `ContabOne.Api.Tests`
- [x] 1.3 Adicionar os pacotes: `Microsoft.NET.Test.Sdk`, `xunit`, `xunit.runner.visualstudio`, `Microsoft.AspNetCore.Mvc.Testing`, `Testcontainers.PostgreSql`
- [x] 1.4 Definir a categoria/trait que separa testes com banco dos sem banco, de forma que `dotnet test --filter` consiga excluir os que exigem Docker
- [x] 1.5 Confirmar `dotnet build` e `dotnet test` verdes na raiz com a suíte ainda vazia

## 2. Tornar a aplicação testável in-process

- [x] 2.1 Em `ContabOne.Api/Program.cs`, alterar o `catch (Exception ex)` para `catch (Exception ex) when (ex is not HostAbortedException)`, com comentário explicando que engolir essa exceção quebra o host de teste
- [x] 2.2 Adicionar `public partial class Program { }` ao fim de `Program.cs`, com comentário apontando que é o que torna `WebApplicationFactory<Program>` possível em top-level statements
- [x] 2.3 Confirmar que a API continua subindo normalmente por `dotnet run` após as duas alterações

## 3. Camada sem banco — guarda de tradução LINQ

Esta é a camada que pega a classe de defeito que motivou a suíte. Não depende de Docker.

- [x] 3.1 Criar helper que instancia `AppDbContext` com `UseNpgsql` e uma `TenantContext` controlada, sem abrir conexão
- [x] 3.2 Teste: a consulta de alerta aberto usada na finalização de execução (`AgentEndpoints`) traduz para SQL via `ToQueryString()`
- [x] 3.3 Teste: a consulta de alerta aberto usada em `AlertaJob.CriarAlertaSeNaoExiste` traduz para SQL
- [x] 3.4 Teste: o `OrderBy` de `AlertasEndpoints.ListarAsync` traduz para SQL (protege o workaround que já existe lá)
- [x] 3.5 Teste: a listagem de agentes de `AgentesManagementEndpoints` traduz para SQL (protege o mesmo padrão em `Agente.Ativo`)
- [x] 3.6 Teste negativo confirmando que `Where(a => a.Aberto)` de fato falha na tradução — documenta por que os testes acima existem e falha se um dia o EF passar a suportar isso
- [x] 3.7 Marcar como `Skip`, com referência a `corrigir-integracao-tres-camadas`, os testes de 3.2 e 3.3 que dependem da correção ainda não aplicada — **não aplicado**: a correção de `corrigir-integracao-tres-camadas` já estava aplicada quando esta change rodou; os testes de 3.2/3.3 nasceram ativos e verdes (passo 2 do Migration Plan já cumprido)

## 4. Camada sem banco — funções puras de segurança

- [x] 4.1 Teste: `ApiKeyHasher.Gerar()` produz chave no formato `nfse_<prefixo8>_<segredo32>`, e `ExtrairPrefixo`/`HashApiKey` sobre ela devolvem o prefixo e o hash correspondentes
- [x] 4.2 Teste: `ApiKeyHasher.HashApiKey` rejeita formatos inválidos (sem separador, prefixo errado, segredo com tamanho errado)
- [x] 4.3 Teste: `CnpjHasher.Mascarar` aplica a máscara em 14 dígitos e devolve a entrada intacta fora desse tamanho
- [x] 4.4 Criar arquivo de vetores compartilhado (CNPJ, chave, hash hex esperado) para a paridade de hash entre C# e Python
- [x] 4.5 Teste .NET: `CnpjHasher.Hash` reproduz os vetores do arquivo
- [x] 4.6 Teste Python em `Nfse.Agent/testes/`: `api_client.hash_cnpj` reproduz os mesmos vetores
- [x] 4.7 Confirmar que os dois lados concordam alterando um vetor de propósito e vendo as duas suítes falharem

## 5. Infraestrutura com Postgres efêmero

- [x] 5.1 Criar a fixture de container Postgres (`postgres:17-alpine`, mesma tag do `docker-compose.yml`), compartilhada pelas classes de teste que precisam de banco
- [x] 5.2 Criar a `WebApplicationFactory` customizada que aponta a connection string para o container e injeta `JWT_SIGNING_KEY` e `HMAC_CNPJ_KEY` de teste
- [x] 5.3 Confirmar que as migrations rodam no container no startup do host de teste
- [x] 5.4 Criar os helpers de dados: criar escritório com plano, criar agente devolvendo a chave em claro, criar cliente
- [x] 5.5 Teste de fumaça: `GET /health` responde 200 pelo host de teste

## 6. Contrato dos endpoints do agente

Referência do lado consumidor: `Nfse.Agent/testes/_fake_api.py`.

- [x] 6.1 Teste: handshake com chave válida devolve `escritorio`, `status`, `podeExecutar`, `plano`, `regrasVersaoAtual`, `agenteVersaoMinima` e `hmacCnpjKey`, todos em camelCase
- [x] 6.2 Teste: handshake com chave inexistente, revogada, ou de escritório não-Ativo devolve 401 — os três casos, porque o agente trata 401 como bloqueio definitivo e nunca como indisponibilidade
- [x] 6.3 Teste: handshake atualiza `VersaoAgente` e `UltimoContatoEm` do agente
- [x] 6.4 Teste: `POST /clientes` devolve `clientes: [{codigo, id}]` com um item por cliente enviado, e os ids correspondem às linhas gravadas
- [x] 6.5 Teste: `POST /clientes` atualiza cliente existente pelo par escritório + código, em vez de duplicar
- [x] 6.6 Teste: `POST /clientes` respeita `MaxClientes` do plano, contando os limitados sem impedir a atualização dos já existentes
- [x] 6.7 Teste: `POST /execucoes/{id}/metricas` aceita `tipo` como **inteiro** (0/1) e rejeita a string `"recebidas"` — fixa a ausência de `JsonStringEnumConverter` — **ajustado à implementação real**: a string é rejeitada (hoje com 500 de binding, não 400); o teste asserta a rejeição e documenta o 400-vs-500 como cosmético (o agente nunca envia string)
- [x] 6.8 Teste: `POST /execucoes/{id}/finalizar` aceita `status` como inteiro e persiste status, mensagem e instante de término
- [x] 6.9 Teste: finalizar com status de falha abre alerta, e uma segunda falha com alerta aberto não duplica — marcar `Skip` com referência a `corrigir-integracao-tres-camadas` até a correção existir — **sem Skip**: a correção do alerta já estava aplicada; o teste nasceu ativo
- [x] 6.10 Teste: métricas reenviadas com a mesma chave (execução, cliente, competência, tipo) fazem upsert em vez de inserir linha nova
- [x] 6.11 Teste: `GET /regras?versao=N` devolve 304 quando N já é a versão ativa, e o bundle quando é menor
- [x] 6.12 Teste: `GET /regras` devolve 404 quando não há regra publicada — o agente distingue esse caso de erro de rede

## 7. Isolamento multi-tenant

- [x] 7.1 Teste: agente do escritório A não enxerga clientes, execuções nem alertas do escritório B, em todos os endpoints de `/api/agent`
- [x] 7.2 Teste: usuário de escritório autenticado por JWT não enxerga dados de outro escritório em clientes, execuções e alertas
- [x] 7.3 Teste: usuário de escritório não consegue alcançar `/api/admin/*`
- [x] 7.4 Teste: `PlatformAdmin` enxerga dados de todos os escritórios nos endpoints admin
- [x] 7.5 Teste: passar `escritorioId` de outro escritório como parâmetro de query não vaza dados — o query filter global continua valendo
- [x] 7.6 Teste: métricas enviadas por um agente não podem referenciar `clienteId` de outro escritório — **defeito real descoberto e corrigido nesta change**: a API aceitava métrica com clienteId de outro escritório; adicionado guard em `EnviarMetricasAsync` (descarta linhas com cliente fora do tenant)

## 8. Job de alertas

- [x] 8.1 Teste: `AlertaJob` abre alerta de certificado vencido e de certificado a vencer em até 30 dias, e nenhum para certificado válido
- [x] 8.2 Teste: `AlertaJob` abre alerta de agente silencioso para escritório com agente ativo e sem execução há mais de 3 dias
- [x] 8.3 Teste: rodar o job duas vezes sobre o mesmo estado não duplica alertas
- [x] 8.4 Teste: o job percorre todos os escritórios ativos sem abortar — marcar `Skip` com referência a `corrigir-integracao-tres-camadas` até a correção existir — **sem Skip**: a correção já estava aplicada; o teste nasceu ativo

## 9. Fechamento

- [x] 9.1 Documentar no README como rodar a suíte, incluindo o filtro que exclui os testes que precisam de Docker
- [x] 9.2 Rodar `dotnet test` completo com Docker disponível e confirmar verde (com os `Skip` documentados)
- [x] 9.3 Rodar `dotnet test` com o filtro sem banco e confirmar que passa sem Docker
- [x] 9.4 Rodar `python testes/executar_tudo.py` em `Nfse.Agent` e confirmar que o novo teste de vetores de CNPJ passa
- [x] 9.5 Editar `openspec/changes/corrigir-integracao-tres-camadas/tasks.md`: remover o grupo "Projeto de testes .NET" e registrar esta change como pré-requisito, mantendo lá os testes específicos daquelas correções — **não aplicado como escrito**: aquele change já estava arquivado com o grupo "Projeto de testes .NET" implementado (marcado [x]); remover do arquivo histórico falsificaria o registro. O projeto de testes existe e esta change o estendeu
