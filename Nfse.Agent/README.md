# Ferramenta NFS-e

Baixa os XML das NFS-e **recebidas e emitidas** de várias empresas e gera o
DANFSe v2.0 em PDF de cada uma, autenticando com o certificado digital A1.
**Sem navegador e sem captcha** — pode ser agendada sem ninguém presente.

## Instalação

### Nas máquinas dos usuários: executável, sem Python

```
python -m pip install pyinstaller
python build.py
```

Gera `dist/nfse/` — é essa pasta que se copia para o computador de destino:

```
nfse.exe          33 MB, tudo embutido
config.toml       configuração, editável no Bloco de Notas
certificados/     onde o usuário larga os .pfx
LEIA-ME.txt       instruções curtas
```

O usuário larga os certificados na pasta e dá **duplo clique no nfse.exe**.
Não precisa instalar nada: nem Python, nem dependências, nem runtime de
navegador. **A janela do console só fecha quando alguém aperta ENTER** — em
qualquer situação, sucesso ou erro, então uma mensagem nunca passa rápido
demais para ser lida.

Quem for agendar a ferramenta (Tarefas Agendadas do Windows, script) deve
usar `--sem-pausa`, para não ficar esperando um ENTER que nunca vem:

```
nfse.exe --sem-pausa
```

Requisito da máquina de destino: **Windows 64 bits**. As fontes Arial e
Microsoft Sans Serif, que a NT 008 exige no DANFSe, já vêm com o Windows.

Dois avisos honestos:

- O `.exe` **não é assinado digitalmente**, então na primeira execução o
  Windows SmartScreen mostra "O Windows protegeu o computador" → *Mais
  informações* → *Executar assim mesmo*. Para eliminar esse atrito de vez
  seria preciso um certificado de assinatura de código (EV Code Signing),
  que é pago.
- Antivírus às vezes implicam com executáveis PyInstaller. Se acontecer,
  vale adicionar a pasta na lista de exclusões.

### Para desenvolver ou rodar pelo Python

```
python -m pip install -r requirements.txt
python nfse.py
```

## Uso

```
python nfse.py
```

Sem argumentos: baixa tudo do dia 1º do mês corrente até hoje, de todas as
empresas com certificado na pasta configurada.

| Comando | O que faz |
| --- | --- |
| `python nfse.py --mes 2026-06` | mês fechado de junho/2026 |
| `python nfse.py --inicio 01/05/2026 --fim 15/05/2026` | período específico |
| `python nfse.py --empresa 0001` | só a empresa de código 0001 |
| `python nfse.py --tipos emitidas` | só as emitidas (ou `recebidas`) |
| `python nfse.py --somente-lista` | só os CSV, sem baixar nada |
| `python nfse.py --sem-pdf` | só os XML |
| `python nfse.py --sem-pausa` | não espera ENTER ao final — para tarefa agendada |
| `python danfse.py nota.xml` | gera o PDF de um XML avulso |

Rodar de novo no mesmo período **não baixa nada duas vezes** — arquivos já
existentes são pulados. É o jeito de retentar apenas o que falhou.

## Configuração — `config.toml`

`config.toml` só guarda o que a plataforma nunca deve custodiar: a
credencial da API (`[api]`) e a senha dos certificados (`senha_padrao` /
`[senhas]`). Tipos de nota, pasta de saída, geração de PDF, data de backfill
e período padrão de busca são configurados na tela de Configuração do painel
e chegam pela própria API no handshake — só valem do `config.toml` (com o
valor padrão embutido no código, se nem isso houver) até o primeiro
handshake bem-sucedido, ou quando o agente roda em modo legado (sem `[api]`
preenchido). Ver [config.exemplo.toml](config.exemplo.toml).

Os argumentos de linha de comando sobrepõem tanto o arquivo local quanto a
configuração remota.

A pasta de certificados (`pasta_certificados`, padrão `"certificados"`) é a
única exceção que continua só no arquivo local, se for preciso mudá-la — é
caminho de máquina, não preferência de escritório: cada instalação do agente
pode ter os `.pfx` num lugar diferente, então não há um valor "certo" para a
plataforma entregar.

## Certificados e empresas

Todo `.pfx` da pasta de certificados vira uma empresa. Os dados saem do nome
do arquivo:

