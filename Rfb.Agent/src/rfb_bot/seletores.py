"""Catálogo de seletores tolerantes a mudanças de layout.

Cada chave lógica aponta para uma *lista de candidatos*, tentados em ordem
até que um funcione. A ordem vai do mais semântico (papel ARIA + nome
acessível, que sobrevive a trocas de CSS) para o mais frágil (CSS/XPath).

Sintaxe dos candidatos (resolvida por ``localizadores.resolver``):

    role=<papel>:<regex do nome>   -> page.get_by_role(papel, name=regex)
    texto=<regex>                  -> page.get_by_text(regex)
    rotulo=<regex>                 -> page.get_by_label(regex)
    titulo=<regex>                 -> page.get_by_title(regex)
    placeholder=<regex>            -> page.get_by_placeholder(regex)
    testid=<valor>                 -> page.get_by_test_id(valor)
    xpath=... | css=... | <css>    -> page.locator(...)

Todos os regex são aplicados com ``re.IGNORECASE``.

ESTADO DE CALIBRAÇÃO: confirmados contra o portal real em 2026-08-29, a
partir do HTML capturado por ``python run.py --dump``. Os seletores de
primeira posição usam ``id`` fixos que o portal expõe
(``#avatar-dropdown-trigger``, ``#input-representar-cpfcnpj``); os demais
candidatos são reserva para quando esses ids mudarem. Se o portal virar,
rode o ``--dump`` de novo e ajuste aqui ou na seção ``[seletores]`` do
config.toml, que sobrescreve o código sem exigir novo deploy.
"""

from __future__ import annotations

