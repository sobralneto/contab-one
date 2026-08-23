## Context

`config.toml` mistura três naturezas diferentes de dado:

1. **Segredo de máquina/certificado** que a plataforma não deve custodiar:
   `senha_padrao`, `[senhas]`.
2. **Credencial da API**: `[api] url`/`chave`.
3. **Preferência operacional do escritório** (`pasta_saida`, `tipos`,
   `gerar_pdf`, `primeira_busca_desde`, `dias_busca_padrao`) — hoje já
   duplicada: existe no arquivo local **e** é entregue pelo handshake
   (`aplicar_configuracao_remota`, `handshake-agente` spec) e editável na
   tela de Configuração (`configuracao-persistencia` spec). O arquivo local
   só deveria valer como *fallback* de bootstrap (primeira execução, antes de
   qualquer handshake bem-sucedido) — não como algo que um escritório edita
   rotineiramente.

O bloco `[senhas]` hoje é indexado por `empresa.codigo`, extraído por regex
do nome do arquivo (`ler_certificado`/`PADRAO_CERTIFICADO*`). Isso amarra a
resolução de senha à convenção de nomenclatura
`codigoEmpresa_CNPJ_NomeEmpresa_...`, que só fazia sentido no uso original,
de um único escritório. Com escritórios genéricos, o `.pfx` pode ter
qualquer nome — a chave estável e sem pré-requisito de convenção é o próprio
nome do arquivo.

Por fim, o bloco `configuracao` do handshake (`Dictionary<string,string>`,
`HandshakeResponse.Configuracao` em `AgentEndpoints.cs`) viaja como JSON
simples dentro do HTTPS da chamada — protegido em trânsito pelo TLS, mas sem
nenhuma camada própria. É a única peça do contrato agente↔API sem isso: a
`[senhas]`/`.pfx` nunca sai da máquina, o `X-Api-Key` é um bearer sobre TLS,
e o cache offline (`_agente_cache.json`) é assinado (HMAC) com a própria
chave do agente. O pedido é que o bloco `configuracao` também passe a ser
cifrado — não apenas assinado — ponta a ponta, com uma chave que **só a API
e a ferramenta conhecem**.

## Goals / Non-Goals

**Goals:**
- Reduzir `config.exemplo.toml` a `[api]` + bloco de senha.
- Trocar a chave de `[senhas]` de código da empresa para nome do arquivo do
  certificado.
- Cifrar o bloco `configuracao` do handshake com uma chave simétrica
  derivada de um segredo que os dois lados já possuem — sem introduzir
  nenhum novo segredo em `config.toml` ou nas variáveis de ambiente da API.
- Preservar o comportamento existente de "valor remoto inválido nunca
  derruba a execução" (`erro_fatal` nunca é chamado por causa de
  configuração remota/cifragem).

**Non-Goals:**
- Não mexe no bundle de regras de coleta (`regras.py`, `RegraColeta`) —
  mecanismo e formato distintos, fora do escopo deste change.
