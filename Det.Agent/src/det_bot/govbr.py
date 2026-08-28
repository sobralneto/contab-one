"""Fluxo de autenticação no gov.br por certificado digital.

Sequência tratada:

    trabalho.gov.br / DET
        -> "Entrar com gov.br"
        -> sso.acesso.gov.br  (escolha do meio de autenticação)
        -> "Seu certificado digital"
        -> certificado.sso.acesso.gov.br  (handshake TLS mútuo)
        -> [diálogo nativo de escolha do certificado / PIN]
        -> [tela opcional de autorização de uso de dados]
        -> redirecionamento de volta ao DET autenticado
        -> troca de perfil: Procurador + CNPJ da empresa + "Selecionar"

O trecho entre o início da autenticação e o retorno ao DET é invisível ao
Playwright -- no modo ``manual`` porque o diálogo de escolha do certificado
é uma janela do Windows fora do DOM; nos modos automáticos porque tudo
acontece no handshake TLS. Por isso a espera não é um ``wait_for_selector``,
e sim um *polling* de URL com orçamento longo (``timeout_login_ms``).

A troca de perfil no fim é o passo que individualiza o cliente: o escritório
autentica uma vez com o próprio certificado e depois assume, uma a uma, a
procuração de cada CNPJ.
"""

from __future__ import annotations

import logging
import re
import time

from playwright.sync_api import BrowserContext, Error as ErroPlaywright, Page

from .erros import ErroAutenticacao, ErroSemProcuracao
from .localizadores import (
    aguardar_ocioso,
    clicar_primeiro,
    clicar_se_existir,
    existe_visivel,
    primeiro_visivel,
    resolver,
)
from .log import AVISO, INICIO, SUCESSO, etapa, normalizar
from .navegador import pagina_ativa
from .settings import MODO_MANUAL, Config, Empresa, normalizar_cnpj

INTERVALO_POLL_S = 1.5


def _casa_algum(url: str, padroes: list[str]) -> bool:
    return any(re.search(p, url, re.I) for p in padroes)


def esta_autenticado(page: Page, cfg: Config) -> bool:
    """Heurística dupla: URL do DET + marcador de sessão na tela.

    Só a URL não basta -- o DET responde na mesma origem antes e depois do
    login. Só o marcador também não basta -- ele pode demorar a renderizar.
    """
    if not _casa_algum(page.url, cfg.padroes_url_autenticado):
        return False
    if _casa_algum(page.url, cfg.padroes_url_login):
        return False
    # Orçamento generoso de propósito: com 2s de piso por candidato, 4s só
    # alcançavam os dois primeiros da lista -- e era exatamente por isso que
    # a tela /servicos, já autenticada, era lida como "login não concluído".
    return existe_visivel(page, cfg.sel("marcador_autenticado"), timeout_ms=12_000)


