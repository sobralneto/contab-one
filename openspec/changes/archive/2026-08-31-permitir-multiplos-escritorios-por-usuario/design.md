## Context

Hoje o vínculo usuário↔escritório é a coluna `Usuario.EscritorioId` (`ContabOne.Api/Domain/Entities.cs:49`),
uma FK anulável. O login lê essa coluna, zera para `PlatformAdmin` e grava o resultado
como claim `escritorio_id` (`Features/Auth/AuthEndpoints.cs:75-77` e `:244-245`). O
`TenantContextMiddleware` (`Infra/TenantContextMiddleware.cs:37-57`) lê o claim de volta a
cada pedido e alimenta o `TenantContext`, que os filtros globais do
`AppDbContext.cs:48-81` usam para escopar as consultas.

Três detalhes da base atual condicionam o desenho:

1. **O escopo já vive no token, não no cadastro.** O middleware nunca consulta o usuário no
   banco — ele confia no claim. Isso significa que "trocar de escritório" já é, por
   construção, "emitir outro token". A mudança não precisa inverter esse desenho; precisa
   apenas passar a validar de onde o claim veio.
2. **O `PlatformAdmin` hoje é binário**: ou vê tudo (`VeTodosOsEscritorios = true`,
   `EscritorioId = null`), ou nada. Não existe estado "admin escopado a um escritório", que
   é justamente o que o pedido do usuário exige.
3. **O refresh token é um JWT sem estado no servidor** (`GenerateRefreshToken`, só `sub`), e
   o logout apenas apaga o cookie. A capability `ciclo-de-vida-da-sessao` já exige
   invalidação no servidor, mas ela ainda não existe no código. Este change **não** vai
   construir esse armazenamento — mas precisa não depender da ausência dele.

No frontend, `stores/auth.ts` decodifica o próprio JWT para montar o usuário da sessão
(`escritorioId: payload.escritorio_id || null`) e `layouts/AppLayout.vue:272-379` tem a
topbar com um bloco de usuário à direita, sem nada sobre escritório.

## Goals / Non-Goals

**Goals:**

- Um usuário pode ter zero, um ou N escritórios, sem conta duplicada.
- A sessão sempre sabe — e mostra — em qual escritório está operando.
- Trocar de escritório é uma operação de um clique, sem novo login.
- O isolamento multi-tenant fica pelo menos tão forte quanto hoje: um token nunca alcança
  escritório fora dos vínculos atuais do usuário.
- A migração preserva todos os acessos existentes, sem intervenção manual.

**Non-Goals:**

- Não implementa o armazenamento de sessões no servidor que `ciclo-de-vida-da-sessao` pede
  (revogação imediata de refresh). Este change se apoia na revalidação **na renovação**, que
  é o que a arquitetura sem estado permite hoje.
- Não introduz papéis por escritório — o papel continua sendo do usuário, global. Um usuário
  é `EscritorioAdmin` em todos os seus escritórios ou em nenhum. Papel por vínculo é
  desejável, mas dobra o escopo deste change.
- Não muda o comportamento do agente (`FromAgente`), que nunca teve usuário.
- Não cria tela nova de gestão de vínculos: a atribuição continua dentro do cadastro de
  usuário, apenas passando de campo único a seleção múltipla.

## Decisions

### 1. Tabela de vínculo explícita, não `Usuario.Escritorios` implícito

Criar `UsuarioEscritorio` como entidade própria (`UsuarioId`, `EscritorioId`, `CriadoEm`,
chave composta), em vez de deixar o EF gerar a tabela de junção implícita a partir de uma
skip navigation.

**Por quê:** a tabela de junção implícita não aceita colunas extras, e vamos precisar
delas — hoje `CriadoEm` para auditoria, e a versão com papel por vínculo (um Non-Goal aqui,
mas provável depois) exigiria a entidade de qualquer forma. Migrar de implícita para
explícita depois custa outra migração sobre a mesma tabela.

**Alternativa considerada:** manter `Usuario.EscritorioId` como "escritório principal" e
acrescentar a tabela só para os extras. Descartada: cria duas fontes de verdade para a
mesma pergunta, e é exatamente o tipo de estado dual que produziu o achado de isolamento
que originou `isolamento-multi-tenant`.

