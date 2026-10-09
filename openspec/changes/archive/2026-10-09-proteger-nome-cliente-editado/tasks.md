## 1. Modelo e migration

- [x] 1.1 Confirmar que o trabalho pendente da outra sessão na API (`Entities.cs`, migration `RemoverPaginasMensagensEExecucoesDoDet`) está commitado
- [x] 1.2 Adicionar `NomeEditadoManualmente` (bool, padrão `false`) a `Cliente` em `Domain/Entities.cs`, com comentário no estilo de `CnpjConfirmadoManualmente`
- [x] 1.3 Gerar a migration com `dotnet ef migrations add AdicionaNomeEditadoManualmenteEmCliente --project ContabOne.Api` (sem editar o snapshot à mão)

## 2. Handshake do agente

- [x] 2.1 Em `Features/Agent/AgentEndpoints.cs`, atribuir `existente.Nome = c.Nome` somente quando `!existente.NomeEditadoManualmente`, com comentário explicando a regra
- [x] 2.2 Manter a criação de cliente novo com o nome do agente e a flag falsa

## 3. Edição pela tela

- [x] 3.1 Em `Features/Clientes/ClientesEndpoints.cs` (PUT), ligar `NomeEditadoManualmente` apenas quando `req.Nome` for diferente do nome gravado, comparando antes de atribuir
- [x] 3.2 Garantir que salvar sem alterar o nome não liga nem desliga a flag

## 4. Testes

- [x] 4.1 `ContratoAgenteTest`: sincronização de cliente com flag ligada não altera o nome
- [x] 4.2 `ContratoAgenteTest`: sincronização de cliente com flag desligada continua atualizando o nome (o teste existente "Nome Novo" segue passando)
- [x] 4.3 `ClientesTest`: PUT que altera o nome liga a flag
- [x] 4.4 `ClientesTest`: PUT que não altera o nome não liga a flag e não desliga uma já ligada
- [x] 4.5 Rodar `npm test` na raiz e `dotnet test` (a camada de banco inclui a migration)

## 5. Dados em produção (pós-deploy, com confirmação explícita)

- [ ] 5.1 Após o deploy, mostrar dry-run e pedir "ok" antes de gravar
- [ ] 5.2 Marcar `NomeEditadoManualmente = true` nas 106 linhas do de/para (L&J e Mudahr) e regravar os 36 nomes que voltaram
- [ ] 5.3 Rodar uma sincronização real do agente e conferir que os nomes não voltam

## 6. Complemento opcional no agente

- [ ] 6.1 Em `Nfse.Agent/nfse.py` (`ler_certificado`), não tratar o nome de arquivo fora do padrão como razão social
- [ ] 6.2 Ajustar `testes/teste_regressao_coleta.py` e rodar `py -3.14 Nfse.Agent/testes/executar_tudo.py`
