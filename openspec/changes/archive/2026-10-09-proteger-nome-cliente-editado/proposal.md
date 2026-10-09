## Why

A sincronização do agente (`AgentEndpoints.cs`, `existente.Nome = c.Nome;`) sobrescreve incondicionalmente o `Nome` de todo cliente já existente. Quando o `.pfx` do escritório está fora do padrão `codigo_CNPJ_Nome_s.SENHA_v.DD.MM.AAAA`, o agente manda o nome do arquivo inteiro como razão social (ex.: `SIMAO E COUTINHO_123456_v.14.01.2027`). Em produção, 36 nomes corrigidos por carga manual voltaram a esse formato na sincronização seguinte, enquanto o CNPJ ficou intacto — porque só ele tem proteção (`CnpjConfirmadoManualmente`).

## What Changes

- `Cliente` ganha a marca `NomeEditadoManualmente` (bool, padrão `false`), análoga a `CnpjConfirmadoManualmente`, com migration.
- A sincronização do agente deixa de gravar `Nome` quando a marca está ligada. Cliente novo continua nascendo com o nome do agente; cliente sem marca continua sendo atualizado como hoje.
- A edição de cliente pela tela liga a marca **somente** quando o nome enviado difere do gravado — salvar outros campos sem mexer no nome não trava o nome.
- Carga pós-deploy em produção (fora do código, com confirmação explícita): marcar as 106 linhas já atualizadas (L&J e Mudahr) e regravar os 36 nomes que voltaram.
- Opcional, depois do servidor protegido: o agente (`Nfse.Agent/nfse.py`, `ler_certificado`) não tratar o nome de arquivo fora do padrão como razão social.

## Capabilities

### New Capabilities

### Modified Capabilities
- `gestao-clientes`: novas regras de precedência do nome — a sincronização do agente respeita o nome editado manualmente, e a edição pela tela marca o nome como editado quando ele muda.

## Impact

- `ContabOne.Api`: `Domain/Entities.cs` (campo), nova migration, `Features/Agent/AgentEndpoints.cs` (handshake), `Features/Clientes/ClientesEndpoints.cs` (PUT); testes em `ContratoAgenteTest`/`ClientesTest`.
- Banco de produção: coluna nova + `UPDATE` de dados pós-deploy.
- Frontend: nenhuma mudança obrigatória (indicador "nome definido manualmente" é opcional).
- Agente em campo: sem mudança — a correção é toda no servidor.
