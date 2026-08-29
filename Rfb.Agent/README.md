# Rfb.Agent — Credenciais do Portal de Tributação sobre Consumo

Robô que gera credenciais do tipo **Chaves Secretas** (Client Id / Client
Secret) no [Portal Nacional de Tributação de Bens e Serviços](https://consumo.tributos.gov.br)
para uma lista de CNPJs em que o escritório figura como **Procurador**, e
grava o resultado em CSV.

> **Portal em beta, automação não oficial.** Os endpoints usados aqui foram
> mapeados observando a interface (DevTools), não documentados. Eles podem
> mudar sem aviso — e provavelmente vão. Tudo que é frágil está isolado em
> `seletores.py` e na seção `[seletores]` do `config.toml`, que sobrescreve
> o código sem exigir novo deploy.

---

## Por que Playwright, e não `requests`

Duas barreiras impedem falar direto com a API por um cliente HTTP:

1. **`tokenCaptcha`.** A troca de representação
   (`POST /representacao/api/MudancaPapel/procurador`) exige um token
   gerado pelo JavaScript da própria página — captcha invisível, amarrado à
   execução real de JS. Não é reproduzível fora de um navegador.
2. **Certificado A1.** O login é por certificado ICP-Brasil (`.pfx`), um
   handshake TLS com autenticação de cliente.

A solução é híbrida: **navegador** para o que exige JS (login e troca de
representação) e **API** para o resto (`page.request`, que reaproveita os
cookies da sessão do próprio navegador). A criação da credencial não passa
pela interface — é mais rápida e imune a mudanças de layout.

---

## Instalação

```bash
pip install -r requirements.txt
```

O robô usa o **Chrome instalado na máquina** (`channel="chrome"`). Se não
houver:

```bash
python -m playwright install chrome
```

Depois:

1. `cp config.exemplo.toml config.toml` e preencha os clientes.
2. `cp .env.example .env` e preencha `RFB_PFX_SENHA`.
3. Coloque o `.pfx` do escritório em `certificado/` (o robô acha o arquivo
   sozinho, desde que seja o único `.pfx` da pasta).

---

## Primeira execução

```bash
python run.py --login
```

Abre o Chrome visível, apresenta o certificado e grava a sessão em
`perfil/`. Execuções seguintes reaproveitam essa sessão.

Se os seletores não baterem com a tela atual do portal:

```bash
python run.py --dump
```

Grava screenshot + HTML da home e da sidebar de representação em `debug/`.
Ajuste a seção `[seletores]` do `config.toml` com o que você encontrar —
sem tocar no código.

---

## Uso

```bash
python run.py --dry-run
```

Representa cada cliente e **consulta** as credenciais existentes, sem criar
nenhuma. É a forma segura de descobrir quem já tem chave antes do lote real
— e de validar os seletores contra a lista inteira.

```bash
python run.py
```

Lote completo. Para um cliente só:

```bash
python run.py --cliente 07467651000135
```

### Todas as flags

| Flag | Efeito |
| --- | --- |
| `-c, --config` | Caminho do TOML (padrão `config.toml`) |
| `--cliente CNPJ` | Processa só este CNPJ (repetível) |
| `-o, --saida CSV` | Sobrescreve o caminho do CSV |
| `--modo-certificado` | `playwright_pfx` (padrão) ou `manual` |
| `--headless` | Sem interface. Incompatível com `manual` |
| `--manter-aberto` | Não fecha o navegador ao final |
| `--login` | Só autentica e grava a sessão |
| `--dry-run` | Consulta, mas não cria nada |
| `--dump` | Grava evidência para calibrar seletores, e encerra |
| `--limpar-perfil` | Apaga o perfil do Chrome (força novo login) |
| `--sem-pausa` | Não espera ENTER (Agendador de Tarefas) |
| `-v, --verbose` | Log em DEBUG |

---

## O fluxo, por cliente

1. **Representar.** Abre a sidebar, digita o CNPJ, escolhe *Procurador* e
   clica em **Representar** — um clique real, para que o JS da página gere
   o `tokenCaptcha`. Nada é inserido entre preencher e clicar: o token
   nasce no clique e tem validade curta.
2. **Confirmar.** Consulta `/login/api/Usuario/dadosUsuario` e exige que o
   CNPJ do cliente apareça na resposta. **Falha fechada**: qualquer outra
   coisa aborta o cliente. Sem essa checagem, uma troca que reverteu em
   silêncio faria o robô criar uma chave *do escritório* e gravá-la no CSV
   sob o nome do cliente — plausível e errado.
3. **Consultar** `GET /api/v1/credenciais`. Se já existe credencial, o
   cliente é **pulado** (status `ja_possuia`); nada é sobrescrito.
4. **Criar** `POST /api/v1/credenciais` com nome, validade e os 3 serviços
   obrigatórios.
5. **Reler** o GET para capturar `clientId` / `clientSecret` — o POST não
   os devolve.
6. **Gravar** a linha no CSV imediatamente, e seguir para o próximo.

O CSV é escrito **dentro** do laço, não ao final: a credencial já existe no
portal no instante em que o POST retorna, e um lote interrompido depois
disso deixaria o operador sem o segredo de uma chave já emitida.

### Validade

`validade_anos` (padrão 5) a partir da data de execução, à **meia-noite em
`America/Sao_Paulo`**, convertida para UTC. Rodando em 2026-08-29 com 5
anos, sai `2031-08-29T03:00:00.000Z` — que é exatamente o valor observado
no portal. Calcular direto em UTC erraria em 3 horas.

No Windows o `zoneinfo` depende do pacote `tzdata` (está no
`requirements.txt`); sem ele o robô para com mensagem explícita, em vez de
gerar uma data errada.

---

## Saída

`resultado/credenciais_geradas.csv`, separado por `;` e em `utf-8-sig` (o
Excel em português abre CSV de vírgula em coluna única).

| Coluna | Conteúdo |
| --- | --- |
| `gerado_em` | Carimbo ISO local |
| `cnpj` | CNPJ formatado |
| `nome_credencial` | Campo "Nome" da credencial |
| `status` | `criada`, `ja_possuia`, `simulado`, `sem_procuracao`, `erro` |
| `client_id` | Preenchido em `criada` e `ja_possuia` |
| `client_secret` | **Só em `criada`** |
| `observacao` | Mensagem do portal ou detalhe do erro |

### Segurança

Esse CSV contém segredos de produção em texto puro. O robô:

- **cria o arquivo com permissão restrita antes de escrever qualquer
  linha** (`chmod 600`; no Windows, `icacls /inheritance:r` + acesso só ao
  usuário atual). Criar aberto e apertar depois deixaria uma janela de
  leitura para outros usuários da máquina;
- **nunca registra `client_secret` no log.** Além de o código não passar o
  valor adiante, um filtro roda sobre todo registro que chega ao logger e
  redige `clientSecret`, `senha`/`password` e `Authorization` — defesa em
  profundidade contra um `log.debug(resposta)` distraído no futuro;
- o arquivo está no `.gitignore` do monorepo, junto com `perfil/`,
  `certificado/`, `debug/`, `logs/` e o `config.toml` real (que lista CNPJs
  de clientes).

Numa v2 isso vira um cofre (Vault / Key Vault / SOPS). Só `saida.py` muda.

---

## Códigos de saída

| Código | Significado |
| --- | --- |
| `0` | Tudo certo |
| `1` | Parcial: houve erro, mas também houve resultado |
| `2` | Total: nenhum cliente concluiu |
| `3` | Erro de configuração (nem abriu o navegador) |

`sem_procuracao` **não** conta como falha: é condição de negócio esperada
(procuração vencida, revogada ou nunca outorgada). Aparece no CSV e no
resumo do log para o contador agir, mas não dispara alerta de robô
quebrado.

---

## Rate limiting

`pausa_entre_clientes_s` (padrão 2s) espaça as trocas de representação — é
a rajada delas que mais provavelmente atrai o limitador. Além disso,
respostas 429/403/5xx rendem até `tentativas_api` tentativas com espera
crescente (`espera_rate_limit_s × tentativa`).

Se um lote grande morrer em 429, aumente a pausa e rode de novo: quem já
tem credencial é detectado na consulta e pulado.

---

## Pontos ainda não validados contra o portal

Estão marcados no código com o motivo. Se você rodar contra o portal real,
confirme e ajuste:

1. **Formato do GET quando não existe credencial.** `consultar()` trata
   como "não existe" toda forma vazia plausível (404, 204, corpo vazio,
   `null`, lista vazia, objeto sem `clientId`) e loga o formato bruto —
   nunca os valores — em DEBUG. Rode `--dry-run -v` contra um CNPJ virgem
   e confira a linha `GET credenciais -> HTTP ... | formato: ...`.
2. **Autenticação da API.** Se ela usar bearer em vez de cookie,
   `page.request` sozinho daria 401. A classe `Sessao` fareja o cabeçalho
   `Authorization` que a própria SPA envia e o reaproveita; se não houver
   nenhum, segue por cookie. Cobre os dois casos sem precisar descobrir
   qual é.
3. **Seletores da sidebar de representação.** Só `campo_documento`
   (`placeholder="Digite o CPF ou CNPJ"`) foi confirmado. O resto é aposta
   informada em convenções do Design System gov.br — use `--dump`.
4. **`client_certificates` no portal.** O padrão é `playwright_pfx`, que
   dispensa a escolha manual do certificado. Se o portal recusar, use
   `--modo-certificado manual` com `--login` e escolha na mão uma vez.
5. **Cancelamento de chave.** Endpoint não mapeado. Como clientes com
   credencial são pulados, não é necessário hoje — mas é o que faltaria
   para reemitir uma chave perdida.

---

## Estrutura

```
Rfb.Agent/
├── run.py                    # entry point
├── config.exemplo.toml       # copie para config.toml
├── .env.example              # copie para .env (RFB_PFX_SENHA)
├── certificado/              # o .pfx do escritório (gitignored)
├── perfil/                   # perfil persistente do Chrome (gitignored)
├── resultado/                # CSV com os segredos (gitignored)
├── debug/                    # screenshots + HTML de falha (gitignored)
└── src/rfb_bot/
    ├── settings.py           # config.toml, CNPJ, validação
    ├── navegador.py          # Chrome + certificado A1 + perfil persistente
    ├── seletores.py          # catálogo de seletores tolerantes
    ├── localizadores.py      # "primeiro candidato que funcionar"
    ├── portal.py             # sessão e troca de representação
    ├── credenciais.py        # API de credenciais + cálculo de validade
    ├── saida.py              # CSV com permissão restrita
    ├── log.py                # logging, etapas, redação de segredos
    ├── erros.py              # exceções por etapa
    └── runner.py             # CLI e laço por cliente
```
