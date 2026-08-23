#!/usr/bin/env python3
"""
Todo o diálogo com a API do SaaS (ContabOne.Api) vive aqui, isolado do resto
da ferramenta — ver PLANO_SAAS_AGENTE.md. Quando a API estiver fora do ar
(ou nunca tiver existido, no caso de um cliente em modo legado), o ponto de
falha é um só, e a coleta em si (nfse.py) continua funcionando e testável
sem rede, exatamente como antes desta ferramenta virar um agente.

Contrato real (não o rascunho do PLANO_SAAS_API.md — checado contra o código
em ContabOne.Api nesta sessão; se algo aqui divergir do que a API faz de
verdade no futuro, o código da API manda):

  * Toda rota fica sob /api/agent/*, autenticada por header `X-Api-Key`.
  * JSON em camelCase (Program.cs configura PropertyNamingPolicy.CamelCase).
  * Os enums TipoNota e StatusExecucao NÃO usam JsonStringEnumConverter (não
    há um registrado em Program.cs) — o System.Text.Json serializa/espera
    enum como INTEIRO por padrão. Ou seja "tipo" e "status" vão como número
    (0/1/2), nunca como a string "recebidas"/"Sucesso". Ver TIPO_NOTA e
    STATUS_EXECUCAO abaixo — é fácil "consertar" isso de volta pra string
    achando que fica mais legível, sem perceber que quebra a integração.
  * POST /agent/clientes devolve, além de {atualizados, novos}, uma lista
    `clientes: [{codigo, id}]` — sem isso não haveria como descobrir o Guid
    que o servidor deu a cada cliente, e /execucoes/{id}/metricas exige esse
    Guid (FK). Esse campo foi adicionado ao endpoint nesta mesma sessão,
    junto com este arquivo — são as duas metades do mesmo contrato.

Duas ressalvas de segurança que valem registrar aqui (não no plano, que não
tinha o código real da API para conferir):

  * 401 (chave inválida/revogada, ou escritório não está Ativo) NUNCA deve
    ser tratado como "API fora do ar" — ver ApiCredenciaisInvalidas.
  * O cache de licença (_agente_cache.json) é assinado com a própria chave
    de API do agente, não com um segredo do servidor (a API real não assina
    nada) — ver avaliar_licenca(). Isso não é criptografia à prova de
    engenharia reversa (quem tem o config.toml tem a chave), só impede a
    edição trivial do cache num editor de texto. Ver comentário lá.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Versão desta ferramenta como agente — enviada em todo handshake/execução e
# comparada com `agenteVersaoMinima` (só gera aviso, nunca bloqueia; ver
# PLANO_SAAS_AGENTE.md §3.2). Bump manual a cada release que muda o contrato
# com a API. 2.1.0: o agente passa a aplicar a configuração remota do
# escritório recebida no handshake (tipos, primeira_busca_desde, pasta_saida,
# gerar_pdf) e a respeitar plano.permiteEmitidas.
VERSAO_AGENTE = "2.1.0"

TIMEOUT_PADRAO = 20.0  # segundos — API leve (JSON), não o portal (60s lá)
PENDENCIA_MAX_DIAS = 30
TOLERANCIA_OFFLINE_PADRAO = 7

NOME_CACHE_LICENCA = "_agente_cache.json"

# .NET serializa enum como inteiro por padrão (ver docstring do módulo).
TIPO_NOTA = {"recebidas": 0, "emitidas": 1}
STATUS_EXECUCAO = {"Sucesso": 0, "Parcial": 1, "Falha": 2}


# --------------------------------------------------------------------------
# Exceções
# --------------------------------------------------------------------------
class ApiError(Exception):
    """Erro genérico de API: resposta inesperada, corpo malformado, etc."""


class ApiIndisponivel(ApiError):
    """Rede fora do ar, timeout, conexão recusada, ou a API respondeu 5xx.
    Tratado como "talvez temporário" — é o único caso elegível para a
    carência offline (§3.2)."""


class ApiCredenciaisInvalidas(ApiError):
    """HTTP 401: chave errada, revogada, ou o escritório não está com status
    Ativo (a API real rejeita os três casos na camada de autenticação, antes
    mesmo do handler de handshake rodar — ver ApiKeyAuthenticationHandler.cs).

    Isto NUNCA deve ser tratado como "API fora do ar": herdar a carência
    offline aqui significaria que revogar uma chave ou suspender um
    escritório inadimplente levaria até `tolerancia_offline_dias` para fazer
    efeito na prática — o oposto do que a revogação existe para fazer."""


class RegraNaoPublicada(ApiError):
    """HTTP 404 em /agent/regras: a plataforma ainda não publicou nenhuma
    versão do bundle de regras. Situação normal de um SaaS recém-criado, não
    um erro de rede — quem chama decide o que fazer (cache local, bundle de
    fábrica, ou parar)."""


def _corpo_erro(resposta: requests.Response) -> str:
    """Extrai uma mensagem curta e segura de uma resposta de erro, sem
    assumir que o corpo é JSON (pode ser HTML de um proxy, texto puro, etc.)."""
    try:
        corpo = resposta.json()
        if isinstance(corpo, dict) and "erro" in corpo:
            return str(corpo["erro"])
        return str(corpo)[:200]
    except ValueError:
        return (resposta.text or "").strip()[:200] or "sem detalhes"


def _sessao_com_retry(total: int = 3, backoff: float = 0.5) -> requests.Session:
    """Retry com backoff exponencial em erro de conexão/timeout e 5xx.
    Inclui POST no retry: das seis chamadas deste cliente, cinco são
    upsert/idempotentes por natureza (handshake, regras, métricas, upsert de
    clientes, finalizar) — só abrir_execucao() cria uma linha nova a cada
    chamada, e mesmo lá o pior caso de um retry após timeout é uma execução
    órfã a mais no dashboard (aceito conscientemente; ver o comentário em
    ApiClient.abrir_execucao)."""
    retry = Retry(
        total=total, connect=total, read=total, status=total,
        backoff_factor=backoff,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=None,  # None = também repete POST, não só métodos idempotentes por padrão
        raise_on_status=False,
    )
    adaptador = HTTPAdapter(max_retries=retry)
    sessao = requests.Session()
    sessao.mount("https://", adaptador)
    sessao.mount("http://", adaptador)
    return sessao


# --------------------------------------------------------------------------
# Cliente HTTP
# --------------------------------------------------------------------------
class ApiClient:
    """Uma instância por execução. Guarda a própria chave (precisa dela de
    novo para assinar o cache de licença) e uma sessão com retry."""

    def __init__(self, base_url: str, chave: str, *,
                timeout: float = TIMEOUT_PADRAO,
                sessao: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.chave = chave
        self.timeout = timeout
        self._sessao = sessao or _sessao_com_retry()

    def _headers(self) -> dict[str, str]:
        return {
            "X-Api-Key": self.chave,
            "User-Agent": f"nfse-agent/{VERSAO_AGENTE}",
            "Content-Type": "application/json",
        }

    def _request(self, metodo: str, caminho: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{caminho}"
        try:
            resposta = self._sessao.request(metodo, url, headers=self._headers(),
                                            timeout=self.timeout, **kwargs)
        except requests.exceptions.RequestException as e:
            raise ApiIndisponivel(f"{metodo} {caminho}: {e}") from e

        if resposta.status_code == 401:
            raise ApiCredenciaisInvalidas(
                "Chave de API inválida, revogada, ou escritório não está ativo.")
        if resposta.status_code >= 500:
            raise ApiIndisponivel(f"{metodo} {caminho}: HTTP {resposta.status_code}")
        return resposta

    # ---- handshake (§3.2) ----
    def handshake(self, regras_versao_local: int, *,
                 versao_agente: str = VERSAO_AGENTE) -> dict[str, Any]:
        resposta = self._request("POST", "/api/agent/handshake", json={
            "versaoAgente": versao_agente,
            "regrasVersaoLocal": regras_versao_local,
            "so": sys.platform,
        })
        if not resposta.ok:
            raise ApiError(f"handshake: HTTP {resposta.status_code}: {_corpo_erro(resposta)}")
        try:
            return resposta.json()
        except ValueError as e:
            raise ApiError(f"handshake: resposta não é JSON válido: {e}") from e

    # ---- regras (§4) ----
    def get_regras(self, versao_local: int) -> dict[str, Any] | None:
        """None quando o servidor confirma que a versão local já é a atual
        (HTTP 304 — sem corpo)."""
        resposta = self._request("GET", "/api/agent/regras", params={"versao": versao_local})
        if resposta.status_code == 304:
            return None
        if resposta.status_code == 404:
            raise RegraNaoPublicada("Nenhuma regra de coleta publicada pela API ainda.")
        if not resposta.ok:
            raise ApiError(f"regras: HTTP {resposta.status_code}: {_corpo_erro(resposta)}")
        try:
            return resposta.json()
        except ValueError as e:
            raise ApiError(f"regras: resposta não é JSON válido: {e}") from e

    # ---- execuções (§5.2) ----
    def abrir_execucao(self, *, versao_agente: str = VERSAO_AGENTE) -> str:
        resposta = self._request("POST", "/api/agent/execucoes",
                                 json={"versaoAgente": versao_agente})
        if not resposta.ok:
            raise ApiError(f"abrir_execucao: HTTP {resposta.status_code}: {_corpo_erro(resposta)}")
        try:
            corpo = resposta.json()
        except ValueError as e:
            raise ApiError(f"abrir_execucao: resposta não é JSON válido: {e}") from e
        execucao_id = corpo.get("execucaoId")
        if not execucao_id:
            raise ApiError(f"abrir_execucao: resposta sem execucaoId: {corpo}")
        return str(execucao_id)

    def enviar_metricas(self, execucao_id: str, linhas: list[dict[str, Any]]) -> None:
        resposta = self._request("POST", f"/api/agent/execucoes/{execucao_id}/metricas",
                                 json={"metricas": linhas})
        if not resposta.ok:
            raise ApiError(f"enviar_metricas: HTTP {resposta.status_code}: {_corpo_erro(resposta)}")

    def finalizar_execucao(self, execucao_id: str, status: str,
                           mensagem_erro: str | None) -> None:
        if status not in STATUS_EXECUCAO:
            raise ValueError(f"status de execução desconhecido: {status!r}")
        resposta = self._request("POST", f"/api/agent/execucoes/{execucao_id}/finalizar", json={
            "status": STATUS_EXECUCAO[status],
            "mensagemErro": mensagem_erro,
        })
        if not resposta.ok:
            raise ApiError(f"finalizar_execucao: HTTP {resposta.status_code}: {_corpo_erro(resposta)}")

    # ---- clientes (§6) ----
    def upsert_clientes(self, clientes: list[dict[str, Any]]) -> dict[str, str]:
        """Devolve o mapa codigo → id (Guid, como string) que o servidor
        atribuiu a cada cliente enviado."""
        resposta = self._request("POST", "/api/agent/clientes", json={"clientes": clientes})
        if not resposta.ok:
            raise ApiError(f"upsert_clientes: HTTP {resposta.status_code}: {_corpo_erro(resposta)}")
        try:
            corpo = resposta.json()
        except ValueError as e:
            raise ApiError(f"upsert_clientes: resposta não é JSON válido: {e}") from e
        return {c["codigo"]: c["id"] for c in corpo.get("clientes", [])}


# --------------------------------------------------------------------------
# CNPJ ofuscado (§6) — puras, sem rede, espelhando ContabOne.Api/Security/CnpjHasher.cs
# byte a byte (mesma entrada → mesmo hash, senão o servidor nunca reconhece o
# mesmo cliente entre execuções).
# --------------------------------------------------------------------------
def _somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def mascarar_cnpj(cnpj: str) -> str:
    """54283546000126 → 54.283.***/**26. Só aplica a máscara em algo com
    exatamente 14 dígitos (após remover pontuação) — espelha
    CnpjHasher.Mascarar, que devolve a entrada como veio quando não tem
    14 caracteres. Nunca lança exceção: CNPJ vazio/curto/com lixo é uma
    situação normal (certificado fora do padrão de nome), não um bug."""
    d = _somente_digitos(cnpj)
    if len(d) != 14:
        return d
    return f"{d[:2]}.{d[2:5]}.***/**{d[12:]}"


