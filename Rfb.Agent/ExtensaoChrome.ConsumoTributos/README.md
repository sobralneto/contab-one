# Trocador de Representação + Credencial — consumo.tributos.gov.br

Extensão de Chrome (Manifest V3) que, para uma **lista de CNPJs**, um após
o outro: troca a representação (ex.: perfil "Procurador") no Portal
Nacional de Tributação de Bens e Serviços e, se der certo, gera uma
credencial de API "Chaves Secretas" para aquela representação. No final,
baixa um CSV com CNPJ, ClientId e ClientSecret de tudo que deu certo.

## O que ela faz

Para cada CNPJ da lista:

1. Abre o menu de "Trocar Representação" no topo da página (o mesmo que
   você abre clicando no seu CNPJ/perfil no canto superior direito).
2. Se este CNPJ **já foi representado antes**, usa o atalho da seção
   "Representações Recentes" (1 clique + confirmação, sem escolher perfil
   de novo — ver "Sobre os seletores usados" abaixo para o porquê). Se é a
   **primeira vez**, preenche o CNPJ, seleciona o perfil (Procurador,
   Matriz, Sucessor ou Ente Federado) e clica em "Representar".
3. Detecta o resultado:
   - **Sucesso** → segue para o passo de credencial (item 4).
   - **Erro** (CNPJ inválido, sem autorização etc.) → registra a mensagem
     de erro exibida na tela e segue para o próximo CNPJ.
   - **CAPTCHA** → **para a automação imediatamente** e espera você
     resolver manualmente. Depois de resolver, clique em "Continuar após
     CAPTCHA" no painel para seguir de onde parou.
4. Com a representação ativa, acessa a página de "Nova Credencial" e clica
   em "Gerar Token" (Chaves Secretas):
   - Se já existe uma credencial para esta representação, o portal pula
     direto para a tela de visualização — a extensão só lê os dados.
   - Se não existe, preenche **Nome** (nome do escritório/procurador
     logado), **Validade** (hoje + 5 anos) e marca o checkbox de
     consentimento, depois clica em "Confirmar".
   - Um CAPTCHA aqui também pausa a automação do mesmo jeito que no passo 2.
5. Lê **Client Id** e **Client Secret** da tela de resultado e guarda,
   associados a este CNPJ.
6. Ao final da lista, baixa um arquivo `.csv` com `CNPJ,ClientId,ClientSecret`
   de todas as credenciais obtidas com sucesso (também dá pra baixar a
   qualquer momento clicando em "Baixar CSV agora" no painel).

## O que ela NÃO faz (de propósito)

Ela nunca tenta detectar, contornar ou resolver o CAPTCHA sozinha. Isso é
proposital — captchas existem justamente para diferenciar humano de
automação, então essa parte fica sempre com você.

## ⚠️ Sobre o CSV de credenciais

O arquivo baixado contém **Client Id e Client Secret em texto puro** — são
credenciais de API reais, com o mesmo peso de uma senha. Trate-o como tal:

- Guarde em um lugar seguro (ex.: gerenciador de senhas/cofre), nunca em
  pasta compartilhada ou anexo de e-mail sem criptografia.
- Depois de importar as credenciais para onde elas realmente vão ser
  usadas, apague o CSV.
- Se desconfiar que o arquivo vazou, revogue/gere uma nova credencial para
  aquele CNPJ na tela "Credenciais de Acesso" do portal.

## Instalação (modo desenvolvedor)

1. Abra `chrome://extensions` no Chrome.
2. Ative o "Modo de desenvolvedor" (canto superior direito).
3. Clique em "Carregar sem compactação" (Load unpacked).
4. Selecione a pasta desta extensão (`extensao-troca-representacao`).
5. Fixe o ícone da extensão na barra do Chrome, se quiser.

## Uso

1. Faça login normalmente no portal (`consumo.tributos.gov.br`).
2. Clique no ícone da extensão e depois em "Abrir painel na página" — um
   painel flutuante aparece no canto superior direito da própria página.
3. Cole a lista de CNPJs (um por linha) na caixa de texto.
4. Escolha o perfil (padrão: "Procurador").
5. Clique em "Iniciar".
6. Acompanhe o log dentro do painel. Se aparecer um CAPTCHA (seja na troca
   de representação ou ao confirmar a credencial), resolva-o na tela e
   clique em "Continuar após CAPTCHA".
7. Ao final, o CSV com CNPJ/ClientId/ClientSecret baixa sozinho. Se fechar
   o painel antes disso ou quiser baixar de novo, use "Baixar CSV agora".

Importante: como cada CNPJ passa por VÁRIAS páginas (troca de
representação → nova credencial → visualizar credencial), a extensão
navega a página sozinha várias vezes durante a execução — isso é esperado,
não feche a aba enquanto estiver rodando. O progresso fica salvo
(`chrome.storage.local`), então se o Chrome cair no meio, reabrir a aba do
portal com o painel aberto retoma de onde parou.

Recomendação: teste primeiro com 1 CNPJ válido antes de rodar a lista
inteira, para confirmar que os seletores ainda batem com o layout atual
do portal.

## Sobre os seletores usados (leia se algo parar de funcionar)

