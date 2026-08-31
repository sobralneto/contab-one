"""Navegação no portal: sessão e troca de representação (Procurador).

Esta é a única parte do robô que **precisa** de navegador. A criação da
credencial em si é feita por API (:mod:`rfb_bot.credenciais`), mas a troca
de representação não pode ser: o ``POST /representacao/api/MudancaPapel/
procurador`` exige um ``tokenCaptcha`` gerado pelo JavaScript da própria
página (captcha invisível, amarrado à execução real de JS). Recriar essa
chamada com um cliente HTTP puro não funciona -- por isso o clique é real,
e por isso nada deve ser inserido entre preencher o CNPJ e clicar em
"Representar": o token nasce no clique e não convém testar sua validade.
"""

from __future__ import annotations

import json
import logging
import re
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Error as ErroPlaywright, Locator, Page, Response

from .erros import (
    ErroCnpjInvalido,
    ErroRepresentacao,
    ErroRepresentacaoDivergente,
    ErroSemProcuracao,
    ErroSessao,
)
from .localizadores import (
    clicar_se_existir,
    esta_habilitado,
    existe_visivel,
    preencher_primeiro,
    primeiro_visivel,
    texto_de,
    texto_do_primeiro,
)
from .log import AVISO, SUCESSO, normalizar
from .settings import Config, Cliente

# Endpoint interno disparado pelo clique em "Representar". O robô não o
# chama: apenas escuta a resposta para saber se a troca foi aceita, o que é
# mais confiável do que interpretar o texto do modal.
FRAGMENTO_MUDANCA_PAPEL = "MudancaPapel"
CAMINHO_DADOS_USUARIO = "/login/api/Usuario/dadosUsuario"

# Trechos que identificam a recusa por falta de procuração -- condição de
# negócio, não falha do robô. Comparados sobre o texto normalizado (sem
# acento). O primeiro item é o texto EXATO confirmado contra o portal real
# em 2026-08-29 (representando um CNPJ com procuração revogada); os
# demais são reserva para variações de redação que o portal talvez use em
# outras negativas do mesmo tipo (procuração vencida vs. nunca outorgada).
_MARCAS_SEM_PROCURACAO = (
    "autorizacao como procurador nao permite acesso",
    "procuracao",
    "nao possui permissao",
    "sem permissao",
    "nao autorizado",
    "nao ha vinculo",
)
# Confirmado contra o portal real: CNPJ com dígito verificador inválido (ou
# inexistente) recusa a representação com esta mensagem -- condição de
# DADO (linha ruim na planilha), não de acesso. Ver ErroCnpjInvalido.
_MARCAS_CNPJ_INVALIDO = ("cnpj invalido", "documento invalido", "ni invalido")
_MARCAS_CAPTCHA = ("captcha", "token invalido", "token expirado")


def url_dados_usuario(cfg: Config) -> str:
    return urljoin(cfg.url_portal, CAMINHO_DADOS_USUARIO)


# ---------------------------------------------------------------------- #
# Sessão
# ---------------------------------------------------------------------- #
def garantir_sessao(page: Page, cfg: Config, log: logging.Logger) -> None:
    """Abre o portal e confirma que a sessão persistida ainda vale.

    Falhar aqui é bem melhor que seguir: sem sessão, todos os seletores
    seguintes dariam timeout um a um, e o operador leria "não achei o botão
    Representar" quando o problema real é que o certificado precisa ser
    reapresentado.
    """
    if urlparse(page.url).netloc != urlparse(cfg.url_portal).netloc:
        page.goto(cfg.url_portal, wait_until="domcontentloaded",
                  timeout=cfg.timeout_navegacao_ms)

    clicar_se_existir(page, cfg.sel("aceitar_cookies"), "aceitar cookies", 5_000, log)

    # Orçamento de login, não o timeout comum: esta espera pode incluir o
    # handshake TLS, os redirecionamentos do SSO e -- no modo manual -- um
    # humano escolhendo o certificado no diálogo do Windows.
    if existe_visivel(page, cfg.sel("marcador_autenticado"), cfg.timeout_login_ms):
        log.info("%s Sessao ativa no portal.", SUCESSO)
        return

    # Ainda pode ser só lentidão de SPA: o login é o veredito, não a
    # ausência do marcador.
    if existe_visivel(page, cfg.sel("tela_login"), 5_000):
        raise ErroSessao(
            "Abrir portal",
            "o portal exibiu a tela de login. A sessao gravada no perfil "
            "expirou. Rode 'python run.py --login' com o navegador visivel "
            "para apresentar o certificado A1 e gravar a sessao novamente.",
        )

    raise ErroSessao(
        "Abrir portal",
        f"nenhum marcador de sessao autenticada apareceu em {page.url}. "
        "Rode 'python run.py --dump' para gravar o HTML da tela e calibrar "
        "'marcador_autenticado' na secao [seletores] do config.toml.",
    )


