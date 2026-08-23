## Context

Ver [proposal.md](proposal.md) para a motivação. As restrições que moldam a abordagem:

- **`Program.cs` usa top-level statements dentro de `try`/`catch (Exception)`** com Serilog. Isso colide diretamente com `WebApplicationFactory`: o `HostFactoryResolver` do ASP.NET Core sobe a aplicação e interrompe o boot lançando `HostAbortedException` para capturar o `IHost` construído. Um `catch (Exception)` largo engole essa exceção e a fábrica falha com "The entry point exited without ever building an IHost".
- **`Program.cs` roda `db.Database.MigrateAsync()` no startup.** Qualquer host de teste que suba a aplicação de verdade vai migrar o banco apontado — o que é desejável contra um container efêmero, e destrutivo contra o banco de desenvolvimento.
- **`AppDbContext` recebe `TenantContext` no construtor** e os query filters globais leem `_tenantContext.EscritorioId` capturado na expressão. Isso significa que o filtro é avaliado com o valor vigente no momento da query, e que um teste de isolamento precisa controlar o `TenantContext` explicitamente.
- **O agente Python já tem uma API falsa** em `Nfse.Agent/testes/_fake_api.py`, modelada a partir de `AgentEndpoints.cs`. Ela é a especificação executável de fato do contrato, do lado do consumidor.
- **Docker 29.6 disponível** na máquina de desenvolvimento.
- **Não existe CI hoje.** Esta mudança cria a base para um, mas não o cria.

## Goals / Non-Goals

**Goals:**

- Pegar a classe de defeito "propriedade computada em predicado EF" sem precisar de banco e sem precisar rodar a aplicação.
- Verificar o contrato do agente contra o schema e o banco reais, não contra mocks — o valor está justamente em pegar divergência entre o que o C# serializa e o que o Python espera.
- Provar o isolamento multi-tenant, que hoje não tem nenhuma verificação e cuja quebra seria o pior defeito possível neste produto.
- Deixar `dotnet test` funcionando na raiz, sem passos manuais.

**Non-Goals:**

- Criar pipeline de CI. A base fica pronta; o workflow é assunto separado.
- Cobrir os endpoints de dashboard, clientes, alertas e admin. Ficam para depois — a escolha aqui foi profundidade no que quebra, não largura.
- Testar o frontend. Camada diferente, ferramenta diferente.
- Corrigir os defeitos que os testes vão expor. As correções vivem em `corrigir-integracao-tres-camadas`; aqui os testes que dependem delas nascem já apontando para o comportamento correto e, portanto, **vermelhos até aquela change ser aplicada** (ver Migration Plan).

## Decisions

### 1. Filtro de exceção em `Program.cs`, não reestruturação

Para o host de teste funcionar, o `HostAbortedException` precisa escapar do `catch`.

Alternativas consideradas:

- **Extrair a construção do host para um método `CreateApp()` chamado pelos testes.** Mais "limpo" na teoria, mas reescreve o arquivo de bootstrap inteiro por causa de um teste, e afasta o código do padrão de top-level statements que o resto do projeto usa.
- **Não usar `WebApplicationFactory`**, testando handlers diretamente. Perde exatamente o que se quer verificar: pipeline de autenticação, middleware de tenant, serialização camelCase e enum-como-inteiro.

Escolha: `catch (Exception ex) when (ex is not HostAbortedException)`. Uma linha, sem reestruturação, e o comportamento em produção fica idêntico — `HostAbortedException` só é lançada por um host que está sendo interrompido de propósito. Mais `public partial class Program { }` no fim do arquivo, o padrão documentado para tornar o entry point visível ao `WebApplicationFactory<Program>`.

### 2. Duas camadas de teste, com fronteira explícita

- **Sem banco** (`ToQueryString()`, funções puras): tradução LINQ, hashers, validadores. Rodam em milissegundos, sem Docker.
- **Com Postgres efêmero** (Testcontainers): endpoints do agente e isolamento multi-tenant.

A fronteira importa: se tudo exigir Docker, a suíte deixa de ser rodada durante o desenvolvimento. A guarda de tradução LINQ — que é o teste mais valioso desta change, porque cobre um defeito que já ocorreu — fica deliberadamente na camada sem banco.

Alternativa considerada: **EF Core InMemory provider** para a camada com banco. Descartado, e este é o ponto mais importante do design — o provider InMemory não traduz LINQ para SQL, então ele passaria alegremente nos dois predicados com `a.Aberto` que quebram em produção. Um teste que não pega o defeito que motivou a suíte é pior que nenhum teste.

### 3. Testcontainers em vez do `docker-compose.yml` existente

Alternativas consideradas:

