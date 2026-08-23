## Why

`config.toml` hoje expõe seis configurações operacionais (`pasta_saida`, `tipos`,
`gerar_pdf`, `primeira_busca_desde`, `dias_busca_padrao`) que o escritório pode
editar direto no Bloco de Notas — mas a plataforma já entrega essas mesmas
chaves pelo handshake e a tela de Configuração já as salva e exibe (ver
`handshake-agente` e `configuracao-persistencia`). Manter os dois caminhos
convida a divergência: o escritório edita o arquivo local pensando que mudou
o comportamento, enquanto o valor que realmente vale na próxima execução é o
que veio do servidor. `config.toml` deve sobrar só como config de máquina
(credencial da API + segredo de certificado que a plataforma nunca deve
guardar).

Duas lacunas correm junto:

1. O bloco `[senhas]` mapeia senha por **código da empresa**, um valor extraído
   por regex do nome do arquivo — exige que todo certificado siga o padrão
   `codigoEmpresa_CNPJ_NomeEmpresa...`. Como a ferramenta agora atende
   escritórios genéricos (não só o uso original), a chave certa é o **nome do
   arquivo do certificado**, que não depende de nenhuma convenção de
   nomenclatura.
2. O bloco `configuracao` do handshake viaja em JSON simples. É a única peça
   do contrato agente↔API sem proteção alguma em trânsito — deve chegar
   cifrada, com uma chave que só a API e a ferramenta conhecem (nenhum
   segredo novo a distribuir: a própria API key do agente, que a API já vê em
   claro em todo request autenticado mas nunca persiste, serve de base para
   a chave simétrica).

## What Changes

- `config.exemplo.toml` passa a documentar somente `[api]` (`url`, `chave`,
  `tolerancia_offline_dias`) e o bloco de senha (`senha_padrao` e
  `[senhas]`) — `pasta_saida`, `tipos`, `gerar_pdf`, `primeira_busca_desde` e
  `dias_busca_padrao` saem do template (continuam com valor padrão embutido
  no código; só a tela de Configuração os altera dali em diante).
- **BREAKING**: `[senhas]` passa a ser indexado pelo **nome do arquivo do
  certificado** (`empresa.pfx.name`), não mais pelo código da empresa.
  `senha_da_empresa()` muda a ordem de busca de acordo.
- O handshake passa a entregar o bloco `configuracao` **cifrado**
  (AES-256-GCM) em vez de JSON em claro. A chave simétrica é derivada da API
  key do agente (`chave`) via HKDF/SHA-256 com um rótulo fixo — calculável
  dos dois lados sem nenhum segredo adicional em `config.toml` ou nas
  variáveis de ambiente da API.
- `api_client.py` decifra o bloco recebido; falha de decifragem (chave
  errada, payload corrompido) é tratada como configuração remota ausente —
  aviso em log, segue com o `config.toml` local — nunca `erro_fatal()`.

## Capabilities

### New Capabilities
- `configuracao-local-agente`: o que pode e o que não pode viver em
  `config.toml`, e como a senha do certificado é resolvida por nome de
  arquivo.

### Modified Capabilities
- `handshake-agente`: o bloco `configuracao` do handshake passa a ser
  entregue cifrado, com a chave derivada da API key do agente.

## Impact

- `Nfse.Agent/config.exemplo.toml` — template reduzido.
- `Nfse.Agent/nfse.py` — `senha_da_empresa()` (chave por nome de arquivo).
- `Nfse.Agent/api_client.py` — cifragem/decifragem do bloco `configuracao`,
  derivação de chave.
- `Nfse.Agent/testes/teste_regressao_coleta.py`,
  `Nfse.Agent/testes/teste_configuracao_remota.py`,
  `Nfse.Agent/testes/testes/fixtures/cnpj_vetores.json` (se aplicável) —
  ajuste dos vetores de senha e do fake handshake para o payload cifrado.
- `ContabOne.Api/Features/Agent/AgentEndpoints.cs` — `HandshakeResponse` passa
  `Configuracao` como string cifrada (`ConfiguracaoCifrada`) em vez de
  `Dictionary<string,string>`.
- `ContabOne.Api.Tests` — contrato do endpoint de handshake (payload cifrado).
- `Nfse.Agent/README.md`, `Nfse.Agent/CLAUDE.md`, `Nfse.Agent/HANDOFF.md` —
  documentação da nova origem de senha e da cifragem.
