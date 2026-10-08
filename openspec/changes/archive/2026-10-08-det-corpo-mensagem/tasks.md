## 1. API

- [x] 1.1 `Domain/Entities.cs`: `MensagemDet` ganha `Corpo` (`string?`) e
      perde `Situacao`; atualizar o comentário da entidade
- [x] 1.2 `dotnet ef migrations add CorpoMensagemDet --project ContabOne.Api`
      (adiciona `Corpo`, remove `Situacao`)
- [x] 1.3 `AgentEndpoints.cs`: `MensagemDetRequest` ganha `Corpo` e perde
      `Situacao`; `EnviarMensagensDetAsync` grava o corpo (cortado em 20.000
      caracteres) na criação e no upsert
- [x] 1.4 `DetEndpoints.ListarAsync`: devolve `corpo`, não devolve `situacao`
- [x] 1.5 `DetMensagensTest.cs`: corpo persistido e devolvido; mensagem sem
      corpo; corpo acima do limite é cortado; payload com `situacao` é aceito
      e a resposta da listagem não traz o campo

## 2. Det.Agent

- [x] 2.1 `api_client._traduzir_mensagens`: envia `corpo`, não envia
      `situacao`
- [x] 2.2 Testes offline: o envio leva o corpo e não leva a situação;
      mensagem sem corpo é enviada com o campo vazio
- [x] 2.3 `README.md`: o que vai para o painel

## 3. Frontend

- [x] 3.1 `api/types.ts`: `MensagemDetDto` ganha `corpo` e perde `situacao`
- [x] 3.2 `DetMensagensView.vue`: remove a coluna Situação e o CSS dos chips;
      adiciona a ação "Ler mensagem" e o modal com o texto
- [x] 3.3 `DetMensagensView.spec.ts`: sem coluna de situação; abrir mensagem
      com texto; abrir mensagem sem texto

## 4. Verificação

- [x] 4.1 `npm test` na raiz e `npm --prefix ContabOne.Frontend run build`
- [x] 4.2 Conferência local: reenviar o texto das mensagens da última
      execução a partir do JSON em `Det.Agent/dados/` e ver o texto no painel