def _aguardar_retorno_do_certificado(
    page: Page,
    contexto: BrowserContext,
    cfg: Config,
    log: logging.Logger,
) -> Page:
    """Aguarda o gov.br concluir o handshake e devolver o navegador ao DET.

    Retorna a página ativa ao final (pode ter mudado se o gov.br abriu o
    fluxo em outra aba).
    """
    limite = time.monotonic() + cfg.timeout_login_ms / 1000
    segundos_totais = int(cfg.timeout_login_ms / 1000)
    ultimo_aviso = 0.0
    captcha_avisado = False

    if cfg.modo_certificado == MODO_MANUAL:
        log.warning(
            "%s ACAO MANUAL: escolha o certificado na janela do Chrome "
            "(e informe o PIN, se for token A3). Aguardando ate %ds.",
            AVISO,
            segundos_totais,
        )

    voltou_ao_inicio = False

    while time.monotonic() < limite:
        page = pagina_ativa(contexto, page)

        # A tela inicial de login (campo de CPF) compartilha o rotulo
        # "Continuar" com a tela real de consentimento -- clicar as cegas
        # aqui submeteria um CPF vazio e prenderia o robo num loop ate o
        # timeout (foi exatamente o que aconteceu antes desta checagem
        # existir). Se a tela voltou ao inicio, so avisar e nao clicar --
        # a sessao/tentativa anterior foi descartada pelo gov.br, e clicar
        # em qualquer coisa aqui e chute.
        if existe_visivel(page, cfg.sel("tela_login_inicial_cpf"), 1_500):
            if not voltou_ao_inicio:
                voltou_ao_inicio = True
                log.warning(
                    "%s O gov.br voltou para a tela inicial de login (nao "
                    "para a autorizacao de dados). A tentativa anterior foi "
                    "descartada -- pode ser CAPTCHA nao resolvido a tempo ou "
                    "limite de tentativas seguidas. O robo NAO vai clicar as "
                    "cegas aqui; escolha 'Certificado digital' manualmente "
                    "na janela se quiser tentar de novo nesta execucao.",
                    AVISO,
                )
        else:
            voltou_ao_inicio = False
            # A tela de consentimento real aparece no meio do caminho em
            # alguns acessos; tratada aqui para nao estourar o timeout.
            if _casa_algum(page.url, cfg.padroes_url_login):
                clicar_se_existir(
                    page, cfg.sel("autorizar_dados"), "Autorizar uso de dados", 3_000, log
                )

        if esta_autenticado(page, cfg):
            log.info("Retorno autenticado detectado em: %s", page.url)
            return page

        # O gov.br pode exigir CAPTCHA no login. O robô não resolve -- apenas
        # avisa e continua esperando, para que uma pessoa resolva na janela.
        if not captcha_avisado and existe_visivel(page, cfg.sel("captcha"), 1_500):
            captcha_avisado = True
            log.warning(
                "%s CAPTCHA na tela do gov.br. Resolva na janela do Chrome -- "
                "o robo nao resolve CAPTCHA e vai continuar aguardando.", AVISO)

        restante = limite - time.monotonic()
        if restante > 0 and time.monotonic() - ultimo_aviso > 20:
            ultimo_aviso = time.monotonic()
            log.info("%s Aguardando autenticacao... (%ds restantes) url=%s",
                     INICIO, int(restante), page.url)

        time.sleep(INTERVALO_POLL_S)

    raise TimeoutError(
        f"o portal nao retornou autenticado em {segundos_totais}s. "
        f"Ultima URL observada: {page.url}. Se a tela ja estava logada, o "
        f"problema e o seletor 'marcador_autenticado' -- confira o HTML "
        f"salvo em {cfg.dir_debug}."
    )


_PREFIXOS_REGEX = ("role=", "texto=", "rotulo=", "titulo=", "placeholder=")


def _specs_tipo_perfil(cfg: Config) -> list[str]:
    """Materializa os candidatos de ``opcao_perfil_det`` com o tipo desejado.

    Os seletores guardam o marcador ``{tipo}``, trocado aqui pelo valor de
    ``tipo_perfil_det`` (por padrão "Procurador"). O valor entra escapado nos
    candidatos que viram regex e cru nos que viram CSS -- ``re.escape`` dentro
    de um ``:has-text('...')`` quebraria o seletor.
    """
    cru = cfg.tipo_perfil_det
    escapado = re.escape(cru)
    return [
        spec.replace("{tipo}", escapado if spec.startswith(_PREFIXOS_REGEX) else cru)
        for spec in cfg.sel("opcao_perfil_det")
    ]


def _garantir_tipo_perfil(page: Page, cfg: Config, log: logging.Logger) -> None:
    """Deixa o combo "Perfil" do modal com o tipo desejado.

    No DET esse campo é um ``ng-select`` do Angular, não um grupo de radios:
    a opção só existe no DOM depois que o dropdown é aberto. E ele costuma
    já vir com "Procurador" escolhido -- nesse caso reabrir o dropdown é
    ruído que pode fechar o modal, então a checagem do valor atual vem antes.
    """
    alvo = normalizar(cfg.tipo_perfil_det)

    atual = ""
    try:
        rotulo, _ = primeiro_visivel(page, cfg.sel("valor_perfil_atual"), 4_000)
        atual = normalizar(rotulo.inner_text(timeout=3_000))
    except (LookupError, ErroPlaywright):
        pass

    if atual == alvo:
        log.info("Combo de perfil ja esta em '%s'.", cfg.tipo_perfil_det)
        return

    if not clicar_se_existir(
        page, cfg.sel("combo_perfil_det"), "Abrir combo de perfil", 6_000, log
    ):
        log.info("Combo de perfil nao encontrado; seguindo para o CNPJ.")
        return

    if clicar_se_existir(
        page, _specs_tipo_perfil(cfg), f"Opcao '{cfg.tipo_perfil_det}'", 6_000, log
    ):
        return

    raise ErroAutenticacao(
        "Selecionar tipo de perfil",
        f"a opcao '{cfg.tipo_perfil_det}' nao apareceu no combo "
        f"(valor atual: '{atual or 'vazio'}')",
    )


