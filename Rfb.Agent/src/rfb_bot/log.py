"""Logging, redação de segredos e o utilitário de "etapas" do robô.

Duas responsabilidades além do logging comum:

* **Etapas.** Cada passo relevante é envolvido por um context manager que
  registra início/fim e, em caso de falha, grava screenshot + HTML da tela
  e converte a exceção em :class:`~rfb_bot.erros.ErroEtapa`.

* **Redação.** Este robô manipula ``clientSecret`` de produção. O filtro
  :class:`FiltroSegredo` roda sobre **todo** registro que passa pelo logger
  (console e arquivo), de modo que um segredo só vaza para o log se
  escapar do logging inteiro. É defesa em profundidade: o código também
  evita passar o segredo adiante, mas basta um ``log.debug(resposta)``
  descuidado no futuro para publicar a chave em texto puro num arquivo que
  vive por 5 rotações.
"""

from __future__ import annotations

import logging
import re
import sys
import unicodedata
from contextlib import contextmanager
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from .erros import ErroEtapa

if TYPE_CHECKING:  # pragma: no cover - apenas para tipagem
    from playwright.sync_api import Page

# Marcadores em ASCII puro: consoles legados do Windows (cp1252) quebram
# com emoji, e o robô costuma rodar em sessão de serviço/agendador.
INICIO = "[>]"
SUCESSO = "[OK]"
FALHA = "[X]"
AVISO = "[!]"

FORMATO = "%(asctime)s | %(levelname)-7s | %(name)-16s | %(message)s"

# Campos cujo valor nunca pode aparecer no log, em JSON ou em texto solto.
_PADROES_SEGREDO = (
    re.compile(r'("?client_?secret"?\s*[:=]\s*"?)([^",\s}]+)', re.I),
    re.compile(r'("?(?:senha|password|passphrase)"?\s*[:=]\s*"?)([^",\s}]+)', re.I),
    # O valor inteiro some, não só a primeira palavra: "Bearer <token>" tem
    # espaço no meio, e mascarar só "Bearer" publicaria o token.
    re.compile(r"""(authorization["']?\s*[:=]\s*["']?)([^"'\r\n]+)""", re.I),
)


def redigir(texto: str) -> str:
    """Substitui valores de segredo por ``***`` preservando o resto do texto."""
    for padrao in _PADROES_SEGREDO:
        texto = padrao.sub(r"\1***", texto)
    return texto


class FiltroSegredo(logging.Filter):
    """Aplica :func:`redigir` na mensagem já formatada de cada registro."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            mensagem = record.getMessage()
        except Exception:  # noqa: BLE001 - log nunca derruba o robô
            return True
        limpa = redigir(mensagem)
        if limpa != mensagem:
            record.msg = limpa
            record.args = ()
        return True


def configurar_logging(dir_logs: Path, nivel: int = logging.INFO) -> logging.Logger:
    """Configura o logger raiz com saída em console e arquivo rotativo."""
    dir_logs.mkdir(parents=True, exist_ok=True)
    raiz = logging.getLogger("rfb")
    raiz.setLevel(nivel)
    raiz.propagate = False
    if raiz.handlers:  # evita handlers duplicados em re-execuções
        return raiz

    formatador = logging.Formatter(FORMATO, datefmt="%Y-%m-%d %H:%M:%S")
    filtro = FiltroSegredo()

    # Consoles legados do Windows (cp1252) levantariam UnicodeEncodeError em
    # acentos: um robô agendado não pode morrer por causa de um log.
    try:
        sys.stdout.reconfigure(errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):  # pragma: no cover - stdout redirecionado
        pass
    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(formatador)
    console.addFilter(filtro)
    raiz.addHandler(console)

    arquivo = RotatingFileHandler(
        dir_logs / "rfb_bot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    arquivo.setFormatter(formatador)
    arquivo.addFilter(filtro)
    raiz.addHandler(arquivo)

    # O Playwright é verboso demais em DEBUG; mantém apenas avisos.
    logging.getLogger("playwright").setLevel(logging.WARNING)
    return raiz


def obter_logger(nome: str) -> logging.Logger:
    return logging.getLogger(f"rfb.{nome}")


def normalizar(texto: str | None) -> str:
    """Minúsculas, sem acentos e com espaços colapsados."""
    if not texto:
        return ""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def _fatiar(nome: str) -> str:
    """Converte o nome de uma etapa em um fragmento seguro para arquivo."""
    limpo = re.sub(r"[^a-z0-9]+", "-", normalizar(nome))
    return limpo.strip("-")[:60] or "etapa"


def salvar_evidencia(
    page: "Page",
    dir_debug: Path,
    rotulo: str,
    prefixo: str = "",
) -> dict[str, str]:
    """Grava screenshot + HTML da página atual para diagnóstico.

    Nunca levanta exceção: uma falha ao coletar evidência não pode mascarar
    o erro original que estamos tentando documentar.
    """
    log = obter_logger("evidencia")
    resultado: dict[str, str] = {}
    try:
        dir_debug.mkdir(parents=True, exist_ok=True)
        carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = "_".join(p for p in (prefixo, carimbo, _fatiar(rotulo)) if p)

        png = dir_debug / f"{base}.png"
        page.screenshot(path=str(png), full_page=True, timeout=15_000)
        resultado["screenshot"] = str(png)

        html = dir_debug / f"{base}.html"
        html.write_text(page.content(), encoding="utf-8", errors="replace")
        resultado["html"] = str(html)

        resultado["url"] = page.url
        log.info("%s Evidencia salva: %s", AVISO, png.name)
    except Exception as exc:  # noqa: BLE001 - best effort por definição
        log.warning("%s Nao foi possivel salvar evidencia (%s)", AVISO, exc)
    return resultado


@contextmanager
def etapa(
    nome: str,
    log: logging.Logger,
    page: "Page | None" = None,
    dir_debug: Path | None = None,
    prefixo_evidencia: str = "",
    tipo_erro: type[ErroEtapa] = ErroEtapa,
) -> Iterator[dict]:
    """Envolve um passo do fluxo com log, evidência e erro nomeado."""
    contexto: dict = {"etapa": nome}
    log.info("%s %s", INICIO, nome)
    try:
        yield contexto
    except ErroEtapa:
        # Já é um erro de etapa (veio de uma sub-etapa): não reembrulhar.
        raise
    except Exception as exc:
        log.error("%s Falha na etapa '%s': %s: %s", FALHA, nome, type(exc).__name__, exc)
        if page is not None and dir_debug is not None:
            contexto["evidencia"] = salvar_evidencia(
                page, dir_debug, nome, prefixo=prefixo_evidencia
            )
        raise tipo_erro(nome, f"{type(exc).__name__}: {exc}") from exc
    else:
        log.info("%s %s", SUCESSO, nome)
