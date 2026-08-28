# Robô DET — Leitura da Caixa Postal (Domicílio Eletrônico Trabalhista)

Automação em Python + Playwright que acessa o portal do **DET/MTE** autenticando
com **certificado digital no gov.br**, navega até a **Caixa Postal** de cada
empresa cliente, extrai as notificações listadas e grava tudo em **JSON**.

---

## 1. Requisitos

| Item | Versão / observação |
|---|---|
| Python | 3.11 ou superior (testado em 3.13) |
| Google Chrome | instalado na máquina (o robô usa o Chrome **nativo**, não o Chromium do Playwright) |
| Certificado | **A1** instalado no repositório de certificados do Windows, ou arquivo `.pfx`; **A3** (token/cartão) funciona apenas no modo `manual` |
| SO | Windows (o fluxo de certificado depende da CryptoAPI do Windows) |

## 2. Instalação

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

**Sobre `playwright install`:** como o robô sobe o **Chrome já instalado** na
máquina (`channel="chrome"`), o download dos navegadores empacotados do
Playwright **não é necessário**. O `pip install playwright` já traz o driver.
Só rode o comando abaixo se a máquina não tiver o Chrome instalado — ele baixa
e registra uma cópia do Chrome estável para o Playwright:

```bash
python -m playwright install chrome
```

> Não use `playwright install chromium`: o Chromium empacotado não tem acesso
> ao repositório de certificados do Windows, que é justamente o que o gov.br
> precisa consultar.

## 3. Configuração

Dois arquivos, com papéis distintos:

| Arquivo | Guarda | Versionado? |
|---|---|---|
| `config/empresas.json` | URLs, seletores, timeouts, caminho do `.pfx` | não (gitignore) |
| `.env` | **senha do certificado** e **lista de CNPJs** | nunca |

```bash
copy config\empresas.example.json config\empresas.json
```

```bash
copy .env.example .env
```

### O certificado

Um único certificado — o do escritório contábil — atende todos os clientes.
Basta **largar o `.pfx` na pasta `certificado/`**: o robô encontra sozinho o
único arquivo dali, independente do nome. Isso importa porque o nome do
arquivo carrega a validade (`..._v.09.12.2026.pfx`) e muda a cada renovação —
trocar o arquivo basta, sem editar configuração.

Só a senha vai no `.env`:

```
DET_PFX_SENHA=sua-senha-aqui
```

A senha só existe no `.env`; o JSON guarda apenas o **nome da variável**. A
validação confere certificado e senha antes de abrir o navegador.

Se houver mais de um `.pfx` na pasta, o robô **para e pede para desambiguar**
em vez de escolher sozinho — nesse caso, preencha `certificado_pfx` no JSON.

### A lista de empresas

Vem sempre da planilha **`empresas/empresas.xlsx`**:

| Coluna A | Coluna B |
| -------- | -------- |
| CNPJ     | Nome     |

A primeira linha pode ser cabeçalho (`CNPJ` / `Nome`) ou já o primeiro dado —
o leitor reconhece os dois casos. Linhas em branco são ignoradas, e CNPJ
digitado como número (que perde o zero à esquerda no Excel) é recomposto.

O **CNPJ é a chave** — é ele que o robô digita na troca de perfil do DET. O
nome é só rótulo; se omitido, vira o próprio CNPJ formatado.

CNPJ com dígito verificador inválido **não bloqueia** a execução (homologação
usa CNPJ fictício), mas rende um `WARNING` alto no log listando os suspeitos.

Para apontar outra planilha numa execução avulsa:

```bash
python run.py --empresas-arquivo "C:\caminho\outra-planilha.xlsx"
```

### O resultado

Cada execução grava `resultado/YYYY-MM-DD_resultado-det.csv`, com as colunas
`CNPJ | Nome | Título | Mensagem`. É gerado automaticamente ao final — não
precisa de um segundo comando.