# ---------------------------------------------------------------------- #
# Troca de representação
# ---------------------------------------------------------------------- #
def representar(page: Page, cfg: Config, cliente: Cliente, log: logging.Logger) -> None:
    """Assume a representação do CNPJ do cliente como Procurador.

    Ao final, a sessão do navegador está operando *como* o cliente, e a
    página aberta é a de nova credencial -- estado que
    :mod:`rfb_bot.credenciais` assume para o POST.
    """
    log.info("Trocando representacao para %s (%s)", cliente.cnpj_formatado, cfg.papel)

    _abrir_sidebar(page, cfg, log)
    campo = preencher_primeiro(
        page,
        cfg.sel("campo_documento"),
        cliente.cnpj_digitos,
        "CPF ou CNPJ",
        cfg.timeout_padrao_ms,
        log,
    )
    _conferir_documento_digitado(campo, cliente, log)
    _selecionar_papel(page, cfg, log)

    resposta = _clicar_representar(page, cfg, log)
    _avaliar_resposta(resposta, log)

    # O modal "A representação foi alterada..." não precisa ser respondido,
    # mas fica sobre a página e interceptaria cliques futuros.
    clicar_se_existir(page, cfg.sel("fechar_modal"), "fechar modal", 5_000, log)

    page.goto(cfg.url_nova_credencial, wait_until="domcontentloaded",
              timeout=cfg.timeout_navegacao_ms)
    confirmar_representacao(page, cfg, cliente, log)


def _abrir_sidebar(page: Page, cfg: Config, log: logging.Logger) -> None:
    """Revela o formulário de representação, em dois passos.

    O portal esconde o formulário atrás de duas camadas: o chip do usuário
    abre a sidebar, e dentro dela um acordeão "Representar" revela os
    campos. Cada passo é condicionado à ausência do campo de documento, e
    não a um estado que o robô ache que a tela tem: clicar num acordeão já
    aberto o FECHA, e o sintoma seria o robô alternar a seção para sempre.
    """
    if existe_visivel(page, cfg.sel("campo_documento"), 2_000):
        log.debug("Formulario de representacao ja estava visivel.")
        return

    _clicar_etapa(page, cfg, log, "abrir_representar", "chip do usuario")
    if existe_visivel(page, cfg.sel("campo_documento"), 3_000):
        return

    _clicar_etapa(page, cfg, log, "expandir_representar", "acordeao Representar")
    if existe_visivel(page, cfg.sel("campo_documento"), cfg.timeout_padrao_ms):
        return

    raise ErroRepresentacao(
        "Abrir formulario de representacao",
        "a sidebar e o acordeao foram acionados, mas o campo de CPF/CNPJ nao "
        "apareceu. Rode 'python run.py --dump' e ajuste 'campo_documento' na "
        "secao [seletores] do config.toml.",
    )


def _clicar_etapa(
    page: Page, cfg: Config, log: logging.Logger, chave: str, descricao: str
) -> None:
    try:
        alvo, spec = primeiro_visivel(
            page, cfg.sel(chave), cfg.timeout_padrao_ms, log
        )
    except LookupError as exc:
        raise ErroRepresentacao(
            f"Abrir formulario de representacao ({descricao})",
            f"{exc}. Rode 'python run.py --dump' e ajuste '{chave}' na secao "
            "[seletores] do config.toml.",
        ) from exc
    alvo.click(timeout=cfg.timeout_padrao_ms)
    log.info("Clique em '%s' via seletor: %s", descricao, spec)


def _conferir_documento_digitado(
    campo: Locator, cliente: Cliente, log: logging.Logger
) -> None:
    """Confere que a máscara do portal aceitou os 14 dígitos.

    O campo usa uma diretiva Angular (``cpfcnpjmask``, ``maxlength=18``).
    ``fill`` dispara o evento de input que ela escuta, mas se um dia a
    máscara passar a exigir digitação tecla a tecla o campo ficaria
    truncado -- e o robô representaria outro CNPJ, ou nenhum. Barato de
    conferir, caro de descobrir depois.
    """
    try:
        digitado = re.sub(r"\D", "", campo.input_value(timeout=5_000))
    except ErroPlaywright as exc:
        log.warning("%s Nao foi possivel reler o campo de documento (%s).", AVISO, exc)
        return
    if digitado != cliente.cnpj_digitos:
        raise ErroRepresentacao(
            "Preencher CPF/CNPJ",
            f"o campo ficou com '{digitado}' em vez de {cliente.cnpj_digitos} "
            "(a mascara do portal provavelmente rejeitou o preenchimento "
            "programatico).",
        )


