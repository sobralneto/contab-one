## 1. API — desfazer o modelo por mensagem

- [x] 1.1 Remover `MensagemDet.Prioridade`, o `PUT /mensagens/{id}/prioridade`, o campo no `GET` e os testes por mensagem de `DetMensagensTest.cs`
- [x] 1.2 Descartar a migration `PrioridadeMensagemDet` ainda não publicada (e restaurar o snapshot) para regerar depois com o modelo novo

## 2. API — prioridade por assunto

- [x] 2.1 Manter o enum `PrioridadeMensagemDet` e criar a entidade `PrioridadeAssuntoDet` (`EscritorioId`, `AssuntoChave`, `Prioridade`, `AtualizadaEm`) em `Domain/Entities.cs`
- [x] 2.2 Em `AppDbContext`: `DbSet`, índice único `(EscritorioId, AssuntoChave)` e query filter de tenant no formato padrão
- [x] 2.3 Gerar a migration com `dotnet ef migrations add PrioridadeAssuntoDet --project ContabOne.Api` (sem editar o snapshot)
- [x] 2.4 `GET /api/det/mensagens` devolve `prioridade` derivada do assunto de cada mensagem (chave normalizada no servidor)
- [x] 2.5 `PUT /api/det/assuntos/prioridade` (`{ assunto, prioridade }`): upsert por chave, nulo remove a linha, `Enum.IsDefined` → 400, `EscritorioId` do `TenantContext`, 204

## 3. Testes da API

- [x] 3.1 `DetMensagensTest`: assunto sem classificação → nulo; definir/trocar/limpar; vale para todas as mensagens do assunto, inclusive variação de caixa/espaços e "sem assunto"; mensagem coletada depois já vem com a prioridade
- [x] 3.2 Valor inválido → 400 sem alterar; chave de agente → negado; reclassificar não duplica registro
- [x] 3.3 `IsolamentoTest`: prioridade de um escritório não aparece nem é alterada por outro; `TraducaoLinqTest` cobre a consulta nova

## 4. Frontend

- [x] 4.1 `api/types.ts`: manter `prioridade: number | null` em `MensagemDetDto` e as constantes; `api/endpoints/det.ts`: trocar por `definirPrioridadeAssuntoDet(assunto, prioridade)` apontando para o `PUT` novo
- [x] 4.2 Manter `.badge-prioridade` em `components.css`; `PrioridadeMensagem.vue` com modo `editavel` (somente na linha do grupo) e modo só selo
- [x] 4.3 `MensagensDet.vue`: controle na linha do grupo (sem expandir o grupo ao acionar), selo do grupo = prioridade do assunto, selo somente leitura na lista plana, nas mensagens expandidas e no modal; remover o controle por mensagem; atualização otimista aplicada a todas as mensagens do assunto, com reversão em erro

## 5. Testes do frontend e verificação

- [x] 5.1 Vitest: cor/classe e texto de cada nível e de "Sem prioridade"; selo do grupo, da lista e do modal vêm do assunto
- [x] 5.2 Vitest: classificar pelo grupo (`PUT` com o assunto certo), refletir na lista plana, limpar, reversão em falha, grupo não expande ao acionar o controle, ausência de controle por mensagem
- [ ] 5.3 Rodar `npm test` e `npm --prefix ContabOne.Frontend run build`; conferir visualmente em `/f/det` nos temas claro e escuro