**Toda empresa aparece pelo menos uma vez**, mesmo sem novidade: quem não tem
mensagem nova sai como `Sem mensagens`. Isso é proposital — um relatório que
omite empresas não prova que elas foram consultadas. Os demais casos saem
como `Sem procuração` (com o texto exato do portal) ou `Erro` (com a etapa em
que parou).

O CSV usa `;` e BOM UTF-8, então abre direto no Excel em pt-BR com duplo
clique, sem assistente de importação e sem quebrar acentuação.

Para regerar o CSV de uma execução antiga, sem consultar o portal:

```bash
python tools/exportar_csv.py --entrada dados/det_20260822_181502.json
```

### Quando a API entrar no lugar da planilha

`src/det_bot/fontes.py` isola a origem da lista. Para trocar:

1. escreva `_da_api(cfg)` devolvendo `list[Empresa]`;
2. registre em `_LEITORES` sob `"api"`;
3. acrescente `"api"` a `FONTES_EMPRESAS` em `settings.py`;
4. troque `"fonte_empresas": "api"` no JSON.

Nenhuma outra parte do código muda — nem o runner, nem o scraping.

## 4. Primeira execução

```bash
python run.py --login
```

Autentica com o certificado e grava a sessão no perfil persistente, sem ler
nada. Como a identidade gov.br é uma só, isso vale para todos os clientes.

## 5. Execução normal

```bash
python run.py
```

```bash
python run.py --empresa acme --empresa betaservicos
```

Principais opções:

| Opção | Efeito |
|---|---|
| `-c, --config` | caminho do JSON de configuração (padrão `config/empresas.json`) |
| `-e, --empresa ID` | processa só essa empresa (pode repetir) |
| `--login` | apenas autentica e grava a sessão no perfil |
| `--dump` | salva screenshot + HTML da Caixa Postal (para calibrar seletores) |
| `--headless` | sem interface (só com sessão já válida ou modo `playwright_pfx`) |
| `--manter-aberto` | não fecha o Chrome ao final |
| `--limpar-perfil` | apaga o perfil da empresa e encerra (força novo login) |
| `--timeout-login SEG` | tempo de espera pelo retorno autenticado |
| `-v, --verbose` | log em DEBUG |

**Códigos de saída** (para o Agendador de Tarefas): `0` tudo ok · `1` sucesso
parcial · `2` todas falharam · `3` erro de configuração.

## 6. Saída

```
dados/
├── det_20260821_101500.json          # consolidado da execução
├── ultimo.json                       # ponteiro estável para a última execução
└── empresas/
    └── acme_20260821_101500.json     # um arquivo por empresa
```

Estrutura de cada mensagem:

```json
{
  "id_mensagem": "482913",
  "numero": "2026/000482913",
  "data_envio": "14/08/2026 09:32",
  "data_envio_iso": "2026-08-14T09:32:00",
  "data_leitura": null,
  "prazo": "24/08/2026",
  "remetente": "Auditoria Fiscal do Trabalho",
  "tipo": "Notificação",
  "assunto": "Notificação para Apresentação de Documentos",
  "situacao": "Não lida",
  "link": "https://det.sit.trabalho.gov.br/caixa-postal/detalhe/482913",
  "pagina": 1,
  "campos_extras": {},
  "hash_linha": "9f2c1ab0d4e75831"
}
```

Cada bloco de empresa traz também **`perfil_confirmado`**: `true` quando o robô
localizou o CNPJ na tela depois da troca de perfil. `false` significa que a
seleção não deu erro, mas o portal não exibiu o CNPJ para conferência — o dado
provavelmente está certo, mas não foi verificado. A integração pode usar esse
campo para decidir o quanto confia no registro; o resumo final lista todos os
não confirmados.

Colunas cujo cabeçalho o robô não reconheceu **não são descartadas**: vão para
`campos_extras` como `coluna_<índice>`, junto com um `WARNING` no log listando
os títulos não mapeados. É assim que se descobre o que ajustar em
`MAPA_COLUNAS` quando o portal ganha uma coluna nova.

