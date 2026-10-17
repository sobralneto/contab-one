## Context

`MensagemDet` é gravada pelo agente via upsert (`AgentEndpoints.EnviarMensagensDetAsync`) e lida pelo painel em `GET /api/det/mensagens` (`DetEndpoints`, policy `EscritorioUsuario`, query filter global por escritório). O painel `/f/det` (`MensagensDet.vue`) tem visão agrupada por assunto (chave = `trim` + minúsculas) e lista plana. A prioridade é uma decisão sobre o *assunto*, que se repete entre clientes e coletas — por isso não pode morar na mensagem.

## Goals / Non-Goals

**Goals:**
- Prioridade em 3 níveis por assunto (por escritório), persistida, compartilhada, valendo também para mensagens futuras; selos coloridos.

**Non-Goals:**
- Prioridade por mensagem; classificação automática; filtro/ordenação por prioridade; alertas; histórico de quem classificou; reescrever mensagens existentes.

## Decisions

- **Nova entidade `PrioridadeAssuntoDet`** (`Id`, `EscritorioId`, `AssuntoChave`, `Prioridade`, `AtualizadaEm`) com índice único `(EscritorioId, AssuntoChave)`. `MensagemDet` **não muda**. Alternativa (coluna em `MensagemDet`, a primeira tentativa) rejeitada: exigiria atualizar N linhas por classificação e não alcançaria mensagens futuras.
- **Tenant:** é entidade tenant-scoped, então ganha o query filter global em `AppDbContext` no formato padrão (`VeTodosOsEscritorios || EscritorioId == ...`), com cobertura em `IsolamentoTest`. Sem isso vazaria entre escritórios.
- **Chave canônica calculada no servidor**: `AssuntoChave = (assunto ?? "").Trim().ToLowerInvariant()`; vazio = grupo "Sem assunto". O cliente envia o assunto cru e o servidor normaliza, para haver uma única implementação. O frontend continua agrupando por `trim + toLocaleLowerCase('pt-BR')`; para texto em português as duas regras coincidem, e um teste cobre acentuadas/maiúsculas.
- **Enum `PrioridadeMensagemDet { Baixa = 1, Media = 2, Alta = 3 }`**, inteiro na rede, valores crescentes com a gravidade. Ausência de linha = sem prioridade (a linha só existe enquanto houver nível definido: limpar remove a linha).
- **Leitura:** `GET /api/det/mensagens` passa a juntar com as prioridades do escritório (`ToDictionary` em memória por chave, uma consulta extra pequena) e devolve `prioridade` em cada item. A expressão de tradução EF fica simples (sem predicado sobre propriedade calculada) e `TraducaoLinqTest` deve cobrir a consulta nova.
- **Escrita:** `PUT /api/det/assuntos/prioridade` com corpo `{ assunto: string | null, prioridade: number | null }` no grupo `/api/det` (`EscritorioUsuario`; a chave de agente não satisfaz). Upsert por `(EscritorioId, AssuntoChave)`; `prioridade` nula remove a linha; valor inválido → 400 via `Enum.IsDefined`. Idempotente, 204. O `EscritorioId` vem do `TenantContext`, nunca do corpo.
- **Cores:** selos com `--kpi-vermelho/-amarelo/-verde` e `-texto` numa classe compartilhada `.badge-prioridade` (+ `--alta/--media/--baixa/--nenhuma`) em `components.css`, sempre com o texto do nível.
- **Frontend:** `PrioridadeMensagem.vue` passa a ter dois usos — `editavel` na linha do grupo (selo + `<select>` nativo com Alta/Média/Baixa/"Sem prioridade") e somente selo na lista plana, nas mensagens expandidas e no modal. O `<select>` na linha do grupo para a propagação do clique (`@click.stop`) para não expandir o grupo. Atualização otimista: a prioridade do assunto é aplicada a todas as mensagens de mesma chave na lista em memória (ou guardada num mapa chave→prioridade usado por grupos, lista e modal), com reversão em erro.
- **Migração do trabalho já feito (não publicado):** remover a coluna `MensagemDet.Prioridade`, o `PUT /mensagens/{id}/prioridade` e seus testes; descartar a migration `PrioridadeMensagemDet` ainda não enviada e gerar uma nova com a tabela nova (sem editar o snapshot à mão).

## Risks / Trade-offs

- [Normalização do servidor e do cliente divergirem para caracteres raros] → teste com acentos/maiúsculas; a lista vem do servidor com `prioridade` pronta, então a divergência só afetaria o agrupamento visual, nunca o valor gravado.
- [Último a gravar vence] → aceitável para um marcador; sem histórico por ora.
- [Mensagens sem assunto compartilham uma prioridade] → intencional e coerente com o grupo "Sem assunto".
