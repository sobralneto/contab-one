## Context

A change `det-agent-paridade-nfse` (arquivada em 2026-09-01) ligou o
`Det.Agent` à API copiando o modelo do `Nfse.Agent`: a lista de empresas vem
de `empresas/empresas.xlsx`, e antes do relatório o agente faz upsert de cada
empresa em `POST /api/agent/clientes` para obter o `Cliente.Id`. No NFS-e isso
faz sentido — lá cada `.pfx` *é* um cliente, e o agente é quem descobre a
carteira. No DET não: o acesso é com **um único certificado, o do escritório**,
e a troca de perfil de Procurador pelo CNPJ de cada cliente. A carteira já
existe no painel. A planilha é uma segunda fonte da verdade, e o upsert dá a
um robô que só deveria *ler* a Caixa Postal o poder de criar e renomear
clientes.

Estado relevante do código:

- `Cliente` guarda só `CnpjHash` (HMAC) e `CnpjMascarado`. O CNPJ completo não
  existe no banco hoje; a change em andamento `cnpj-completo-cliente`
  introduz `Cliente.CnpjCifrado` (AES-256-GCM, `Security/CnpjCipher.cs`) e o
  preenche no cadastro/edição manual e na importação do PGDAS-D.
- `Escritorio` tem `CnpjHash`/`CnpjMascarado`.
- `Det.Agent/src/det_bot/fontes.py` já isola a origem da lista, com
  `_LEITORES` e um passo a passo no README para a fonte `"api"`.
- `Det.Agent` já resolve sozinho o único `.pfx` de `certificado/` e a senha
  por `config.toml`.
- `EnviarMensagensDetAsync` descarta mensagens cujo `ClienteId` não é do
  tenant, então receber o `Cliente.Id` direto da API não abre um caminho novo.

## Goals / Non-Goals

**Goals:**

- A carteira de empresas do DET vem do painel, via API, filtrada pelo
  escritório da chave.
- `Det.Agent` não escreve em `Escritorio` nem em `Cliente`, e isso é
  verificável por teste nos dois lados.
- Rodar com o certificado de outra empresa na pasta falha cedo e explica por
  quê.

**Non-Goals:**

- Mudar o `Nfse.Agent` ou `POST /api/agent/clientes`: o NFS-e continua
  descobrindo clientes pelos certificados.
- Preencher o CNPJ completo de clientes que ainda não o têm. Isso é
  `cnpj-completo-cliente` (confirmação manual na tela).
- Suportar um certificado por cliente no DET. Continua um certificado só, o do
  escritório, com troca de perfil.
- Escolher no painel quais clientes o DET consulta (por exemplo, uma flag
  "consultar DET"). Todo cliente ativo com CNPJ completo é consultado; um
  filtro fica para quando houver pedido.
- Mudar a página `/f/det/mensagens`.

## Decisions

### D1. Endpoint novo `GET /api/agent/det/clientes`, e não um `GET` em `/api/agent/clientes`

A resposta tem este formato:

```json
{
  "escritorioCnpjHash": "…",
  "clientes": [ { "id": "guid", "nome": "…", "cnpj": "00000000000000" } ],
  "semCnpjCompleto": 2
}
```

O prefixo `det/` deixa explícito no caminho que é um contrato do produto DET.
Ele também evita que `/api/agent/clientes` tenha semânticas opostas por verbo:
o `POST` escreve, e é chamado pelo NFS-e. A consulta filtra `Ativo &&
CnpjCifrado != null` pelo global query filter do tenant. Ela não chama
`IgnoreQueryFilters`, e usa `AsNoTracking` para deixar claro, no próprio
código, que é leitura.

*Alternativa considerada:* devolver a carteira no handshake. Foi rejeitada
porque o handshake é comum a todos os agentes, e o CNPJ completo iria para o
NFS-e também, sem necessidade.

### D2. Restrição ao produto `det` pelo código do próprio agente

O handler carrega o `Agente` da chave (`ResolverIdsDoAgente`) com seu
`Produto` e responde 403 se `Produto.Codigo != "det"`. `Produto.Codigo` é
imutável, então comparar com um literal é seguro e segue a regra de
`ApiKeyAuthenticationHandler`, que compara a chave contra o código do próprio
agente e não contra o catálogo. Isso é **autorização**: a autenticação
continua como está.

*Alternativa considerada:* uma policy nova no `Program.cs`. Foi rejeitada
porque exigiria uma claim de produto no principal do agente. É uma mudança em
`ApiKeyAuthenticationHandler`, uma peça sensível, só para um endpoint.

### D3. CNPJ completo decifrado na API e enviado em claro, dentro do TLS

O agente precisa digitar os 14 dígitos na troca de perfil, e não existe
alternativa com hash. O CNPJ trafega por HTTPS, só para o agente DET do
próprio escritório. O agente o mantém só em memória e nos artefatos locais que
já recebiam CNPJ (log e JSON em `dados/`, que ficam na máquina do
escritório). O que o agente devolve à API continua sem CNPJ: as mensagens vão
por `Cliente.Id`.

### D4. A conferência do certificado usa o CNPJ do próprio certificado, não o nome do arquivo

