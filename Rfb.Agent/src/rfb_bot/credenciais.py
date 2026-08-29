"""Consulta e criação de credenciais (Chaves Secretas) pela API do portal.

A criação **não** é feita clicando na interface: uma vez que a sessão está
representando o cliente, ``page.request`` reaproveita os cookies do próprio
navegador e fala direto com ``/api/v1/credenciais``. É mais rápido e imune
a mudanças de layout -- que, num portal em beta, são a fonte mais provável
de quebra.

Endpoints não documentados. Nada aqui deve assumir formato de resposta com
mais confiança do que o observado: em particular, o GET de consulta é
tratado como "não existe credencial" em toda forma vazia plausível (404,
204, corpo vazio, ``null``, lista vazia, objeto sem ``clientId``), porque o
custo de errar para o lado permissivo é criar uma segunda credencial para
quem já tinha uma.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime, time as hora, timezone, tzinfo
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from playwright.sync_api import APIResponse, BrowserContext, Error as ErroPlaywright, Page

from .erros import ErroCredencial, ErroLimiteRequisicoes, ErroRobo
from .log import AVISO, SUCESSO, normalizar
from .settings import Config, Cliente


@lru_cache(maxsize=1)
def fuso_brasilia() -> tzinfo:
    """Fuso de Brasília, com erro acionável quando a base de fusos falta.

    O Windows não traz o banco IANA, então ``zoneinfo`` depende do pacote
    ``tzdata``. Sem ele o erro nativo é um ``ZoneInfoNotFoundError`` cru --
    e, se a busca fosse feita no import do módulo, derrubaria o robô inteiro
    antes de qualquer mensagem útil aparecer.
    """
    try:
        return ZoneInfo("America/Sao_Paulo")
    except ZoneInfoNotFoundError as exc:
        raise ErroRobo(
            "Base de fusos horarios indisponivel (America/Sao_Paulo). No "
            "Windows ela vem do pacote 'tzdata': rode 'pip install tzdata'. "
            "Sem ela a validade da credencial sairia com 3 horas de erro."
        ) from exc

# Status que valem nova tentativa. 429 é rate limit explícito; 403 aparece
# em portais gov.br como resposta a rajadas (e não só como negativa
# definitiva); 5xx é instabilidade do lado deles.
_STATUS_RETENTAVEIS = frozenset({403, 429, 500, 502, 503, 504})


def calcular_validade(anos: int, agora: datetime | None = None) -> str:
    """Data de validade em ISO 8601 UTC, a partir da meia-noite em Brasília.

    O portal espera o instante UTC equivalente à meia-noite local do dia
    alvo -- rodando em 2026-08-29 com ``anos=5``, o valor observado foi
    ``2031-08-29T03:00:00.000Z`` (00:00 BRT = 03:00 UTC). Calcular em UTC
    direto erraria em 3 horas, e o horário de verão (se voltar a existir)
    mudaria o offset sem aviso -- por isso o cálculo é feito no fuso e só
    depois convertido.
    """
    fuso = fuso_brasilia()
    referencia = (agora or datetime.now(fuso)).astimezone(fuso).date()
    try:
        alvo = referencia.replace(year=referencia.year + anos)
    except ValueError:
        # 29/02 + N anos caindo em ano não bissexto.
        alvo = date(referencia.year + anos, 2, 28)
    instante = datetime.combine(alvo, hora.min, tzinfo=fuso)
    utc = instante.astimezone(timezone.utc)
    return f"{utc.strftime('%Y-%m-%dT%H:%M:%S')}.{utc.microsecond // 1000:03d}Z"


class Sessao:
    """Captura o cabeçalho ``Authorization`` que o próprio SPA usa.

    ``page.request`` herda os cookies do contexto, o que basta se a API for
    autenticada por cookie. Se ela exigir um bearer guardado em memória
    pela SPA (padrão comum em portais Angular do gov.br), o cookie sozinho
    daria 401 -- e o robô falharia por um motivo difícil de diagnosticar.

    A escuta abaixo resolve os dois casos sem ter de descobrir qual é: ao
    carregar a página de nova credencial, a própria SPA chama a API, e o
    cabeçalho que ela mandou é reaproveitado. Se não houver nenhum, nada é
    enviado e o fluxo segue por cookie.
    """

    def __init__(self, contexto: BrowserContext, cfg: Config) -> None:
        self._prefixo = f"{cfg.base_credencial.rstrip('/')}/api/"
        self.autorizacao: str | None = None
        contexto.on("request", self._observar)

    def _observar(self, requisicao: Any) -> None:
        # Handler de evento do Playwright: uma exceção aqui não tem quem a
        # trate e ainda polui o log a cada requisição da SPA.
        try:
            if not requisicao.url.startswith(self._prefixo):
                return
            valor = requisicao.headers.get("authorization")
        except Exception:  # noqa: BLE001 - requisição já descartada, etc.
            return
        if valor:
            self.autorizacao = valor

    def cabecalhos(self, corpo_json: bool = False) -> dict[str, str]:
        cabecalhos = {"Accept": "application/json"}
        if corpo_json:
            cabecalhos["Content-Type"] = "application/json"
        if self.autorizacao:
            cabecalhos["Authorization"] = self.autorizacao
        return cabecalhos


# ---------------------------------------------------------------------- #
# Transporte
# ---------------------------------------------------------------------- #
def _requisitar(
    page: Page,
    cfg: Config,
    metodo: str,
    url: str,
    log: logging.Logger,
    cabecalhos: dict[str, str],
    corpo: str | None = None,
) -> APIResponse:
    """Executa a chamada com retentativa e espera crescente em rate limit."""
    ultima: APIResponse | None = None
    for tentativa in range(1, cfg.tentativas_api + 1):
        try:
            if metodo == "GET":
                resposta = page.request.get(
                    url, headers=cabecalhos, timeout=cfg.timeout_padrao_ms
                )
            else:
                resposta = page.request.post(
                    url, headers=cabecalhos, data=corpo,
                    timeout=cfg.timeout_padrao_ms,
                )
        except ErroPlaywright as exc:
            raise ErroCredencial(
                f"{metodo} {url}", f"falha de transporte: {exc}"
            ) from exc

        if resposta.status not in _STATUS_RETENTAVEIS:
            return resposta

        ultima = resposta
        if tentativa == cfg.tentativas_api:
            break
        espera = cfg.espera_rate_limit_s * tentativa
        log.warning(
            "%s %s respondeu HTTP %s (tentativa %d/%d). Aguardando %.0fs.",
            AVISO, metodo, resposta.status, tentativa, cfg.tentativas_api, espera,
        )
        time.sleep(espera)

    assert ultima is not None  # o laço só sai por aqui após ao menos uma volta
    if ultima.status == 429:
        raise ErroLimiteRequisicoes(
            f"{metodo} {url}",
            f"o portal manteve HTTP 429 apos {cfg.tentativas_api} tentativa(s). "
            "Aumente 'pausa_entre_clientes_s' no config.toml e rode de novo: "
            "quem ja tem credencial e detectado na consulta e pulado.",
        )
    return ultima


def _corpo_json(resposta: APIResponse) -> Any:
    """Corpo da resposta como objeto Python, ou ``None`` se vazio/ilegível."""
    try:
        texto = resposta.text()
    except ErroPlaywright:
        return None
    if not texto or not texto.strip():
        return None
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------- #
# Consulta (idempotência)
# ---------------------------------------------------------------------- #
def consultar(
    page: Page, cfg: Config, sessao: Sessao, log: logging.Logger
) -> dict[str, Any] | None:
    """Devolve a credencial já existente do contribuinte representado, ou ``None``.

    O formato de "não existe" ainda não foi confirmado contra um CNPJ
    virgem, então o log registra status e formato bruto (nunca valores) na
    primeira execução -- é com isso que se calibra esta função, se preciso.
    """
    resposta = _requisitar(
        page, cfg, "GET", cfg.url_api_credenciais, log, sessao.cabecalhos()
    )

    if resposta.status in (404, 204):
        log.info("Nenhuma credencial existente (HTTP %s).", resposta.status)
        return None
    if not resposta.ok:
        corpo = _corpo_json(resposta)
        if _e_ausencia_de_credencial(corpo):
            log.info("Nenhuma credencial existente (HTTP %s, codigo %s).",
                     resposta.status, (corpo or {}).get("codigo"))
            return None
        raise ErroCredencial(
            "Consultar credenciais",
            f"GET respondeu HTTP {resposta.status}: {(corpo or 'sem corpo')!s:.200}",
        )

    dados = _corpo_json(resposta)
    # Guardado antes de desembrulhar a lista: é esta descrição que serve de
    # calibração para o formato real de "não existe credencial".
    formato = _descrever_formato(dados)
    log.debug("GET credenciais -> HTTP %s | formato: %s", resposta.status, formato)

    if isinstance(dados, list):
        dados = dados[0] if dados else None
    if not isinstance(dados, dict) or not dados.get("clientId"):
        log.info("Nenhuma credencial existente (HTTP %s, corpo %s).",
                 resposta.status, formato)
        return None
    return dados


def _e_ausencia_de_credencial(corpo: Any) -> bool:
    """Diz se um erro do portal significa apenas "este CNPJ não tem credencial".

    Confirmado contra o portal real em 2026-08-29, representando um CNPJ sem
    credencial: a resposta **não** é 404 nem 200 vazio, é um ``422`` com
    corpo de erro::

        {"codigo": "INT0016",
         "titulo": "Erro ao recuperar crendencial ",
         "descricao": "Não foi encontrado Credencial associada ao
                       applicationName fornecido."}

    Ou seja, o portal trata "não tem" como falha. Sem esta tradução o robô
    aborta o cliente exatamente no caso em que ele deveria agir -- o CNPJ
    virgem, que é o alvo de toda a ferramenta.

    O código é o critério primário; a descrição é reserva, porque um código
    novo para a mesma condição é mais provável que uma mudança de texto (o
    título do portal já vem com "crendencial" escrito errado, sinal de que
    essas strings não passam por revisão).
    """
    if not isinstance(corpo, dict):
        return False
    if str(corpo.get("codigo", "")).strip().upper() == "INT0016":
        return True
    descricao = normalizar(str(corpo.get("descricao", "")))
    return "nao foi encontrado" in descricao and "credencial" in descricao


def _descrever_formato(dados: Any) -> str:
    """Descreve a forma do corpo sem expor nenhum valor (o segredo mora aqui)."""
    if dados is None:
        return "vazio/null"
    if isinstance(dados, list):
        return f"lista[{len(dados)}]"
    if isinstance(dados, dict):
        return "objeto{" + ",".join(sorted(dados)) + "}"
    return type(dados).__name__


# ---------------------------------------------------------------------- #
# Criação
# ---------------------------------------------------------------------- #
def criar(
    page: Page, cfg: Config, sessao: Sessao, cliente: Cliente, log: logging.Logger
) -> dict[str, Any]:
    """Cria a Chave Secreta e devolve a credencial com ``clientId``/``clientSecret``.

    O POST não devolve o par de chaves: quem o entrega é o GET seguinte,
    sobre a mesma sessão representada.
    """
    validade = calcular_validade(cfg.validade_anos)
    corpo = json.dumps(
        {
            "consentimentoAssinaturaQualificada": cfg.consentimento_assinatura_qualificada,
            "nome": cliente.nome_credencial,
            "validade": validade,
            "idsFederadorServicos": list(cfg.servicos_padrao),
        },
        ensure_ascii=False,
    )

    log.info("Criando credencial '%s' com validade ate %s (%d servicos).",
             cliente.nome_credencial, validade, len(cfg.servicos_padrao))
    resposta = _requisitar(
        page, cfg, "POST", cfg.url_api_credenciais, log,
        sessao.cabecalhos(corpo_json=True), corpo=corpo,
    )
    if not resposta.ok:
        raise ErroCredencial(
            "Criar credencial",
            f"POST respondeu HTTP {resposta.status}: "
            f"{(_corpo_json(resposta) or 'sem corpo')!s:.200}",
        )

    credencial = consultar(page, cfg, sessao, log)
    if credencial is None or not credencial.get("clientSecret"):
        raise ErroCredencial(
            "Ler credencial criada",
            "o POST foi aceito, mas o GET seguinte nao trouxe clientId/"
            "clientSecret. A credencial pode ter sido criada no portal sem "
            "que o par de chaves tenha sido capturado -- confira na tela do "
            "cliente antes de tentar de novo.",
        )

    # clientId identifica a credencial e é útil na auditoria; clientSecret
    # nunca aparece no log (ver FiltroSegredo em log.py).
    log.info("%s Credencial criada para %s (clientId %s).",
             SUCESSO, cliente.cnpj_formatado, credencial["clientId"])
    return credencial
