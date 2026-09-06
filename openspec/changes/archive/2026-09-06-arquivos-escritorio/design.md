## Context

Hoje nada na plataforma armazena binário. O `.pfx` fica na máquina do escritório,
XML e PDF de nota nunca chegam à API, e o PGDAS-D é lido no navegador — só os
números sobem. O único conteúdo grande que a API recebe é JSON de métrica.

Esta change introduz o primeiro repositório de binário do produto. Três
consequências que moldam o desenho:

1. **A API está no Railway** e o bucket também. Railway Buckets são
   S3-compatíveis, **privados** (não existe modo público), rodam sobre Tigris,
   suportam presigned URLs e multipart, e cobram **egress de bucket a zero** —
   mas o egress do *serviço* é cobrado. Isso decide quem transmite os bytes no
   download.
2. **O isolamento multi-tenant é a propriedade mais cara de errar** neste repo:
   filtro global no `AppDbContext`, `TenantContext` nunca lido de parâmetro de
   rota, `IsolamentoTest` como guarda. Um armazenamento de objetos acrescenta um
   segundo espaço de nomes que o filtro global **não** cobre — a chave do objeto
   precisa carregar o isolamento por conta própria.
3. **O contrato de privacidade é o que deixa o produto existir.** Um lugar onde o
   usuário empurra arquivo é exatamente por onde um `.pfx` ou um PDF de nota
   entraria "sem querer". A lista fechada de formatos e a checagem de conteúdo
   real não são higiene genérica de upload: são o que mantém a fronteira.

O estado atual relevante: `Domain/Entities.cs` e `Domain/Enums.cs` concentram o
modelo; fatias verticais em `Features/<Area>/`; `Program.cs` declara grupo, policy
e rate limit por rota; o menu lateral tem uma seção "Escritório" **escrita à mão**
(Clientes, Tarefas, Agentes, Usuários) para o que é transversal e não entra no
catálogo de produtos.

## Goals / Non-Goals

**Goals:**

- Guardar documentos administrativos do escritório com tipo, e dar ao escritório
  o CRUD do seu próprio catálogo de tipos.
- Manter o conteúdo fora do Postgres e fora da malha de egress da API no
  download.
- Estender o isolamento multi-tenant ao armazenamento de objetos, não só ao
  banco.
- Fechar a porta para certificado e para conteúdo fiscal por regra explícita e
  testada, não por omissão.
- Degradar de forma legível quando o bucket não estiver configurado — o
  desenvolvedor sem credencial continua rodando a API inteira.

**Non-Goals:**

- Vincular arquivo a cliente, tarefa ou onboarding.
- Versionamento, pastas, lixeira, OCR, antivírus, link público.
- Mover para o bucket algo que hoje vive em outro lugar (nada é migrado).
- Qualquer envolvimento dos agentes Python.

## Decisions

### 1. Railway Bucket via `AWSSDK.S3`, atrás de uma interface própria

Dependência nova: `AWSSDK.S3`. O bucket é S3-compatível, então o SDK oficial serve
sem adaptação; o que muda em relação à AWS é o `ServiceURL` (`ENDPOINT` do bucket,
hoje `https://t3.storageapi.dev`) e a `AuthenticationRegion` (`auto`).

O acesso fica atrás de `IArmazenamentoArquivos` em `Infra/`, com três operações —
gravar, assinar leitura, excluir. Não porque se pretenda trocar de provedor, mas
porque **o teste precisa de uma implementação em memória**: a suíte
`Category!=Banco` roda em ~2s sem Docker, e chamar rede num teste de endpoint
mataria isso.