O agente abre o `.pfx` com `cryptography` (já dependência, usada na cifra da
configuração). Ele extrai o CNPJ do OID ICP-Brasil do e-CNPJ
`2.16.76.1.3.3`. Na falta dele, usa o sufixo `:CNPJ` do CN do sujeito. Depois
calcula `hash_cnpj(cnpj, hmacCnpjKey)` e compara com `escritorioCnpjHash`. O
nome do arquivo não é confiável: muda a cada renovação e pode não seguir
padrão algum.

Resultados possíveis:

- Hashes diferentes: saída `3` (configuração).
- Escritório sem `CnpjHash`: aviso, e a execução segue. Bloquear seria punir o
  escritório por um cadastro incompleto no admin.
- Certificado sem CNPJ legível (modos `manual`/`politica_chrome`, em que o
  agente não tem o `.pfx`): aviso, e a execução segue. Nesses modos o gov.br é
  quem escolhe o certificado.

### D5. A fonte Excel sai, não fica como alternativa

A fonte `excel` sai de `_LEITORES`, e com ela saem `fonte_empresas`,
`empresas_arquivo`, `--empresas-arquivo`, o leitor de `.xlsx` e `openpyxl`.
Deixar a planilha como plano B manteria viva justamente a segunda fonte da
verdade que a mudança elimina, e ela voltaria a precisar de upsert para ter
`Cliente.Id`. Uma chave de config antiga (`fonte_empresas: "excel"`) em
`config/empresas.json` é ignorada com um aviso, para não quebrar a instalação.

### D6. `Empresa` passa a carregar o `Cliente.Id`, e o pipeline de envio usa o id direto

`Empresa.id` passa a ser o `Cliente.Id` (Guid). Isso preserva o uso atual do
campo como identificador de log, de arquivo em `dados/empresas/` e de
`--empresa`. Além disso, `--empresa` aceita o CNPJ, que é o que o operador
conhece.

`_montar_clientes_api` e `upsert_clientes` são removidos, e
`_traduzir_mensagens` recebe o `clienteId` já na mensagem. O formato da
pendência muda de `{clientes, mensagens, …}` para `{mensagens, …}`. Uma
pendência antiga, gravada no formato de upsert, traz em `cliente_codigo` os
14 dígitos do CNPJ. Ela é reenviada traduzindo esse CNPJ para o `Cliente.Id`
pela carteira atual. Por isso o reenvio de pendências roda depois da leitura
da carteira, e não antes, como na versão anterior. As mensagens que não
acharem cliente são descartadas com aviso. A alternativa seria chamar o
upsert uma última vez, o que violaria a regra nova.

### D7. O que o agente ainda escreve na API, e por que isso não fere a regra

Isso fica anotado para não ser confundido com cadastro:

- O handshake grava `Agente.VersaoAgente`: é o próprio agente, não o
  escritório nem um cliente.
- Abrir e finalizar cria e atualiza `Execucao`. Finalizar com `Falha` pode
  abrir um `Alerta`.
- O envio de mensagens grava `MensagemDet`.

Nada disso toca `Escritorio` ou `Cliente`. O teste do lado da API afirma
exatamente isso sobre o endpoint novo, e o teste do lado Python afirma que a
fake API nunca recebe `POST /api/agent/clientes`.

## Risks / Trade-offs

- [A carteira fica vazia enquanto os CNPJs completos não forem confirmados no
  painel. Hoje nenhum cliente tem CNPJ completo.] → O agente loga
  `semCnpjCompleto` com a instrução de completar o cadastro em Clientes, e a
  execução termina sem erro. A Migration Plan coloca a confirmação dos CNPJs
  antes do deploy do agente.
- [Dependência dura de `cnpj-completo-cliente`, ainda não aplicada.] → As
  tarefas desta change começam verificando que `CnpjCifrado`/`CnpjCipher`
  existem. Sem eles, o apply para.
- [Uma API fora do ar agora impede a coleta, porque não há lista local.] →
  Isso é aceito de propósito (D5). O agente já depende da API para licença, e
  a carência offline do handshake não se estende à carteira: sem carteira,
  não há o que consultar.
- [Escritório com muitos clientes deixa a execução longa, sem paginação.] →
  O volume de um escritório (centenas) cabe numa resposta. Paginação fica
  para quando houver caso real.
- [Um agente DET comprometido obtém os CNPJs completos da carteira.] → É o
  mesmo escritório que já os conhece, e a chave é revogável (401 imediato). O
  escopo é o tenant da chave e o produto `det`.

## Migration Plan

1. Aplicar e publicar `cnpj-completo-cliente` (API e frontend).
2. Confirmar pelo painel o CNPJ completo dos clientes que o DET deve
   consultar.
3. Publicar a API com o endpoint novo. Nada quebra: nenhum agente o chama
   ainda.
4. Gerar o `det.exe` novo e substituí-lo na máquina do escritório. A planilha
   `empresas/empresas.xlsx` pode ser apagada.

**Rollback:** voltar o `det.exe` anterior, que ainda usa planilha e upsert. O
endpoint novo pode ficar publicado, porque é só leitura e sem consumidor.

## Open Questions

- A troca de perfil do DET aceita que o *próprio escritório* esteja na
  carteira? Se o escritório também for cadastrado como cliente, consultar a
  caixa dele exigiria o perfil de Empregador, não o de Procurador. Proposta:
  a primeira validação ponta a ponta observa esse caso, e até lá ele cai como
  falha da empresa, isolada, como qualquer outra.
