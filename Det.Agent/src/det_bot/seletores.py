"""Catálogo de seletores tolerantes a mudanças de layout.

Cada chave lógica aponta para uma *lista de candidatos*, tentados em ordem
até que um funcione. A ordem vai do mais semântico (papel ARIA + nome
acessível, que sobrevive a trocas de CSS) para o mais frágil (CSS/XPath).

Sintaxe dos candidatos (resolvida por ``localizadores.resolver``):

    role=<papel>:<regex do nome>   -> page.get_by_role(papel, name=regex)
    texto=<regex>                  -> page.get_by_text(regex)
    rotulo=<regex>                 -> page.get_by_label(regex)
    titulo=<regex>                 -> page.get_by_title(regex)
    testid=<valor>                 -> page.get_by_test_id(valor)
    xpath=... | css=... | <css>    -> page.locator(...)

Todos os regex são aplicados com ``re.IGNORECASE``.
"""

from __future__ import annotations

SELETORES_PADRAO: dict[str, list[str]] = {
    # ------------------------------------------------------------------ #
    # Portal do DET -> gov.br
    # ------------------------------------------------------------------ #
    "botao_entrar_govbr": [
        r"role=button:entrar com gov\.?\s?br",
        r"role=link:entrar com gov\.?\s?br",
        r"role=button:^\s*entrar\s*$",
        r"role=link:^\s*entrar\s*$",
        r"texto=entrar com gov\.?\s?br",
        "css=a[href*='sso.acesso.gov.br']",
        "css=#btn-entrar-govbr, .br-sign-in, [id*='govbr' i], [class*='govbr' i]",
    ],
    # ------------------------------------------------------------------ #
    # Tela de login do gov.br
    # ------------------------------------------------------------------ #
    "opcao_certificado_digital": [
        r"role=button:certificado digital",
        r"role=link:certificado digital",
        r"texto=seu certificado digital",
        r"texto=certificado digital",
        "css=#login-certificate, a[href*='certificado'], button[id*='certificad' i]",
        "xpath=//*[self::a or self::button][contains(., 'ertificado')]",
    ],
    # CAPTCHA do gov.br. O robô apenas DETECTA para avisar o operador e
    # esperar a resolução humana -- resolver automaticamente está fora de
    # questão, e é o que torna o login um passo assistido.
    "captcha": [
        "css=iframe[src*='recaptcha' i], iframe[title*='recaptcha' i]",
        "css=.g-recaptcha, #recaptcha, [class*='captcha' i], [id*='captcha' i]",
        "css=iframe[src*='hcaptcha' i]",
    ],
    # Tela de consentimento "Autorização de uso de dados pessoais".
    #
    # ATENÇÃO: confirmado contra o portal real 2026-08-21 que "Continuar"
    # sozinho é PERIGOSO aqui -- a tela inicial de login do gov.br (campo de
    # CPF) também tem um botão "Continuar", e não é o mesmo botão. Se o
    # login cair de volta nessa tela (sessão expirada, rate-limit, CAPTCHA
    # não resolvido a tempo), o candidato genérico clica cegamente nesse
    # "Continuar" -- que só tenta submeter o CPF vazio -- e o robô fica
    # preso repetindo o clique até estourar o timeout, sem nunca progredir
    # nem soar como erro. Por isso o texto de consentimento verdadeiro tem
    # que aparecer junto ("dados pessoais"/"autoriza"), e o id do botão real
    # do OAuth do gov.br vem primeiro.
    "autorizar_dados": [
        "css=#buttonAuthorize, button[value='authorize']",
        r"role=button:^\s*autorizar\s*$",
        r"role=button:^\s*permitir\s*$",
        r"role=button:continuar.{0,3}$",  # so quando dentro do contexto certo, ver check abaixo
    ],
    # Marca a tela inicial de login (campo de CPF) para o robô conseguir
    # DISTINGUIR "apareceu a autorização de dados" de "voltou para o
    # começo" -- as duas telas compartilham um botão "Continuar" genérico.
    "tela_login_inicial_cpf": [
        r"placeholder=digite seu cpf",
        r"texto=identifique-se no gov\.?\s?br",
        "css=input[name='identificacao' i], input[id*='cpf' i]",
    ],
    # ------------------------------------------------------------------ #
    # Painel do DET
    # ------------------------------------------------------------------ #
    # ------------------------------------------------------------------ #
    # Troca de perfil: o escritório entra como PROCURADOR de cada cliente,
    # informando o CNPJ da empresa e confirmando.
    # Nas chaves abaixo, "{tipo}" é substituído em tempo de execução pelo
    # valor de `tipo_perfil_det` da configuração (por padrão "Procurador").
    # ------------------------------------------------------------------ #
    "abrir_troca_perfil": [
        r"role=button:(alterar|trocar|selecionar|mudar) perfil",
        "css=button.br-button:has-text('Trocar Perfil')",
        r"role=link:(alterar|trocar|selecionar|mudar) perfil",
        r"texto=(selecione|alterar|trocar) o? ?perfil",
        "css=button[id*='perfil' i], a[id*='perfil' i], [class*='trocar-perfil' i]",
    ],
    # O campo "Perfil" do modal é um ng-select (Angular), não um radio: é
    # preciso abrir o dropdown antes de escolher a opção.
    "combo_perfil_det": [
        "css=br-select[formcontrolname='perfil'] ng-select",
        "css=.modal-content ng-select",
        "css=ng-select[role='combobox'], ng-select",
        r"role=combobox:perfil",
    ],
    # Valor já selecionado no combo -- evita reabrir o dropdown à toa.
    "valor_perfil_atual": [
        "css=br-select[formcontrolname='perfil'] .ng-value-label",
        "css=.modal-content ng-select .ng-value-label",
        "css=ng-select .ng-value-label",
    ],
    "opcao_perfil_det": [
        "css=.ng-dropdown-panel .ng-option:has-text('{tipo}')",
        "css=.ng-option:has-text('{tipo}')",
        "role=option:{tipo}",
        "role=radio:{tipo}",
        "role=cell:{tipo}",
        r"texto=^\s*{tipo}\s*$",
        "css=option[value*='procurador' i]",
    ],
    # Confirmado contra o portal real: é um componente <br-input> do Design
    # System gov.br com validação própria (atributo `brvalidcpfcnpj`) e
    # `formcontrolname="niRepresentado"`. O `id` é gerado em runtime
    # (id3f7f9e...) e não serve como seletor; o `formcontrolname` sim, e vem
    # primeiro por ser o mais específico e rápido de resolver.
    "campo_cnpj_perfil": [
        "css=[formcontrolname='niRepresentado'] input",
        "css=br-input[brvalidcpfcnpj] input",
        r"placeholder=informe\s+cnpj",
        r"placeholder=cnpj",
        "css=.modal-content input[placeholder*='CNPJ' i]",
        r"rotulo=cnpj",
        "css=input[formcontrolname*='cnpj' i]",
        "css=input[name*='cnpj' i], input[id*='cnpj' i]",
    ],
    # Feedback visual de sucesso do <br-input> -- mais confiável que reler o
    # valor do campo, porque reflete o veredito da PRÓPRIA validação
    # (`brvalidcpfcnpj`) do portal, e não fica obsoleto se o Angular
    # recriar o elemento do input como parte de aplicar essa validação.
    "cnpj_validado_feedback": [
        "css=.valid-feedback:visible",
        "css=[class*='valid-feedback']:not(:empty)",
    ],
    "botao_selecionar_perfil": [
        r"role=button:^\s*selecionar\s*$",
        "css=.modal-content button.br-button.is-primary",
        r"role=button:^\s*(confirmar|acessar|continuar|entrar|buscar)\s*$",
        "css=button[type='submit']:not([disabled])",
    ],
    # O próprio modal de troca de perfil. Ele FECHAR é a prova mais
    # confiável de que a troca foi aceita -- não depende de acertar o
    # seletor da mensagem de erro, que varia. Ver
    # `_aguardar_modal_fechar` em govbr.py.
    "modal_perfil": [
        "css=modal-container.modal.show",
        "css=.modal.show, .modal.fade.show",
        "css=modal-container[role='dialog']",
    ],
    # Mensagem de erro após tentar assumir o perfil (CNPJ sem procuração,
    # procuração vencida, CNPJ inexistente). Sem checar isto, o CNPJ exibido
    # *dentro da mensagem de erro* seria lido como confirmação do perfil.
    "erro_perfil": [
        "css=[role='alert']",
        "css=.alert-danger, .alert-error, .br-message.danger, .br-message.error",
        "css=.invalid-feedback, .error-message, .mensagem-erro, .msg-erro",
        "css=[id*='erro' i], [class*='erro' i]",
    ],
    # Na tela /servicos a Caixa Postal é um CARD -- `<div tabindex="0"
    # class="cardListItem">` dentro de `<br-card>` --, não um link nem um
    # button. Seletores por papel ARIA não a encontram; daí o CSS vir antes.
    "menu_caixa_postal": [
        "css=.cardListItem:has-text('CAIXA POSTAL')",
        "css=br-card:has-text('CAIXA POSTAL') .cardListItem",
        r"role=link:caixa postal",
        r"role=button:caixa postal",
        r"role=menuitem:caixa postal",
        "css=a[href*='caixa'], a[href*='mensagem'], a[routerlink*='caixa' i]",
        r"texto=^\s*caixa postal\s*$",
    ],
    # Botão que expande o menu lateral, quando o portal inicia recolhido.
    "abrir_menu": [
        r"role=button:(menu|abrir menu|navega)",
        "css=button.menu-toggle, .br-menu-trigger, [aria-label*='menu' i]",
    ],
    # Confirmado contra o portal real: as abas não são <div role="tab">,
    # são links `.folder` dentro de `.menu-caixa-postal`, cada um com o
    # contador de NÃO LIDAS entre parênteses ("Caixa de Entrada (3)"). A
    # aba de entrada normalmente já abre ativa (classe `.active`).
    "aba_caixa_entrada": [
        "css=.menu-caixa-postal .folder:has-text('Caixa de Entrada')",
        r"role=link:caixa de entrada",
        r"texto=caixa de entrada",
    ],
    # Contador de não lidas ao lado do nome da aba -- é o que decide se
    # vale a pena continuar (ver `caixa_postal.deve_ler_mensagens`).
    "contador_nao_lidas": [
        "css=.menu-caixa-postal .folder.active",
        "css=.menu-caixa-postal .folder:has-text('Caixa de Entrada')",
    ],
    # Link que restringe a listagem às mensagens não lidas. É a MESMA
    # filtragem que o portal usa internamente -- mais confiável que o robô
    # tentar inferir "lida/não lida" a partir de um ícone.
    "filtro_nao_lidas": [
        "css=a.filtro:has-text('Exibir apenas')",
        r"texto=exibir apenas.{0,4}n[aã]o lidas",
    ],
    # ------------------------------------------------------------------ #
    # Lista de mensagens -- NÃO é uma <table>: cada mensagem é um
    # `.tabela.mensagens.linha-dividida` dentro do container abaixo, com os
    # campos identificados por classe (.tipo/.origem/.hora/.titulo), não por
    # posição de coluna.
    # ------------------------------------------------------------------ #
    "tabela_mensagens": [
        "css=.form-group.tabela_mensagens",
        "css=.tabela_mensagens",
    ],
    "linha_mensagem": [
        "css=.tabela.mensagens.linha-dividida",
    ],
    # Painel lateral que exibe o texto completo ao clicar em uma mensagem
    # (confirmado contra o portal real: card "CAIXA POSTAL" -> coluna
    # direita "painel_mensagens" -> "#painel-mensagem .corpo-mensagem").
    # Antes de qualquer clique, esse painel mostra apenas o texto de
    # instrucao "Para visualizar uma mensagem, clique nela." -- e essa
    # diferenca de conteudo e o sinal usado para saber que o clique
    # realmente atualizou o painel.
    "painel_mensagem": [
        "css=#painel-mensagem .corpo-mensagem",
        "css=.painel_mensagens .corpo-mensagem",
        "css=#painel-mensagem",
    ],
    # Indicadores de carregamento a aguardar antes de ler a tela.
    "carregando": [
        "css=.loading, .spinner, .br-loading",
        "css=[aria-busy='true']",
    ],
    # O botão de próxima página tem id FIXO no portal real -- confirmado
    # 2026-08-21. Fica primeiro por ser o mais estável; o resto é reserva
    # para o caso de o componente de paginação mudar.
    "proxima_pagina": [
        "css=#btn-next-page:not([disabled])",
        r"role=button:p[áa]gina seguinte",
        "css=.arrows button:last-child:not([disabled])",
    ],
    # "Exibir: N" -- maximizar reduz o número de páginas a percorrer.
    "itens_por_pagina": [
        "css=br-pagination-table .pgitem ng-select",
    ],
    # Marcadores de sessão autenticada. Confirmados contra o portal real em
    # 2026-08-21: o "Sair" do DET é um custom element `<br-button>`, que NÃO
    # expõe papel ARIA de button -- por isso `role=button:sair` não o
    # encontrava, e o robô concluía que o login tinha falhado quando na
    # verdade já estava autenticado na tela /servicos.
    "marcador_autenticado": [
        r"role=button:trocar perfil",
        r"texto=empregador\s*:",
        "css=br-button.logout, .logout.br-button",
        r"texto=caixa postal",
        "css=[class*='usuario' i], [class*='avatar' i]",
    ],
    # Botão "Sair" no canto superior direito. Mesma armadilha do
    # `marcador_autenticado`: é um `<br-button>` (custom element) que NÃO
    # expõe papel ARIA de button, então `role=button:sair` não o encontra --
    # o CSS vem primeiro, e o texto entra ancorado (`^sair$`) para não casar
    # com "Sair" no meio de outra frase.
    "botao_sair": [
        "css=br-button.logout, .logout.br-button",
        "css=br-button.logout button, .logout.br-button button",
        "css=[class*='logout' i] button, button[class*='logout' i]",
        r"texto=^\s*sair\s*$",
        "css=a[href*='logout' i], a[href*='sair' i]",
    ],
    # Confirmação que alguns portais gov.br pedem antes de encerrar.
    "confirmar_sair": [
        r"role=button:^\s*(sim|confirmar|sair)\s*$",
        "css=.modal.show button.br-button.is-primary",
    ],
    # Faixa "Empregador: 00.000.000/0000-00 | RAZAO SOCIAL" exibida no topo
    # de toda tela autenticada. É a ÚNICA fonte na tela que diz de quem são
    # os dados exibidos -- ver `confirmar_empregador_na_tela` em
    # caixa_postal.py para por que isso é conferido na hora da leitura.
    "faixa_empregador": [
        r"texto=empregador\s*:",
        "css=[class*='empregador' i]",
    ],
}