- **Apontar para o Postgres do `docker-compose`.** Exige que alguém tenha subido o compose antes, e compartilha instância com o banco de desenvolvimento — um teste que trunca tabelas apaga dados de trabalho. Contornável com um banco separado, mas o contorno é manual e fácil de esquecer.

Escolha: Testcontainers sobe um container por execução da suíte, com ciclo de vida gerenciado. Cada classe de teste com banco compartilha o container e isola por escritório, não por banco — criar escritórios distintos é mais barato que recriar schema, e é exatamente o eixo que os testes de isolamento precisam exercitar.

A migration roda dentro do container, o que dá um efeito colateral bom: **as migrations passam a ser exercitadas a cada execução da suíte**, incluindo o seed de `RegraColeta` que `corrigir-integracao-tres-camadas` introduz.

### 4. O contrato do agente é verificado contra o `_fake_api.py`, não reinventado

`Nfse.Agent/testes/_fake_api.py` já codifica o que o agente espera: nomes de campo em camelCase, `tipo`/`status` como inteiro, `clientes: [{codigo, id}]` na resposta do upsert. Os testes de contrato do lado C# afirmam as mesmas propriedades, com referência explícita ao arquivo Python nos comentários.

Isso não é acoplamento entre suítes — nenhuma importa a outra. É reconhecer que o consumidor real já documentou o contrato, e que divergir dele silenciosamente é o defeito que se quer pegar. Em particular, os testes fixam que **os enums viajam como inteiro** nos endpoints do agente e **como string** nos endpoints do frontend, porque não há `JsonStringEnumConverter` registrado e cada lado depende disso de forma oposta.

### 5. Paridade do hash de CNPJ entre C# e Python

`CnpjHasher.Hash` (C#) e `api_client.hash_cnpj` (Python) precisam produzir o mesmo hex para a mesma entrada — se divergirem, o servidor deixa de reconhecer o mesmo cliente entre execuções e duplica cadastros silenciosamente. Hoje nada verifica isso; `CnpjHasher` sequer é chamado pela API.

O teste fixa vetores conhecidos (entrada, chave, hash esperado) num arquivo compartilhado, verificado dos dois lados — mesma técnica do corpus de bundles proposto em `corrigir-integracao-tres-camadas`.

### 6. xUnit

Escolha convencional para .NET, é o que a documentação do `Microsoft.AspNetCore.Mvc.Testing` assume, e o que qualquer pessoa contratada para mexer nisso vai reconhecer. NUnit e TUnit resolveriam igual; não há motivo neste projeto para divergir do padrão.

## Risks / Trade-offs

- **Docker vira dependência para rodar parte da suíte** → Mitigação: separação por trait/categoria, de forma que `dotnet test --filter Category!=Banco` rode a camada rápida sem Docker. A guarda de tradução LINQ fica sempre nessa camada.
- **Primeira execução baixa a imagem do Postgres e é lenta** → Aceito. Execuções seguintes reaproveitam a imagem. Fixar a mesma tag do `docker-compose.yml` (`postgres:17-alpine`) evita baixar uma segunda imagem e mantém teste e desenvolvimento no mesmo motor.
- **Mexer em `Program.cs` por causa de teste** → É o custo mínimo conhecido para host in-process em top-level statements. O filtro é preciso o bastante para não alterar comportamento em produção, e um comentário no código explica por que ele existe — sem isso, alguém "limpa" o filtro em seis meses e a suíte quebra de um jeito confuso.
- **Testes nascem vermelhos** → Os testes de finalização com falha e do job de alertas descrevem o comportamento correto, que só passa depois de `corrigir-integracao-tres-camadas`. Se as duas changes não forem aplicadas em sequência, fica uma suíte vermelha no repositório, que é o pior estado possível para uma suíte nova. Ver Migration Plan.
- **Testcontainers ainda não cobre o job de alertas** → `CronRunner` monta o próprio host a partir de `DATABASE_URL`, fora do `WebApplicationFactory`. Testá-lo exige instanciar `AlertaJob` diretamente com um `AppDbContext` apontado para o container, o que é feito, mas não exercita o caminho de linha de comando.

## Migration Plan

1. **Aplicar esta change primeiro**, deixando de fora os testes que dependem de correção — ou marcando-os como `Skip` com referência explícita à outra change. A suíte entra no repositório verde.
2. **Aplicar `corrigir-integracao-tres-camadas`** e, no grupo de correções de defeito, remover o `Skip` dos testes correspondentes. Eles passam a ser a verificação daquelas correções, em vez de dívida.
3. Remover o grupo "Projeto de testes .NET" do `tasks.md` de `corrigir-integracao-tres-camadas` e registrar esta change como pré-requisito.

**Rollback**: excluir o projeto de teste e a solution, e reverter as duas linhas de `Program.cs`. Nenhum dado, nenhuma migration, nenhum contrato afetado.
