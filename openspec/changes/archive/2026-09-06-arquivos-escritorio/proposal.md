## Why

O escritório guarda documentos que não são de nenhuma ferramenta — contrato
social, procuração, alvará, cartão CNPJ, comprovante de entrega, foto de um
protocolo — e hoje eles vivem em pasta de rede, e-mail e WhatsApp. Tarefas e
onboarding já vivem no painel; falta o lugar onde o documento em si fica, com
nome, tipo e data, à mão de quem precisa dele.

O escritório precisa também classificar esses documentos do seu jeito: "Contrato
social" e "Procuração" não são a mesma lista em todo escritório. Por isso o tipo
é cadastro do próprio escritório, com CRUD, e não um enum fixo no código.

## What Changes

- **Tipo de arquivo como cadastro do escritório**, com **CRUD completo**: nome
  obrigatório e único dentro do escritório, descrição opcional e um estado
  ativo/inativo. Tipo **em uso não é excluído** — é inativado, para que o arquivo
  já guardado não fique órfão de classificação.
- **Arquivo do escritório** com **tipo obrigatório**. Cada arquivo tem nome de
  exibição, o arquivo em si, tamanho, data de envio e quem enviou. O vínculo é
  com o escritório e com o tipo — **não há vínculo com cliente** nesta change.
- **Formatos aceitos, e só eles**: `xls`, `xlsx`, `pdf`, `doc`, `docx`, `jpg`
  (`jpeg` como o mesmo formato) e `png`. A recusa é por **extensão e por
  conteúdo real** (assinatura binária do arquivo) — renomear `.exe` para `.pdf`
  não passa. Há teto de tamanho por arquivo.
- **`.pfx`/`.p12` nunca entram.** O certificado digital continua fora da
  plataforma; a lista de formatos aceitos é fechada e o certificado não está
  nela — dito como requisito, não como consequência.
- **Bytes guardados no Railway Bucket** (S3-compatível, privado), fora do
  Postgres. O banco guarda só metadado e a chave do objeto.
- **Upload pela API, download por URL assinada.** O `POST` multipart passa pela
  API, que valida extensão, conteúdo e tamanho antes de gravar; o download
  devolve uma **URL assinada de curta duração** direto do bucket — egress de
  bucket é grátis, o do serviço não, e a API não fica segurando thread por
  download.
- **A chave do objeto começa pelo id do escritório.** O isolamento não depende só
  da consulta: um objeto de um escritório não é alcançável pela chave de outro.
- **Página `/arquivos` na seção "Escritório" do menu**, ao lado de Clientes,
  Tarefas e Agentes: rota transversal, fora da família `/f/:produto`. Arquivo não
  é ferramenta, não entra no catálogo, não tem gate comercial nem agente.
- **Sem credencial de bucket, a funcionalidade se recusa em voz alta** — a API
  sobe normalmente (o desenvolvedor sem bucket continua rodando o resto), mas os
  endpoints de arquivo respondem "armazenamento não configurado" em vez de falhar
  de um jeito confuso.

**Sobre o contrato de privacidade.** O produto se define por *não* ser
depositário de conteúdo fiscal de terceiro: o `.pfx` nunca sai da máquina do
escritório e XML/PDF de nota nunca chegam à API (AGENTS.md). Esta change abre uma
exceção **estreita e deliberada**, e a fronteira precisa ficar escrita: o que
entra aqui é documento **administrativo do próprio escritório**, enviado **à mão
por um humano** que decidiu enviá-lo. Nada é coletado por agente, nada é
automático, o certificado continua barrado por lista de formatos, e nenhum
caminho novo se abre para o robô empurrar conteúdo de nota para cá.

## Capabilities

### New Capabilities

- `tipos-de-arquivo`: o cadastro de tipos de arquivo do escritório — CRUD, nome
  único por escritório, estado ativo/inativo, e a proteção do tipo em uso contra
  exclusão.
- `arquivos-do-escritorio`: o arquivo em si — tipo obrigatório, formatos aceitos
  e a recusa por conteúdo real, teto de tamanho, envio, listagem, download por
  URL assinada, exclusão, isolamento por escritório na consulta e na chave do
  objeto, e o comportamento quando o armazenamento não está configurado.

### Modified Capabilities

Nenhuma. As entidades novas entram no filtro global de tenant pelo padrão já
descrito em `isolamento-multi-tenant`, e a página fica fora do catálogo de
produtos — `navegacao-por-dominio` não muda.

## Impact

**API (`ContabOne.Api/`)**
- `Domain/Entities.cs`: `TipoArquivo` e `ArquivoEscritorio`.
- `Infra/AppDbContext.cs`: `DbSet`s, filtro global de tenant nas duas entidades,
  índice único `(EscritorioId, Nome)` em `TipoArquivo` e índice por
  `(EscritorioId, TipoArquivoId)` em `ArquivoEscritorio`.
- `Features/Arquivos/ArquivosEndpoints.cs`, `TiposArquivoEndpoints.cs` e
  `ValidadorArquivo.cs` (extensão + assinatura binária).
- `Infra/ArmazenamentoArquivos.cs`: cliente S3 (`AWSSDK.S3`, dependência nova),
  `PUT` do objeto e geração da URL assinada de leitura.
- Grupo `/api/arquivos` em `Program.cs` sob `EscritorioUsuario`, com política de
  rate limit própria para o envio e limite explícito de tamanho de corpo.
- Migration EF nova.
- `.env.example`: `ARQUIVOS_BUCKET`, `ARQUIVOS_ENDPOINT`, `ARQUIVOS_REGION`,
  `ARQUIVOS_ACCESS_KEY_ID`, `ARQUIVOS_SECRET_ACCESS_KEY`.

**Frontend (`ContabOne.Frontend/`)**
- `views/ArquivosView.vue` e `components/arquivos/` (envio, lista, formulário de
  tipo).
- `layouts/AppLayout.vue`: item "Arquivos" na seção "Escritório".
- `router/index.ts`: rota transversal `/arquivos`.
- `api/endpoints/arquivos.ts` e tipos em `api/types.ts`.

**Infraestrutura (Railway)**
- Variáveis do serviço da API apontando, por *variable reference*, para as
  credenciais do bucket já criado.

**Testes**
- `IsolamentoTest.cs` e `TraducaoLinqTest.cs` cobrindo as duas entidades novas.
- Testes de API para a recusa por extensão, a recusa por conteúdo real, o teto de
  tamanho, a unicidade do nome do tipo, o tipo em uso e a resposta com
  armazenamento não configurado.
- Vitest para a validação de formato e tamanho no cliente e para a lista.
- Playwright para enviar um arquivo → aparecer na lista → baixar.

**Fora de escopo**
- Vínculo do arquivo com cliente, com tarefa ou com onboarding.
- Versionamento de arquivo, pastas, lixeira e busca por conteúdo (OCR).
- Compartilhamento externo (link público) e antivírus.
- Qualquer participação de agente Python — arquivos são só painel.
