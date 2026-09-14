## Context

Ver [proposal.md](proposal.md) — Why. O que importa aqui é onde o CNPJ
completo já chega hoje e é descartado, e onde ele nunca chega:

- `ClientesEndpoints.cs` (`DerivarCnpj`, usado por `CriarAsync` e
  `AtualizarAsync`) — recebe `req.Cnpj` completo no cadastro/edição manual,
  deriva hash e máscara, descarta o valor pleno.
- `PgdasEndpoints.cs` — recebe o CNPJ completo lido do documento (extraído no
  navegador) na importação, mesma coisa: deriva e descarta.
- `AgentEndpoints.cs` (`UpsertClientesAsync`) — **nunca recebe** o CNPJ
  completo. O agente já calcula hash e máscara na máquina do escritório
  (`Nfse.Agent/nfse.py` + `api_client.py`) e só envia os dois valores
  derivados; a API não tem como persistir o que nunca chega. No bloco de
  atualização de cliente existente, `CnpjMascarado`/`CnpjHash` são
  sobrescritos incondicionalmente a cada sincronização — sem a comparação
  "só avança" que `CertificadoValidade` já tem, nem a exclusão total que
  `RegimeTributario`/`ModeloOnboardingId`/`Ativo` já têm.
- `ClientesView.vue` — o campo CNPJ do modal de edição já aceita o valor
  completo digitado (não é pré-mascarado; `cnpjMask` só formata dígitos com
  pontuação), mas fica `:disabled` quando `clienteEdit?.origem === 'Agente'`
  — decisão explícita da change arquivada `validade-certificado-editavel`
  ("o agente é a única fonte, não há caso de uso de correção manual"), que
  esta mudança reverte.
- Existe precedente de campo cifrado em repouso neste projeto:
  `Security/ConfiguracaoCipher.cs` (AES-256-GCM, chave derivada por
  HMAC-SHA256 de um segredo existente com rótulo de versão). Nenhum CNPJ
  completo é persistido hoje em lugar nenhum — nem cifrado.

## Goals / Non-Goals

**Goals:**

- Persistir o CNPJ completo nos dois pontos que já o recebem hoje (cadastro
  /edição manual, importação do PGDAS-D), cifrado em repouso.
- Deixar o campo de CNPJ editável na tela para cliente de qualquer origem,
  sem que a edição seja apagada silenciosamente pela sincronização seguinte
  do agente.
- Exibir o CNPJ completo na dashboard do PGDAS (`/f/pgdas/dashboard/{id}` e
  os exports HTML/PDF, que são o mesmo documento) quando disponível, com
  fallback para a máscara quando não.

**Non-Goals (deste change):**

- O agente NFS-e **não** passa a enviar o CNPJ completo automaticamente.
  Continua enviando só hash e máscara; a API passa a *respeitar* uma
  confirmação manual (não sobrescrever), mas não ganha uma fonte automática
  nova de CNPJ completo para cliente de origem agente. Colocar o agente para
  enviar o valor pleno é uma Fase 2 deliberadamente adiada — ver Decisão 4.
- Nenhuma outra tela muda de exibição: listagem de clientes, sidebar da
  lista de apurações do PGDAS, exportação CSV de clientes continuam
  mascaradas. Só a dashboard do PGDAS (e seus exports) passam a mostrar o
  valor completo.
- Sem backfill para cliente já cadastrado sem CNPJ completo — impossível,
  hash é HMAC.

## Decisions

**1. CNPJ completo fica cifrado em repouso, não em texto puro.**

Nova coluna `Cliente.CnpjCifrado` (string?, nullable) guarda o envelope
`base64(nonce[12] ‖ ciphertext ‖ tag[16])` de AES-256-GCM — mesmo formato de
`ConfiguracaoCipher`. A chave é derivada com o mesmo tipo de rótulo de
versão: `HMAC-SHA256(key = HMAC_CNPJ_KEY, msg = "cnpj-completo-v1")`. Vai
para uma classe nova, `Security/CnpjCipher.cs`, ao lado de `CnpjHasher`
(que continua cuidando só de hash e máscara — não muda).

Alternativa considerada: coluna em texto puro. Rejeitada — reintroduziria
exatamente a exposição que a arquitetura original existia para evitar
(AGENTS.md: CNPJs completos de todos os tenants recuperáveis a partir de um
dump do Postgres compartilhado), quando mitigar isso custa uma classe já
precedentada no projeto e nenhum segredo novo (reaproveita `HMAC_CNPJ_KEY`,
que já é obrigatório e já é tratado como permanente).

