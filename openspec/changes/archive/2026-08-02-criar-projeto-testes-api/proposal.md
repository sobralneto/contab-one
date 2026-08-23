## Why

A API não tem nenhum teste automatizado — não existe `.sln`, projeto de teste nem workflow de CI. A revisão das três camadas encontrou dois defeitos que só aparecem em runtime (`a.Aberto` num predicado EF, que derruba a finalização de execuções com falha e o job diário de alertas) e que nenhum build pega: `dotnet build` passa limpo com os dois presentes.

O agente Python, em contraste, tem suíte offline com 7 arquivos e fixtures de API falsa. A camada que mais quebra é justamente a que não tem rede de proteção — e é a única das três que outras duas dependem.

## What Changes

- Criar `ContabOne.Api.Tests` (xUnit) e uma solution na raiz reunindo API e testes.
- Ajustar o `catch` de `Program.cs` para não engolir `HostAbortedException`, e expor `Program` como classe parcial pública — sem isso o host de teste in-process não consegue subir a aplicação.
- **Guarda de tradução LINQ**: teste que compila para SQL via `ToQueryString()` sem abrir conexão, cobrindo as consultas que usam propriedades computadas não-mapeadas (`Alerta.Aberto`, `Agente.Ativo`). É a classe de defeito que já ocorreu duas vezes.
- **Contrato dos endpoints do agente**: handshake, upsert de clientes, envio de métricas e finalização de execução, verificados contra Postgres real efêmero — incluindo o mapa `codigo → id` do upsert e os enums trafegando como inteiro.
- **Isolamento multi-tenant**: testes que provam que os query filters globais impedem um escritório de enxergar dados de outro, e que `IgnoreQueryFilters()` só aparece onde o admin precisa.
- Testes das funções puras de segurança (`ApiKeyHasher`, `CnpjHasher`), incluindo a paridade do hash de CNPJ com a implementação Python do agente.

## Capabilities

Esta mudança é de tooling: cria infraestrutura de teste para comportamento que já existe e já está implementado. Nenhum requisito novo é introduzido e nenhum comportamento observável do produto muda — os ajustes em `Program.cs` afetam apenas o caminho de host de teste. Por isso o change declara `skip_specs: true` no seu `.openspec.yaml`.

Os defeitos que motivaram esta mudança são corrigidos em `corrigir-integracao-tres-camadas`, e é lá que a especificação do comportamento correto vive.

## Impact

**Novo projeto**

- `ContabOne.Api.Tests/` — xUnit, referência a `ContabOne.Api`
- `ContabOne.sln` na raiz

**Alterações no código existente**

- `ContabOne.Api/Program.cs` — filtro de exceção no `catch` e `public partial class Program`

**Dependências novas (apenas no projeto de teste)**

- `xunit`, `Microsoft.NET.Test.Sdk`
- `Microsoft.AspNetCore.Mvc.Testing` — host in-process
- `Testcontainers.PostgreSql` — Postgres efêmero por execução. Requer Docker disponível na máquina e no CI.

**Relação com outras changes**

- `corrigir-integracao-tres-camadas` tinha um grupo de tarefas criando este projeto. Esse grupo sai de lá e passa a apontar para esta change como pré-requisito; os testes específicos daquelas correções continuam lá.