def _campo_estavel(page: Page, cfg: Config, timeout_ms: int = 6_000):
    """Localiza o campo de CNPJ e espera ele parar de se recriar.

    Escolher "Procurador" no combo faz o Angular reconstruir o campo de CNPJ
    (ele tem um ``*ngIf`` condicionado ao tipo de perfil) -- foi por isso que
    a primeira execução real interagiu com um nó que estava saindo do DOM e
    ficou com o campo vazio. A recriação troca o atributo ``id`` gerado em
    runtime, então usamos justamente essa instabilidade como sinal: só
    seguimos quando o mesmo elemento (mesmo id) aparece em duas checagens
    seguidas.
    """
    limite = time.monotonic() + timeout_ms / 1000
    id_anterior = None
    while time.monotonic() < limite:
        try:
            campo, _ = primeiro_visivel(page, cfg.sel("campo_cnpj_perfil"), 3_000)
            id_atual = campo.evaluate("el => el.id || el.outerHTML.length")
        except (LookupError, ErroPlaywright, TimeoutError):
            id_anterior = None
            page.wait_for_timeout(150)
            continue
        if id_atual == id_anterior:
            return campo
        id_anterior = id_atual
        page.wait_for_timeout(150)
    # Orçamento esgotado: segue com o que tiver, e deixa o chamador decidir.
    return campo


def _preencher_cnpj(
    page: Page, cfg: Config, empresa: Empresa, log: logging.Logger
) -> None:
    """Escreve o CNPJ no campo e **confere** o que ficou lá.

    Três estratégias, na ordem que se mostrou mais confiável contra o
    portal real: o campo tem uma diretiva de máscara Angular que só
    reformata corretamente quando recebe eventos de teclado reais
    (``keydown``/``keypress``), então a digitação tecla a tecla vem
    primeiro; os dois ``fill`` ficam como fallback para o caso de a máscara
    aceitar valor injetado direto.

    O campo é **re-localizado a cada tentativa** via :func:`_campo_estavel`,
    que espera a recriação do Angular assentar antes de interagir -- ver a
    docstring de lá para o porquê.
    """
    # O dropdown do ng-select pode continuar aberto sobre o formulário.
    try:
        page.keyboard.press("Escape")
    except ErroPlaywright:
        pass
    aguardar_ocioso(page, cfg.sel("carregando"), 3_000)

    tentativas = (
        ("tecla a tecla", lambda c: c.press_sequentially(
            empresa.cnpj_digitos, delay=80, timeout=20_000)),
        ("fill formatado", lambda c: c.fill(empresa.cnpj_formatado)),
        ("fill digitos", lambda c: c.fill(empresa.cnpj_digitos)),
    )

    ultimo = ""
    for rotulo, escrever in tentativas:
        try:
            campo = _campo_estavel(page, cfg)
            campo.scroll_into_view_if_needed(timeout=3_000)
            campo.click(timeout=8_000)
            try:
                campo.fill("")
            except ErroPlaywright:
                pass
            page.wait_for_timeout(120)
            escrever(campo)
            # A validação do campo (`brvalidcpfcnpj`) é assíncrona e pode
            # recriar o elemento ao concluir -- foi assim que a primeira
            # correção ainda falhou: ela relia o valor do MESMO Locator que
            # acabara de escrever, que podia já ter saído do DOM. Por isso a
            # leitura abaixo **re-localiza** o campo do zero, e o feedback
            # visual de validação do próprio portal entra como confirmação
            # adicional para quando o valor não puder ser relido a tempo.
            page.wait_for_timeout(500)
            try:
                recarregado = _campo_estavel(page, cfg, timeout_ms=3_000)
                ultimo = _valor_campo(recarregado)
            except (LookupError, ErroPlaywright, TimeoutError):
                ultimo = _valor_campo(campo)

            if normalizar_cnpj(ultimo) == empresa.cnpj_digitos:
                log.info("CNPJ preenchido via '%s': %s", rotulo, ultimo)
                return
            if existe_visivel(page, cfg.sel("cnpj_validado_feedback"), 1_500):
                log.info(
                    "CNPJ preenchido via '%s': portal sinalizou o campo como "
                    "valido (valor relido: %r).", rotulo, ultimo)
                return
            log.debug("Estrategia '%s' resultou em %r", rotulo, ultimo)
        except (LookupError, ErroPlaywright, TimeoutError) as exc:
            log.debug("Estrategia '%s' falhou: %s", rotulo, exc)

    raise ErroAutenticacao(
        "Informar CNPJ do perfil",
        f"nenhuma estrategia preencheu o campo (ultimo valor: {ultimo!r}; "
        f"esperado {empresa.cnpj_formatado})",
    )


