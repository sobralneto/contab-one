"""Abertura do Chrome com perfil persistente e certificado digital A1.

Por que ``launch_persistent_context`` e não ``browser.new_context()``:

1. **Reaproveitamento de sessão.** O ``user_data_dir`` guarda cookies,
   ``localStorage`` e decisões de certificado. Depois do primeiro acesso
   assistido, as execuções seguintes tendem a cair direto no portal
   autenticado, sem novo diálogo de certificado.

2. **Certificado no modo manual.** Quem escolhe e assina com a chave
   privada é o *navegador*, conversando com a Windows CryptoAPI. Nenhuma
   API do Playwright participa desse handshake: por isso é preciso subir o
   Chrome instalado na máquina (``channel="chrome"``), com interface, e não
   o Chromium empacotado em headless.

O modo ``playwright_pfx`` é a alternativa que dispensa a intervenção
humana: o Playwright termina o TLS por conta própria e apresenta o .pfx às
origens configuradas. É o padrão -- o modo manual fica como rede de
segurança para quando o portal muda o host que exige o certificado.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Error as ErroPlaywright, Page, Playwright

from .erros import ErroRobo
from .log import AVISO
from .settings import MODO_PFX, Config

# Argumentos de linha de comando do Chrome.
# - AutomationControlled: reduz a chance de o portal barrar o navegador por
#   detectar `navigator.webdriver`.
# - As flags de primeira execução evitam telas de boas-vindas que roubam o
#   foco do robô em perfis recém-criados.
ARGS_CHROME = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-popup-blocking",
    "--start-maximized",
    "--lang=pt-BR",
]

# O Playwright injeta `--enable-automation`, que faz o Chrome exibir a barra
# "controlado por software de teste" e altera algumas heurísticas.
ARGS_IGNORADOS = ["--enable-automation"]


def _perfil_em_uso(dir_perfil: Path) -> bool:
    """Heurística para detectar um Chrome já aberto sobre este perfil."""
    return (dir_perfil / "SingletonLock").exists() or (dir_perfil / "lockfile").exists()


def _certificados_cliente(cfg: Config) -> list[dict[str, Any]] | None:
    """Monta a lista ``client_certificates`` quando o modo é ``playwright_pfx``.

    O certificado é **um só** -- o do escritório contábil -- e não varia por
    cliente: quem individualiza a empresa é a troca de representação dentro
    do portal. A mesma entrada é repetida por origem porque o Playwright só
    apresenta o certificado à origem que casar exatamente.
    """
    if cfg.modo_certificado != MODO_PFX:
        return None

    caminho = str(cfg.caminho_certificado())
    senha = cfg.senha_certificado()
    entradas: list[dict[str, Any]] = []
    for origem in cfg.origens_certificado:
        entrada: dict[str, Any] = {"origin": origem, "pfxPath": caminho}
        if senha:
            entrada["passphrase"] = senha
        entradas.append(entrada)
    return entradas


def abrir_contexto(
    pw: Playwright, cfg: Config, log: logging.Logger
) -> tuple[BrowserContext, Page]:
    """Sobe o Chrome com o perfil persistente e devolve a aba ativa."""
    dir_perfil = cfg.dir_perfil.resolve()
    dir_perfil.mkdir(parents=True, exist_ok=True)

    if _perfil_em_uso(dir_perfil):
        log.warning(
            "%s Perfil '%s' parece estar em uso. Feche o Chrome aberto sobre "
            "esta pasta antes de continuar.",
            AVISO,
            dir_perfil,
        )

    parametros: dict[str, Any] = {
        "user_data_dir": str(dir_perfil),
        "channel": cfg.canal_navegador,
        "headless": cfg.headless,
        "args": list(ARGS_CHROME),
        "ignore_default_args": list(ARGS_IGNORADOS),
        "locale": "pt-BR",
        "timezone_id": "America/Sao_Paulo",
        # Sem viewport fixo: a janela real (--start-maximized) é usada, o
        # que reduz layouts responsivos inesperados.
        "no_viewport": True,
    }

    certificados = _certificados_cliente(cfg)
    if certificados:
        parametros["client_certificates"] = certificados
        log.info(
            "Certificado .pfx (%s) sera apresentado a: %s",
            Path(certificados[0]["pfxPath"]).name,
            ", ".join(cfg.origens_certificado),
        )

    log.info(
        "Abrindo %s | perfil=%s | headless=%s | modo_certificado=%s",
        cfg.canal_navegador,
        dir_perfil.name,
        cfg.headless,
        cfg.modo_certificado,
    )

    try:
        contexto = pw.chromium.launch_persistent_context(**parametros)
    except ErroPlaywright as exc:
        raise ErroRobo(_diagnosticar_falha(exc, cfg, dir_perfil)) from exc

    contexto.set_default_timeout(cfg.timeout_padrao_ms)
    contexto.set_default_navigation_timeout(cfg.timeout_navegacao_ms)

    page = contexto.pages[0] if contexto.pages else contexto.new_page()
    try:
        page.bring_to_front()
    except ErroPlaywright:
        pass
    return contexto, page


def _diagnosticar_falha(exc: ErroPlaywright, cfg: Config, dir_perfil: Path) -> str:
    """Traduz erros crus do Playwright em orientação acionável."""
    texto = str(exc).lower()
    if "executable doesn't exist" in texto or "channel" in texto:
        return (
            f"Nao foi possivel iniciar o canal '{cfg.canal_navegador}'. Instale o "
            "Google Chrome ou rode: python -m playwright install chrome"
        )
    if "singleton" in texto or "profile" in texto or "in use" in texto:
        return (
            f"O perfil {dir_perfil} ja esta em uso por outra instancia do Chrome. "
            "Feche o navegador (ou remova SingletonLock) e tente novamente."
        )
    if "client_certificates" in texto or "pfx" in texto:
        return (
            "Falha ao carregar o certificado .pfx. Confira o caminho, a senha na "
            f"variavel de ambiente e se o arquivo e um PKCS#12 valido. Detalhe: {exc}"
        )
    return f"Falha ao iniciar o navegador: {exc}"


def fechar_contexto(contexto: BrowserContext, cfg: Config, log: logging.Logger) -> None:
    """Fecha o contexto respeitando ``fechar_navegador`` da configuração."""
    if not cfg.fechar_navegador:
        log.info("%s 'fechar_navegador=false': janela mantida aberta.", AVISO)
        return
    try:
        contexto.close()
    except ErroPlaywright as exc:
        log.warning("%s Erro ao fechar o navegador: %s", AVISO, exc)


def pagina_ativa(contexto: BrowserContext, atual: Page) -> Page:
    """Devolve a aba relevante quando o portal abre o login em nova janela."""
    abertas = [p for p in contexto.pages if not p.is_closed()]
    if not abertas:
        return atual
    if atual in abertas and len(abertas) == 1:
        return atual
    nova = abertas[-1]
    if nova is not atual:
        try:
            nova.bring_to_front()
        except ErroPlaywright:
            pass
    return nova


def limpar_perfil(cfg: Config, log: logging.Logger) -> None:
    """Descarta o perfil persistente (força novo login com certificado)."""
    dir_perfil = cfg.dir_perfil.resolve()
    if not dir_perfil.exists():
        log.info("Perfil '%s' ja estava ausente.", dir_perfil)
        return
    shutil.rmtree(dir_perfil, ignore_errors=True)
    log.info("Perfil '%s' removido.", dir_perfil)


def resumo_ambiente() -> dict[str, str]:
    """Metadados do ambiente, úteis no log de auditoria."""
    return {
        "maquina": os.getenv("COMPUTERNAME") or platform.node(),
        "usuario_so": os.getenv("USERNAME") or os.getenv("USER") or "",
    }