SELETORES_PADRAO: dict[str, list[str]] = {
    # ------------------------------------------------------------------ #
    # Sessão
    # ------------------------------------------------------------------ #
    # Marcadores de que a sessão está viva e autenticada no portal. O chip
    # do usuário (avatar + CNPJ, canto superior direito) só existe logado, e
    # é o marcador mais barato de conferir.
    "marcador_autenticado": [
        "css=#avatar-dropdown-trigger",
        "css=.header-avatar .br-sign-in, .header-login .avatar",
        "css=span.ni-pessoa",
    ],
    # Faixa "17.409.737/0001-65" dentro do chip: mostra de quem é a sessão
    # em tela. Confirmação visual complementar à consulta de dadosUsuario.
    "ni_pessoa_chip": [
        "css=#avatar-dropdown-trigger span.ni-pessoa",
        "css=span.ni-pessoa",
    ],
    # Marcadores de que caímos de volta no login/SSO. Quando algum destes
    # aparece, a sessão persistida expirou e o certificado precisa ser
    # reapresentado -- o robô aborta em vez de ficar clicando no vazio.
    "tela_login": [
        r"texto=entrar com gov\.?\s?br",
        r"texto=certificado digital",
        "css=input[name='identificacao' i], input[id*='cpf' i]",
        "css=#login-certificate, a[href*='certificado']",
    ],
    # Telas opcionais que roubam o clique se não forem dispensadas antes.
    "aceitar_cookies": [
        r"role=button:^\s*(aceitar|entendi|ok|concordo)\s*$",
        "css=[class*='cookie' i] button.br-button.is-primary",
    ],
    # ------------------------------------------------------------------ #
    # Troca de representação: o escritório assume o papel de PROCURADOR do
    # CNPJ do cliente. É a etapa mais frágil do robô -- ver o cabeçalho.
    # ------------------------------------------------------------------ #
    # Chip do usuário no canto superior direito: abre a sidebar. O texto é o
    # nome do escritório (varia por instalação), então os candidatos apostam
    # no id e na estrutura, nunca no texto.
    "abrir_representar": [
        "css=#avatar-dropdown-trigger",
        "css=.header-avatar button.br-sign-in",
        "css=.avatar.dropdown > button",
    ],
    # A sidebar traz "Representar" como um ACORDEÃO fechado: o formulário
    # (`div.representacao-container.representar.collapse`) só é revelado
    # depois deste clique. Note que este botão também se chama
    # "Representar" -- a mesma legenda do submit --, e é por isso que
    # `botao_representar` abaixo se ancora em `type=submit`: um seletor por
    # texto casaria com o acordeão e o fluxo travaria aqui, reabrindo e
    # fechando a seção sem nunca enviar o formulário.
    "expandir_representar": [
        "css=button.expandir[aria-controls='collapse']",
        "css=.div-input-representar button.expandir",
        "css=button.expandir",
    ],
    # Confirmado contra a tela real: id fixo, com máscara de CPF/CNPJ
    # (atributo `cpfcnpjmask`, maxlength=18).
    "campo_documento": [
        "css=#input-representar-cpfcnpj",
        "css=input[name='representar-cpfcnpj']",
        r"placeholder=digite o cpf ou cnpj",
        "css=input[cpfcnpjmask]",
    ],
    # Confirmado: é um <br-select name="perfil-select"> do DS gov.br
    # envolvendo um ng-select pesquisável -- não um <select> nativo. O
    # tratamento de <select> continua em portal.py como reserva, caso o
    # portal simplifique o componente.
    "combo_papel": [
        "css=br-select[name='perfil-select'] ng-select",
        "css=br-select[name='perfil-select'] input[role='combobox']",
        "css=.representacao-container ng-select",
        "css=select[name*='perfil' i], select[name*='papel' i]",
    ],
    # "{papel}" é substituído em tempo de execução pelo `papel` do
    # config.toml (por padrão "Procurador").
    "opcao_papel": [
        "css=.ng-dropdown-panel .ng-option:has-text('{papel}')",
        "css=.ng-option:has-text('{papel}')",
        "role=option:{papel}",
        "role=radio:{papel}",
        r"texto=^\s*{papel}\s*$",
    ],
    # Valor já selecionado no combo -- evita reabrir o dropdown à toa.
    "valor_papel_atual": [
        "css=br-select[name='perfil-select'] .ng-value-label",
        "css=.representacao-container ng-select .ng-value-label",
    ],
    # Submit do formulário. Ancorado em `type=submit` de propósito: o
    # acordeão que expande a seção usa a MESMA legenda "Representar", e
    # casar por texto pegaria o botão errado (ver `expandir_representar`).
    # Nasce `disabled` e só habilita com CNPJ válido + papel escolhido --
    # o que torna o predicado `esta_habilitado` um teste real de que o
    # formulário foi preenchido a contento.
    "botao_representar": [
        "css=form .representacao-container button[type='submit']",
        "css=form button[type='submit'].br-button.primary",
        "css=.representacao-container button[type='submit']",
    ],
    # Mensagem de erro exibida quando a representação é recusada (sem
    # procuração, procuração vencida, CNPJ inexistente). Sem ler isto, o
    # robô confundiria "recusado" com "ainda carregando".
    "erro_representacao": [
        "css=[role='alert']",
        "css=.alert-danger, .alert-error, .br-message.danger, .br-message.error",
        "css=.invalid-feedback, .error-message, .mensagem-erro",
    ],
    # Modal "A representação foi alterada. É necessário acessar novamente a
    # Credencial API." Não precisa ser respondido -- o robô navega direto
    # para a URL da credencial --, mas serve como confirmação visual e é
    # dispensado para não interceptar cliques de uma eventual etapa seguinte.
    "modal_representacao_alterada": [
        r"texto=representa[cç][aã]o foi alterada",
        "css=.modal.show, modal-container.modal.show",
    ],
    "fechar_modal": [
        r"role=button:^\s*(ok|fechar|entendi|continuar)\s*$",
        "css=.modal.show button.br-button.is-primary",
        "css=.modal.show button.close, .modal.show [aria-label*='fechar' i]",
    ],
    # Indicadores de carregamento a aguardar antes de ler a tela.
    "carregando": [
        "css=.loading, .spinner, .br-loading",
        "css=[aria-busy='true']",
    ],
}
