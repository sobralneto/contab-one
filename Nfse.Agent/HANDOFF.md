# Handoff — Ferramenta NFS-e

Documento de retomada. Se você está começando uma sessão nova (com Claude ou
sozinho) e não acompanhou o histórico, este arquivo te deixa no mesmo ponto.

Data desta versão: 01/08/2026, com uma alteração posterior em 09/08/2026 (a
remoção do dashboard local — ver a seção "Decisões que valem lembrar"; o
resto do documento continua sendo de 01/08). Para o estado exato do código,
`git log` não se aplica (não é um repositório git) — confie nos arquivos e
neste documento, não na memória de conversas anteriores.

**Esta ferramenta virou o agente de um SaaS.** O que está descrito nas duas
seções seguintes ("O que a ferramenta faz" / próxima seção de arquitetura)
ainda é 100% verdade — nada disso mudou. O que mudou é que, opcionalmente
(seção [api] no config.toml), a ferramenta agora também fala com uma API
(`ContabOne.Api`, projeto irmão em `../ContabOne.Api`): valida licença,
reporta métricas agregadas e dados de certificado (nunca XML/PDF/senha/CNPJ
completo), e busca regras de coleta atualizadas. Ver
[PLANO_SAAS_AGENTE.md](../PLANO_SAAS_AGENTE.md) (o plano que motivou isso) e
a seção **"O agente SaaS"** mais abaixo (arquitetura, decisões, armadilhas).
Sem `[api]` preenchido no config.toml, o comportamento é idêntico ao de
antes — zero chamada de rede além do próprio Portal Nacional NFS-e.

## O que a ferramenta faz

Baixa os XML de todas as NFS-e **recebidas e emitidas** de uma ou mais
empresas no Portal Nacional NFS-e, e gera o DANFSe (PDF) de cada uma. Tudo
autenticado por certificado digital A1, **sem navegador e sem captcha**, em
segundos — dá para agendar sem ninguém presente.

Distribuída como executável Windows único (`nfse.exe`, ~33 MB) que roda em
máquinas sem Python instalado.

## Para retomar agora mesmo

```
python nfse.py                    # roda com o Python do projeto
python build.py                   # gera dist/nfse/nfse.exe
python testes/executar_tudo.py    # roda a suíte de testes inteira (offline, ~20s)
```

Arquivos de configuração e dados ficam em:
- `config.toml` — pastas, senha padrão, período de backfill, seção `[api]` opcional (agente SaaS)
- `certificados/` — os `.pfx`
- `notas/` — a saída (uma pasta por cliente)

Teste offline (não toca a rede, roda em segundos):
```
python testes/executar_tudo.py
```
Ao contrário das suítes de sessões anteriores a 01/08/2026 (ver "Testes
existentes" abaixo), os testes escritos a partir desta data vivem dentro do
projeto, em `testes/`, e não em scratchpad — persistem entre sessões.

## Arquitetura

### Autenticação e coleta (sem navegador)

Foi cogitado usar Playwright (Chromium) para lidar com o certificado
digital, mas ele exige ~150 MB de runtime só para apresentar um certificado
por mTLS. Descobrimos que `requests` + `requests-pkcs12` faz exatamente a
mesma coisa: o `.pfx` é lido do disco e carregado **em memória** a cada
execução — nunca é instalado na loja de certificados do Windows, nunca é
gravado em disco em texto claro (a lib usa um arquivo temporário com senha
aleatória de 128 bits, apagado logo em seguida).

Fluxo:
1. `GET https://certificado.nfse.gov.br/EmissorNacional/Certificado` com o
   certificado apresentado via mTLS — esse subdomínio responde 403 sem
   certificado, e autenticado redireciona para o Dashboard. Cookies ficam na
   sessão `requests`.
2. Listagem via HTML: `GET /EmissorNacional/Notas/Recebidas` e
   `.../Notas/Emitidas`, com filtro de data na querystring. O HTML é
   parseado com regex simples (não BeautifulSoup) porque o único dado
   realmente estável é o padrão da URL do link de download
   (`/Notas/Download/NFSe/{chave}`) — a estrutura da tabela pode mudar sem
   aviso, mas isso não quebraria a extração da chave.
3. XML pela API oficial: `GET https://sefin.nfse.gov.br/sefinnacional/nfse/{chave}`
   devolve JSON com `nfseXmlGZipB64` (base64 + gzip). **Sem captcha** — o
   hCaptcha da interface web protege só os botões de download da página, não
   essa API. Confirmado byte a byte: o XML daqui é idêntico ao baixado pela
   interface depois de resolver o captcha manualmente.

### Duas armadilhas do portal, descobertas testando (não documentadas em
lugar nenhum)

- **Paginação usa `pg=`, não `pagina=`.** A primeira versão usava o nome
  errado, o portal ignorava o parâmetro silenciosamente, e qualquer período
  com mais de 15 notas baixaria só as 15 primeiras — sem erro, sem aviso.
  Só apareceu ao testar um mês com 53 notas emitidas (4 páginas).
- **O filtro de data aceita no máximo 31 dias.** Acima disso o portal
  responde "Nenhum registro encontrado", como se o período estivesse
  genuinamente vazio. Descoberto por busca binária. A ferramenta quebra
  períodos maiores em janelas de 31 dias automaticamente
  (`janelas()` em `nfse.py`).
- Detalhe menor: `/Notas/Recebidas` exige `executar=1` na querystring;
  `/Notas/Emitidas` **não aceita** esse parâmetro (com ele, devolve vazio).

### PDF: DANFSe v2.0 conforme NT 008/2026