def _selecionar_papel(page: Page, cfg: Config, log: logging.Logger) -> None:
    """Escolhe "Procurador" no combobox de papel.

    Trata as duas formas possíveis do componente: um ``<select>`` nativo ou
    um combobox custom do Design System gov.br (que só revela as opções
    depois de aberto). A comparação é feita sobre o texto normalizado, para
    não depender de acentuação nem de caixa.
    """
    desejado = normalizar(cfg.papel)

    atual = texto_do_primeiro(page, cfg.sel("valor_papel_atual"), 2_000)
    if atual and desejado in normalizar(atual):
        log.debug("Papel '%s' ja estava selecionado.", cfg.papel)
        return

    try:
        combo, spec = primeiro_visivel(
            page, cfg.sel("combo_papel"), cfg.timeout_padrao_ms, log
        )
    except LookupError as exc:
        raise ErroRepresentacao(
            "Selecionar papel", f"combobox de papel nao encontrado: {exc}"
        ) from exc

    if (combo.evaluate("el => el.tagName") or "").lower() == "select":
        _selecionar_em_select_nativo(combo, cfg, desejado)
        log.info("Papel '%s' selecionado no <select> via: %s", cfg.papel, spec)
        return

    combo.click(timeout=cfg.timeout_padrao_ms)
    try:
        opcao, spec_opcao = primeiro_visivel(
            page, cfg.sel("opcao_papel", papel=cfg.papel), cfg.timeout_padrao_ms, log
        )
    except LookupError as exc:
        raise ErroRepresentacao(
            "Selecionar papel",
            f"a opcao '{cfg.papel}' nao apareceu no combobox: {exc}",
        ) from exc
    opcao.click(timeout=cfg.timeout_padrao_ms)
    log.info("Papel '%s' selecionado via: %s", cfg.papel, spec_opcao)


def _selecionar_em_select_nativo(combo: Locator, cfg: Config, desejado: str) -> None:
    opcoes = combo.locator("option")
    total = opcoes.count()
    for indice in range(total):
        if desejado in normalizar(opcoes.nth(indice).inner_text()):
            combo.select_option(index=indice)
            return
    rotulos = [texto_de(opcoes.nth(i)) for i in range(total)]
    raise ErroRepresentacao(
        "Selecionar papel",
        f"'{cfg.papel}' nao esta entre as opcoes do combobox: {rotulos}",
    )


def _clicar_representar(page: Page, cfg: Config, log: logging.Logger) -> Response | None:
    """Clica em "Representar" e devolve a resposta da troca de papel.

    O botão é resolvido *antes* de abrir a escuta e clicado imediatamente
    depois: o ``tokenCaptcha`` é gerado no clique, e qualquer espera
    inserida aqui só aumentaria a chance de ele chegar vencido ao servidor.
    """
    try:
        botao, spec = primeiro_visivel(
            page,
            cfg.sel("botao_representar"),
            cfg.timeout_padrao_ms,
            log,
            predicado=esta_habilitado,
        )
    except LookupError as exc:
        raise ErroRepresentacao(
            "Clicar em Representar", f"botao nao encontrado ou desabilitado: {exc}"
        ) from exc

    # `clicou` separa duas falhas que o Playwright reporta com o mesmo tipo:
    # o clique não acontecer (fatal -- nada foi enviado) e o clique acontecer
    # sem que a resposta esperada apareça (não fatal -- a confirmação decide).
    clicou = False
    try:
        with page.expect_response(
            lambda r: FRAGMENTO_MUDANCA_PAPEL in r.url,
            timeout=cfg.timeout_padrao_ms,
        ) as espera:
            botao.click(timeout=cfg.timeout_padrao_ms)
            clicou = True
        log.info("Clique em 'Representar' via seletor: %s", spec)
        return espera.value
    except ErroPlaywright as exc:
        if not clicou:
            raise ErroRepresentacao(
                "Clicar em Representar", f"o clique nao foi efetivado: {exc}"
            ) from exc
        # `confirmar_representacao` decide o veredito olhando de quem é a
        # sessão -- fonte mais confiável que qualquer tela ou modal.
        log.warning(
            "%s Nenhuma resposta de %s foi observada apos o clique; a "
            "confirmacao vai depender de %s.",
            AVISO, FRAGMENTO_MUDANCA_PAPEL, CAMINHO_DADOS_USUARIO,
        )
        return None