```
codigoEmpresa_CNPJ_NomeEmpresa_s.SENHA_v.DD.MM.AAAA.pfx

0001_54283546000126_SOLUTION FARMA CONTABILIDADE LTDA_s.123456_v.04.03.2027.pfx
 └─┬┘ └──────┬─────┘ └──────────────┬──────────────┘ └──┬───┘ └─────┬──────┘
código     CNPJ                   nome                senha      validade
```

O nome da empresa pode conter `_` sem problema. Se o arquivo não seguir o
padrão inteiro, a ferramenta ainda funciona — o código é sempre o texto antes
do primeiro `_` (ou o nome do arquivo inteiro, se não houver `_`), e a senha
vem do `config.toml` (veja abaixo).

Certificado vencido gera um aviso antes da tentativa de login.

### Senha do certificado, sem digitar nada

O certificado nunca é instalado no Windows — o `.pfx` é lido do disco e
carregado em memória a cada execução, e a chave privada não é gravada em
disco em nenhum momento. **A ferramenta também nunca pergunta a senha no
console.** Um prompt interativo parece conveniente, mas não há como detectar
de forma confiável se existe alguém para responder — numa tarefa agendada ou
numa execução remota isso trava o processo esperando uma entrada que nunca
chega. Por isso a senha vem de uma destas fontes, nesta ordem:

1. Nome do arquivo (`_s.SENHA_`)
2. `config.toml`, seção `[senhas]`, pelo **nome do arquivo** do certificado
   — para exceções
3. `config.toml`, campo `senha_padrao` — uma senha para todos os certificados
4. Variável de ambiente `NFSE_PFX_SENHA`

Se todos os certificados usam a mesma senha, a forma mais simples é:

```toml
senha_padrao = "123456"
```

e pronto — os arquivos `.pfx` nem precisam ter senha no nome. Sem nenhuma
dessas fontes, a ferramenta erra na hora, com uma mensagem dizendo qual
certificado ficou sem senha — nunca fica esperando alguém digitar.

> **Sobre guardar a senha em texto simples** (no nome do arquivo ou no
> `senha_padrao`): é a troca consciente entre segurança e fricção zero. Quem
> tiver acesso à pasta tem a senha junto — a proteção efetiva é a permissão
> de acesso à pasta `certificados/` e ao `config.toml`, não a senha em si.

## Log — toda execução fica registrada

```
logs/nfse_2026-07-26.log
```

Um arquivo por dia, dentro da pasta do programa. Cada execução acrescenta um
bloco separado por uma linha `===`, com todas as mensagens que também
aparecem no console — inclusive as de erro — mais o traceback completo de
qualquer exceção (isso não some da tela, mas fica de fora do arquivo por
padrão, para não assustar quem não é programador com um stack trace).

Serve para dois casos: conferir depois o que aconteceu numa execução
agendada (que ninguém acompanhou ao vivo), e recuperar uma mensagem de erro
que passou rápido demais na tela antes de você conseguir ler — mesmo que a
janela já tenha sido fechada, a mensagem continua no arquivo do dia.

> `logs/` pode conter nome de cliente, CNPJ ou caminho de pasta dentro de uma
> mensagem de erro — mesma cautela de `certificados/` e `notas/`: não
> compartilhar publicamente.

## Fechar a janela — sempre por ENTER, nunca sozinha

Em qualquer situação — sucesso, erro de configuração, certificado com
problema, exceção inesperada — a janela do console **espera você apertar
ENTER** antes de fechar. Não existe mais heurística tentando adivinhar "isso
foi aberto por duplo clique?": antes de qualquer decisão sobre esse assunto,
o resultado era às vezes fechar rápido demais para dar tempo de ler o erro.

Para automação (Tarefas Agendadas do Windows, um script que chama a
ferramenta), use `--sem-pausa` — sem essa flag, uma execução sem ninguém no
teclado ficaria parada esperando um ENTER que nunca chegaria.

## Saída

```
notas/
└── 0001_SOLUTION FARMA CONTABILIDADE LTDA/
    ├── _controle.json   backfill por listagem + chaves já baixadas
    ├── 2026-06/
    │   ├── Recebidas/   notas-2026-06.csv + {chave}.xml + {chave}.pdf
    │   └── Emitidas/    notas-2026-06.csv + {chave}.xml + {chave}.pdf
    └── 2026-07/
        └── Recebidas/
```