O PDF **não vem do portal** — a rota `/sefinnacional/danfse/{chave}` responde
501 Not Implemented porque a própria Nota Técnica nº 008 (05/05/2026,
SE/CGNFS-e) informa que essa API foi suspensa em 01/07/2026. Gerar
localmente a partir do XML é o caminho previsto pela norma para ERPs e
sistemas fiscais — não é workaround.

`danfse.py` monta o PDF do zero com ReportLab, seguindo a especificação
exata da NT 008 (item 2.2 a 2.4.5): A4 retrato, margem 0,15-0,20cm, borda
1pt, linhas 0,5pt, sombreamento 5% nos títulos e nos campos "Emitente da
NFS-e"/"Valor Líquido + IBS/CBS", fontes Arial (títulos) e Microsoft Sans
Serif (conteúdo) já presentes no Windows, QR Code 1,52cm em X17,48/Y1,67
apontando para a consulta pública oficial. Validado campo a campo (30/30)
contra um DANFS-e real baixado do portal, e o QR Code foi decodificado de
verdade (não só "existe uma imagem ali") para confirmar que aponta pro lugar
certo com a chave certa.

Um bug real encontrado e corrigido: réguas horizontais estavam sendo
desenhadas entre TODAS as faixas de campos, inclusive dentro de um mesmo
bloco — isso cortava o QR Code ao meio. No Anexo I da NT 008 as linhas
existem só ENTRE blocos, nunca dentro de um. Corrigido; os 75 PDFs em
produção foram regerados depois da correção.

`municipios_ibge.json` (código IBGE → "Município - UF") é usado porque o
XML só traz o código do município do tomador, não o nome.

### Multi-empresa e nomenclatura de certificado

Todo `.pfx` em `pasta_certificados` vira uma empresa processada. O nome do
arquivo é parseado no padrão:

```
codigoEmpresa_CNPJ_NomeEmpresa_s.SENHA_v.DD.MM.AAAA.pfx
```

mas a ferramenta tolera desvios (sem senha/validade no nome, sem underscore
nenhum) — o único dado que **nunca pode falhar** na extração é o código
(sempre o texto antes do primeiro `_`, ou o nome inteiro se não houver `_`),
porque ele é a chave usada para achar a pasta do cliente e a senha no
config.

**Senha do certificado — nunca há prompt no console.** Ordem de prioridade:
nome do arquivo → `config.toml [senhas]` **pelo nome do arquivo do
certificado** → `config.toml senha_padrao` → variável de ambiente
`NFSE_PFX_SENHA`. Sem nenhuma dessas fontes, erro imediato (0.000s, não
tenta ler stdin). Isso foi uma correção em cima de uma primeira tentativa
que tentava detectar "há console interativo?" via `isatty()` — essa
detecção falhou num teste e travou o processo 5 minutos esperando uma senha
que nunca chegaria. Não confie em `isatty()` para decidir se é seguro chamar
`input()`/`getpass()`.

`[senhas]` era indexado pelo **código da empresa** (extraído por regex do
nome do arquivo) até o change `agente-config-minima-cifrada`; trocado para o
nome do arquivo porque o sistema passou a atender escritórios genéricos, sem
exigir que o `.pfx` siga a convenção `codigoEmpresa_CNPJ_NomeEmpresa...` só
para ter uma exceção de senha reconhecida. **BREAKING** para quem já usava
`[senhas]` por código — não havia uso documentado desse caminho em produção
(o README sempre recomendou `senha_padrao`).

**Pasta do cliente é localizada pelo código, não pelo nome** (`pasta_da_empresa`
em `nfse.py`). Se a razão social mudar no nome do certificado, o histórico
continua na mesma pasta em vez de duplicar.

### Controle por cliente (`_controle.json`)

Cada cliente tem um `_controle.json` na raiz da própria pasta, guardando:

```json
{
  "versao": 1,
  "backfill_concluido": {"recebidas": true, "emitidas": false},
  "notas_baixadas": {"recebidas": ["chave1", "chave2", ...], "emitidas": [...]}
}
```

Duas funções:

1. **Backfill automático.** Cliente sem esse arquivo (ou com o campo
   `false` para uma listagem) tem a busca estendida até
   `primeira_busca_desde` do config (padrão `2026-01-01`), mesmo pedindo só
   um mês — assim atender um cliente novo já traz o histórico inteiro sem
   precisar lembrar de rodar manualmente com data antiga.

2. **Evita rebaixar.** Antes de chamar a API para uma chave, pula se o
   arquivo `.xml` já existe no disco OU se a chave já está no controle —
   o segundo caso cobre notas cujo arquivo foi movido/arquivado para fora
   da pasta depois de baixado.

**Detalhe de correção importante:** `backfill_concluido` só é marcado
**depois que todos os downloads daquele período terminam sem falha** — nunca
logo após a listagem. A primeira versão marcava logo após listar, e isso
tinha um bug real: se o processo caísse no meio dos downloads (queda de
energia, janela fechada), a próxima execução veria "backfill já feito" e
voltaria a consultar só o período pedido originalmente — os meses no meio do
caminho ficariam órfãos **para sempre**, sem nenhuma consulta futura
alcançá-los. Isso foi encontrado e corrigido antes de ir para produção; veja
`teste_interrupcao.py` (ou a descrição dele nesta seção de testes) para o
cenário reproduzido.

Gravação é atômica (escreve em `.tmp` e substitui) para não corromper o
controle anterior numa queda no meio da escrita.

## O agente SaaS