def _valor_campo(campo) -> str:
    try:
        return campo.input_value(timeout=5_000) or ""
    except ErroPlaywright:
        return ""


def _erro_na_tela(page: Page, cfg: Config) -> str:
    """Devolve o texto da primeira mensagem de erro visível, ou string vazia.

    Só conta o que está visível **e** tem texto: contêineres de erro vazios
    ficam no DOM o tempo todo em SPAs, e tratá-los como falha travaria toda
    execução legítima.
    """
    for spec in cfg.sel("erro_perfil"):
        try:
            alvo = resolver(page, spec).first
            if not alvo.is_visible(timeout=1_500):
                continue
            texto = (alvo.inner_text(timeout=2_000) or "").strip()
            if texto:
                return re.sub(r"\s+", " ", texto)[:300]
        except (ErroPlaywright, TimeoutError):
            continue
    return ""


def _modal_perfil_aberto(page: Page, cfg: Config) -> bool:
    """O modal de troca de perfil ainda está na tela?"""
    return existe_visivel(page, cfg.sel("modal_perfil"), timeout_ms=1_500)


def _texto_modal(page: Page, cfg: Config) -> str:
    """Texto visível do modal de troca de perfil, achatado; vazio se fechado."""
    for spec in cfg.sel("modal_perfil"):
        try:
            alvo = resolver(page, spec).first
            if not alvo.is_visible(timeout=1_500):
                continue
            texto = (alvo.inner_text(timeout=2_000) or "").strip()
            if texto:
                return re.sub(r"\s+", " ", texto)
        except (ErroPlaywright, TimeoutError):
            continue
    return ""


# A frase útil dentro do texto cru do modal. O `inner_text` do modal traz
# rótulos de campo e botões junto ("Trocar Perfil ... Fechar Perfil
# (Obrigatório) ... CancelarSelecionar"); só a sentença da recusa interessa
# ao contador. Confirmado contra o portal real em 2026-08-22.
_RX_FRASE_ERRO = re.compile(
    r"(n[aã]o existe procura[cç][aã]o.*?trabalhista)", re.I | re.S
)


def _frase_util(texto: str) -> str:
    """Extrai a sentença de recusa do texto cru do modal, se reconhecível."""
    achado = _RX_FRASE_ERRO.search(texto)
    return achado.group(1).strip() if achado else texto


def _aguardar_modal_fechar(page: Page, cfg: Config, timeout_ms: int = 15_000) -> bool:
    """Espera o modal de troca de perfil sumir. ``True`` se fechou.

    O fechamento do modal é o sinal **estrutural** de que o portal aceitou a
    troca -- ao contrário da mensagem de erro, que exige acertar um seletor
    CSS que o portal pode mudar (e que de fato não casou na execução real de
    2026-08-22, deixando passar um "sem procuração" como sucesso). Enquanto
    o modal estiver aberto, a troca não se efetivou.
    """
    limite = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < limite:
        if not _modal_perfil_aberto(page, cfg):
            return True
        page.wait_for_timeout(500)
    return False


def _perfil_confere(page: Page, empresa: Empresa) -> bool:
    """Procura o CNPJ da empresa no texto da tela após a troca de perfil.

    Verificação **positiva**: encontrar o CNPJ confirma que o perfil ativo é
    o esperado. Não encontrar não prova o contrário -- o portal pode
    simplesmente não exibi-lo --, então o chamador trata isso como aviso, e
    o resultado sai marcado com ``perfil_confirmado: false``.

    Faz um pequeno polling em vez de checar uma vez só: confirmado contra o
    portal real que o header ("Empregador: ...") leva um instante para
    atualizar depois do modal fechar -- checar só uma vez, cedo demais,
    produzia falso negativo mesmo com a troca já efetivada.
    """
    for _ in range(6):  # ~3s no total
        try:
            texto = page.locator("body").inner_text(timeout=2_000)
        except (ErroPlaywright, TimeoutError):
            texto = ""
        if empresa.cnpj_formatado and empresa.cnpj_formatado in texto:
            return True
        if empresa.cnpj_digitos in re.sub(r"\D", "", texto):
            return True
        page.wait_for_timeout(500)
    return False


