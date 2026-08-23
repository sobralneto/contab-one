# Plano — Mudanças na ferramenta local (agente)

Status: **plano, nada implementado**. Escrito para ser executado numa sessão
futura.

Documentos irmãos: [PLANO_SAAS_API.md](PLANO_SAAS_API.md) ·
[PLANO_SAAS_FRONTEND.md](PLANO_SAAS_FRONTEND.md)
Estado atual do código: [HANDOFF.md](HANDOFF.md) — **leia antes**, tem as
armadilhas do portal e as decisões que não devem ser desfeitas.

---

## 1. O que muda e o que não muda

A ferramenta deixa de ser um executável autônomo customizado e passa a ser o
**agente** do SaaS: continua fazendo exatamente o mesmo trabalho pesado
(mTLS, coleta, DANFSe), mas agora se identifica, obedece a licenciamento e
reporta o que fez.

**Não muda (e não deve mudar):**
- o `.pfx` continua sendo lido em memória, na máquina do escritório, e
  **nunca sai dela**
- XML e PDF das notas continuam **só no disco local** — a API recebe contagem,
  não conteúdo fiscal
- todo o miolo já validado: janelas de 31 dias, `pg=`, `executar=1` só em
  Recebidas, `_controle.json`, backfill, DANFSe conforme NT 008
- ~~o `dashboard.html` local continua existindo (é a visão offline; a web é
  complementar, não substituta)~~ — **revisto em 09/08/2026**: o dashboard
  local (`dashboard.py` + `dashboard.html`) foi removido, o painel passou a
  ser só o frontend web. Ver "Decisões que valem lembrar" no
  [HANDOFF.md](Nfse.Agent/HANDOFF.md).

**Passa a existir:**
1. identidade do agente (API key) e checagem de adimplência
2. envio de métricas de execução
3. envio dos dados dos donos de certificado (nome, CNPJ ofuscado, validade)
4. regras de coleta vindas da API, com cache local

---

## 2. Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `api_client.py` | **novo** — todo o diálogo com a API fica aqui, isolado |
| `regras.py` | **novo** — busca/cacheia/valida o bundle; expõe as constantes que hoje são literais |
| `nfse.py` | handshake no `main()`, coleta de métricas no `processar_empresa()`, envio no fim |
| `config.toml` | seção `[api]` |
| `build.py` | embutir os módulos novos; versão do agente |
| `dashboard.py` | inalterado (removido do projeto em 09/08/2026, junto com `dashboard.html`) |
| `danfse.py` | inalterado |

Manter `api_client.py` isolado importa: quando a API estiver fora do ar, o
ponto de falha é um só, e a lógica de coleta continua testável sem rede — como
já é hoje.

---

## 3. Identidade e adimplência

### 3.1 Configuração

```toml
[api]
url = "https://api.seudominio.com.br"
chave = "nfse_a1b2c3d4_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# Dias que o agente continua funcionando se a API estiver fora do ar.
tolerancia_offline_dias = 7
```

### 3.2 Handshake, no início do `main()`

Antes de qualquer certificado ser tocado:

```
POST /api/agent/handshake   { versaoAgente, regrasVersaoLocal, so: "win32" }
→ { status, podeExecutar, mensagem, plano, regrasVersaoAtual, agenteVersaoMinima }
```

Comportamento por resposta:

| Situação | O que o agente faz |
|---|---|
| `podeExecutar: true` | segue normal; grava o resultado no cache |
| `podeExecutar: false` | **para**, exibe `mensagem` da API (ex.: "Assinatura suspensa — fale com o suporte"), sai com código 3 |
| API inacessível, cache válido | segue normal, avisa "trabalhando offline, última validação há X dias" |
| API inacessível, cache vencido | **para** com mensagem explicando que precisa de conexão |
| `agenteVersaoMinima` > versão atual | avisa no log, mas **não** bloqueia (bloquear por versão trava o cliente num momento ruim) |

**A carência é o detalhe que sustenta o licenciamento.** Sem prazo de validade
no cache, bastaria bloquear a API no firewall para usar de graça para sempre.
Com 7 dias, uma queda real da sua infra não para o escritório, mas o bloqueio
deliberado para de funcionar em uma semana.

O cache (`_agente_cache.json`) guarda a última resposta + timestamp. Vale
assinar o payload no servidor (HMAC) e validar no agente — sem isso, editar o
JSON local para `podeExecutar: true` é trivial.

---

## 4. Regras vindas da API