Implementado em 01/08/2026 a partir de [PLANO_SAAS_AGENTE.md](../PLANO_SAAS_AGENTE.md).
Dois módulos novos, isolados do resto: `api_client.py` (todo o diálogo HTTP
com `ContabOne.Api`, mais as funções puras de CNPJ e o cache de licença) e
`regras.py` (busca/cacheia/valida o bundle de regras de coleta). `nfse.py`
só orquestra: chama esses módulos em pontos específicos de `main()`/
`processar_empresa()` e nunca fala HTTP diretamente.

**Sem `[api]` preenchido no config.toml (`url` e `chave` os dois vazios),
nada nesta seção roda** — é o modo legado, byte a byte o mesmo comportamento
de antes. `config["api"]` é `{}` nesse caso; com os dois campos preenchidos
vira truthy e liga o modo agente. Um `[api]` pela metade (só `url` ou só
`chave`) é erro de configuração (`erro_fatal`), nunca um modo silencioso
intermediário.

### Handshake e licenciamento (`api_client.avaliar_licenca`)

Primeira coisa que `main()` faz, antes de sequer listar `certificados/`.
`POST /api/agent/handshake` devolve `podeExecutar`, a versão atual das
regras, o plano, e — importante — `hmacCnpjKey` (a chave HMAC pra mascarar/
hashear CNPJ, igual pra todos os agentes do mesmo escritório; nunca fica no
config.toml, vem sempre fresca do servidor).

**Carência offline:** se a API não responder (timeout, conexão recusada,
5xx), o agente cai pro cache assinado `_agente_cache.json`. Dentro de
`tolerancia_offline_dias` (padrão 7, configurável), segue rodando com o que
tinha; passado esse prazo, para com uma mensagem clara. Sem isso, bloquear a
API no firewall seria "grátis pra sempre"; com isso, uma queda real da
infra não incomoda ninguém no dia a dia, mas um bloqueio deliberado para de
funcionar numa semana.

**Ponto que exigiu atenção lendo o código real da API (não só o plano):**
`ApiKeyAuthenticationHandler.cs` rejeita com **401** tanto uma chave errada
quanto um escritório com `Status != Ativo` — os dois casos nunca chegam a
entrar no handler de handshake que devolveria `podeExecutar: false` com
mensagem. Ou seja, na prática, `mensagem` do handshake (§3.2 do plano) só é
alcançável para status que a própria checagem de autenticação já filtrou
como Ativo — o `switch` em `HandshakeAsync` que mapeia
Inadimplente/Suspenso/Cancelado pra uma mensagem específica é código morto
hoje. **Por isso `avaliar_licenca` trata HTTP 401 como um bloqueio
IMEDIATO, nunca como "API fora do ar"** — herdar a carência offline aqui
significaria que revogar uma chave ou suspender um escritório inadimplente
levaria até `tolerancia_offline_dias` pra fazer efeito, o oposto do que a
revogação deveria fazer. Isso não foi "corrigido" do lado da API nesta
sessão (fora do escopo do PLANO_SAAS_AGENTE.md) — só documentado aqui e
coberto por teste (`teste_licenca.py`,
`teste_401_nunca_herda_carencia_mesmo_com_cache_valido`) pra não se perder.

**Sobre a assinatura do cache:** é HMAC-SHA256 do payload usando a própria
chave de API do agente como segredo — não uma assinatura do servidor (a API
real não assina nada; `salvar_cache_licenca`/`carregar_cache_licenca` fazem
isso só do lado do agente). Isso não é criptografia à prova de engenharia
reversa (quem tem o config.toml tem a chave usada pra assinar), só impede a
edição TRIVIAL do `_agente_cache.json` num editor de texto — que é
exatamente o ataque que o plano descreve querer evitar (§3.2/§8). Ver o
comentário longo em `api_client._assinar_payload`.

**`agenteVersaoMinima` nunca bloqueia**, só loga um aviso — bloquear por
versão travaria o cliente justamente no momento em que a API/rede já é o
ponto frágil.

### Configuração do escritório cifrada (change `agente-config-minima-cifrada`)

O handshake também entrega a configuração do escritório (tipos de nota,
`primeira_busca_desde`, `pasta_saida`, `gerar_pdf`, `dias_busca_padrao` —
editada na tela de Configuração do painel) num campo `configuracaoCifrada`,
não mais como dicionário em claro. Motivo: com isso, `config.toml` só
precisa guardar `[api]` e o bloco de senha — tudo o mais é preferência de
escritório, já duplicada entre arquivo local e painel, e a duplicata some.

Cifra: AES-256-GCM, envelope `base64(nonce[12] ‖ ciphertext ‖ tag[16])`. A
chave simétrica **não é um segredo novo** — é `HMAC-SHA256(key = API key
bruta do agente, msg = "nfse-configuracao-v1")`. Funciona porque a API já
vê a API key em claro em todo request autenticado (header `X-Api-Key`),
mesmo persistindo só o hash dela no banco (`ApiKeyHasher`); e o agente já
tem a mesma chave em `config["api"]["chave"]`. Implementado nos dois lados
sem trocar mais nada entre eles: `ContabOne.Api/Security/ConfiguracaoCipher.cs`
cifra ao montar `HandshakeResponse`; `api_client.decifrar_configuracao()`
decifra assim que o handshake responde, **antes** de gravar
`_agente_cache.json` — o cache guarda o dicionário já decifrado (não o
envelope), para não precisar de rede/decifragem de novo justamente quando a
API pode estar fora do ar.

Falha ao decifrar (chave errada, payload corrompido, campo ausente por API
antiga) nunca é `erro_fatal()` — é tratada exatamente como "configuração
remota ausente": aviso em log, segue com `config.toml` local. Mesma política
já usada para bundle de regras inválido e para qualquer valor remoto
inválido em `aplicar_configuracao_remota`.

### Regras de coleta remotas (`regras.py`)

