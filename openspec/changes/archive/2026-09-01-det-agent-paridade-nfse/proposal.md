## Why

`Det.Agent` hoje é um robô isolado: lê senha e CNPJs de `.env`/`empresas.xlsx`
locais, nunca fala com `ContabOne.Api`, e entrega o resultado como um CSV que
o contador abre manualmente. Isso significa nenhuma licença, nenhum registro
de execução no painel, nenhum alerta de agente silencioso e nenhuma forma de
ver as notificações do DET pelo hub — exatamente os ganhos que `Nfse.Agent`
já tem. Trazer o DET para o mesmo modelo do NFS-e (handshake, licenciamento,
vínculo por CNPJ/escritório, dado consultável no painel) fecha essa lacuna
sem inventar um segundo padrão de integração agente↔SaaS.

## What Changes

- **Det.Agent** ganha `config.toml` no mesmo formato de `Nfse.Agent`
  (`[api] url`/`chave` obrigatórios — sem eles a ferramenta recusa rodar —,
  `senha_padrao` e bloco `[senhas]` por nome de arquivo de certificado). O
  `.env` atual (senha do certificado + lista de CNPJs) é substituído: senha
  migra para `config.toml`, lista de empresas continua vindo de
  `empresas.xlsx` (fora de escopo mudar a fonte agora — `fontes.py` já
  isola isso para uma troca futura).
- Ao final da execução, `Det.Agent` autentica com a chave de API (mesmo
  esquema `det_<prefixo8>_<segredo32>` já reservado em `ApiKeyHasher`),
  resolve o `Cliente.Id` de cada CNPJ via upsert (mesmo endpoint
  `POST /api/agent/clientes` que `Nfse.Agent` usa) e envia as mensagens
  coletadas para a API, vinculadas ao cliente certo e ao escritório
  identificado pela própria chave.
- **BREAKING** para quem já roda `Det.Agent` manualmente: a geração do CSV
  local (`resultado/YYYY-MM-DD_resultado-det.csv`) é removida do fluxo
  principal — o resultado passa a viver no painel. `tools/exportar_csv.py`
  continua existindo para quem precisar de um CSV pontual a partir do JSON
  já salvo em `dados/`.
- `ContabOne.Api` ganha uma tabela nova para guardar, por execução, as
  mesmas informações que hoje só existiam no CSV (CNPJ do cliente, título,
  mensagem, datas, situação, link) — não é uma métrica agregada como
  `ExecucaoMetrica`, é o conteúdo por notificação, porque é isso que o
  painel precisa listar.
- `ContabOne.Frontend` ganha uma página nova (entra no catálogo de páginas
  do produto DET, sem menu hard-coded) para visualizar essas mensagens,
  filtráveis por cliente.

## Capabilities

### New Capabilities
- `agente-det-integracao-api`: `Det.Agent` exige `[api] url`/`chave` para
  rodar, autentica como agente, faz upsert de clientes por CNPJ e envia o
  relatório de mensagens da execução para a API em vez de gravar CSV local.
- `registro-mensagens-det`: a API recebe e armazena as mensagens da Caixa
  Postal DET por execução, vinculadas a `Cliente` e `Execucao`, e expõe uma
  forma de consultá-las filtrando por cliente do escritório autenticado.
- `visualizacao-mensagens-det`: o painel oferece uma página, declarada nas
  `Paginas` do produto DET, que lista as mensagens recebidas com filtro por
  cliente.

### Modified Capabilities
- `configuracao-local-agente`: a regra de `config.toml` (só credencial de
  API e segredo de certificado, resolução de senha por nome de arquivo)
  deixa de ser exclusiva de `Nfse.Agent` e passa a valer, do mesmo jeito,
  para o `config.toml` de `Det.Agent`.

## Impact

- `Det.Agent/`: novo `config.toml`/`config.exemplo.toml`, novo
  `api_client.py` (modelado no de `Nfse.Agent`, reaproveitando o mesmo
  esquema de handshake/licença/upsert/relatório), remoção do `.env` e da
  geração de CSV do fluxo principal, ajuste em `runner.py`/`settings.py`.
- `ContabOne.Api/`: nova entidade + migration para mensagens DET, novos
  endpoints em `Features/Agent/AgentEndpoints.cs` (ou um `DetEndpoints.cs`
  próprio) para receber o relatório e para o painel consultar, possível
  cadastro do produto `det` no catálogo (dado, via admin — não deploy).
- `ContabOne.Frontend/`: nova view + rota `/f/det/mensagens` (ou nome
  equivalente), item de menu vindo do catálogo, sem hardcode.
- `Nfse.Agent/api_client.py` e `AgentEndpoints.cs` permanecem como estão —
  são a referência, não são alterados por esta mudança.