Substitui os literais de hoje em `nfse.py` — `LISTAGENS`, `MAX_DIAS_FILTRO`,
`PARAM_PAGINA`, `URL_NOTAS`, as regex de parsing.

```
GET /api/agent/regras?versao=7   → 304 se já é a atual, senão o bundle novo
```

Fluxo em `regras.py`:

1. handshake informou `regrasVersaoAtual`
2. se for maior que a local → baixa, **valida o schema**, grava em
   `_regras_cache.json`
3. se a validação falhar → **mantém a versão antiga e avisa**. Nunca adotar um
   bundle quebrado: uma regra ruim publicada pararia todos os agentes ao mesmo
   tempo, e o rollback dependeria de publicar de novo com a API já em pânico
4. sem cache e sem API → para com mensagem clara (não há como coletar sem saber
   as URLs)

O agente embarca um **bundle mínimo de fábrica** (o snapshot do que está no
código hoje), usado só no primeiro contato de uma instalação nova. Assim uma
instalação limpa não fica órfã se a API estiver fora no momento exato do setup.

> O layout do DANFSe **não** entra no bundle — a NT 008 é pública e o payload
> seria enorme. Ver justificativa em [PLANO_SAAS_API.md §8](PLANO_SAAS_API.md).

---

## 5. Métricas

### 5.1 O que o `resumo` precisa virar

Hoje `processar_empresa()` devolve o agregado
`{"xml", "pdf", "pulados", "falhas"}`. Para o dashboard web precisa quebrar por
cliente, tipo e competência — que é exatamente a granularidade que o laço
`por_mes` já percorre:

```python
{
  "cliente_codigo": "0001",
  "tipo": "recebidas",
  "competencia": "2026-06",
  "qtd_baixadas": 14, "qtd_puladas": 0, "qtd_falhas": 0,
  "duracao_ms": 8200
}
```

Uma linha por `(cliente, tipo, competência)`. O agregado atual continua sendo
calculado a partir disso, para o resumo no console não mudar.

### 5.2 Envio

```
POST /api/agent/execucoes                    → { execucaoId }   (no início)
POST /api/agent/execucoes/{id}/metricas      → lote              (no fim)
POST /api/agent/execucoes/{id}/finalizar     → status + erro
```

Abrir a execução **antes** de processar e finalizar depois faz o dashboard
mostrar "rodando agora" e, mais importante, deixa visível a execução que
**começou e nunca terminou** — que é o sintoma de travamento que hoje ninguém
enxerga.

### 5.3 Fila local para não perder dado

Se o envio falhar (internet caiu no meio), gravar em
`_pendencias/{timestamp}.json` e tentar de novo na próxima execução, antes de
tudo. Descartar pendência com mais de 30 dias.

Enviar métrica **nunca pode derrubar a execução**: falha de rede aqui gera
aviso no log, não erro fatal. O trabalho real (baixar notas) já foi feito e não
pode ser invalidado por um POST que não passou — mesmo princípio já usado no
`_escrever_no_arquivo()`.

---

## 6. Dados dos donos de certificado

Boa notícia: o `dataclass Empresa` já extrai tudo isso do nome do arquivo
(`codigo`, `cnpj`, `nome`, `validade`). Falta só ofuscar e enviar.

```
POST /api/agent/clientes
[{
  "codigo": "0001",
  "nome": "SOLUTION FARMA CONTABILIDADE LTDA",
  "cnpjMascarado": "54.283.***/**26",
  "cnpjHash": "9f2a...c1",              # HMAC-SHA256, chave do config
  "certificadoValidade": "2027-03-04",
  "certificadoNomeArquivo": "0001_...pfx",
  "certificadoVencido": false
}]
```

Duas funções novas, ambas puras e fáceis de testar:

```python
def mascarar_cnpj(cnpj: str) -> str:       # 54283546000126 → 54.283.***/**26
def hash_cnpj(cnpj: str, chave: str) -> str:  # HMAC-SHA256 → identidade estável
```

O `cnpjHash` é o que permite ao servidor saber que é o mesmo cliente entre
execuções sem nunca guardar o CNPJ cheio (ver
[PLANO_SAAS_API.md §4.3](PLANO_SAAS_API.md)).

**A chave HMAC precisa ser a mesma para todos os agentes do mesmo escritório**
— senão o mesmo cliente vira dois registros. Vem no handshake, não no
`config.toml` (assim o usuário não a perde ao reinstalar).