def assumir_perfil_procurador(
    page: Page,
    empresa: Empresa,
    cfg: Config,
    log: logging.Logger,
) -> bool:
    """Troca o perfil no DET para procurador da empresa informada.

    Sequência real do portal: abrir a troca de perfil -> escolher o tipo
    (Procurador) -> digitar o CNPJ da empresa -> "Selecionar".

    Devolve ``True`` se conseguiu **confirmar** o perfil ativo na tela. Como
    o mesmo navegador atende vários clientes em sequência, falhar aqui em
    silêncio significaria ler a caixa postal do cliente anterior e gravá-la
    sob o nome deste -- por isso todo passo obrigatório levanta
    :class:`ErroAutenticacao` (ou, se o motivo for falta de procuração,
    :class:`ErroSemProcuracao` -- uma condição de negócio, não uma falha
    técnica), e só a confirmação final é tolerante.
    """
    log.info("Assumindo perfil '%s' de %s (%s)",
             cfg.tipo_perfil_det, empresa.nome, empresa.cnpj_formatado)

    # A tela de troca pode já estar aberta logo após o login; abrir é
    # opcional, mas os passos seguintes não são.
    clicar_se_existir(
        page, cfg.sel("abrir_troca_perfil"), "Abrir troca de perfil",
        8_000, log,
    )

    _garantir_tipo_perfil(page, cfg, log)

    _preencher_cnpj(page, cfg, empresa, log)

    try:
        clicar_primeiro(
            page, cfg.sel("botao_selecionar_perfil"), "Selecionar",
            cfg.timeout_padrao_ms, log,
        )
    except (LookupError, ErroPlaywright) as exc:
        raise ErroAutenticacao(
            "Selecionar perfil",
            f"botao de confirmacao nao encontrado ({exc})",
        ) from exc

    aguardar_ocioso(page, cfg.sel("carregando"), cfg.timeout_padrao_ms)

    # A checagem de erro vem ANTES da confirmação, e não é detalhe: o portal
    # ecoa o CNPJ recusado dentro da própria mensagem de erro ("CNPJ sem
    # procuração: 99...."). Confirmar primeiro leria esse eco como sucesso e
    # o robô seguiria para a Caixa Postal do cliente anterior.
    erro = _erro_na_tela(page, cfg)

    # O modal continuar aberto significa que a troca NÃO se efetivou, mesmo
    # que `erro_perfil` não tenha casado com nada. Confirmado contra o
    # portal real em 2026-08-22: uma recusa por falta de procuração passou
    # batida pelos seletores de erro, e o CNPJ ecoado dentro do modal ainda
    # aberto foi lido como confirmação -- o robô seguiu e acabou lendo a
    # caixa postal do escritório. O texto do modal entra como detalhe para
    # não perder a mensagem do portal quando o seletor específico falha.
    if not erro and not _aguardar_modal_fechar(page, cfg):
        bruto = _texto_modal(page, cfg)
        erro = _frase_util(bruto) if bruto else (
            "o modal de troca de perfil continuou aberto apos 'Selecionar', "
            "sem mensagem de erro legivel"
        )

    if erro:
        # "Sem procuração" é uma condição de negócio esperada (procuração
        # nunca outorgada, vencida ou revogada) -- distinta de uma falha
        # técnica do robô. O texto exato do portal (ex.: "Não existe
        # procuração entre {escritório} e {CNPJ} para o Domicílio
        # Eletrônico Trabalhista") é preservado para o relatório final.
        if "procuracao" in normalizar(erro):
            raise ErroSemProcuracao(erro)
        raise ErroAutenticacao(
            "Selecionar perfil",
            f"o portal recusou o CNPJ {empresa.cnpj_formatado}: {erro}",
        )

    if _perfil_confere(page, empresa):
        log.info("%s Perfil confirmado na tela: %s", SUCESSO, empresa.cnpj_formatado)
        return True

    log.warning(
        "%s Perfil selecionado sem erro, mas o CNPJ %s nao foi localizado na "
        "tela. Os dados sairao com perfil_confirmado=false.",
        AVISO, empresa.cnpj_formatado,
    )
    return False