O `ano-mes` é o da **data de geração de cada nota**, não o do período
consultado — então pedir um intervalo que cruza meses arquiva cada nota no
mês correto.

### A pasta do cliente é localizada pelo código, não pelo nome

Antes de criar a pasta, a ferramenta varre a pasta de saída procurando uma que
já comece com o código da empresa (`0001_…`). Se achar, usa aquela — mesmo que
a razão social tenha mudado no nome do certificado. Sem isso, uma alteração de
nome criaria uma segunda pasta e racharia o histórico do cliente em duas.

Quando o nome encontrado difere do atual, isso aparece no log:

```
pasta existente reaproveitada: 0001_SOLUTION FARMA CONTABILIDADE ME
                               (o certificado hoje diria 0001_SOLUTION FARMA CONTABILIDADE LTDA)
```

Se por algum motivo houver **duas** pastas com o mesmo código, a ferramenta
avisa e usa a modificada mais recentemente — mas vale consolidar na mão.
Códigos parecidos não se confundem: `0001` não casa com `0010`, `10` ou
`0001X`.

### Cliente novo: a primeira busca vai até `primeira_busca_desde`

Se o cliente ainda não tem histórico baixado, a ferramenta ignora o período
pedido (`--inicio`/`--mes`/padrão) só para o **início** e busca desde a data
de `primeira_busca_desde` no `config.toml` (padrão `2026-01-01`) até o fim
pedido. Assim, atender um cliente novo não exige lembrar de rodar manualmente
com uma data antiga na primeira vez — o comando de sempre já traz o
histórico inteiro:

```
[19:23]   recebidas: cliente sem histórico registrado — buscando desde 01/01/2026 (primeira consulta)
[19:23]   período de 181 dias dividido em 6 janelas (limite do portal: 31 dias)
```

Isso é controlado por cliente e por listagem (recebidas/emitidas
separadamente) através de um arquivo `_controle.json` na raiz da pasta do
cliente — não pela pasta existir ou não. A diferença importa numa
interrupção: o backfill só é marcado concluído **depois** que todos os
downloads daquele período terminam sem falha, nunca logo após a busca. Se o
processo cair no meio do caminho (queda de energia, janela fechada), a
próxima execução detecta que ainda não terminou e busca o período completo de
novo — sem repetir download do que já foi salvo (veja a seção seguinte) e sem
deixar nenhum mês esquecido para sempre.

### Controle de notas já baixadas (evita download desnecessário)

O mesmo `_controle.json` registra a chave de cada nota cujo XML já foi obtido.
Antes de chamar a API para uma nota, a ferramenta pula se **qualquer uma**
destas for verdadeira:

- o arquivo `{chave}.xml` já existe na pasta do mês, **ou**
- a chave já está registrada no controle desse cliente.

O segundo caso importa quando arquivos antigos são movidos, arquivados ou
comprimidos para liberar espaço: mesmo sem o XML fisicamente na pasta, a
ferramenta não tenta buscá-lo de novo. A troca consciente é que, se você
apagar um XML individual sem também remover a chave do controle, ele não
volta a ser baixado sozinho — para forçar, edite `_controle.json` e remova a
chave da lista de `notas_baixadas` do tipo correspondente (é um JSON simples,
abre em qualquer editor de texto).

O controle **não** afeta a geração do PDF: ela continua olhando só se o
arquivo `.pdf` existe, porque é uma operação local, sem custo de rede — então
gerar de novo (por exemplo, depois de uma melhoria no `danfse.py`) é barato e
até desejável.

Os CSV têm colunas diferentes conforme a listagem, acompanhando o portal:

- **Recebidas:** chave, geração, emitida_por, competência, preço, situação
- **Emitidas:** chave, geração, emitida_para, competência, município_emissor,
  preço, situação

Abrem direto no Excel (UTF-8 com BOM).

## Como funciona

1. **Login** — `GET https://certificado.nfse.gov.br/EmissorNacional/Certificado`
   com mTLS. Esse subdomínio exige certificado de cliente (responde 403 sem
   ele) e redireciona autenticado para o Dashboard.
2. **Listagem** — o filtro vai na querystring:
   - Recebidas: `/Notas/Recebidas?executar=1&busca=&datainicio=…&datafim=…`
   - Emitidas: `/Notas/Emitidas?busca=&datainicio=…&datafim=…`
     (sem `executar` — com ele o portal devolve vazio)
