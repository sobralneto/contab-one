## 1. Det.Agent

- [x] 1.1 `runner.py`: remover `conferir_certificado` e a chamada em
      `executar`. A execução segue direto da carteira para as empresas.
- [x] 1.2 Apagar `certificado.py` e, de `api_client.py`, `hash_cnpj` e
      `mascarar_cnpj`. Mover `_somente_digitos` para junto das pendências.
- [x] 1.3 Testes: tirar os de `certificado.py` e da conferência, tirar
      `escritorioCnpjHash` do `_fake_api`, e provar que um hash divergente na
      carteira não bloqueia a execução.
- [x] 1.4 `README.md` e o `LEIA-ME` do `build.py` sem a conferência.

## 2. ContabOne.Api

- [x] 2.1 `CarteiraDetAsync` e `CarteiraDetResponse` sem
      `EscritorioCnpjHash`.
- [x] 2.2 `CarteiraDetTest`: provar que a resposta não traz o campo e
      remover `EscritorioSemCnpj_DevolveHashVazio`.

## 3. Specs

- [x] 3.1 Ajustar o `Purpose` de `agente-det-integracao-api` e de
      `carteira-clientes-agente-det`, que citavam a conferência.

## 4. Validação e distribuição

- [x] 4.1 Suíte Python do `Det.Agent` e camada `Category!=Banco` da API.
- [x] 4.2 `npm test` com Docker no ar: `CarteiraDetTest` e as demais classes
      afetadas da API, mais a suíte do `Det.Agent`.
- [x] 4.3 Gerar o `det.exe` novo e instalar na pasta da L&J.