**Nunca enviar:** o `.pfx`, a senha, o CNPJ completo, conteúdo de XML/PDF.
Vale um teste automatizado que faz asserção sobre isso — o payload não pode
conter nenhum desses campos. É o tipo de invariante que se perde numa
refatoração distraída.

---

## 7. Fases

**Fase 1 — Cliente de API.** `api_client.py` com timeout, retry com backoff,
`User-Agent` versionado. Testes com servidor HTTP fake (a API real ainda não
existe). Nada plugado no `nfse.py` ainda.

**Fase 2 — Handshake e licenciamento.** Config `[api]`, cache assinado,
carência offline, bloqueio quando inadimplente. Casa com a Fase 3 da API.

**Fase 3 — Métricas.** Expandir o `resumo`, abrir/finalizar execução, fila de
pendências.

**Fase 4 — Clientes/certificados.** Mascaramento, HMAC, upsert.

**Fase 5 — Regras remotas.** `regras.py`, cache, validação de schema, bundle de
fábrica. **Deliberadamente por último** — é a mudança mais invasiva no miolo já
estabilizado; fazer depois que o resto está no ar reduz o risco de regressão em
cima do que hoje funciona.

**Fase 6 — Distribuição.** Versão no `build.py`, canal de atualização, instalador
que já pede a chave no setup.

---

## 8. Testes

Somar às suítes existentes (ver HANDOFF.md §Testes), mantendo o padrão:
offline, sem rede real.

- `api_client` contra `http.server` local: sucesso, 401, 500, timeout, conexão
  recusada
- **carência offline**: com cache válido roda; com cache vencido para; com
  cache adulterado (assinatura inválida) para
- **bloqueio por inadimplência**: `podeExecutar: false` → sai com código 3 e
  não toca em nenhum `.pfx`
- **bundle inválido não substitui o bom** — o cenário do §4
- `mascarar_cnpj` / `hash_cnpj`: casos normais, CNPJ curto, vazio, com
  pontuação; hash estável entre chamadas e diferente com chave diferente
- **teste de vazamento do payload**: nenhum campo enviado contém `.pfx`, senha,
  CNPJ completo ou conteúdo de nota
- fila de pendências: grava ao falhar, reenvia na execução seguinte, descarta
  vencidas
- **regressão**: as suítes atuais têm que continuar passando sem alteração —
  se alguma quebrar, é sinal de que a mudança vazou para o miolo de coleta

---

## 9. Compatibilidade e migração

Os dois clientes que já usam a versão atual (ver HANDOFF.md) precisam continuar
funcionando. Ordem sugerida:

1. Publicar a versão nova aceitando `[api]` **ausente** → modo legado, roda como
   hoje. Permite atualizar o binário sem coordenar nada.
2. Cadastrar os escritórios no SaaS, gerar chaves, preencher o `config.toml`.
3. Só depois de todos migrados, tornar `[api]` obrigatório.

O `_controle.json` de cada cliente **não muda de formato** — o histórico de
backfill e de notas baixadas continua válido. Um cliente que já baixou 2026-01
a 2026-07 não pode rebaixar tudo só porque virou agente.

---

## 10. Riscos

| Risco | Mitigação |
|---|---|
| API fora do ar para todos os clientes | carência offline (§3.2) + cache de regras |
| Bundle de regras quebrado em produção | validação de schema no agente + preview do diff antes de publicar |
| Agente adulterado (cache/licença editados) | payload assinado; a API é a fonte da verdade |
| Métrica duplicada (dois agentes, mesmo cliente) | upsert por `(cliente, tipo, competência)` no servidor |
| Escritório se recusa a "mandar dados para fora" | ser explícito no material comercial: sobem contagens e metadados, não notas nem certificado — §1 |

## 11. Perguntas em aberto

1. **Qual granularidade de métrica** é realmente usada no dashboard? Modelei
   `(cliente, tipo, competência)`. Se ninguém olhar competência, o volume de
   linhas cai muito.
2. **Um agente por máquina ou por escritório?** Se o escritório roda em dois
   PCs, os dois reportam os mesmos clientes — daí o upsert do risco acima.
3. **O agente deve receber ordens da API** (ex.: "rode agora", agendamento
   central)? Isso exige *polling* ou conexão persistente e muda bastante o
   desenho. O plano atual é só o agente falando com a API, nunca o contrário.
4. **Auto-atualização** do agente: baixar e trocar o próprio `.exe` é cômodo,
   mas é também o vetor perfeito para distribuir código malicioso se a API for
   comprometida. Se for fazer, exigir assinatura do pacote.
