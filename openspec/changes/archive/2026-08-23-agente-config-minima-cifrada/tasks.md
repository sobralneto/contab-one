## 1. API — cifragem do bloco `configuracao` no handshake

- [x] 1.1 Criar helper de derivação de chave (HMAC-SHA256 da API key bruta do
      request com rótulo fixo `"nfse-configuracao-v1"`) e helper de
      cifragem/decifragem AES-256-GCM (`nonce ‖ ciphertext ‖ tag` em base64),
      ao lado de `ApiKeyHasher`/`CnpjHasher` em `ContabOne.Api/Security/`.
- [x] 1.2 Em `AgentEndpoints.HandshakeAsync`, capturar o valor bruto do
      header `X-Api-Key` do request atual (já usado para autenticação) e
      cifrar o dicionário `configuracao` com a chave derivada dele.
- [x] 1.3 Trocar `HandshakeResponse.Configuracao` (`Dictionary<string,string>`)
      por `ConfiguracaoCifrada` (`string`, base64) — remover o campo em
      claro.
- [x] 1.4 Atualizar `ContabOne.Api.Tests` (contrato do handshake) para
      decifrar `ConfiguracaoCifrada` com a mesma derivação e comparar o
      dicionário resultante, em vez de ler `Configuracao` diretamente.

## 2. Agente — decifragem e derivação de chave

- [x] 2.1 Adicionar `cryptography` a `Nfse.Agent/requirements.txt` e como
      `--hidden-import` em `build.py`.
- [x] 2.2 Em `api_client.py`, implementar a derivação de chave (HMAC-SHA256
      de `config["api"]["chave"]` com o mesmo rótulo `"nfse-configuracao-v1"`)
      e a decifragem AES-256-GCM do envelope `configuracaoCifrada`.
- [x] 2.3 Ajustar `avaliar_licenca()`/o ponto que lê `resp.get("configuracao")`
      para ler `resp.get("configuracaoCifrada")`, decifrar, e cair para
      "configuração ausente" (log de aviso, nunca `erro_fatal`) em qualquer
      falha de decifragem/parsing ou campo ausente.
- [x] 2.4 Confirmar que `_agente_cache.json` continua guardando o dicionário
      já decifrado (mesmo formato de hoje) — nenhuma mudança no cache
      offline além da origem do valor.

## 3. Senha do certificado por nome de arquivo

- [x] 3.1 Alterar `senha_da_empresa()` em `nfse.py` para buscar
      `config["senhas"][empresa.pfx.name]` em vez de
      `config["senhas"][empresa.codigo]`.
- [x] 3.2 Atualizar `testes/teste_regressao_coleta.py` (`teste_senha_precedencia`
      e qualquer outro teste que use `[senhas]` por código) para a nova
      chave.

## 4. `config.exemplo.toml` e documentação

- [x] 4.1 Reduzir `Nfse.Agent/config.exemplo.toml` a `[api]` (`url`, `chave`,
      `tolerancia_offline_dias`) e o bloco de senha (`senha_padrao`,
      `[senhas]` com exemplo por nome de arquivo) — remover
      `pasta_certificados`, `pasta_saida`, `tipos`, `gerar_pdf`,
      `primeira_busca_desde`, `dias_busca_padrao` do template (os valores
      padrão embutidos em `CONFIG_PADRAO` continuam valendo).
- [x] 4.2 Atualizar `Nfse.Agent/README.md` (seção "Configuração —
      config.toml" e "Senha do certificado, sem digitar nada") para refletir
      o template reduzido e a chave de `[senhas]` por nome de arquivo.
- [x] 4.3 Atualizar `Nfse.Agent/CLAUDE.md` e `Nfse.Agent/HANDOFF.md` com a
      decisão de cifragem do bloco `configuracao` e a mudança de chave de
      `[senhas]` (código → nome do arquivo), incluindo o porquê de
      `pasta_certificados` continuar de fora do template.

## 5. Testes de ponta a ponta

- [x] 5.1 Atualizar `testes/teste_configuracao_remota.py` e o fake
      `/api/agent/handshake` em `testes/_fake_api.py` para responder com
      `configuracaoCifrada` no formato cifrado, cobrindo: decifragem
      correta, chave incompatível (aviso + config local), payload corrompido
      e campo ausente (API antiga).
- [x] 5.2 Rodar `py -3.14 testes/executar_tudo.py` e `dotnet test` e
      confirmar suíte verde.
