## 1. Det.Agent

- [x] 1.1 `certificado.py`: restaurar a leitura do CNPJ do titular (OID
      ICP-Brasil, depois sufixo do CN) e um helper que só lê no modo
      `playwright_pfx` e avisa quando não consegue.
- [x] 1.2 `settings.Config`: campo com o CNPJ do titular, preenchido pelo
      `runner` antes de abrir o navegador.
- [x] 1.3 `govbr.autenticar`: para a empresa titular, pular a troca de perfil
      e só conferir o CNPJ na tela (`perfil_confirmado`).
- [x] 1.4 Testes: leitura do CNPJ (OID, CN, ausente, senha errada); o runner
      preenche o titular só em `playwright_pfx` e não bloqueia com
      certificado ilegível; o titular não abre a troca de perfil e os demais
      abrem.
- [x] 1.5 `README.md` e o `LEIA-ME` do `build.py`.

## 2. Validação e distribuição

- [x] 2.1 Suíte Python do `Det.Agent` (`npm test`).
- [ ] 2.2 Gerar o `det.exe` novo e rodar na L&J: a L&J sai `ok`, sem troca de
      perfil.