Substitui os literais que antes eram fixos em `nfse.py`: `LISTAGENS`,
`MAX_DIAS_FILTRO`, `PARAM_PAGINA`, `URL_NOTAS`, `URL_LOGIN_CERTIFICADO`,
`URL_API_NFSE`, e as três regex de parsing (chave da nota, linha da tabela,
total de registros) — ver `aplicar_regras()` em `nfse.py`.

**Como isso não quebrou nada que já funcionava:** esses valores continuam
sendo módulo-globais com o valor de fábrica de sempre (idêntico ao que
existia antes desta sessão) como padrão. `aplicar_regras(bundle)` só é
chamada quando o modo agente está ligado; sem `[api]`, ninguém nunca chama
essa função, e todo o resto do código (`montar_url`, `extrair_notas`,
`janelas`, `total_registros`) lê esses globais exatamente como sempre leu.
As funções puras em si não mudaram de assinatura nem de lógica.

**Um bug sutil e real, achado escrevendo o teste, não depois:**
`janelas(inicio, fim, max_dias: int = MAX_DIAS_FILTRO)` tinha o limite como
**valor padrão de parâmetro** — em Python isso é calculado UMA VEZ, na
definição da função (import do módulo), não a cada chamada. Como
`aplicar_regras()` reatribui `MAX_DIAS_FILTRO` depois que o módulo já
carregou, esse default ficaria travado em 31 pra sempre, ignorando
silenciosamente qualquer bundle remoto que mudasse o limite. Corrigido pra
ler o global dentro do corpo da função (`if max_dias is None: max_dias =
MAX_DIAS_FILTRO`). Se algum dia mais alguma constante virar
"substituível por regras remotas", conferir se ela não está escondida como
default de parâmetro em algum lugar — é fácil não perceber.

**Bundle de fábrica embutido** (`regras.BUNDLE_FABRICA`) é o snapshot de
todos esses literais. Só é usado quando não há cache local utilizável
(`_regras_cache.json` ausente/corrompido/inválido) E a API não pôde ser
contatada — na prática, o primeiro contato de uma instalação nova no
momento exato em que a API está fora do ar. **Bundle inválido nunca
substitui um bom**: `regras.validar_bundle()` roda antes de qualquer
`salvar_cache`, e uma falha de validação só loga um aviso e mantém a
versão em cache (ver `teste_bundle_invalido_nao_substitui_o_bom`).

### Métricas e dados de certificado (§5/§6 do plano)

`processar_empresa()` agora devolve `(resumo, metricas)` em vez de só
`resumo` — `metricas` é uma linha por `(tipo, competência)`, incrementada
nos MESMOS pontos do código que já incrementavam `resumo`, então as duas
nunca podem divergir uma da outra. `main()` acumula isso de todas as
empresas e, no fim (depois que os downloads reais já terminaram), chama
`api_client.enviar_relatorio_execucao()`: upsert de clientes → abre
execução → envia métricas → finaliza. **Nunca lança** — falha de rede aí
vira aviso + uma pendência em `_pendencias/{timestamp}.json`, retentada no
início da próxima execução (`api_client.reenviar_pendencias`, descarta
pendências com mais de 30 dias). O trabalho real (baixar as notas) já
terminou antes dessa seção rodar; um POST que falha não pode invalidar
isso — mesmo princípio já usado em `_escrever_no_arquivo`.

**Achado real ao escrever `teste_payload_vazamento.py` (antes de rodar,
não depois):** a primeira versão de `_montar_payload_clientes` mandava
`empresa.pfx.name` (o nome de arquivo ORIGINAL) como `certificadoNomeArquivo`.
No padrão de nome recomendado
(`codigoEmpresa_CNPJ_NomeEmpresa_s.SENHA_v.DD.MM.AAAA.pfx`), esse nome
embute o **CNPJ completo e a senha em texto claro** — exatamente os dois
campos que o plano proíbe enviar (§6). Corrigido: `certificadoNomeArquivo`
agora é reconstruído só a partir do código + extensão
(`_nome_arquivo_sanitizado`, ex.: `"0001.pfx"`), nunca o nome original —
mesmo no caso de um certificado fora do padrão, onde não dá pra garantir
que o texto que sobrou no nome não seja sensível.

**`clienteId` nas métricas é um Guid do servidor, não o `codigo` local** —
`ExecucaoMetrica.ClienteId` é FK contra `Cliente.Id` no banco. Isso expôs
uma lacuna real de contrato: `POST /api/agent/clientes` não devolvia essa
correspondência codigo→id, então não havia como montar o payload de
métricas de jeito nenhum. Corrigido adicionando um campo `clientes:
[{codigo, id}]` na resposta desse endpoint
(`ContabOne.Api/Features/Agent/AgentEndpoints.cs`, `UpsertClientesAsync`) —
mudança pequena, aditiva, fora do escopo original do PLANO_SAAS_AGENTE.md
mas necessária pra ele funcionar de ponta a ponta; confirmada com um
handshake→upsert→métricas real contra a API rodando localmente (Postgres
via `docker-compose.yml`).

**Formato de `tipo`/`status` no JSON: inteiro, não string.** `TipoNota` e
`StatusExecucao` no lado .NET não têm `JsonStringEnumConverter` registrado
em `Program.cs` (conferido nesta sessão) — o System.Text.Json serializa
enum como número por padrão. `api_client.TIPO_NOTA`/`STATUS_EXECUCAO` fazem
essa tradução; é fácil "consertar" isso de volta pra string achando que
fica mais legível sem perceber que quebra a integração (a API responderia
400, silenciosamente do lado errado pra quem só olha o agente).

### Fila de pendências e modo legado