def hash_cnpj(cnpj: str, chave: str) -> str:
    """HMAC-SHA256(cnpj_só_dígitos, chave) em hex minúsculo — espelha
    CnpjHasher.Hash. `chave` é o hmacCnpjKey devolvido no handshake, igual
    para todos os agentes do mesmo escritório (nunca fica no config.toml)."""
    d = _somente_digitos(cnpj)
    return hmac.new(chave.encode("utf-8"), d.encode("utf-8"), hashlib.sha256).hexdigest()


# --------------------------------------------------------------------------
# Configuração cifrada (change agente-config-minima-cifrada) — decifra o
# bloco `configuracaoCifrada` do handshake. Espelha ConfiguracaoCipher.cs
# byte a byte: mesma derivação de chave, mesmo layout de envelope, senão a
# API e o agente nunca concordam.
# --------------------------------------------------------------------------
_ROTULO_CIFRA_CONFIGURACAO = b"nfse-configuracao-v1"
_NONCE_LENGTH = 12


def _derivar_chave_configuracao(chave_api: str) -> bytes:
    """HMAC-SHA256(key=chave_api, msg=rótulo fixo) — a mesma chave que a API
    deriva a partir do valor bruto do header X-Api-Key do request de
    handshake. Nenhum segredo novo: os dois lados já conhecem `chave_api`."""
    return hmac.new(chave_api.encode("utf-8"), _ROTULO_CIFRA_CONFIGURACAO, hashlib.sha256).digest()