> **LGPD.** O JSON e os screenshots de debug podem conter dados pessoais de
> empregados e da empresa. `dados/`, `debug/`, `logs/` e `perfis/` estão no
> `.gitignore` — mantenha-os fora de repositório e de compartilhamentos abertos.

## 7. Como o script lida com o certificado digital

### Por que perfil persistente

A autenticação por certificado no gov.br é um **handshake TLS com autenticação
de cliente (mTLS)**. Quem escolhe o certificado e assina o desafio com a chave
privada é o **navegador**, conversando com a **CryptoAPI do Windows** (A1) ou
com o driver PKCS#11 do token (A3). Nenhuma API do Playwright participa desse
handshake — não existe `page.click()` que resolva isso.

Daí as três decisões de arquitetura em [`navegador.py`](src/det_bot/navegador.py):

1. **`channel="chrome"`** — sobe o Chrome instalado na máquina, que enxerga o
   repositório de certificados do Windows. O Chromium empacotado do Playwright
   não enxerga.
2. **`launch_persistent_context(user_data_dir=...)`** — o `user_data_dir` grava
   cookies, `localStorage` e as decisões de certificado da sessão. Depois do
   primeiro login assistido, as execuções seguintes tendem a cair direto no
   painel do DET, sem novo diálogo, enquanto a sessão do gov.br durar. Por isso
   `autenticar()` começa checando `esta_autenticado()` e pula o login inteiro
   quando a sessão ainda vale.
3. **`headless=False`** — o diálogo de escolha do certificado é uma janela
   **nativa do Windows**, fora do DOM. Sem interface gráfica, ele não aparece e
   o handshake falha.

Como esse trecho é invisível ao Playwright, a espera não é um
`wait_for_selector`: é um *polling* de URL (`_aguardar_retorno_do_certificado`)
que observa a barra de endereços até o portal responder autenticado, dentro do
orçamento de `timeout_login_ms`.

### Os três modos (`modo_certificado`)

| Modo | Como funciona | Quando usar |
|---|---|---|
| `playwright_pfx` *(padrão)* | O Playwright apresenta o `.pfx` diretamente na camada TLS (`client_certificates`), sem envolver o Windows. | Execução desatendida; permite `--headless` e roda em qualquer máquina que tenha o arquivo |
| `politica_chrome` | A política `AutoSelectCertificateForUrls` faz o Chrome escolher sozinho, sem diálogo. | Certificado A1 já no repositório do Windows, máquina fixa; sem senha em disco |
| `manual` | O operador escolhe o certificado no diálogo do Windows. O robô espera. | Certificado A3 (token/cartão), homologação |

**No modo `playwright_pfx`**, o certificado é apresentado à origem
`origem_certificado` (por padrão `https://certificado.sso.acesso.gov.br`, e
configurável caso o gov.br mude o host). O handshake foi verificado contra um
servidor mTLS local: o Playwright apresenta o certificado do escritório
corretamente. O que resta validar é o outro lado — se o gov.br aceita esse
caminho na prática.

Contrapartida a considerar: `.pfx` + senha juntos são a identidade completa do
escritório, e portáteis. Trate o `.env` como credencial de produção. Se preferir
que a chave privada nunca saia do Windows, use `politica_chrome` e gere o `.reg`
com:

```bash
python tools/gerar_politica_certificado.py --cn "SEU ESCRITORIO:00000000000000"
```

O script apenas **gera** o arquivo; importar no registro (`reg import`, como
Administrador) é um passo consciente seu.

### A troca de perfil: Procurador + CNPJ

Depois de autenticado, o robô assume a procuração de cada cliente
(`govbr.assumir_perfil_procurador`):

1. abre a troca de perfil;
2. escolhe o tipo — `tipo_perfil_det`, por padrão **Procurador**;
3. digita o CNPJ **tecla a tecla** (`press_sequentially`), porque `fill()` não
   dispara os eventos que as máscaras de CNPJ escutam, e confere o valor que
   ficou no campo;