Nomes das variáveis: `ARQUIVOS_BUCKET`, `ARQUIVOS_ENDPOINT`, `ARQUIVOS_REGION`,
`ARQUIVOS_ACCESS_KEY_ID`, `ARQUIVOS_SECRET_ACCESS_KEY`. Prefixadas de propósito —
os nomes que o Railway expõe (`BUCKET`, `ENDPOINT`, `REGION`, `ACCESS_KEY_ID`,
`SECRET_ACCESS_KEY`) são genéricos demais para conviver com `DATABASE_URL`,
`JWT_SIGNING_KEY` e o que vier depois no mesmo serviço. No Railway, cada uma é
uma *variable reference* apontando para o bucket, e não um valor copiado — assim
uma rotação de credencial no bucket chega à API sem ninguém colar segredo de novo.

*Alternativa descartada:* Volume do Railway montado na API. Mais simples e sem
credencial, mas prende o serviço a uma réplica, não tem URL assinada (todo
download viraria egress de serviço) e some junto com o serviço.

*Alternativa descartada:* guardar o binário em `bytea` no Postgres. Elimina o
segundo espaço de nomes e o problema de órfão, mas infla backup e migração — e a
suíte `Category=Banco` sobe Postgres efêmero a cada `dotnet test`.

### 2. Upload pela API, download por URL assinada

Assimétrico de propósito.

**Upload pela API** porque a validação precisa ser real: extensão, assinatura
binária e tamanho só têm valor se acontecerem onde o usuário não escreve o
código. Um presigned `PUT` entregaria ao navegador o direito de gravar qualquer
coisa na chave combinada — a validação viraria confiança no cliente, e o `.pfx`
que a spec barra entraria por ali.

**Download por presigned `GET`** porque o custo e o benefício se invertem: a
autorização já pode ser resolvida *antes* de assinar (o handler checa o tenant,
depois assina), o egress de bucket é grátis enquanto o de serviço não é, e a API
não fica com thread presa transmitindo arquivo de 20 MB. A URL leva
`response-content-disposition: attachment; filename="<nome de exibição>"`, para
que o navegador salve com o nome que o usuário vê, e não com a chave opaca.

Validade da URL: **5 minutos**. Curto o bastante para que um link vazado de
histórico não seja um arquivo aberto, longo o bastante para um download começar
em conexão ruim.

*Alternativa descartada:* proxiar o download pela API. Controle de autorização
byte a byte, mas paga egress de serviço em todo download e não acrescenta
segurança real — a autorização já acontece antes da assinatura.

### 3. A chave do objeto é `escritorios/{escritorioId}/arquivos/{arquivoId}{ext}`

O nome enviado pelo usuário **nunca** entra na chave. Ele vira `NomeExibicao`,
uma coluna de texto.

Duas razões, e a segunda é a que importa:

- Nome de arquivo é entrada hostil: `../`, byte nulo, unicode ambíguo, 4 KB de
  nome.
- **O filtro global do EF não alcança o bucket.** Toda a disciplina de isolamento
  deste repo vive no `AppDbContext`; o armazenamento de objetos é um segundo
  espaço de nomes onde ela não chega. Prefixar pelo `EscritorioId` faz a chave
  carregar o isolamento sozinha: mesmo que uma consulta futura esqueça o escopo,
  a chave que ela produzir não aponta para objeto de outro escritório.

`{arquivoId}` é o `Guid` da linha — a chave é derivável do registro, e a limpeza
de órfão é possível varrendo o prefixo contra a tabela.

### 4. Validação em três camadas, sendo a do navegador só cortesia

1. **Extensão** contra a lista fechada (`xls, xlsx, pdf, doc, docx, jpg, jpeg,
   png`), normalizada para minúscula.
2. **Assinatura binária** dos primeiros bytes:

   | Formato | Assinatura |
   |---|---|
   | pdf | `25 50 44 46` (`%PDF`) |
   | png | `89 50 4E 47 0D 0A 1A 0A` |
   | jpg/jpeg | `FF D8 FF` |
   | xlsx, docx | `50 4B 03 04` (ZIP — OOXML é um zip) |
   | xls, doc | `D0 CF 11 E0 A1 B1 1A E1` (OLE2/CFB) |