### 2. O claim `escritorio_id` passa a significar "em foco", e o nome não muda

O claim continua se chamando `escritorio_id` e continua sendo um único GUID opcional. O que
muda é a semântica: antes era "o escritório do usuário", agora é "o escritório que esta
sessão está enxergando".

**Por quê:** o middleware, os filtros globais e o `TenantContext` não precisam de nenhuma
alteração estrutural — só de deixar de recusar `PlatformAdmin` com escritório. Renomear o
claim quebraria todo token em circulação no deploy, sem ganho.

**Consequência deliberada:** não colocamos a lista de escritórios do usuário no token.
Ela é obtida por endpoint (`GET /auth/escritorios-disponiveis`). Um usuário com 40
escritórios inflaria o header de toda requisição, e a lista muda sem que o token saiba.

### 3. `PlatformAdmin` com foco é escopado; sem foco vê tudo

`TenantContext` ganha uma terceira construção: `FromAdminComFoco(usuarioId, escritorioId)`,
que marca `Papel = "PlatformAdmin"`, `EscritorioId = escritorioId` e
`VeTodosOsEscritorios = false`.

**Por quê:** a alternativa — deixar `VeTodosOsEscritorios = true` e escopar só na camada de
apresentação — significaria que o admin "focado" ainda enxerga tudo no banco, e qualquer
consulta que esquecesse o filtro vazaria. Escopar no `TenantContext` faz o filtro global
valer, que é onde a garantia realmente mora.

Os endpoints que hoje aceitam escritório alvo por parâmetro para `PlatformAdmin`
(`isolamento-multi-tenant`, requisito do escopo pelo pedido) continuam funcionando **apenas
quando o admin está sem foco**. Com foco, o parâmetro é ignorado como para qualquer outro
usuário.

### 4. O foco viaja também no refresh token

`GenerateRefreshToken` passa a incluir o `escritorio_id` em foco. `RefreshAsync` lê esse
valor, revalida contra os vínculos atuais e reemite o acesso com o mesmo foco.

**Por quê:** sem isso, a renovação silenciosa (que roda a cada 15 minutos) jogaria o usuário
de volta ao escritório padrão no meio do trabalho — um bug de perda de contexto disfarçado
de sessão renovada. E é a revalidação no refresh que dá efeito à revogação de vínculo, já
que não há armazenamento de sessão para invalidar.

**Alternativa considerada:** guardar o foco no `sessionStorage` do frontend e mandá-lo no
refresh. Descartada: o cliente passaria a escolher o próprio escopo, que é precisamente o
que `isolamento-multi-tenant` proíbe.

### 5. A escolha do foco no login é determinística

Quando o usuário tem vários vínculos, o login escolhe o escritório de **nome
alfabeticamente menor** entre os ativos.

**Por quê:** o login precisa de uma regra, e a regra precisa ser estável entre sessões — se
o foco inicial variar, o usuário nunca ganha memória muscular de onde cai ao entrar.
Alfabético é previsível e não exige coluna nova.

**Alternativa considerada:** lembrar o último escritório usado. Melhor experiência, mas
exige persistir preferência por usuário — vale como melhoria posterior, não como parte
deste change.

Se nenhum vínculo aponta para escritório ativo, o login é recusado, coerente com o
requisito de foco em escritório inativo.

### 6. A troca de foco reemite acesso **e** refresh

`POST /auth/trocar-escritorio` recebe o escritório alvo, valida contra os vínculos atuais e
o status do escritório, devolve o novo `accessToken` e regrava o cookie de refresh com o
novo foco.

O token antigo continua válido até vencer (até 15 min) — escopado ao escritório antigo. Isso
é aceitável e está escrito no spec: ele nunca alcança o escritório novo, então a janela é de
acesso legítimo continuado ao antigo, não de escalada.

### 7. No frontend, a troca é um recomeço de estado, não uma navegação

Após a troca bem-sucedida: gravar o novo token, limpar `catalogoStore`, recarregar o
catálogo, e então navegar para a página inicial (`/`) — não permanecer na rota atual.