4. clica em **Selecionar**;
5. checa se o portal exibiu **mensagem de erro** — CNPJ sem procuração,
   procuração vencida — e, se houver, falha com o texto do portal;
6. procura o CNPJ na tela para confirmar o perfil ativo.

A ordem dos passos 5 e 6 não é acidental: o portal **ecoa o CNPJ recusado
dentro da própria mensagem de erro**, então confirmar antes de checar o erro
leria esse eco como sucesso — e o robô seguiria para a Caixa Postal do cliente
anterior. Foi exatamente o que um teste pegou.

## 8. Robustez e diagnóstico

* **Seletores em cascata.** Cada elemento tem uma *lista* de candidatos em
  [`seletores.py`](src/det_bot/seletores.py), tentados em ordem — do mais
  semântico (`get_by_role` + nome acessível, que sobrevive a troca de CSS) ao
  mais frágil (CSS/XPath). O log registra **qual** seletor funcionou, o que
  transforma a primeira execução em uma calibração.
* **Override sem tocar no código.** A chave `seletores` do
  `config/empresas.json` substitui a lista padrão de qualquer elemento:

  ```json
  "seletores": {
    "menu_caixa_postal": ["css=a[href='/caixa-postal']"]
  }
  ```

* **Etapas nomeadas.** Todo passo relevante roda dentro do context manager
  `etapa()` ([`log.py`](src/det_bot/log.py)). Uma falha vira
  `ErroEtapa("Clicar em 'Entrar com gov.br'", ...)` — o log e o JSON dizem
  exatamente onde parou, sem stack trace para interpretar.
* **Screenshot + HTML automáticos.** Qualquer erro crítico grava
  `debug/<empresa>_<carimbo>_<etapa>.png` e o `.html` correspondente.
* **Isolamento por empresa.** Cada cliente é lido dentro do seu próprio
  try/except: a falha de um não interrompe os demais, nem os outros do mesmo
  grupo. O resumo final lista todas as falhas com a etapa de cada uma. Se o
  navegador de um grupo sequer abrir, todas as empresas daquele grupo aparecem
  no relatório como falha — nenhuma some silenciosamente.
* **Troca de perfil verificada.** Em perfil compartilhado, não conseguir
  selecionar o `perfil_det` é erro, não aviso: seguir adiante leria a caixa
  postal do cliente anterior.
* **Extração dirigida por cabeçalho.** O mapeamento coluna → campo é feito
  lendo o `<thead>`, não por índice fixo. Uma coluna nova no meio da tabela não
  desloca os dados.
* **Paginação com trava.** A varredura só avança se o conteúdo da tabela
  efetivamente mudar (hash da tabela), evitando laço infinito em paginadores
  que não desabilitam o botão na última página. Linhas repetidas entre páginas
  são deduplicadas por `hash_linha`.

### Quando o layout mudar

```bash
python run.py --dump --empresa acme --manter-aberto
```

Isso grava screenshot e HTML da tela em `debug/`. Abra o HTML, identifique o
seletor correto e fixe-o na chave `seletores` do `config/empresas.json` — sem
recompilar nem editar o pacote.

## 9. Estrutura do projeto