3. **Tamanho** — teto de **25 MB** por arquivo, mais
   `RequestSizeLimit`/`MultipartBodyLengthLimit` no endpoint, para que o corpo
   grande demais seja cortado no pipeline em vez de ser lido inteiro na memória.

O par ZIP/OLE2 não distingue `xlsx` de `docx` nem `xls` de `doc` — ambos os
formatos de cada par compartilham o contêiner. Isso é **aceito**: a checagem
existe para barrar "executável renomeado", não para arbitrar entre dois formatos
Office igualmente aceitos. Abrir o zip para conferir `[Content_Types].xml` seria
processar arquivo não confiável para ganhar uma distinção que a spec não pede.

A validação no navegador (`accept` + checagem de tamanho antes de subir) existe
só para dar erro rápido; a spec diz explicitamente que ela não é a barreira.

### 5. `TipoArquivo` inativa em vez de excluir quando está em uso

FK de `ArquivoEscritorio.TipoArquivoId` com `DeleteBehavior.Restrict` — o banco
recusa a exclusão de tipo com arquivo. O endpoint checa antes e responde 409 com
a contagem de arquivos, em vez de deixar vazar erro de FK.

O par "exclui se vazio, inativa se em uso" evita a alternativa ruim: um tipo
excluído que deixa arquivos sem classificação, ou um soft-delete universal que
enche a lista de fantasmas. O estado `Ativo` também serve ao caso comum de
escritório que parou de usar um tipo mas quer manter o histórico legível.

Unicidade: índice único em `(EscritorioId, NomeNormalizado)`, onde
`NomeNormalizado` é uma coluna gerada pela aplicação (trim + minúscula). Coluna
persistida, e não `.HasFilter()` com `lower()`, porque a comparação
case-insensitive precisa valer também nas checagens do handler sem depender de
collation.

### 6. Autorização: tipos são de admin, arquivos são de qualquer usuário

`EscritorioAdmin` para criar/editar/inativar/excluir tipo — mesma família de
Configuração e Agentes, que também são cadastro estruturante. `EscritorioUsuario`
para **ler** tipos (sem isso não há como preencher o seletor no envio) e para
enviar, listar, baixar e excluir arquivo.

O escopo de arquivo é o **tenant inteiro**, não a participação do usuário: ao
contrário de `Tarefa`, um arquivo do escritório é do escritório. O filtro global
do `AppDbContext` resolve tudo, e nenhum predicado extra é aplicado no handler.

Dois grupos em `Program.cs`, porque as policies diferem: `/api/arquivos` sob
`EscritorioUsuario` e `/api/arquivos/tipos` sob a policy do grupo, com
`EscritorioAdmin` aplicado por endpoint nas escritas — o mesmo padrão que
`OnboardingEndpoints` já usa.

### 7. Ordem das operações no envio e na exclusão

**Envio:** validar → gravar objeto → gravar linha. Se a gravação do objeto falhar,
nada foi para o banco. Se a gravação da linha falhar depois de o objeto ter ido,
o objeto é removido no `catch` — e, se essa remoção também falhar, fica o log com
a chave.

A janela restante (processo morre entre `PUT` e `INSERT`) produz **objeto órfão**,
não registro quebrado. É a assimetria certa: órfão custa centavos de
armazenamento e é varrível pelo prefixo; registro sem conteúdo é um arquivo que a
tela promete e não entrega.

**Exclusão:** remover linha → remover objeto, pelo mesmo raciocínio.

### 8. Sem credencial, os endpoints respondem 503 — a API sobe

`HMAC_CNPJ_KEY` derruba o boot de propósito, porque sem ela o envio de métricas
morreria em silêncio. Aqui é diferente: quem roda a API local sem bucket precisa
continuar trabalhando em Clientes, Tarefas e no resto.

Então: `IArmazenamentoArquivos` resolve para uma implementação "não configurado"
quando falta variável; envio e download respondem **503** com mensagem explícita;
**a listagem continua funcionando** (é só banco), e a tela informa que envio e
download estão indisponíveis. Um log de aviso no boot registra que a
funcionalidade subiu desligada.