def _avaliar_resposta(resposta: Response | None, log: logging.Logger) -> None:
    """Traduz a resposta da troca de papel em sucesso, recusa ou falha."""
    if resposta is None:
        return
    if resposta.ok:
        log.debug("Troca de papel respondeu HTTP %s.", resposta.status)
        return

    corpo = _texto_seguro(resposta)
    normalizado = normalizar(corpo)
    mensagem = _mensagem_do_corpo(corpo) or f"HTTP {resposta.status}"

    if any(marca in normalizado for marca in _MARCAS_SEM_PROCURACAO):
        raise ErroSemProcuracao(mensagem)
    if any(marca in normalizado for marca in _MARCAS_CNPJ_INVALIDO):
        raise ErroCnpjInvalido(mensagem)
    if any(marca in normalizado for marca in _MARCAS_CAPTCHA):
        raise ErroRepresentacao(
            "Clicar em Representar",
            f"o portal recusou o tokenCaptcha ({mensagem}). O token e gerado "
            "no clique e tem validade curta: reduza a concorrencia e evite "
            "pausas entre preencher o CNPJ e clicar em Representar.",
        )
    raise ErroRepresentacao("Clicar em Representar", mensagem)


def _texto_seguro(resposta: Response) -> str:
    try:
        return resposta.text()
    except ErroPlaywright:
        return ""


_CHAVES_MENSAGEM = ("mensagem", "message", "detail", "title", "titulo", "erro", "error",
                    "descricao", "description")


def _mensagem_do_corpo(corpo: str) -> str:
    """Extrai a mensagem de erro do JSON de resposta, com fallback no texto cru.

    A comparação de chave é case-insensitive: o endpoint de troca de papel
    devolve ``{"Sessao": null, "Erro": "..."}`` (confirmado contra o portal
    real), com maiúscula -- diferente do padrão ``{"codigo", "descricao"}``
    em minúsculas usado pela API de credenciais. Comparar só em minúsculas
    faria a extração falhar bem no formato mais comum de erro do portal, e o
    CSV acabaria com o JSON inteiro na coluna de observação em vez da frase.
    """
    try:
        dados = json.loads(corpo)
    except (json.JSONDecodeError, TypeError):
        return re.sub(r"\s+", " ", corpo).strip()[:300]
    if isinstance(dados, dict):
        por_chave_minuscula = {str(k).lower(): v for k, v in dados.items()}
        for chave in _CHAVES_MENSAGEM:
            valor = por_chave_minuscula.get(chave)
            if isinstance(valor, str) and valor.strip():
                return valor.strip()
    return re.sub(r"\s+", " ", corpo).strip()[:300]


# ---------------------------------------------------------------------- #
# Confirmação
# ---------------------------------------------------------------------- #
def confirmar_representacao(
    page: Page, cfg: Config, cliente: Cliente, log: logging.Logger
) -> None:
    """Confere, contra o servidor, de quem é a representação ativa.

    Guarda mais importante do robô. Uma troca de papel que "pareceu dar
    certo" mas reverteu (sessão renovada, SPA recarregada, erro silencioso)
    faria o passo seguinte criar uma Chave Secreta **do escritório** e
    gravá-la no CSV como se fosse do cliente. O resultado seria plausível e
    errado -- e entregaria acesso de API de um contribuinte a quem não
    deveria tê-lo. Por isso a checagem falha fechada: qualquer coisa que não
    seja "o CNPJ do cliente está na resposta" aborta o cliente.
    """
    url = url_dados_usuario(cfg)
    try:
        resposta = page.request.get(url, headers={"Accept": "application/json"},
                                    timeout=cfg.timeout_padrao_ms)
    except ErroPlaywright as exc:
        raise ErroRepresentacaoDivergente(
            cliente.cnpj_formatado, f"falha ao consultar {url}: {exc}"
        ) from exc

    if not resposta.ok:
        raise ErroRepresentacaoDivergente(
            cliente.cnpj_formatado, f"{url} respondeu HTTP {resposta.status}"
        )

    corpo = _texto_seguro(resposta)
    # A pontuação some para que o CNPJ case tanto formatado quanto cru --
    # o portal usa as duas formas em campos diferentes da mesma resposta.
    compacto = re.sub(r"[.\-/\s]", "", corpo)
    if cliente.cnpj_digitos not in compacto:
        raise ErroRepresentacaoDivergente(
            cliente.cnpj_formatado,
            "o CNPJ nao aparece na resposta de dadosUsuario (a sessao segue "
            "representando outro contribuinte)",
        )
    log.info("%s Representacao confirmada para %s.", SUCESSO, cliente.cnpj_formatado)
