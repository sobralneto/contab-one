## Why

`Det.Agent` hoje tira a lista de empresas de uma planilha local
(`empresas/empresas.xlsx`) e, antes de enviar o relatório, faz **upsert** de
cada uma como `Cliente` do escritório (`POST /api/agent/clientes`). Isso
duplica, numa planilha que ninguém sincroniza, o cadastro de clientes que o
escritório já mantém no painel, e dá a um robô de *leitura* o poder de criar e
alterar clientes — foi o que um teste local mostrou: a ferramenta não roda sem
a planilha, e rodar com ela escreve no cadastro. O DET deve ser uma consulta
pura: o certificado do escritório na pasta, a carteira de clientes vinda do
painel, e só as mensagens voltando para a API.

## What Changes

- **BREAKING** A lista de empresas consultadas passa a vir **da API**: um
  endpoint novo, só de leitura, devolve ao agente DET os clientes **ativos**
  do escritório identificado pela chave (`X-Api-Key`), com o `Cliente.Id` e o
  CNPJ completo necessário para a troca de perfil no portal. A planilha
  `empresas.xlsx`, a opção `--empresas-arquivo` e a dependência `openpyxl`
  deixam de existir no fluxo do agente.
- **BREAKING** `Det.Agent` **nunca** escreve dados de escritório ou de
  cliente: deixa de chamar `POST /api/agent/clientes` e vincula as mensagens
  diretamente ao `Cliente.Id` recebido na lista. As únicas escritas que o
  agente faz na API são as da própria execução — abrir/finalizar `Execucao` e
  enviar `MensagemDet`.
- O certificado único da pasta `certificado/` (o do escritório) é conferido
  contra o escritório da chave antes de abrir o navegador: o agente lê o CNPJ
  do certificado e compara o hash HMAC com o do escritório informado pela API.
  Certificado de outro CNPJ bloqueia a execução.
- Clientes ativos **sem CNPJ completo cadastrado** (não há como digitá-los na
  troca de perfil) não são consultados: a API informa quantos são, o agente
  registra no log e no resultado, e o painel continua sendo o lugar de
  completar o cadastro.
- O endpoint novo é servido só a agentes do produto `det`; um agente NFS-e
  com chave válida recebe 403.

## Capabilities

### New Capabilities
- `carteira-clientes-agente-det`: a API expõe ao agente DET, só para leitura,
  a carteira de clientes ativos do escritório da chave (id, nome, CNPJ
  completo) e o hash do CNPJ do escritório, sem qualquer efeito colateral de
  escrita no cadastro.

### Modified Capabilities
- `agente-det-integracao-api`: a origem das empresas muda da planilha para a
  API; o requirement de vínculo por upsert de CNPJ é substituído pelo vínculo
  direto ao `Cliente.Id` da carteira; entram os requirements "o agente nunca
  escreve cadastro" e "o certificado da pasta tem de ser do escritório da
  chave"; o cenário de recusa sem `[api]` deixa de citar `empresas.xlsx`.

## Impact

- **Dependência de outra change:** requer `cnpj-completo-cliente` aplicada —
  é ela que introduz `Cliente.CnpjCifrado` e `CnpjCipher`. Sem ela a API não
  tem CNPJ completo algum para entregar, e toda a carteira cairia em "sem
  CNPJ completo".
- **API** (`ContabOne.Api/`): novo `GET` no grupo `/api/agent` em
  `Features/Agent/AgentEndpoints.cs`, com os DTOs de resposta; nenhuma
  migration; `POST /api/agent/clientes` não muda (o NFS-e continua usando).
  Testes em `ContabOne.Api/tests/` (contrato, isolamento multi-tenant,
  403 para produto ≠ `det`, nenhuma escrita em `Clientes`/`Escritorios`).
- **Agente** (`Det.Agent/`): `fontes.py` ganha a fonte `api` e perde a de
  Excel; `runner.py` deixa de montar o payload de upsert; `api_client.py`
  ganha a chamada de leitura e perde `upsert_clientes`; `settings.py`/`Config`
  perdem `empresas_arquivo`/`fonte_empresas`; conferência do CNPJ do
  certificado (via `cryptography`, já dependência); `requirements.txt` perde
  `openpyxl`; `README.md`, `config/empresas.example.json` e `build.py`
  atualizados; fake API e testes offline em `Det.Agent/testes/`.
- **Frontend:** nenhuma mudança — `/f/det/mensagens` continua listando por
  `Cliente.Id`.
- **Privacidade:** o CNPJ completo passa a trafegar da API para a máquina do
  escritório (sentido inverso ao dos demais agentes), por HTTPS, só para
  clientes do próprio escritório e só para o agente DET. O `.pfx` continua sem
  sair da máquina, e nenhum conteúdo novo sobe para a API.