Ver `_salvar_pendencia`/`reenviar_pendencias` em `api_client.py`. Cada
pendência é o payload local inteiro (clientes + métricas + status) — não
tenta retomar uma `Execucao` meio-aberta do lado do servidor; a próxima
tentativa simplesmente abre uma execução nova. Uma `Execucao` que nunca
recebeu métricas/finalização por causa disso é, de propósito, exatamente o
sintoma que o dashboard deveria mostrar como "travou" — não é escondido.

Migração (§9 do plano): publicar aceitando `[api]` ausente = modo legado
já está feito (é o comportamento padrão sem a seção preenchida). Não
existe ainda nenhum escritório real cadastrado além dos dados de
desenvolvimento (`/api/seed/dev`) usados pra testar.

## Estrutura de arquivos

```
Nfse.Agent/
├── nfse.py              programa principal — CLI, autenticação, coleta, controle, log, orquestra o agente
├── api_client.py         diálogo com ContabOne.Api: handshake/licenciamento, CNPJ, métricas, pendências
├── regras.py             bundle de regras de coleta remoto: busca, cache, validação, fábrica
├── danfse.py            gerador do DANFSe v2.0 (NT 008), usável também isolado
├── build.py             empacota tudo + recursos em dist/nfse/nfse.exe
├── config.toml          configuração (pastas, senha, período de backfill, [api] opcional)
├── requirements.txt     requests, requests-pkcs12, reportlab
├── logo_nfse.png         logomarca oficial NFS-e (embutida no .exe, exigida pela NT 008)
├── municipios_ibge.json  tabela IBGE código→município/UF (embutida no .exe)
├── certificados/        .pfx de cada empresa (NÃO versionar/compartilhar — tem CNPJ+senha)
├── notas/               saída: {codigo}_{nome}/{ano-mes}/Recebidas|Emitidas/
├── logs/                 um nfse_AAAA-MM-DD.log por dia (criado no primeiro run; mesma
│                          cautela de certificados/notas — pode ter nome/CNPJ de cliente)
├── _agente_cache.json    cache assinado do último handshake (só existe com [api] configurado)
├── _regras_cache.json    cache do bundle de regras (idem)
├── _pendencias/          relatórios de execução que falharam ao enviar, retentados no próximo run
├── testes/               suíte offline (ver "Testes existentes") — python testes/executar_tudo.py
├── dist/nfse/            pacote pronto para distribuir (gerado por build.py)
├── README.md             documentação de uso, mais detalhada que este handoff
├── HANDOFF.md            este arquivo
└── PLANO_DASHBOARD.md    plano do dashboard LOCAL, removido em 09/08/2026 — só histórico
```

`danfse.py` pode ser chamado sozinho: `python danfse.py nota.xml [saida.pdf]`.

Documentos irmãos fora desta pasta (`contab-one/`, um nível acima):
[PLANO_SAAS_AGENTE.md](../PLANO_SAAS_AGENTE.md) (este documento, o plano que
motivou a seção "O agente SaaS"), [PLANO_SAAS_API.md](../PLANO_SAAS_API.md)
(a API .NET, `../ContabOne.Api/`), [PLANO_SAAS_FRONTEND.md](../PLANO_SAAS_FRONTEND.md)
(o painel web, `../ContabOne.Frontend/`).

## Testes existentes

Várias suítes offline (não tocam rede):

- **teste_nfse.py** (53 asserts) — extração de dados do certificado pelo nome
  do arquivo, janelas de 31 dias, montagem de URL (`pg=` não `pagina=`,
  `executar=1` só em Recebidas), parsing das duas listagens (colunas
  diferentes por tipo), config.toml.
- **teste_controle.py** (16 asserts) — round-trip do `_controle.json`,
  recuperação de JSON corrompido, `baixar_xml` consultando o controle sem
  tocar a API, precedência de senha (arquivo > `[senhas]` > `senha_padrao` >
  env var), erro imediato sem nenhuma fonte de senha.
- **teste_interrupcao.py** (6 asserts) — reproduz o bug do backfill marcado
  cedo demais, e confirma que o código atual só marca `backfill_concluido`
  depois do laço de download inteiro, condicionado a zero falhas.
- **teste_dashboard.py** (26 asserts) — `gerar_dados()` contra uma árvore de
  pastas fake, contagem por mês/tipo/cliente, certificado vencido, backfill
  parcial, `_dashboard.json`/`.data.js` gravados atomicamente,
  `sincronizar_html`. (Sem objeto de teste desde 09/08/2026: o dashboard
  local foi removido — não recriar.)
- **teste_log_pausa.py** (13 asserts) — `log()`/`log_excecao()` gravando no
  arquivo do dia, `erro_fatal()` saindo com código inteiro (nunca string), a
  dica de caminho-Windows-quebra-TOML aparecendo, `_escrever_no_arquivo`
  nunca lançando exceção mesmo com a pasta de log inacessível.
- **teste_subprocess_pausa.py** (19 asserts) — end-to-end via `subprocess`
  real (não dá para provar "a janela espera ENTER" só com teste de unidade):
  processo fica vivo esperando `input()`, destrava ao receber ENTER,
  `--sem-pausa` sai sozinho, stdin fechado não trava mesmo sem a flag,
  `--ajuda` também passa pela pausa.
- **teste_exe_pausa.py** — repete os cenários de pausa/log contra o `.exe`
  compilado (não só o `.py` cru), para garantir que o PyInstaller não muda
  esse comportamento.

