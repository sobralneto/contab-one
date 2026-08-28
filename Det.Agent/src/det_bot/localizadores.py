"""Resolução de seletores tolerantes e utilidades de espera.

Este módulo transforma as strings declarativas do :mod:`det_bot.seletores`
em ``Locator`` do Playwright e implementa a estratégia de "primeiro
candidato que funcionar", que é o que dá resiliência ao robô quando o
portal muda classes CSS mas mantém os textos/papéis.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Callable

from playwright.sync_api import Error as ErroPlaywright
from playwright.sync_api import Locator, Page, TimeoutError as TimeoutPlaywright

from .erros import ErroEtapa
from .log import AVISO

# Prefixos suportados -> construtor do Locator.
_PREFIXOS_GET_BY: dict[str, Callable[[Page | Locator, re.Pattern], Locator]] = {
    "texto=": lambda raiz, rx: raiz.get_by_text(rx),
    "rotulo=": lambda raiz, rx: raiz.get_by_label(rx),
    "titulo=": lambda raiz, rx: raiz.get_by_title(rx),
    "placeholder=": lambda raiz, rx: raiz.get_by_placeholder(rx),
}


def resolver(raiz: Page | Locator, spec: str) -> Locator:
    """Converte uma spec textual em um ``Locator``.

    Ver a docstring de :mod:`det_bot.seletores` para a gramática aceita.
    """
    spec = spec.strip()

    if spec.startswith("role="):
        corpo = spec[len("role=") :]
        papel, sep, nome = corpo.partition(":")
        papel = papel.strip()
        if sep and nome.strip():
            return raiz.get_by_role(papel, name=re.compile(nome.strip(), re.I))  # type: ignore[arg-type]
        return raiz.get_by_role(papel)  # type: ignore[arg-type]

    if spec.startswith("testid="):
        return raiz.get_by_test_id(spec[len("testid=") :].strip())

    for prefixo, fabrica in _PREFIXOS_GET_BY.items():
        if spec.startswith(prefixo):
            return fabrica(raiz, re.compile(spec[len(prefixo) :].strip(), re.I))

    # css=..., xpath=..., //..., ou CSS puro -> engine nativo do Playwright.
    return raiz.locator(spec)


# Classes que marcam "desabilitado" sem usar o atributo `disabled` -- comuns
# em PrimeNG/Bootstrap, onde o botão continua visível e só perde o
# `pointer-events`. Sem checar isso, o clique fica repetindo até o timeout.
CLASSES_DESABILITADO = ("p-disabled", "disabled", "ui-state-disabled", "is-disabled")


def esta_habilitado(alvo: Locator) -> bool:
    """Diz se o elemento aceita clique de fato (não só se está visível)."""
    try:
        if not alvo.is_enabled(timeout=2_000):
            return False
        if (alvo.get_attribute("aria-disabled") or "").strip().lower() == "true":
            return False
        classes = (alvo.get_attribute("class") or "").lower().split()
        return not any(marca in classes for marca in CLASSES_DESABILITADO)
    except (TimeoutPlaywright, ErroPlaywright):
        return False


def primeiro_visivel(
    raiz: Page | Locator,
    specs: list[str],
    timeout_ms: int,
    log: logging.Logger | None = None,
    predicado: Callable[[Locator], bool] | None = None,
    estado: str = "visible",
) -> tuple[Locator, str]:
    """Retorna o primeiro candidato visível e a spec que o encontrou.

    ``timeout_ms`` é o orçamento **total**, não por candidato: cada
    tentativa recebe uma fatia (com piso de 2s, para não descartar um
    seletor válido em tela lenta), mas nunca além do tempo que resta. Sem
    esse teto, uma lista de 5 candidatos transformaria um orçamento de 6s
    em 10s de espera -- custo pago em toda última página da paginação,
    multiplicado pelo número de empresas.

    Consequência a ter em mente ao ajustar timeouts: com orçamento apertado
    e muitos candidatos, os últimos da lista podem não ser tentados. Como os
    candidatos vão do mais provável ao mais genérico, mantenha
    ``timeout_padrao_ms`` >= 2000 x (número de candidatos) para garantir que
    todos tenham vez.
    """
    limite = time.monotonic() + timeout_ms / 1000
    fatia = max(2_000, timeout_ms // max(1, len(specs)))
    falhas: list[str] = []

    for spec in specs:
        restante_ms = int((limite - time.monotonic()) * 1000)
        if restante_ms <= 0:
            falhas.append(f"{spec} -> orcamento esgotado")
            break
        try:
            alvo = resolver(raiz, spec).first
            alvo.wait_for(state=estado, timeout=min(fatia, restante_ms))
            if predicado is not None and not predicado(alvo):
                falhas.append(f"{spec} -> visivel mas reprovado no predicado")
                continue
            if log:
                log.debug("Seletor resolvido: %s", spec)
            return alvo, spec
        except (TimeoutPlaywright, ErroPlaywright) as exc:
            falhas.append(f"{spec} -> {type(exc).__name__}")

    raise LookupError(
        f"nenhum dos seletores candidatos ficou '{estado}': " + " | ".join(falhas)
    )


def clicar_primeiro(
    raiz: Page | Locator,
    specs: list[str],
    descricao: str,
    timeout_ms: int,
    log: logging.Logger,
    predicado: Callable[[Locator], bool] | None = None,
) -> str:
    """Clica no primeiro candidato disponível; devolve a spec vencedora."""
    alvo, spec = primeiro_visivel(raiz, specs, timeout_ms, log, predicado)
    try:
        alvo.scroll_into_view_if_needed(timeout=5_000)
    except ErroPlaywright:
        pass  # elemento já visível ou sem scroll: seguir para o clique
    alvo.click(timeout=timeout_ms)
    log.info("Clique em '%s' via seletor: %s", descricao, spec)
    return spec


def clicar_se_existir(
    raiz: Page | Locator,
    specs: list[str],
    descricao: str,
    timeout_ms: int,
    log: logging.Logger,
) -> bool:
    """Clica se o elemento existir; ausência não é erro.

    Usado em telas opcionais do fluxo (consentimento de dados, escolha de
    perfil, menu recolhido), que aparecem só em alguns acessos.
    """
    try:
        clicar_primeiro(raiz, specs, descricao, timeout_ms, log)
        return True
    except (LookupError, ErroPlaywright) as exc:
        log.debug("Etapa opcional '%s' ignorada (%s)", descricao, exc)
        return False


def existe_visivel(raiz: Page | Locator, specs: list[str], timeout_ms: int = 3_000) -> bool:
    """Verificação booleana e barata da presença de um elemento."""
    try:
        primeiro_visivel(raiz, specs, timeout_ms)
        return True
    except (LookupError, ErroPlaywright):
        return False


def aguardar_ocioso(page: Page, specs_carregando: list[str], timeout_ms: int) -> None:
    """Espera spinners sumirem e a rede assentar.

    O DET é uma SPA: ``networkidle`` pode nunca disparar por causa de
    long-polling, então a espera é best-effort e nunca derruba o fluxo.
    """
    limite = time.monotonic() + timeout_ms / 1000
    for spec in specs_carregando:
        restante = max(0.0, limite - time.monotonic())
        if restante <= 0:
            break
        try:
            resolver(page, spec).first.wait_for(
                state="hidden", timeout=int(restante * 1000)
            )
        except (TimeoutPlaywright, ErroPlaywright):
            continue
    try:
        page.wait_for_load_state("networkidle", timeout=5_000)
    except (TimeoutPlaywright, ErroPlaywright):
        page.wait_for_timeout(500)


def texto_de(alvo: Locator) -> str:
    """Texto visível normalizado de um elemento (string vazia em erro)."""
    try:
        return re.sub(r"\s+", " ", (alvo.inner_text(timeout=5_000) or "")).strip()
    except (TimeoutPlaywright, ErroPlaywright):
        return ""


def exigir(
    condicao: bool,
    etapa_nome: str,
    mensagem: str,
    log: logging.Logger,
    tipo_erro: type[ErroEtapa] = ErroEtapa,
) -> None:
    """Levanta :class:`ErroEtapa` nomeada quando a condição não se sustenta."""
    if not condicao:
        log.error("%s %s", AVISO, mensagem)
        raise tipo_erro(etapa_nome, mensagem)
