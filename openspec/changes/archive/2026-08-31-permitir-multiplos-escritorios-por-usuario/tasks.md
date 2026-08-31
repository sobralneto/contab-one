## 1. Modelo de dados e migração

- [x] 1.1 Criar a entidade `UsuarioEscritorio` em `ContabOne.Api/Domain/Entities.cs` com
      `UsuarioId`, `EscritorioId`, `CriadoEm` e chave composta
- [x] 1.2 Substituir `Usuario.EscritorioId`/`Usuario.Escritorio` pela coleção
      `Usuario.Escritorios` e acrescentar a coleção inversa em `Escritorio`
- [x] 1.3 Configurar a entidade no `AppDbContext` (chave composta, índice por
      `EscritorioId`, cascade delete a partir de usuário e de escritório)
- [x] 1.4 Gerar a migração EF que cria `UsuariosEscritorios`, copia os `EscritorioId` não
      nulos para linhas de vínculo e só então remove a coluna e a FK
- [x] 1.5 Escrever o `Down` da migração recriando a coluna a partir do vínculo mais antigo
      por usuário
- [ ] 1.6 Rodar a migração num dump de produção e conferir que a contagem de vínculos bate
      com a contagem de usuários que tinham `EscritorioId` não nulo

## 2. Escopo do pedido (TenantContext)

- [x] 2.1 Acrescentar `TenantContext.FromAdminComFoco(usuarioId, escritorioId)` com
      `VeTodosOsEscritorios = false`
- [x] 2.2 Fazer `TenantContextMiddleware` usar `FromAdminComFoco` quando o token de
      `PlatformAdmin` trouxer `escritorio_id`, e `FromAdmin` quando não trouxer
- [x] 2.3 Confirmar que os filtros globais de `AppDbContext.cs:48-81` seguem o
      `EscritorioId` do contexto sem alteração, inclusive para o admin focado
- [x] 2.4 Revisar os endpoints que hoje aceitam escritório alvo por parâmetro para
      `PlatformAdmin` e garantir que o parâmetro só é honrado quando não há foco

## 3. Emissão de credenciais

- [x] 3.1 Extrair um resolvedor de foco (`ResolverFocoAsync`) que, dado o usuário e um
      escritório pretendido opcional, devolve o foco válido ou a razão da recusa —
      validando vínculo e status do escritório
- [x] 3.2 Aplicar a regra do foco inicial no login: vínculo único direto; vários, o de nome
      alfabeticamente menor entre os ativos; `PlatformAdmin` sem vínculo, sem foco
- [x] 3.3 Recusar o login quando o usuário tem papel de escritório e nenhum vínculo com
      escritório em status operável
- [x] 3.4 Incluir o foco no refresh token gerado por `GenerateRefreshToken`
- [x] 3.5 Fazer `RefreshAsync` ler o foco do refresh token, revalidá-lo contra os vínculos
      atuais e recusar a renovação quando o vínculo não existe mais
- [x] 3.6 Tratar em `RefreshAsync` o refresh token legado sem foco resolvendo pela regra do
      login, para não derrubar as sessões em curso no deploy
- [x] 3.7 Ajustar `TrocarSenhaAsync` para preservar o foco corrente no token reemitido

## 4. Endpoints de foco e vínculos

- [x] 4.1 Criar `GET /auth/escritorios-disponiveis` devolvendo os escritórios que o usuário
      pode focar, com o foco atual marcado; para `PlatformAdmin`, todos mais a opção sem
      foco
- [x] 4.2 Criar `POST /auth/trocar-escritorio` que valida o alvo pelo resolvedor de foco,
      reemite o acesso e regrava o cookie de refresh com o novo foco
- [x] 4.3 Devolver erro distinguível para "sem vínculo" e para "escritório não operável",
      para que a topbar consiga explicar a recusa
- [x] 4.4 Alterar criação e edição de usuário em `Features/Usuarios/UsuariosEndpoints.cs`
      para receber a lista de escritórios e reconciliar os vínculos
- [x] 4.5 Validar na criação/edição que usuário com papel de escritório fica com ao menos um
      vínculo, e que `EscritorioAdmin` só manipula vínculos dos escritórios que ele enxerga
- [x] 4.6 Filtrar a listagem de usuários para `EscritorioAdmin` — só usuários com vínculo em
      comum, e no DTO só os vínculos que o solicitante enxerga
- [x] 4.7 Invalidar as sessões do usuário quando ele fica sem nenhum vínculo

## 5. Frontend — sessão

- [x] 5.1 Estender `stores/auth.ts` com o escritório em foco (id e nome) e a lista de opções
      de foco, carregada de `/auth/escritorios-disponiveis`
- [x] 5.2 Implementar a ação de troca de foco na store: chama o endpoint, grava o novo
      token, limpa `catalogoStore`, recarrega o catálogo e navega para `/`
- [x] 5.3 Manter o foco anterior intacto e sinalizar a falha quando a troca não completa,
      sem derrubar a sessão
- [x] 5.4 Garantir que o logout limpa também o foco e a lista de opções

## 6. Frontend — topbar

- [x] 6.1 Acrescentar o indicador de escritório em foco na topbar de
      `layouts/AppLayout.vue`, à esquerda do bloco de usuário
- [x] 6.2 Renderizar texto estático quando há uma opção só, e `<select>` nativo (convenção
      de `EscritoriosView.vue`) quando há mais de uma
- [x] 6.3 Exibir o estado "todos os escritórios" para `PlatformAdmin` sem foco, com a opção
      de focar um
- [x] 6.4 Exibir estado de carregamento enquanto o nome do escritório não resolveu, sem
      mostrar nome de sessão anterior
- [x] 6.5 Confirmar que o indicador não aparece antes da confirmação de autenticação,
      coerente com `controle-exibicao-layout`

## 7. Frontend — gestão de usuários

- [x] 7.1 Trocar o campo de escritório único por seleção múltipla no cadastro e na edição de
      usuário
- [x] 7.2 Exibir os escritórios do usuário na listagem, limitados aos que o solicitante
      enxerga

## 8. Testes

- [x] 8.1 Atualizar os testes de `ContabOne.Api.Tests` que montam usuário com `EscritorioId`
      para montar vínculo
- [x] 8.2 Testar que usuário vinculado a A e B, com A em foco, não lê nada de B — inclusive
      passando o id de B por query string
- [x] 8.3 Testar que o foco em escritório sem vínculo é recusado e o foco anterior sobrevive
- [x] 8.4 Testar que a renovação é recusada depois de o vínculo em foco ser removido
- [x] 8.5 Testar que `PlatformAdmin` com foco é escopado e sem foco vê tudo
- [x] 8.6 Testar que criar ou editar usuário de escritório sem nenhum vínculo é rejeitado
- [x] 8.7 Testar que `EscritorioAdmin` não vincula usuário a escritório fora do seu alcance
      nem enxerga na listagem os vínculos alheios
- [x] 8.8 Testar que o refresh token legado sem foco continua renovando

## 9. Verificação em execução

- [ ] 9.1 Subir a aplicação e percorrer o fluxo com um usuário de dois escritórios: entrar,
      conferir o nome na topbar, trocar, conferir que menu e listagens trocaram
- [ ] 9.2 Percorrer o fluxo com usuário de um escritório só e confirmar que não há seletor
- [ ] 9.3 Percorrer o fluxo do `PlatformAdmin`: sem foco, com foco, e voltando para sem foco
- [ ] 9.4 Deixar a sessão aberta além da validade do acesso e confirmar que a renovação
      silenciosa preserva o escritório em foco