Esses seis arquivos ficaram no diretório de scratchpad da sessão Claude que
os escreveu, não dentro do projeto, e não estavam mais acessíveis nesta
sessão (01/08/2026) — cada sessão tem seu próprio scratchpad. Os cenários
mais próximos do que esta sessão mexeu foram reconstruídos em
`testes/teste_regressao_coleta.py` (não é literalmente o mesmo arquivo, é
uma cobertura equivalente pra `pg=`/`executar=1`/janelas de 31 dias/parsing/
`ler_certificado`/`senha_da_empresa`/`_controle.json`); o resto (dashboard,
DANFSe, pausa/log) não foi tocado por esta sessão e continua só descrito
acima, sem teste reconstruído — se for mexer nessas partes, vale recriar o
cenário como um novo `testes/teste_*.py`, seguindo o padrão dos arquivos
que já existem na pasta. (O caso "dashboard" saiu dessa lista em
09/08/2026: o recurso não existe mais.)

**A partir de 01/08/2026, os testes vivem em `testes/` dentro do projeto,
não em scratchpad** — decisão desta sessão, pra parar de perder as suítes
entre sessões (é literalmente o "pasta que ainda não existe" mencionado
acima em versões anteriores deste documento). `testes/_fake_api.py` e
`testes/_harness.py` são fixtures compartilhadas (não são testes em si —
`executar_tudo.py` os ignora). Arquivos atuais:

- **teste_api_client.py** (39 asserts) — as seis chamadas HTTP contra um
  fake local (`http.server`): sucesso, 401→`ApiCredenciaisInvalidas`,
  500→`ApiIndisponivel`, 404 em `/regras`→`RegraNaoPublicada`, timeout,
  conexão recusada; `tipo`/`status` vão como inteiro no JSON (não string —
  ver seção "O agente SaaS"); política de retry configurada;
  `mascarar_cnpj`/`hash_cnpj`/`versao_desatualizada`.
- **teste_licenca.py** (31 asserts) — `avaliar_licenca`: sucesso online,
  bloqueio pelo servidor, **401 nunca herda a carência offline mesmo com
  cache válido** (o teste mais importante do arquivo), cache válido roda
  offline, cache vencido bloqueia, cache adulterado (assinatura não bate) é
  tratado como inexistente, cache cujo último estado já era bloqueado
  continua bloqueado offline.
- **teste_regras.py** (38 asserts) — validação de esquema (cada campo
  obrigatório, um de cada vez), cache local, instalação nova cai pro bundle
  de fábrica (com e sem API acessível), **bundle inválido nunca substitui
  um bom em cache**, 304 mantém o cache, versão local já atual não bate na
  API, 404 (SaaS sem nenhuma regra publicada) não é tratado como pânico.
- **teste_pendencias.py** (16 asserts) — `enviar_relatorio_execucao` nunca
  lança mesmo com a API fora do ar, grava pendência, `reenviar_pendencias`
  reenvia e apaga em caso de sucesso, mantém em caso de nova falha, descarta
  pendência com mais de 30 dias ou corrompida.