O portal parece ser uma SPA (Angular ou similar) com classes CSS
provavelmente geradas/ofuscadas a cada build — por isso o `content.js`
localiza os elementos **pelo texto visível** (rótulos como "Trocar
Representação", "Representar", nomes dos perfis) em vez de por classes
CSS fixas. Isso é mais resistente a pequenas mudanças de estilo, mas
ainda pode quebrar se o portal:

- mudar o texto dos rótulos/botões;
- mudar a ordem dos campos dentro do painel (o script assume que o
  1º input visível é o CNPJ e o 2º é o seletor de perfil);
- passar a exigir mais passos entre o clique no cabeçalho e o
  aparecimento do painel de troca.

Se algo não funcionar, abra o DevTools (F12) na aba do portal, reproduza
o passo manualmente e ajuste as funções correspondentes em `content.js`:

- `openRepresentationMenuIfNeeded()` — abre o menu no cabeçalho.
- `fillCnpj()` / `selectPerfil()` / `clickRepresentar()` — preenchem o
  formulário de troca de representação (CNPJ novo, nunca representado).
- `tentarRepresentarViaRecentes()` — atalho para CNPJ **já** representado
  antes (ver caixa abaixo — é importante entender por que isso existe).
- `detectOutcome()` — decide se a troca de representação foi sucesso, erro
  ou captcha.
- `detectCaptcha()` — heurística de detecção de captcha (iframes
  conhecidos + textos comuns em português). Ajuste a lista `iframeHints`
  ou `hints` se o provedor de captcha do portal usar outro nome.
- `capturarNomeEscritorio()` — lê o nome do escritório logado (usado como
  "Nome" da credencial).
- `dataValidadeEm5Anos()` — calcula a data de validade (hoje + 5 anos).
- `encontrarCheckboxConsentimento()` / `typeInto()` (fase
  `preencher-credencial` dentro de `tick()`) — preenchem o formulário de
  "Chaves Secretas".
- `lerCampoView()` — lê Client Id / Client Secret / Nome / Validade da
  tela de visualização de uma credencial.
- `baixarCsv()` — gera e baixa o CSV final.

### Por que existe `tentarRepresentarViaRecentes()`?

Descoberta ao vivo, não óbvia: se um CNPJ **já foi representado antes**
(o grant já existe), o formulário normal de "Trocar Representação" **para
de oferecer qualquer perfil** — o campo de perfil mostra só o placeholder
"Não encontrado", porque não há nada novo para conceder. Sem tratar esse
caso, a extensão erraria (incorretamente) todo CNPJ que já tivesse sido
processado antes, mesmo sendo válido e já autorizado — e isso É o caso
mais comum ao reprocessar a mesma lista de CNPJs para gerar credenciais
depois de já ter trocado a representação numa rodada anterior.

O caminho certo é a seção "Representações Recentes" do mesmo painel: cada
linha tem um botão de atalho que reabre aquela representação com só uma
confirmação num modal — sem escolher perfil de novo. `processarUmCnpj()`
tenta esse atalho primeiro; se o CNPJ não estiver nos recentes (é novo), a
função retorna `null` e o fluxo cai no formulário normal.

**Detalhe que já causou um bug real:** o botão "Representar" desse modal
de confirmação **não reage a um `.click()` simples** (`clickEl()`) — fica
ali parado, sem erro nenhum, como se nada tivesse acontecido. Precisa da
sequência completa `mousedown`+`mouseup`+`click` (`clickSequence()`), o
mesmo problema que o `ng-select` já tinha. Por precaução, os botões
"Gerar Token" e "Confirmar" da tela de credencial também usam
`clickSequence()` agora, mesmo sem termos confirmado ao vivo que
precisavam — o risco de um clique silenciosamente ignorado ali é alto
(trava a extensão inteira sem log de erro claro) e o custo de usar
`clickSequence()` em vez de `clickEl()` é zero.

### Caso real: CNPJ válido, mas a representação não habilitava

Já aconteceu de um CNPJ válido não conseguir habilitar a representação
porque, na hora de clicar em "Representar", o campo de perfil estava
vazio — mesmo a extensão tendo "clicado" na opção certa (ex.: Procurador)
um instante antes. A causa mais provável: o clique na opção do `ng-select`
foi registrado no DOM, mas a página (SPA Angular) ainda não tinha
atualizado o texto exibido no combobox fechado quando o código seguiu em
frente e clicou em "Representar" — ou seja, um problema de tempo, não de
seletor errado.

Duas mudanças tratam isso:

1. `selectPerfil()` agora **confirma** que o valor exibido no combobox
   fechado (`.ng-value-label`) realmente mudou para o perfil escolhido
   antes de retornar — se não confirmar em até 3s, tenta de novo (reabrindo
   o dropdown do zero); só desiste e reporta erro depois de 2 tentativas.
   Isso é mais confiável do que só aumentar um delay fixo, porque não
   depende de adivinhar quanto tempo a SPA vai demorar num dia mais lento.
2. Mesmo assim, os atrasos entre digitar/selecionar/confirmar aumentaram
   um pouco por segurança: a digitação caractere-a-caractere foi de 25ms
   para 40ms (`typeInto(..., { charDelay })`, ajustável por chamada), e as
   pausas fixas entre preencher o CNPJ → selecionar o perfil → clicar em
   "Representar" (em `processarUmCnpj()`) subiram de 400/300ms para
   600/400ms.

## Arquivos

- `manifest.json` — configuração da extensão (Manifest V3).
- `content.js` — toda a lógica de automação + painel flutuante injetado na página.
- `popup.html` / `popup.js` — popup simples da barra de ferramentas, só
  para abrir/fechar o painel na página.