```
det-trabalhista/
├── run.py                      # ponto de entrada (dispensa pip install -e)
├── build.py                    # gera o det.exe (ver seção 10)
├── requirements.txt
├── config/empresas.example.json
├── tools/
│   ├── exportar_csv.py         # regera o CSV de um JSON antigo
│   └── gerar_politica_certificado.py   # modo politica_chrome (plano B)
├── .env                        # senha do certificado (nunca versionar)
├── certificado/                # o .pfx do escritório (nunca versionar)
├── empresas/empresas.xlsx      # a lista a consultar (nunca versionar)
├── resultado/                  # o CSV do dia -- é o que o contador abre
└── src/det_bot/
    ├── runner.py               # CLI, laço por grupo/empresa, resumo, códigos de saída
    ├── settings.py             # carga/validação da configuração e utilidades de CNPJ
    ├── fontes.py               # de onde vem a lista de empresas (planilha hoje, API depois)
    ├── navegador.py            # Chrome nativo + perfil persistente + certificado
    ├── govbr.py                # login gov.br, troca de perfil e logout
    ├── caixa_postal.py         # navegação, conferência do empregador e scraping
    ├── localizadores.py        # resolução de seletores em cascata e esperas
    ├── seletores.py            # catálogo de seletores e mapa de colunas
    ├── saida.py                # gravação atômica dos JSON
    ├── relatorio.py            # geração do CSV de resultado
    ├── log.py                  # logging, etapas nomeadas e evidências
    └── erros.py                # exceções por etapa
```

## 10. Gerar o executável (máquinas sem Python)

```bash
pip install pyinstaller
python build.py
```

Sai em `dist/det/`, e é essa pasta inteira que se copia para o computador de
destino:

```
dist/det/
├── det.exe            # ~46 MB, com Playwright e o driver Node embutidos
├── config/empresas.json
├── certificado/       # o usuário larga o .pfx aqui
├── empresas/          # o usuário larga o empresas.xlsx aqui
├── .env.exemplo       # renomear para .env e preencher a senha
└── LEIA-ME.txt
```

**A máquina de destino precisa de Windows 64 bits e Google Chrome instalado.**
Python e Node **não** precisam: o Playwright conversa com o navegador através
de um driver Node próprio (`playwright/driver/node.exe`), que o
`--collect-all playwright` empacota junto.

O Chrome não é embutido de propósito — a autenticação no gov.br é um handshake
TLS com certificado de cliente, conduzido pelo navegador junto à CryptoAPI do
Windows. Ver a seção 7 e o cabeçalho de `navegador.py`.

Dois detalhes que o modo congelado exige, e que já estão tratados:

* `RAIZ_PADRAO` passa a ser a pasta do `.exe`, não `sys._MEIPASS` — senão o
  robô procuraria certificado e planilha dentro do temporário que o
  `--onefile` apaga ao sair, e gravaria o resultado lá.
* A janela espera `ENTER` ao terminar (`--sem-pausa` desliga, para o
  Agendador de Tarefas), inclusive quando dá erro: sem isso o duplo clique
  abre e fecha a janela num piscar, levando junto a mensagem que explicaria
  o problema.

## 11. Limitações conhecidas

* **Seletores do DET não foram validados contra o portal em produção.** O
  catálogo cobre os padrões usuais do Design System gov.br (`br-*`) e de
  tabelas PrimeNG/Angular, mas a primeira execução com `--dump` é parte do
  processo de implantação, não um contorno de defeito. Vale sobretudo para a
  tela de troca de perfil, cujo layout exato eu não conheço.
* **O gov.br aceitar o `client_certificates` do Playwright não foi verificado
  de ponta a ponta.** O handshake mTLS foi provado contra um servidor local; o
  comportamento do portal real só a primeira execução dirá. Se falhar,
  `politica_chrome` é o plano B, e o certificado já está no repositório do
  Windows.
* **O certificado vence.** Quando vencer, o robô para de autenticar até a
  renovação — vale monitorar a data.
* **Certificado A3** (token/cartão) exige presença física para o PIN — não há
  execução desatendida nesse caso, apenas o modo `manual`.
* **Sessão gov.br expira.** Quando expirar, o robô refaz o login sozinho; no
  modo `manual`, isso volta a exigir o operador. Em um grupo compartilhado, a
  expiração no meio da varredura afeta só a empresa da vez — as seguintes
  reautenticam no mesmo navegador.
* **O robô lê a listagem**, não abre cada mensagem. Extrair o corpo de cada
  notificação é uma extensão natural a partir do campo `link`.