def encerrar_sessao(page: Page, cfg: Config, log: logging.Logger) -> bool:
    """Clica em "Sair" para encerrar a sessão no portal. ``True`` se clicou.

    Chamado uma vez por grupo, depois da última empresa: fechar o navegador
    sem sair deixa a sessão do certificado do escritório viva no lado do
    servidor (e no perfil persistente, reaproveitada na próxima execução).
    Encerrar explicitamente é higiene de segurança -- é o certificado do
    escritório, com procuração de vários clientes, que fica pendurado.

    Best-effort de propósito: os dados já foram coletados e gravados quando
    isto roda, então nenhuma falha aqui pode derrubar a execução ou mascarar
    o resultado -- só vira aviso no log.
    """
    if page.is_closed():
        return False

    try:
        if not clicar_se_existir(page, cfg.sel("botao_sair"), "Sair", 8_000, log):
            log.warning(
                "%s Botao 'Sair' nao encontrado; a sessao sera encerrada apenas "
                "pelo fechamento do navegador.", AVISO,
            )
            return False

        # Alguns fluxos gov.br pedem confirmação; ausência não é problema.
        clicar_se_existir(page, cfg.sel("confirmar_sair"), "Confirmar saida", 4_000, log)
        aguardar_ocioso(page, cfg.sel("carregando"), 8_000)
        log.info("%s Sessao encerrada pelo botao 'Sair'.", SUCESSO)
        return True
    except (ErroPlaywright, TimeoutError) as exc:
        log.warning("%s Nao foi possivel clicar em 'Sair' (%s).", AVISO, exc)
        return False


def autenticar(
    contexto: BrowserContext,
    page: Page,
    cfg: Config,
    empresa: Empresa,
    log: logging.Logger,
) -> tuple[Page, bool]:
    """Autentica (ou reaproveita a sessão) e assume o perfil da empresa.

    Devolve a página pronta e se o perfil pôde ser **confirmado** na tela --
    ver :func:`assumir_perfil_procurador`.
    """
    prefixo = empresa.id
    kw = {"page": page, "dir_debug": cfg.dir_debug, "prefixo_evidencia": prefixo,
          "tipo_erro": ErroAutenticacao}

    with etapa(f"Acessar o portal ({cfg.url_portal})", log, **kw):
        page.goto(cfg.url_portal, wait_until="domcontentloaded",
                  timeout=cfg.timeout_navegacao_ms)

    # Sessão reaproveitada do perfil persistente: pula o login inteiro.
    if esta_autenticado(page, cfg):
        log.info("Sessao previa valida no perfil '%s'; login dispensado.",
                 empresa.dir_perfil)
        with etapa("Assumir perfil de procurador", log, **kw) as ctx:
            confirmado = assumir_perfil_procurador(page, empresa, cfg, log)
            ctx["perfil_confirmado"] = confirmado
        return page, confirmado

    with etapa("Clicar em 'Entrar com gov.br'", log, **kw) as ctx:
        ctx["seletor"] = clicar_primeiro(
            page, cfg.sel("botao_entrar_govbr"), "Entrar com gov.br",
            cfg.timeout_padrao_ms, log,
        )

    with etapa("Aguardar a tela de login do gov.br", log, **kw):
        page = pagina_ativa(contexto, page)
        page.wait_for_url(
            re.compile("|".join(cfg.padroes_url_login), re.I),
            timeout=cfg.timeout_navegacao_ms,
        )
        kw["page"] = page

    with etapa("Selecionar autenticacao por 'Certificado digital'", log, **kw) as ctx:
        ctx["seletor"] = clicar_primeiro(
            page, cfg.sel("opcao_certificado_digital"), "Certificado digital",
            cfg.timeout_padrao_ms, log,
        )

    with etapa("Aguardar handshake do certificado e retorno ao DET", log, **kw):
        page = _aguardar_retorno_do_certificado(page, contexto, cfg, log)
        kw["page"] = page

    with etapa("Assumir perfil de procurador", log, **kw) as ctx:
        confirmado = assumir_perfil_procurador(page, empresa, cfg, log)
        ctx["perfil_confirmado"] = confirmado

    return page, confirmado