**Por quê:** permanecer na rota atual exigiria que cada tela soubesse se sobrevive à troca
(a rota `/f/:produto/...` pode apontar para ferramenta não contratada pelo destino; um
`/clientes/:id` aponta para cliente de outro escritório). Ir para a raiz é uma regra só, e
elimina a classe inteira de "tela do escritório novo com id do antigo". O custo é perder o
lugar — aceitável numa ação que o usuário tomou de propósito.

O guard de rota já devolve à raiz ferramenta não contratada
(`navegacao-por-dominio`), então essa decisão está alinhada com o comportamento existente,
não sobreposta a ele.

### 8. Indicador na topbar: `<select>` nativo quando há mais de uma opção

Seguir a convenção existente do `EscritoriosView.vue`, que usa `<select>`/`<option>` nativos
— não há componente de combobox no projeto e este change não é o lugar para introduzir o
primeiro. Com uma opção só, renderizar texto estático.

## Risks / Trade-offs

**A migração de dados é irreversível na prática** → A migração cria a tabela, copia
`EscritorioId` para linhas de vínculo e **só então** derruba a coluna. O `Down` recria a
coluna e copia de volta o vínculo mais antigo por usuário — funciona para quem nunca teve
mais de um, que é todo mundo no momento do deploy. Rodar a migração com backup e validar a
contagem de linhas de vínculo contra a contagem de usuários com `EscritorioId` não nulo
antes de aceitar o deploy.

**Toda sessão em curso quebra no deploy** → Os tokens em circulação têm o claim
`escritorio_id` no formato antigo, que continua sendo lido igual — então na verdade **não**
quebram. Mas o refresh token antigo não tem foco: `RefreshAsync` precisa tratar sua ausência
resolvendo o foco pela mesma regra do login, em vez de recusar. Sem esse cuidado, todo
usuário logado cai na tela de login no momento do deploy.

**`PlatformAdmin` escopado pode quebrar telas que assumem visão global** → As telas de
administração da plataforma (escritórios, catálogo de ferramentas) presumem
`VeTodosOsEscritorios`. Elas precisam continuar funcionando com o admin em foco, ou ficar
explicitamente indisponíveis nesse estado. Decisão: as rotas de administração da plataforma
continuam exigindo o papel, e o filtro global não se aplica a `Escritorio` em si — o admin
focado ainda administra todos os escritórios, só não enxerga os **dados** dos outros.

**Revogação de vínculo demora até 15 minutos para ter efeito** → O acesso já emitido
continua valendo até vencer. É o mesmo comportamento que a plataforma já tem para
desativação de usuário, e a mitigação real é o armazenamento de sessões que
`ciclo-de-vida-da-sessao` pede — fora do escopo deste change. Registrar a limitação em vez
de fingir que a revalidação no refresh é imediata.

**O `EscritorioAdmin` administrando vínculos pode vazar existência de escritórios** → A
listagem de usuários precisa filtrar os vínculos exibidos, não só os usuários. Um
`EscritorioAdmin` de A que veja "este usuário também atende B, C, D" descobre a carteira do
colega. O spec cobre isso; a implementação precisa lembrar de projetar o DTO, não devolver a
entidade.

## Migration Plan

1. Migração EF em três passos numa transação: criar `UsuariosEscritorios`; `INSERT ... SELECT`
   dos `EscritorioId` não nulos; remover a coluna e a FK.
2. Deploy da API com `RefreshAsync` tolerante a refresh token sem foco (compatibilidade com
   os cookies em circulação).
3. Deploy do frontend.
4. Após uma janela maior que a validade do refresh token, remover a tolerância do passo 2.

**Rollback:** o `Down` da migração recria a coluna com o vínculo mais antigo por usuário.
Válido enquanto ninguém tiver sido vinculado a um segundo escritório — ou seja, só na janela
imediatamente após o deploy.

## Open Questions

- O `PlatformAdmin` deve poder focar um escritório sem estar vinculado a ele (decisão atual:
  sim, qualquer um), ou deveria precisar de vínculo explícito para focar? A opção atual é
  mais prática e não amplia o que ele já pode ver.
- Quando o único escritório de um usuário é suspenso, ele deve ser recusado no login ou
  entrar com aviso e acesso somente leitura? O spec atual recusa; vale confirmar com a
  operação se isso não trava suporte a cliente inadimplente.