def decifrar_configuracao(chave_api: str, envelope_base64: str) -> dict[str, Any]:
    """Decifra `configuracaoCifrada` (base64 de nonce[12] ‖ ciphertext ‖
    tag[16], AES-256-GCM). Levanta ValueError em qualquer falha — base64
    inválido, envelope curto demais, tag que não bate (chave errada ou
    payload adulterado), ou JSON decifrado que não é um objeto. Quem chama
    trata ValueError como "configuração remota ausente" (aviso em log,
    nunca erro_fatal — mesma política de regras.validar_bundle e de
    aplicar_configuracao_remota para qualquer valor remoto inválido)."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        envelope = base64.b64decode(envelope_base64, validate=True)
        if len(envelope) < _NONCE_LENGTH + 16:
            raise ValueError("envelope cifrado curto demais")
        nonce, resto = envelope[:_NONCE_LENGTH], envelope[_NONCE_LENGTH:]
        chave = _derivar_chave_configuracao(chave_api)
        plaintext = AESGCM(chave).decrypt(nonce, resto, None)
        dados = json.loads(plaintext)
        if not isinstance(dados, dict):
            raise ValueError("payload decifrado não é um objeto JSON")
        return dados
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"falha ao decifrar configuração remota: {e}") from e


# --------------------------------------------------------------------------
# Licenciamento: handshake + carência offline + cache assinado (§3)
# --------------------------------------------------------------------------
@dataclass
class DecisaoLicenca:
    pode_executar: bool
    mensagem: str | None
    modo: str  # "online" | "offline" | "bloqueado"
    regras_versao_atual: int | None = None
    hmac_cnpj_key: str | None = None
    plano: dict[str, Any] | None = None
    dias_offline: int | None = None
    agente_versao_minima: str | None = None
    # Configuração do escritório (dicionário cru {chave: valor}) recebida no
    # handshake. None = o servidor não enviou o bloco (API antiga) — quem
    # consome trata como "sem configuração remota". Em carência offline vem do
    # cache de licença (que guarda a última resposta de handshake intacta).
    configuracao: dict[str, Any] | None = None


def _assinar_payload(payload: dict[str, Any], chave: str) -> str:
    """HMAC-SHA256 sobre o JSON canônico do payload, usando a própria chave
    de API do agente como segredo.

    Isto NÃO é uma defesa contra alguém disposto a ler o código e reproduzir
    a assinatura — a chave usada para assinar mora no mesmo config.toml que
    o usuário já pode abrir e editar, então não é um segredo que o agente
    tem e o usuário não. O único objetivo real (e o único que o plano pede —
    ver PLANO_SAAS_AGENTE.md §3.2 e §8) é impedir a edição TRIVIAL do cache
    num editor de texto: abrir o _agente_cache.json no Bloco de Notas e
    trocar "podeExecutar" para true ou adiantar o "obtida_em" para resetar a
    contagem da carência. Qualquer alteração no payload sem recalcular a
    assinatura correta faz o cache ser tratado como inexistente."""
    canonico = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hmac.new(chave.encode("utf-8"), canonico.encode("utf-8"), hashlib.sha256).hexdigest()


def salvar_cache_licenca(caminho: Path, resposta_handshake: dict[str, Any], chave: str) -> None:
    payload = {**resposta_handshake, "obtida_em": datetime.now(timezone.utc).isoformat()}
    documento = {"payload": payload, "assinatura": _assinar_payload(payload, chave)}
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(".tmp")
    tmp.write_text(json.dumps(documento, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(caminho)


def carregar_cache_licenca(caminho: Path, chave: str) -> dict[str, Any] | None:
    """None se o arquivo não existe, está corrompido, OU a assinatura não
    bate com a chave atual — um cache adulterado é tratado exatamente como
    "sem cache nenhum", nunca como um cache válido cujo conteúdo se pode
    confiar parcialmente."""
    if not caminho.exists():
        return None
    try:
        documento = json.loads(caminho.read_text(encoding="utf-8"))
        payload = documento["payload"]
        assinatura = documento["assinatura"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return None
    if not hmac.compare_digest(_assinar_payload(payload, chave), assinatura):
        return None
    return payload


def avaliar_licenca(cliente: ApiClient, regras_versao_local: int, caminho_cache: Path,
                    tolerancia_dias: int = TOLERANCIA_OFFLINE_PADRAO, *,
                    log: Callable[[str], None] = print) -> DecisaoLicenca:
    """O núcleo do licenciamento (§3.2). Tenta o handshake; se a API não
    responder, cai para o cache local assinado, mas só dentro do prazo de
    carência — e nunca para uma chave explicitamente rejeitada (401), que é
    uma negativa, não uma ausência de resposta."""
    try:
        resp = cliente.handshake(regras_versao_local)
    except ApiCredenciaisInvalidas as e:
        return DecisaoLicenca(False, str(e), "bloqueado")
    except ApiIndisponivel:
        payload = carregar_cache_licenca(caminho_cache, cliente.chave)
        if payload is None:
            return DecisaoLicenca(
                False,
                "Não foi possível contatar o servidor de licenciamento e não há um "
                "cache local válido. Verifique a conexão com a internet e tente novamente.",
                "bloqueado",
            )
        try:
            obtida_em = datetime.fromisoformat(payload["obtida_em"])
        except (KeyError, ValueError):
            return DecisaoLicenca(
                False, "Cache de licenciamento local corrompido. Verifique a conexão "
                "com a internet e tente novamente.", "bloqueado",
            )
        dias = (datetime.now(timezone.utc) - obtida_em).days
        if dias > tolerancia_dias:
            return DecisaoLicenca(
                False,
                f"Servidor de licenciamento inacessível há mais de {tolerancia_dias} "
                f"dia(s) (última validação bem-sucedida: há {dias} dia(s)). Verifique "
                f"a conexão com a internet e tente novamente.",
                "bloqueado", dias_offline=dias,
            )
        if not payload.get("podeExecutar", False):
            return DecisaoLicenca(
                False, payload.get("mensagem") or "Execução bloqueada (última verificação online).",
                "bloqueado", dias_offline=dias,
            )
        return DecisaoLicenca(
            True, f"trabalhando offline — última validação com o servidor há {dias} dia(s)",
            "offline", payload.get("regrasVersaoAtual"), payload.get("hmacCnpjKey"),
            payload.get("plano"), dias, payload.get("agenteVersaoMinima"),
            payload.get("configuracao"),
        )

    # Decifra a configuração antes de cachear — o cache guarda o dicionário
    # já decifrado (nunca o envelope cifrado), para não depender de decifrar
    # de novo justamente quando a API pode estar inacessível (design.md,
    # Decisão 4). Falha de decifragem nunca bloqueia a execução: é tratada
    # como "configuração remota ausente", com aviso em log.
    configuracao: dict[str, Any] | None = None
    cifrada = resp.get("configuracaoCifrada")
    if cifrada:
        try:
            configuracao = decifrar_configuracao(cliente.chave, cifrada)
        except ValueError as e:
            log(f"  AVISO: {e} — seguindo sem configuração remota")

    # Handshake respondeu — grava o cache sempre (mesmo bloqueado), para que
    # uma queda futura da API encontre o estado mais recente possível offline.
    resp_para_cache = {k: v for k, v in resp.items() if k != "configuracaoCifrada"}
    resp_para_cache["configuracao"] = configuracao or {}
    salvar_cache_licenca(caminho_cache, resp_para_cache, cliente.chave)

    if not resp.get("podeExecutar", False):
        return DecisaoLicenca(False, resp.get("mensagem") or "Execução não autorizada pelo servidor.",
                              "bloqueado")

    return DecisaoLicenca(True, None, "online", resp.get("regrasVersaoAtual"),
                          resp.get("hmacCnpjKey"), resp.get("plano"),
                          agente_versao_minima=resp.get("agenteVersaoMinima"),
                          configuracao=configuracao)


def _tupla_versao(v: str) -> tuple[int, ...] | None:
    """None quando a string não tem nenhum componente numérico reconhecível
    — sinaliza para versao_desatualizada() que não dá pra comparar com
    confiança (em vez de silenciosamente tratar "lixo" como "versão zero,
    logo desatualizada", o que soaria como um aviso válido sem ser um)."""
    partes = [int(m.group()) for p in (v or "").split(".") if (m := re.match(r"\d+", p))]
    return tuple(partes) if partes else None


def versao_desatualizada(atual: str, minima: str) -> bool:
    """Compara duas versões estilo semver de forma tolerante — nunca lança
    exceção por causa de um formato inesperado, e nunca "avisa" a partir de
    uma comparação que não dá pra fazer com confiança (o pior caso aceitável
    é não avisar quando deveria, nunca um aviso espúrio nem travar a
    execução por causa disso)."""
    try:
        t_atual, t_minima = _tupla_versao(atual), _tupla_versao(minima)
        if t_atual is None or t_minima is None:
            return False
        return t_atual < t_minima
    except Exception:
        return False


# --------------------------------------------------------------------------
# Métricas: tradução para o formato da API + relato de uma execução completa
# --------------------------------------------------------------------------
def _traduzir_metricas(metricas: list[dict[str, Any]],
                       mapa_codigo_para_id: dict[str, str]) -> list[dict[str, Any]]:
    linhas = []
    for m in metricas:
        cliente_id = mapa_codigo_para_id.get(m["cliente_codigo"])
        if cliente_id is None:
            continue  # upsert não devolveu id pra este código — não dá pra reportar essa linha
        linhas.append({
            "clienteId": cliente_id,
            "tipo": TIPO_NOTA[m["tipo"]],
            "competencia": m["competencia"],
            "qtdBaixadas": m["qtd_baixadas"],
            "qtdPuladas": m["qtd_puladas"],
            "qtdFalhas": m["qtd_falhas"],
            "duracaoMs": m["duracao_ms"],
        })
    return linhas


def enviar_relatorio_execucao(cliente: ApiClient, pasta_pendencias: Path, *,
                              clientes: list[dict[str, Any]],
                              metricas: list[dict[str, Any]],
                              status: str, mensagem_erro: str | None,
                              log: Callable[[str], None] = print) -> None:
    """Upsert de clientes + abrir + métricas + finalizar, como uma unidade.
    NUNCA deixa uma exceção escapar: o trabalho real (baixar as notas) já
    terminou antes desta função ser chamada, e um POST que falha não pode
    invalidar isso — mesmo princípio de `_escrever_no_arquivo` em nfse.py.
    Falhando em qualquer etapa, grava uma pendência para tentar de novo na
    próxima execução (ver reenviar_pendencias) em vez de perder o dado."""
    try:
        mapa = cliente.upsert_clientes(clientes) if clientes else {}
        execucao_id = cliente.abrir_execucao()
        linhas = _traduzir_metricas(metricas, mapa)
        if linhas:
            cliente.enviar_metricas(execucao_id, linhas)
        cliente.finalizar_execucao(execucao_id, status, mensagem_erro)
        log(f"  relatório enviado à API (execução {execucao_id}, {len(linhas)} métrica(s))")
    except Exception as e:
        log(f"  AVISO: não foi possível enviar o relatório desta execução à API ({e}) "
            f"— será tentado de novo na próxima execução")
        _salvar_pendencia(pasta_pendencias, {
            "clientes": clientes, "metricas": metricas,
            "status": status, "mensagemErro": mensagem_erro,
        })


# --------------------------------------------------------------------------
# Fila local de pendências (§5.3) — nunca perder uma métrica por causa de
# uma queda de rede no meio do envio.
# --------------------------------------------------------------------------
def _salvar_pendencia(pasta: Path, payload: dict[str, Any]) -> None:
    try:
        pasta.mkdir(parents=True, exist_ok=True)
        agora = datetime.now(timezone.utc)
        destino = pasta / f"{agora:%Y%m%dT%H%M%S%f}.json"
        documento = {"criado_em": agora.isoformat(), **payload}
        tmp = destino.with_suffix(".tmp")
        tmp.write_text(json.dumps(documento, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(destino)
    except OSError:
        pass  # nem a fila de pendências pode derrubar a execução


def reenviar_pendencias(cliente: ApiClient, pasta: Path,
                        log: Callable[[str], None] = print) -> None:
    """Tenta reenviar cada pendência gravada em execuções anteriores, mais
    antiga primeiro. Descarta silenciosamente pendências corrompidas ou com
    mais de PENDENCIA_MAX_DIAS. Nunca lança — chamado no início de main(),
    antes do relatório da execução atual, para a fila não crescer sem limite."""
    if not pasta.exists():
        return
    agora = datetime.now(timezone.utc)
    for arquivo in sorted(pasta.glob("*.json")):
        try:
            documento = json.loads(arquivo.read_text(encoding="utf-8"))
            criado_em = datetime.fromisoformat(documento["criado_em"])
        except (OSError, json.JSONDecodeError, KeyError, ValueError):
            log(f"  pendência corrompida descartada: {arquivo.name}")
            arquivo.unlink(missing_ok=True)
            continue

        idade_dias = (agora - criado_em).days
        if idade_dias > PENDENCIA_MAX_DIAS:
            log(f"  pendência de {criado_em:%d/%m/%Y} descartada (mais de "
                f"{PENDENCIA_MAX_DIAS} dias sem conseguir enviar)")
            arquivo.unlink(missing_ok=True)
            continue

        try:
            clientes = documento.get("clientes") or []
            mapa = cliente.upsert_clientes(clientes) if clientes else {}
            execucao_id = cliente.abrir_execucao()
            linhas = _traduzir_metricas(documento.get("metricas") or [], mapa)
            if linhas:
                cliente.enviar_metricas(execucao_id, linhas)
            cliente.finalizar_execucao(execucao_id, documento.get("status", "Parcial"),
                                       documento.get("mensagemErro"))
        except Exception as e:
            log(f"  pendência de {criado_em:%d/%m/%Y} ainda não pôde ser enviada ({e})")
            continue  # deixa o arquivo — tenta de novo na próxima execução

        arquivo.unlink(missing_ok=True)
        log(f"  pendência de {criado_em:%d/%m/%Y} enviada com sucesso")