- Não remove `pasta_certificados` de `config.toml`: é caminho de máquina
  (onde estão os `.pfx` nesta instalação específica), não preferência de
  escritório — não existe versão "certa" para entregar via API porque cada
  máquina do escritório pode ter uma pasta diferente. Continua com o padrão
  embutido (`"certificados"`) e continua **fora** do template, pelo mesmo
  motivo de hoje (comentário em `nfse.py`: "segredo/caminho de máquina, não
  configuração de plataforma").
- Não implementa rotação de chave de cifragem: a chave é derivada
  deterministicamente da API key vigente; revogar/trocar a API key do agente
  (já suportado — `Agente` tem sua própria chave) já invalida a cifragem
  antiga como efeito colateral.
- Não versiona o formato do payload cifrado (sem campo `versao` dentro do
  envelope) — mudança de formato futura é tratada como quebra de contrato
  normal entre agente e API (mesma política já aplicada a
  `agenteVersaoMinima`).

## Decisions

### Decisão 1 — Chave de `[senhas]` = nome do arquivo do certificado

`senha_da_empresa(empresa, config)` passa a consultar
`config["senhas"].get(empresa.pfx.name)` (nome completo do arquivo,
incluindo extensão — é o único identificador que não depende de nenhum
parsing) em vez de `config["senhas"].get(empresa.codigo)`. Ordem de
precedência inalterada (nome do arquivo do `.pfx` → `[senhas]` →
`senha_padrao` → variável de ambiente). `config.exemplo.toml` passa a
mostrar:

```toml
[senhas]
# "NomeDoCertificado.pfx" = "senha-so-deste-certificado"
```

Alternativa descartada: manter a chave por `empresa.codigo` mas relaxar o
parsing do nome do arquivo. Rejeitada porque o código já é "o texto antes do
primeiro `_`, ou o nome inteiro" — funciona como identificador best-effort
para nomear a pasta do cliente, mas não é um identificador estável o
suficiente para mapear senha quando o objetivo é desacoplar completamente da
convenção de nome do arquivo.

Isto é **BREAKING** para quem já usa `[senhas]` por código — não há uso em
produção documentado desse bloco (só `senha_padrao` é mencionado como o
caminho recomendado no README), então não há migração automática; o
`HANDOFF.md`/README documentam a mudança.

### Decisão 2 — Chave de cifragem derivada da API key do agente

A API key do agente (`chave`) já é conhecida pelos dois lados: o agente a
guarda em `config.toml`, e a API a recebe em claro no header `X-Api-Key` em
**toda** chamada autenticada — inclusive a própria chamada de handshake —
mesmo persistindo só o hash SHA-256 dela no banco (`ApiKeyHasher`). Isso
permite derivar, nos dois lados, a mesma chave simétrica **sem introduzir
nenhum segredo novo** em `config.toml` nem em variável de ambiente da API:

```
chave_cifra = HMAC-SHA256(key = chave_api_bruta, msg = "nfse-configuracao-v1")
```

- No agente: `chave_api_bruta` é `config["api"]["chave"]`, já em memória.
- Na API: `chave_api_bruta` é o valor bruto do header `X-Api-Key` do próprio
  request do handshake — disponível no momento de montar a resposta, nunca
  persistido (mesma garantia de hoje: só o hash vai para o banco).

`HMAC-SHA256` (e não simplesmente `SHA256(chave + rotulo)`) porque é a
primitiva correta para derivar uma subchave a partir de um segredo mantido
em memória — mesmo raciocínio já usado em `_assinar_payload` do cache de
licença.

Alternativa descartada: gerar um segredo de cifragem novo (env var na API +
campo em `config.toml`). Rejeitada por contrariar o próprio objetivo do
change (menos coisa em `config.toml`) e por exigir um mecanismo de
distribuição que a API key já resolve.

### Decisão 3 — AES-256-GCM, envelope `nonce ‖ ciphertext ‖ tag` em base64

Escolhido AEAD (AES-GCM) em vez de cifra sem autenticação (ex.: AES-CBC)
porque o bloco decifrado alimenta `aplicar_configuracao_remota()`, que já
confia razoavelmente no conteúdo (tipos, datas, flags) — autenticação evita
que um payload adulterado em trânsito (ainda que só teoricamente, já que TLS
cobre isso) seja aceito como configuração válida sem pelo menos falhar a
verificação de tag antes de chegar à lógica de aplicação.

Formato do campo (substitui `Configuracao: Dictionary<string,string>` por
`ConfiguracaoCifrada: string`, JSON UTF-8 do dicionário original antes de
cifrar):

```
base64( nonce[12 bytes] || ciphertext || tag[16 bytes] )
```

- .NET: `System.Security.Cryptography.AesGcm` (biblioteca padrão, sem nova
  dependência).
- Python: biblioteca `cryptography` (`cryptography.hazmat.primitives.ciphers.aead.AESGCM`)
  — **nova dependência** em `requirements.txt`, adicionada a
  `--hidden-import` do `build.py` (mesmo padrão de `api_client`/`regras`,
  ver comentário em `CLAUDE.md` sobre `_versao_agente()` lido por regex para
  não herdar dependências desnecessárias — aqui a dependência é necessária
  de verdade, não incidental).

Alternativa descartada: `pycryptodome`. Rejeitada só por convenção — a lib
`cryptography` é a mais usada no ecossistema Python e tem wheels
pré-compiladas para Windows, reduzindo risco de falha de build/PyInstaller.

### Decisão 4 — Falha de decifragem é tratada como "configuração remota ausente"

Chave errada, payload corrompido, ou campo `configuracaoCifrada` ausente
(agente novo falando com API antiga, ou vice-versa) resultam em: aviso em
log, e a execução segue com o `config.toml` local e/ou o último valor válido
em cache offline — nunca `erro_fatal()`. Mesma política já aplicada a
qualquer valor remoto inválido (`regras.validar_bundle`,
`aplicar_configuracao_remota`): dado vindo da rede não é confiável o
suficiente para derrubar o processo.

O cache de licença (`_agente_cache.json`) já guarda o resultado de
`avaliar_licenca()`, incluindo `configuracao` — ele passa a guardar o
dicionário **já decifrado** (não o envelope cifrado), preservando o formato
existente do cache e evitando ter que re-decifrar a partir do cache offline
(a API pode não estar acessível justamente quando o cache é consultado).

## Risks / Trade-offs

- [Risco] Agente com API key errada/revogada não consegue decifrar o bloco,
  mesmo que a autenticação HTTP em si já tivesse barrado o request com 401
  antes de a resposta existir → não é um cenário novo: 401 já bloqueia a
  execução por `ApiCredenciaisInvalidas` antes de qualquer configuração
  remota ser considerada (`handshake-agente`, requisito "A chave de
  ofuscação de CNPJ é sempre entregue" e o tratamento de
  `ApiCredenciaisInvalidas`).
- [Risco] Nova dependência (`cryptography`) no agente aumenta o tamanho do
  `.pfx` — irrelevante — e do executável PyInstaller → aceitável; é uma lib
  madura, com wheel binário para Windows, mesmo tier de risco que
  `requests-pkcs12` já trazido.
- [Trade-off] Trocar a chave de `[senhas]` por nome de arquivo quebra quem já
  usa `[senhas]` por código → mitigado por ser, pelo próprio README, o
  caminho **não recomendado** (o caminho recomendado documentado é
  `senha_padrao`); documentar a mudança no `HANDOFF.md`.

## Migration Plan

1. API: adicionar `ConfiguracaoCifrada` ao `HandshakeResponse`, cifrando o
   dicionário existente com a chave derivada da API key do request; remover
   o campo `Configuracao` em claro.
2. Agente: `api_client.py` decifra `configuracaoCifrada` logo após o
   handshake, antes de popular `DecisaoLicenca.configuracao` — o restante do
   fluxo (`aplicar_configuracao_remota`, cache offline) não muda de forma.
3. `senha_da_empresa()` muda a chave de busca; `config.exemplo.toml`,
   README, CLAUDE.md e HANDOFF.md atualizados juntos.
4. Como agente e API deste produto são distribuídos e atualizados pela
   mesma equipe (não há terceiros consumindo o contrato), não é necessário
   suportar as duas versões do payload simultaneamente — o deploy da API e o
   rebuild do `nfse.exe` acontecem na mesma janela de mudança.

## Open Questions

Nenhuma pendente — decisões acima cobrem os pontos identificados no
proposal.