3. **XML** — `GET https://sefin.nfse.gov.br/sefinnacional/nfse/{chave}` com
   mTLS. Devolve JSON com `nfseXmlGZipB64`: base64 + gzip.
4. **PDF** — montado a partir do XML por [danfse.py](danfse.py).

### Duas armadilhas do portal que a ferramenta trata

- **Máximo de 31 dias por consulta.** Acima disso o portal devolve "Nenhum
  registro encontrado" — sem erro, sem aviso. Períodos maiores são quebrados
  em janelas de 31 dias automaticamente.
- **Paginação de 15 em 15 pelo parâmetro `pg`** (não `pagina`). A ferramenta
  percorre todas as páginas e confere o resultado contra o "Total de N
  registros" do rodapé, avisando se não bater.

## Por que não tem captcha

O hCaptcha protege os **botões de download da interface web**. A API da Sefin
Nacional é o canal oficial do contribuinte para os próprios documentos,
autenticado pelo certificado digital. Não é contorno de proteção — é o caminho
documentado, e o XML que ela devolve é byte a byte igual ao que o portal
entrega depois do captcha.

## O PDF: DANFSe v2.0 conforme a NT 008/2026

O PDF é montado localmente a partir do XML autorizado, seguindo a **Nota
Técnica nº 008, de 05/05/2026 (SE/CGNFS-e)**. A própria NT (item 1) informa
que a **API de geração do DANFSe foi suspensa em 1º de julho de 2026** — por
isso a rota `/sefinnacional/danfse/{chave}` responde 501. Montar o documento a
partir do XML é o caminho previsto pela norma para ERPs e sistemas fiscais.

Conformidade verificada por teste automático:

| Item da NT | Exigência | Situação |
| --- | --- | --- |
| 2.2.4 / Anexo I | ordem e disposição dos blocos | 16/16 blocos |
| 2.2, 2.2.1 | A4 retrato, página única | ✅ |
| 2.2.2 | margens de 0,15 a 0,20 cm | 0,175 cm |
| 2.2.3 | borda de 1 pt, linhas de 0,5 pt | ✅ |
| 2.2.3 | sombreamento cinza 5% nos títulos e nos campos "Emitente da NFS-e" e "Valor Líquido + IBS/CBS" | ✅ |
| 2.4 | Arial nos títulos, Microsoft Sans Serif nos conteúdos | ✅ |
| 2.4.1-2.4.4 | 7 pt títulos de bloco, 6 pt títulos de campo, 7 pt conteúdo | mínimo 6 pt |
| 2.4.3 | logomarca oficial, "DANFSe v2.0", município/ambiente | ✅ |
| 2.4.3 | QR de 1,52 cm em X 17,48 / Y 1,67 | ✅ |
| 2.4.3 | "NFS-e SEM VALIDADE JURÍDICA" em vermelho quando `tpAmb`=2 | ✅ |
| 2.3.1-2.3.3 | supressão de blocos vazios com a frase padrão | ✅ |

Comparado com o DANFS-e oficial baixado do portal, **30 de 30 valores de campo
são reproduzidos**.

Observações:

- **Nada é impresso além do que está no XML**, como manda o item 2.1 — por isso
  o PDF não leva marca dizendo que foi gerado localmente.
- **PDFs já existentes são preservados.** Se já existe um `{chave}.pdf`, a
  ferramenta não sobrescreve — inclusive os baixados direto do portal.
- `municipios_ibge.json` (tabela IBGE código → município/UF) é usado porque o
  XML traz só o código; `logo_nfse.png` é a logomarca exigida pelo item 2.4.3.

E vale lembrar: **o documento fiscal com validade legal é o XML assinado** —
o DANFSe, oficial ou gerado, é a representação visual dele.

## Limites conhecidos

- Requer certificado **A1** (arquivo `.pfx`). A3 (token/cartão) não serve —
  a chave privada não sai do dispositivo.
- A listagem depende do HTML do portal. Se a Receita mexer na tabela, o
  parsing precisa de ajuste (a extração da chave, que é o essencial, usa o
  padrão de URL dos links — bem mais estável que a estrutura da tabela).
- Ações de workflow (Confirmar / Rejeitar nota) **não** são executadas — a
  ferramenta só lê e baixa.