Hash e máscara continuam em colunas próprias, sem mudança — são o que
sustenta busca e identificação (`CnpjHash` no `WHERE`) sem precisar decifrar
nada, e são o que as telas que continuam mascaradas usam.

**2. Precedência da sincronização é por marcação, não por comparação.**

Novo campo `Cliente.CnpjConfirmadoManualmente` (bool, default `false`).
`AtualizarAsync` (`ClientesEndpoints.cs`) grava `true` sempre que a
requisição informa um CNPJ. `UpsertClientesAsync` (`AgentEndpoints.cs`) só
sobrescreve `CnpjMascarado`/`CnpjHash`/`CnpjCifrado` de um cliente existente
quando esse campo for `false`.

Alternativa considerada: regra "só avança", igual à validade do certificado.
Rejeitada — CNPJ não tem ordem natural (não existe "CNPJ mais recente"), só
"confirmado por uma pessoa" ou não. Comparar valores não faz sentido aqui;
só a marcação faz.

**3. O campo cifrado só é decifrado nos endpoints que precisam exibi-lo.**

Só o endpoint da dashboard do PGDAS (`GET
/api/pgdas/clientes/{clienteId}/dashboard`) decifra e inclui o CNPJ
completo na resposta. Listagem de clientes, sidebar de apurações e export
CSV continuam projetando só `CnpjMascarado` — `CnpjCifrado` nunca entra
nessas projeções, então não precisam de guarda adicional para continuar
mascaradas. A cifragem em repouso é defesa em profundidade; a fronteira
principal continua sendo "que DTO inclui o campo".

**4. Fase 1 (este change) não toca o agente Python — é uma Fase 2 à parte.**

Este change cobre só cadastro/edição manual e importação do PGDAS-D, que já
recebem o CNPJ completo em algum request hoje — trabalho contido em
`ContabOne.Api` + `ContabOne.Frontend`, sem coordenar deploy com o `nfse.exe`
já instalado nas máquinas dos escritórios.

Fazer o agente enviar o CNPJ completo automaticamente (para que cliente de
origem agente ganhe o valor pleno sem depender de confirmação manual) exige
atualizar `Nfse.Agent/nfse.py` + `api_client.py`, reconciliar
`teste_payload_vazamento.py` (que hoje testa exatamente a ausência desse
valor no payload — é um teste de *segurança*, não um teste qualquer, e
merece revisão própria, não um ajuste de passagem), e lidar com o parque de
agentes heterogêneo (só quem atualizar o `nfse.exe` passa a enviar o valor). Isso é
maior e mais arriscado que o resto desta mudança, e fica para uma change
futura — listado em Non-Goals, não esquecido.

## Risks / Trade-offs

- **Rotação de `HMAC_CNPJ_KEY` invalida todo `CnpjCifrado` além de todo
  `CnpjHash`** → Mitigação: nenhuma nova — a chave já é tratada como
  permanente (AGENTS.md), essa mudança só estende o raio de uma operação já
  proibida, não cria uma restrição nova.
- **Cliente já cadastrado sem CNPJ completo continua sem ele** →
  Mitigação: fallback para a máscara na dashboard; é o estado esperado,
  documentado no proposal, não um bug a corrigir aqui.
- **Um DTO futuro inclui `CnpjCifrado`/CNPJ completo por engano numa tela que
  deveria continuar mascarada** (listagem, sidebar, CSV) → Mitigação: teste
  dedicado (espelhando o espírito de `teste_payload_vazamento.py`, do lado
  C#) que afirma que essas respostas nunca carregam o campo.
- **Maioria dos clientes é de origem agente, e a Fase 1 não os alcança
  automaticamente** → Mitigação aceita: o caminho imediato é a confirmação
  manual (o próprio pedido que motivou esta parte da mudança); alcance
  automático é a Fase 2, deliberadamente adiada.

## Migration Plan

1. Uma migration EF Core: `Clientes` ganha `CnpjCifrado` (string?, nullable)
   e `CnpjConfirmadoManualmente` (bool, not null, default `false`). Sem dado
   a migrar — colunas nascem vazias/`false` para todo mundo.
2. Deploy da API primeiro (aditivo — payload de sincronização do agente não
   muda de formato, nenhum agente em campo precisa de atualização para este
   change). Depois o frontend (tela de clientes + dashboard do PGDAS).
3. Rollback: reverter a migration (`dotnet ef database update` para a
   anterior) remove as duas colunas; nenhum dado de hash/máscara é afetado.

## Open Questions

- Quando priorizar a Fase 2 (agente passa a enviar o CNPJ completo)? Não
  muda specs, decisões ou tasks deste change — fica para quando fizer
  sentido no roadmap, tratada como change própria.
