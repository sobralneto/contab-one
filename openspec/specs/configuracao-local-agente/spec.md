## Purpose

Define o que pode e o que não pode viver em `config.toml`, o arquivo de
configuração local de qualquer agente (`Nfse.Agent`, `Det.Agent` e os que
vierem depois), e como a senha do certificado é resolvida — para que a
plataforma nunca precise custodiar segredos que só fazem sentido na máquina
do escritório.

## Requirements

### Requirement: `config.toml` só documenta credencial de API e segredo de certificado

O template `config.exemplo.toml` de qualquer agente (`Nfse.Agent`, `Det.Agent` e os que vierem depois) DEVE (MUST) documentar apenas: a seção
`[api]` (`url`, `chave`, `tolerancia_offline_dias`) e o bloco de senha de
certificado (`senha_padrao` e `[senhas]`). Preferências operacionais do
escritório próprias de cada ferramenta (tipos de nota, pasta de saída,
geração de PDF, data de backfill, tamanho do período padrão, tipo de perfil
DET) NÃO DEVEM (MUST NOT) constar no template. Esses valores são entregues
pelo handshake e editados na tela de Configuração.

#### Scenario: Novo escritório copia o template

- **WHEN** um escritório copia `config.exemplo.toml` para `config.toml` pela
  primeira vez, em qualquer agente
- **THEN** o arquivo resultante contém somente `[api]` e o bloco de senha, e
  a ferramenta usa os valores padrão embutidos no código para tudo o mais
  até o primeiro handshake bem-sucedido

#### Scenario: `config.toml` antigo com as chaves removidas do template

- **WHEN** um `config.toml` existente ainda declara valores operacionais que
  o template não documenta mais (ex.: `pasta_saida`, `tipos`, `gerar_pdf`,
  `primeira_busca_desde`, `dias_busca_padrao`)
- **THEN** a ferramenta continua lendo esses valores normalmente como
  configuração local de fallback — a remoção do template não invalida
  arquivos existentes

#### Scenario: `Det.Agent` migra de `.env` para `config.toml`

- **WHEN** um escritório que já usava `Det.Agent` com `.env` passa a usar
  `config.toml`
- **THEN** a senha do certificado (antes em `DET_PFX_SENHA`) passa a ser
  lida de `senha_padrao` ou `[senhas]` em `config.toml`, seguindo a mesma
  ordem de resolução de qualquer outro agente

### Requirement: Senha do certificado resolvida pelo nome do arquivo

A seção `[senhas]` de `config.toml`, em qualquer agente, DEVE (MUST) ser
indexada pelo nome do arquivo do certificado (`nome_do_arquivo.pfx`), não
pelo código da empresa extraído do nome. A ordem de resolução de senha
permanece: senha embutida no nome do arquivo → `[senhas]` pelo nome do
arquivo → `senha_padrao` → variável de ambiente específica do agente
(`NFSE_PFX_SENHA`, `DET_PFX_SENHA`, …).

#### Scenario: Certificado com exceção de senha

- **WHEN** um `.pfx` chamado `ClienteExemplo.pfx` não traz senha no nome e
  `config.toml` tem `[senhas]` com a chave `"ClienteExemplo.pfx"`
- **THEN** a ferramenta usa a senha dessa entrada para abrir o certificado

#### Scenario: Certificado sem entrada em `[senhas]`

- **WHEN** o nome do arquivo do certificado não tem entrada correspondente
  em `[senhas]`
- **THEN** a ferramenta usa `senha_padrao`, e só falha se `senha_padrao`
  também estiver ausente

#### Scenario: Certificado sem convenção de nomenclatura

- **WHEN** um `.pfx` não segue nenhuma convenção de nome que embuta a senha
  (caso de `Det.Agent`, que usa um único certificado do escritório na pasta
  `certificado/`)
- **THEN** a resolução de senha por `[senhas]` continua funcionando, pois
  depende apenas do nome completo do arquivo, não de nenhum campo extraído
  dele