- **teste_payload_vazamento.py** (17 asserts) — nenhum campo enviado à API
  contém a senha, o CNPJ completo, ou o nome de arquivo original do
  certificado (achou o bug do `certificadoNomeArquivo` — ver seção "O
  agente SaaS"); métricas não carregam nada parecido com conteúdo de nota.
- **teste_regressao_coleta.py** (47 asserts) — `montar_url` (`pg=`,
  `executar=1` só em Recebidas), `janelas` (31 dias exatos, 32 já quebra em
  duas), `extrair_notas`/`total_registros`, `ler_certificado` (padrão
  completo, sem senha, totalmente fora do padrão), `senha_da_empresa`
  (ordem de precedência completa), round-trip/corrupção de `_controle.json`,
  `carregar_config` com `[api]` ausente/incompleto/completo.
- **teste_subprocess_agente.py** (12 asserts) — ponta a ponta via
  `subprocess` real (exit code só dá pra observar de fora): `--ajuda` sai
  0, **bloqueio por inadimplência sai com código 3 e nunca chega a tocar o
  `.pfx`** (mtime e conteúdo bit a bit idênticos antes/depois — o item mais
  crítico do checklist do plano), chave revogada também sai 3, modo legado
  sem `[api]` nunca tenta rede.

`python testes/executar_tudo.py` roda tudo (~20s) e resume o resultado.
Cada teste também roda sozinho (`python testes/teste_licenca.py`).

**O que esta sessão NÃO fez:** rodar `dist/nfse/nfse.exe` compilado contra
os mesmos cenários de bloqueio/licenciamento (só contra `--ajuda` e um
bloqueio por inadimplência, manualmente, não como parte de
`executar_tudo.py` — reconstruir isso como `teste_exe_agente.py` se quiser
essa cobertura automatizada; precisa buildar antes, então normalmente não
entra no ciclo rápido de teste).

Validação ao vivo feita (não só testes unitários): backfill real trazendo
373 notas de um cliente novo (6 janelas de 31 dias, 192s), reexecução
idempotente do mesmo período (3s, 0 downloads), tudo repetido pelo `.exe`
compilado com os mesmos resultados. Em 01/08/2026, o agente foi validado
de ponta a ponta contra a API real (`ContabOne.Api` local + Postgres via
`docker-compose.yml`, não um fake): handshake, busca de regras (200 e 304),
upsert de clientes (recebendo o Guid real de volta), abrir/enviar métricas/
finalizar execução — conferido depois direto no Postgres (`SELECT` nas
tabelas `Clientes`/`Execucoes`/`ExecucaoMetricas`) que os valores batiam
exatamente com o que foi enviado.

## Estado atual dos dados reais

`notas/` tem hoje **2 clientes**, ambos já com `_controle.json` (o recurso
de controle e o backfill já passaram por eles pelo menos uma vez):

- `0001_SOLUTION FARMA CONTABILIDADE LTDA` — 75 XML
- `00097_LEJ CONTABIL_123456_v.09.12.2026` — 84 XML (nome de pasta reflete um
  certificado cujo arquivo está fora do padrão completo — o `_123456_v...`
  ali é literalmente o restante do nome do arquivo, não senha/validade
  interpretadas; é só um exemplo real de "código antes do primeiro `_`
  continua funcionando mesmo com o resto do nome bagunçado")

Os dois têm `2026-01` a `2026-07` de **Recebidas apenas** (75 e 84 XML,
respectivamente) — nenhum dos dois tem XML de Emitidas ainda, mesmo a pasta
`Emitidas/` existindo em alguns meses (só o CSV foi gerado ali, sem baixar).
Ou seja: a próxima execução sem `--tipos recebidas` vai buscar Emitidas pela
primeira vez para os dois — confira no disco antes de assumir o que já foi
baixado, este documento pode estar desatualizado por sessões futuras.

## Decisões que valem lembrar (para não desfazer sem querer)

- **Nunca há prompt de senha no console**, em nenhuma circunstância. Foi
  uma escolha deliberada depois de um teste travar 5 minutos — não
  reintroduzir `getpass()`/`input()` para isso.
- **PDF nunca sobrescreve um já existente**, nem os poucos que vieram
  direto do portal (leiaute v1.0, antes desta ferramenta existir) nem os
  gerados por `danfse.py`.
- **O controle usa o disco como fonte de verdade quando possível** (o
  `baixar_xml` primeiro olha se o arquivo existe, só depois consulta o
  `_controle.json`) — segue o mesmo princípio já usado em `gerar_pdf`.
- **PDF não é afetado pelo controle de "já baixado"** — só o download do
  XML (que tem custo de rede). Gerar o PDF de novo a partir de um XML já
  existente é local e barato, então continua condicionado só à existência
  do próprio `.pdf`.
- **Build compila fora do OneDrive** (`%TEMP%\build-nfse`) porque o
  sincronizador segura arquivos durante a escrita do PyInstaller e gera
  `PermissionError` no meio do build.
- **A janela do console só fecha com ENTER, sempre, sem exceção** (a menos
  que rode com `--sem-pausa`). Isso substituiu uma heurística antiga
  (`aberto_por_duplo_clique()`, removida) que tentava adivinhar via
  `GetConsoleProcessList` se valia a pena esperar — ela falhava
  silenciosamente em cenários reais (Windows Terminal/ConPTY no Windows 11
  conta processos de forma diferente do conhost clássico) e, pior, **nem
  chegava a rodar** em boa parte dos casos de erro: todo `sys.exit("mensagem")`
  levanta `SystemExit`, que não é subclasse de `Exception` — o
  `except Exception` no `__main__` não pegava, e o processo terminava antes
  de alcançar a linha da pausa. Foi exatamente isso que causou um relato real
  de usuário ("recebi um erro mas a janela fechou antes de eu ler"). A
  correção: todo `sys.exit(str)` de mensagem de erro foi trocado por
  `erro_fatal()` (loga e sai com código 1, nunca string), e o bloco final do
  `__main__` agora captura `SystemExit` explicitamente antes da pausa, então
  não importa de onde veio o erro — a pausa sempre roda. Se mexer nesse
  bloco de novo, **não reintroduza um `sys.exit(str)` direto** em código
  novo — use `erro_fatal()`.
- **Log em arquivo, um por dia** (`logs/nfse_AAAA-MM-DD.log`, dentro de
  `RAIZ`). `log()` grava em console E arquivo automaticamente — todo call
  site existente continuou igual. Exceções reais usam `log_excecao()`, que
  manda uma linha curta pro console mas o traceback completo só pro arquivo
  (não assusta o usuário leigo com stack trace na tela, mas preserva o
  detalhe pra diagnosticar depois). Mesma cautela de `certificados/`/`notas/`
  se aplica: o arquivo pode conter nome de cliente/CNPJ dentro de uma
  mensagem de erro, então não é para compartilhar/commitar sem revisar.
- **Isso não contradiz "nunca há prompt de senha no console"** (linha acima)
  — são mecanismos diferentes. A pausa final (`input("Pressione ENTER...")`)
  acontece **depois** que tudo já rodou, só para dar tempo de ler a tela; não
  há decisão de negócio nem senha esperando resposta ali. Por isso é seguro
  ter um `input()` incondicional no fim, mas continua errado ter um no meio
  da lógica de autenticação — a diferença é o que está do outro lado
  esperando: nada de crítico trava se ninguém apertar Enter (o processo já
  terminou seu trabalho), então mesmo sem `--sem-pausa` o pior caso é a
  janela ficar aberta sem uso, não uma tarefa agendada travada para sempre
  (e o `except (EOFError, OSError)` ao redor do `input()` cobre até esse
  caso, se o stdin realmente não existir).
- **HTTP 401 do `/api/agent/*` nunca é tratado como "API fora do ar"**,
  sempre como negativa explícita e imediata (bloqueia, não entra na
  carência offline). Ver "O agente SaaS" acima — é o mesmo princípio da
  regra anterior (nunca prompt de senha), aplicado a licenciamento: um
  "não" claro do servidor não pode se comportar como um "não sei".
- **`certificadoNomeArquivo` enviado à API nunca é o nome de arquivo
  original** — é reconstruído (`_nome_arquivo_sanitizado`) porque o padrão
  de nome recomendado embute CNPJ completo e senha. Se um dia alguém achar
  "estranho" que esse campo não bate com o arquivo real no disco e for
  "corrigir" pra mandar o nome original, é uma regressão de segurança, não
  uma correção — ver o teste `teste_payload_vazamento.py`.
- **`erro_fatal()` aceita um `codigo` opcional** (padrão 1, preserva todo
  call site existente); o bloqueio de licenciamento usa `codigo=3` de
  propósito, pra ser distinguível de um erro de configuração comum por
  quem só olha o exit code (ex.: um agendador de tarefas).
- **O dashboard local foi removido em 09/08/2026** — `dashboard.py`,
  `dashboard.html`, a geração de `_dashboard.json`/`_dashboard.data.js`, o
  `--add-data`/`--hidden-import` correspondentes no `build.py` e o bloco
  "---- dashboard ----" no fim da `main()`. Motivo: o painel do escritório
  agora é o frontend web do SaaS (`../ContabOne.Frontend/`), que lê os mesmos números
  pelas métricas que o agente já reporta; manter uma segunda
  implementação do mesmo relatório, com nome e **CNPJ completo** dos
  clientes em texto claro dentro de `notas/`, era superfície de dado
  sensível sem contrapartida. O agente voltou a fazer só o que o nome diz:
  baixar XML/PDF e reportar. Se um dia isso voltar a fazer falta offline, o
  caminho é reimplementar de propósito (o `PLANO_DASHBOARD.md` continua na
  pasta como histórico), não "desfazer a remoção" — nada mais no código
  depende desses arquivos.
- **`LISTAGENS`/`MAX_DIAS_FILTRO`/`PARAM_PAGINA`/`URL_NOTAS`/as três regex
  de parsing são globais reatribuíveis**, não mais só constantes fixas —
  `aplicar_regras()` os sobrescreve quando o modo agente está ligado. Eles
  continuam com o valor de fábrica de sempre por padrão; se adicionar uma
  função nova que precise de um desses valores, leia o global dentro do
  corpo da função, nunca como valor padrão de parâmetro (`def f(x=CONST)`)
  — esse é exatamente o bug que `janelas()` tinha (ver "O agente SaaS").

## Limitações conhecidas

- Requer certificado **A1** (arquivo `.pfx`). A3 (token/cartão) não serve —
  a chave privada não sai do dispositivo, não dá para apresentar via mTLS
  por software.
- `.exe` não é assinado digitalmente — Windows SmartScreen avisa na
  primeira execução ("Executar assim mesmo"). Resolver isso de vez exige
  certificado de assinatura de código (EV Code Signing), que é pago.
- Parsing da listagem depende do HTML do portal. A extração da chave (via
  padrão de URL) é resiliente a mudanças de layout; os demais campos das
  colunas (situação, valores) são mais sensíveis a isso.
- Ações de workflow (Confirmar/Rejeitar nota) não são implementadas — a
  ferramenta só lê e baixa.
- **Auto-atualização do agente não foi implementada** — deliberadamente. O
  plano (§11.4) já sinalizava isso como arriscado (baixar e trocar o
  próprio `.exe` é o vetor perfeito pra distribuir código malicioso se a
  API for comprometida) e "se for fazer, exigir assinatura do pacote" —
  como não há infraestrutura de assinatura de código nesta sessão, a
  decisão foi não construir isso agora. `agenteVersaoMinima` só avisa (ver
  "O agente SaaS"); atualizar continua sendo trocar a pasta manualmente.
- **Não existe instalador com wizard pedindo a chave de API.** A Fase 6 do
  plano menciona isso; o que existe é o `config.toml` com a seção `[api]`
  comentada por padrão (o usuário preenche à mão) e um parágrafo novo no
  `LEIA-ME.txt` explicando. Não foi construído um instalador de verdade
  (Inno Setup ou similar) — não existia infraestrutura de instalador nesta
  base de código pra começo de conversa, e um wizard interativo pedindo
  input no meio da execução iria contra o princípio já estabelecido de
  "nunca há prompt no console" (ver seção de decisões) se fosse aplicado
  ao próprio `nfse.exe`; um instalador SEPARADO (que só roda uma vez, antes
  do agente propriamente dito) não teria esse problema, mas construir um do
  zero ficou fora do escopo desta sessão.
- **A fila de pendências (`_pendencias/`) não tem limite de tamanho além da
  expiração de 30 dias** — um escritório com a API fora do ar por semanas
  seguidas acumula um arquivo por execução. Não é um problema de
  correção (cada um é pequeno, JSON), só algo a observar se algum dia
  virar reclamação de usuário.

## Próximo passo planejado

O [PLANO_DASHBOARD.md](PLANO_DASHBOARD.md) descreve um dashboard local que
lia `notas/` direto do disco. Foi implementado e depois **removido em
09/08/2026** (ver "Decisões que valem lembrar") — o painel do escritório é
o frontend web. O documento fica na pasta só como histórico; não é um
"próximo passo" nem uma pendência.

O que falta do [PLANO_SAAS_AGENTE.md](../PLANO_SAAS_AGENTE.md) depois desta
sessão: as perguntas em aberto do próprio plano (§11) continuam abertas —
granularidade de métrica realmente usada pelo dashboard web (modelei
`(cliente, tipo, competência)`, é o que o plano sugeriu), um agente por
máquina vs. por escritório (upsert por `(ClienteId, Competencia, Tipo)` já
cobre duplicata do lado da API, então múltiplos agentes já funcionam sem
mudança extra), e se o agente algum dia deveria receber ordens da API
(hoje é só agente→API, nunca o contrário — nada nesta sessão mudou isso).
Auto-atualização e instalador com wizard: ver "Limitações conhecidas"
acima — avaliados e deliberadamente não construídos, não esquecidos.