### 9. Rate limit próprio para o envio

Política `arquivos` em `Program.cs`, particionada pela **sessão** (não pelo IP,
como `auth` e `agent`: aqui o pedido é sempre autenticado, e o escritório atrás de
um NAT compartilha IP). Fixed window, na ordem de **30 envios por minuto** —
folgado para quem sobe uma pasta à mão, apertado o bastante para que um laço não
encha o bucket. Só o `POST` de envio entra na política; listar e assinar não.

## Risks / Trade-offs

- **Objeto órfão no bucket** (processo morre entre gravar objeto e gravar linha) →
  a chave é derivável do `Guid` da linha, então um script de varredura por prefixo
  contra a tabela resolve. Não entra nesta change; o desenho só garante que seja
  possível.
- **A checagem de assinatura não separa `xlsx` de `docx`** (mesmo contêiner ZIP) →
  aceito e registrado na decisão 4. Ambos são formatos aceitos; a checagem existe
  para barrar o que não é Office nem PDF nem imagem.
- **Um ZIP arbitrário renomeado para `.xlsx` passa** pela assinatura → mesmo
  motivo. Mitigação real seria antivírus/inspeção de conteúdo, explicitamente
  fora de escopo. O arquivo é privado ao escritório que o enviou, e o download é
  sempre `attachment`.
- **A fronteira de privacidade agora depende de disciplina, não de arquitetura** →
  antes, conteúdo fiscal não chegava à API porque não havia caminho; agora há um
  caminho e o que o fecha é a lista de formatos. Mitigação: a lista é fechada,
  `.pfx`/`.p12` viram cenário de teste nomeado, e a proposta registra a fronteira
  por escrito para a próxima pessoa que pensar em "só aceitar XML também".
- **URL assinada é um link que funciona sem sessão** durante 5 minutos →
  aceito; é a natureza do mecanismo. Mitigada pela validade curta e por a
  autorização acontecer antes da assinatura.
- **Custo cresce com o uso**, e nada limita o total por escritório → não há cota
  por escritório nesta change. $0,015/GB-mês torna isso barato por bastante tempo,
  mas é uma dívida consciente: um escritório pode subir 500 GB e ninguém é
  avisado.
- **`AWSSDK.S3` é dependência nova e pesada** na API → aceito; é o cliente S3 de
  referência em .NET e escrever assinatura SigV4 à mão seria pior.

## Migration Plan

1. Criar o bucket no Railway (**feito** — o usuário já criou).
2. No serviço da API, adicionar as cinco variáveis como *variable references*
   para o bucket, no ambiente `production`.
3. Deploy da API com a migration nova: as duas tabelas nascem vazias; nada
   existente é tocado.
4. Deploy do frontend (`VITE_API_URL` é assado no build — nenhuma variável nova
   do lado do painel).
5. Cada escritório cadastra seus tipos. **Não há seed de tipos**: nenhum conjunto
   de tipos é comum a todo escritório, e um seed errado vira lista que ninguém
   apaga.

**Rollback:** remover o item de menu e o grupo de rotas desliga a funcionalidade
sem migration reversa — as tabelas ficam, vazias ou com poucas linhas. Reverter a
migration exige decidir o que fazer com os objetos já no bucket; enquanto houver
arquivo enviado, o caminho é desligar a tela, não dropar as tabelas.

## Open Questions

- **Cota por escritório.** Nenhuma nesta change. Vale um teto por escritório
  (número de arquivos ou GB) antes de o primeiro cliente descobrir que pode subir
  o que quiser?
- **Limpeza de órfãos.** O desenho torna a varredura possível mas não a
  implementa. Vira job (`--job=orfaos`, no molde de `--job=alertas`) quando?
- **Nome do formato na listagem.** A tela mostra a extensão (`pdf`, `xlsx`) ou um
  rótulo ("Planilha", "Documento")? Detalhe de apresentação, decidível na
  implementação.
