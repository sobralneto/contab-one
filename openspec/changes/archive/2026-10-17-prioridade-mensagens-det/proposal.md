## Why

Nem toda mensagem da Caixa Postal DET tem o mesmo peso: uma notificação de pendência fiscal exige ação imediata, um informativo genérico não. Como o mesmo aviso chega para dezenas de clientes, a prioridade é uma propriedade do **assunto**, não de cada mensagem individual — classificar uma vez deve valer para todas as mensagens daquele assunto, inclusive as que ainda vão chegar.

## What Changes

- Nova **classificação de prioridade por assunto** de mensagem DET, com 3 níveis — **Alta**, **Média** e **Baixa** — ou nenhuma (assunto ainda não classificado, estado inicial).
- A prioridade pertence ao **assunto dentro do escritório** (assuntos comparados sem espaços nas pontas e sem diferença de maiúsculas/minúsculas, a mesma regra do agrupamento) e vale para todas as mensagens desse assunto, presentes e futuras. **Não existe prioridade por mensagem.**
- Quem classifica é o usuário do escritório, manualmente, **na linha do grupo** da visão agrupada de `/f/det`. A classificação é persistida na API e compartilhada entre os usuários do escritório.
- Cores de sinalização por nível, sempre com o texto do nível: Alta = vermelho, Média = amarelo, Baixa = verde, via tokens `--kpi-*`. Na lista plana e no modal de leitura a prioridade aparece só como selo (somente leitura), herdada do assunto.
- Nova tabela de prioridades por assunto e novo endpoint de painel para definir/limpar; o agente não participa e o contrato C#/Python não muda.

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `registro-mensagens-det`: a API guarda a prioridade por assunto (por escritório), devolve em cada mensagem a prioridade do seu assunto, e oferece a operação de definir/limpar pelo painel.
- `visualizacao-mensagens-det`: o painel exibe a prioridade com cores de sinalização e a classificação é feita na linha do grupo por assunto.

## Impact

- API: `Domain/Entities.cs` (nova entidade `PrioridadeAssuntoDet`), `Domain/Enums.cs`, `Infra/AppDbContext.cs` (DbSet + **query filter por escritório**), migration EF, `Features/Det/DetEndpoints.cs` (prioridade derivada no GET + `PUT`), testes em `ContabOne.Api/tests` (incluindo `IsolamentoTest` para a nova entidade).
- Frontend: `api/types.ts`, `api/endpoints/det.ts`, `components/det/MensagensDet.vue`, `components.css`, testes Vitest.
- `Nfse.Agent`/`Det.Agent` e `_fake_api.py` não mudam. `MensagemDet` não ganha coluna. Privacidade preservada: metadado do escritório, nenhum conteúdo fiscal novo trafega.
- Este change ainda não foi arquivado nem enviado; o trabalho já feito com prioridade por mensagem (branch `feature/prioridade-mensagens-det`, coluna `MensagemDet.Prioridade` e sua migration) é **substituído** por esta versão.
