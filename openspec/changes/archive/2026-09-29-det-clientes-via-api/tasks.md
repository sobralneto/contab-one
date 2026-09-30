## 0. Pré-requisito

- [x] 0.1 Confirmar que `cnpj-completo-cliente` está aplicada: `Cliente.CnpjCifrado`
      e `ContabOne.Api/Security/CnpjCipher.cs` existem. Se não, parar e aplicar
      aquela change antes.

## 1. API — carteira de clientes para o agente DET

- [x] 1.1 DTOs `CarteiraDetResponse` (`EscritorioCnpjHash`, `Clientes`,
      `SemCnpjCompleto`) e `ClienteCarteiraDet` (`Id`, `Nome`, `Cnpj`) em
      `Features/Agent/AgentEndpoints.cs`
- [x] 1.2 Handler `CarteiraDetAsync` mapeado como `GET /det/clientes` no grupo
      `/api/agent`: resolve o agente por `ResolverIdsDoAgente`, 403 se o
      `Produto.Codigo` do agente não for `det`, 403 se o escritório não está
      ativo (`EscritorioEstaAtivoAsync`), consulta `AsNoTracking` de clientes
      `Ativo` com `CnpjCifrado != null` decifrando com `CnpjCipher`, conta os
      ativos sem CNPJ completo e devolve o `CnpjHash` do escritório
- [x] 1.3 Testes de integração (`Category=Banco`) em
      `ContabOne.Api/tests/`: lista só ativos com CNPJ completo e conta os
      demais; não vaza cliente de outro escritório; 403 para agente `nfse`;
      401 para escritório suspenso; devolve o `CnpjHash` do escritório;
      `AtualizadoEm` de `Cliente`/`Escritorio` inalterados após duas chamadas
- [x] 1.4 Se a consulta usar predicado novo sobre propriedade computada,
      cobrir em `TraducaoLinqTest.cs`

## 2. Det.Agent — cliente HTTP

- [x] 2.1 `api_client.py`: `ApiClient.carteira_det()` → `GET /api/agent/det/clientes`,
      401 como bloqueio (mesma regra das demais chamadas)
- [x] 2.2 Remover `ApiClient.upsert_clientes` e o upsert de
      `enviar_relatorio_execucao`; `_traduzir_mensagens` passa a usar o
      `clienteId` já presente em cada mensagem
- [x] 2.3 Pendências no formato novo (`{mensagens, status, mensagemErro}`);
      `reenviar_pendencias` aceita o formato antigo filtrando as mensagens
      pelos ids da carteira atual e descartando o resto com aviso (design D6)

## 3. Det.Agent — fonte de empresas e certificado

- [x] 3.1 `fontes.py`: fonte `api` construindo `Empresa(id=Cliente.Id, cnpj, nome)`
      a partir da carteira; remover `_do_excel` e o leitor de `.xlsx`
- [x] 3.2 `settings.py`/`Config`: remover `fonte_empresas`/`empresas_arquivo`
      (chave antiga no JSON vira aviso, não erro); `Empresa.id` aceita Guid
- [x] 3.3 `runner.py`: buscar a carteira depois do handshake e antes de abrir o
      navegador; carteira vazia encerra sem navegador; API indisponível na
      carteira encerra com erro; logar `semCnpjCompleto` como aviso; remover
      `_montar_clientes_api` e `--empresas-arquivo`; `--empresa` casa por id
      ou por CNPJ
- [x] 3.4 Conferência do certificado (design D4): extrair o CNPJ do `.pfx`
      (OID `2.16.76.1.3.3`, fallback no CN), comparar `hash_cnpj` com
      `escritorioCnpjHash`; divergência → saída `3`; hash do escritório vazio
      ou modo sem `.pfx` → aviso e segue
- [x] 3.5 Remover `openpyxl` de `requirements.txt` e do `build.py`

## 4. Det.Agent — testes offline

- [x] 4.1 `testes/_fake_api.py`: rota `GET /api/agent/det/clientes` e registro
      de todas as chamadas recebidas
- [x] 4.2 Testes: a execução não faz nenhum `POST /api/agent/clientes`
      (inclusive no reenvio de pendência); mensagens chegam com o
      `clienteId` da carteira; carteira vazia não abre navegador; carteira
      indisponível encerra com erro; 401 na carteira bloqueia
- [x] 4.3 Testes da conferência do certificado com `.pfx` gerado no próprio
      teste (e-CNPJ fictício): mesmo CNPJ segue, CNPJ diferente sai com `3`,
      escritório sem hash segue com aviso
- [x] 4.4 Reenvio de pendência no formato antigo (filtra por carteira)

## 5. Documentação

- [x] 5.1 `Det.Agent/README.md`: seções 3 (sem planilha; carteira vem do
      painel; clientes sem CNPJ completo), 5 (`--empresa` por CNPJ, sem
      `--empresas-arquivo`) e 9 (estrutura sem `empresas/`)
- [x] 5.2 `config/empresas.example.json` sem `fonte_empresas`/`empresas_arquivo`
      e sem a menção a `.env`/`DET_PFX_SENHA` desatualizada

## 6. Verificação

- [x] 6.1 `npm test` na raiz (roda o afetado de cada sub-repo, incluindo
      `Det.Agent`)
- [x] 6.2 Teste local ponta a ponta: API local, cliente de seed com CNPJ
      completo confirmado, chave `det_…`, `python run.py` com o certificado do
      escritório — mensagens aparecendo em `/f/det/mensagens` e nenhuma
      alteração em `Clientes`/`Escritorios`
