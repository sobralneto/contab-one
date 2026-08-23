#!/usr/bin/env python3
"""
Regras de coleta vindas da API (§4 do PLANO_SAAS_AGENTE.md): busca a versão
mais nova quando o handshake aponta uma, valida o esquema antes de aceitar,
cacheia localmente, e nunca deixa um bundle quebrado substituir um bom —
uma regra ruim publicada pararia todos os agentes ao mesmo tempo, e o
rollback dependeria de publicar de novo com a API já em pânico.

Este módulo não sabe nada sobre HTTP diretamente — recebe um ApiClient (de
api_client.py) já pronto e chama `get_regras` nele. Não importa nfse.py (a
direção é sempre nfse.py → regras.py, nunca o contrário), então pode ser
testado e usado de forma totalmente isolada.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

import api_client

NOME_CACHE = "_regras_cache.json"

# Snapshot dos literais que hoje vivem soltos em nfse.py (LISTAGENS,
# MAX_DIAS_FILTRO, PARAM_PAGINA, URL_NOTAS, URL_LOGIN_CERTIFICADO,
# URL_API_NFSE, e as três regex de parsing). Usado SÓ quando não há cache
# local utilizável (arquivo ausente ou corrompido/adulterado — ver
# carregar_cache) e a API não pôde ser contatada: tipicamente o primeiro
# contato de uma instalação nova, no momento exato em que a API está fora do
# ar. Nunca é a fonte "normal" de regras — é a rede de segurança de última
# instância para uma instalação não ficar órfã por causa de um mau timing.
#
# Se o portal mudar e alguém publicar uma regra nova pra compensar, ESTE
# bundle não é atualizado automaticamente — ele é literalmente "o que o
# código sabia fazer sozinho na data em que este arquivo foi escrito". Mantê
# -lo forever-desatualizado é aceitável; é só o ponto de partida de uma
# instalação limpa até ela conseguir falar com a API pela primeira vez.
BUNDLE_FABRICA: dict[str, Any] = {
    "portal": {
        "urlLogin": "https://certificado.nfse.gov.br/EmissorNacional/Certificado",
        "urlNotas": "https://www.nfse.gov.br/EmissorNacional/Notas",
        "urlApiXml": "https://sefin.nfse.gov.br/sefinnacional/nfse",
        "maxDiasFiltro": 31,
        "paramPagina": "pg",
        "pausaEntreChamadasMs": 250,
        "listagens": {
            "recebidas": {
                "rota": "Recebidas",
                "executar": True,
                "colunas": ["geracao", "emitida_por", "competencia", "preco_servico", "situacao"],
            },
            "emitidas": {
                "rota": "Emitidas",
                "executar": False,
                "colunas": ["geracao", "emitida_para", "competencia", "municipio_emissor",
                            "preco_servico", "situacao"],
            },
        },
    },
    "parsing": {
        "regexChave": r"/Notas/Download/NFSe/(\d{40,60})",
        "regexLinha": r"<tr[^>]*>(.*?)</tr>",
        "regexTotalRegistros": r"Total de\s*(\d+)\s*registros?",
    },
}


# --------------------------------------------------------------------------
# Validação de esquema — nunca lança, devolve a lista de problemas (vazia =
# válido). Um bundle malformado é dado não confiável vindo da rede, não um
# bug local para deixar estourar uma exceção.
# --------------------------------------------------------------------------
def validar_bundle(conteudo: Any) -> list[str]:
    erros: list[str] = []
    if not isinstance(conteudo, dict):
        return ["conteúdo não é um objeto JSON"]

    portal = conteudo.get("portal")
    if not isinstance(portal, dict):
        erros.append("'portal' ausente ou não é um objeto")
        portal = {}

    for campo in ("urlLogin", "urlNotas", "urlApiXml"):
        valor = portal.get(campo)
        if not isinstance(valor, str) or not valor.startswith("https://"):
            erros.append(f"portal.{campo} ausente ou não é uma URL https")

    max_dias = portal.get("maxDiasFiltro")
    if not isinstance(max_dias, int) or isinstance(max_dias, bool) or not (0 < max_dias <= 366):
        erros.append("portal.maxDiasFiltro ausente ou fora da faixa esperada (1-366)")

    if not isinstance(portal.get("paramPagina"), str) or not portal.get("paramPagina"):
        erros.append("portal.paramPagina ausente ou vazio")

    listagens = portal.get("listagens")
    if not isinstance(listagens, dict):
        erros.append("portal.listagens ausente ou não é um objeto")
        listagens = {}
    for tipo in ("recebidas", "emitidas"):
        lst = listagens.get(tipo)
        if not isinstance(lst, dict):
            erros.append(f"portal.listagens.{tipo} ausente ou não é um objeto")
            continue
        if not isinstance(lst.get("rota"), str) or not lst.get("rota"):
            erros.append(f"portal.listagens.{tipo}.rota ausente ou vazia")
        if not isinstance(lst.get("executar"), bool):
            erros.append(f"portal.listagens.{tipo}.executar ausente ou não é booleano")
        colunas = lst.get("colunas")
        if not isinstance(colunas, list) or not colunas or not all(isinstance(c, str) for c in colunas):
            erros.append(f"portal.listagens.{tipo}.colunas ausente ou inválida")

    parsing = conteudo.get("parsing")
    if not isinstance(parsing, dict):
        erros.append("'parsing' ausente ou não é um objeto")
        parsing = {}
    for campo in ("regexChave", "regexLinha", "regexTotalRegistros"):
        padrao = parsing.get(campo)
        if not isinstance(padrao, str) or not padrao:
            erros.append(f"parsing.{campo} ausente ou vazio")
            continue
        try:
            re.compile(padrao)
        except re.error as e:
            erros.append(f"parsing.{campo} não é uma expressão regular válida: {e}")

    return erros


assert not validar_bundle(BUNDLE_FABRICA), (
    "BUNDLE_FABRICA embutido não passa na própria validação — isso é um bug "
    "no código, não um problema de rede; corrija antes de distribuir."
)


# --------------------------------------------------------------------------
# Cache local (_regras_cache.json) — sem assinatura: um bundle não é fronteira
# de segurança/licenciamento (isso é o _agente_cache.json, em api_client.py),
# só protocolo de coleta. Editar este arquivo na mão só pode quebrar a
# própria coleta de quem editou.
# --------------------------------------------------------------------------
def carregar_cache(caminho: Path) -> dict[str, Any] | None:
    """None se o arquivo não existe, está corrompido, ou o conteúdo guardado
    não passa mais na validação de esquema (trata como se não houvesse cache
    — nunca usa um bundle que não confiamos mais)."""
    if not caminho.exists():
        return None
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(dados, dict) or "versao" not in dados or "conteudo" not in dados:
        return None
    if validar_bundle(dados["conteudo"]):
        return None
    return dados


def salvar_cache(caminho: Path, versao: int, publicada_em: Any, conteudo: dict[str, Any]) -> None:
    documento = {"versao": versao, "publicadaEm": publicada_em, "conteudo": conteudo}
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(".tmp")
    tmp.write_text(json.dumps(documento, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(caminho)


def versao_em_cache(caminho: Path) -> int:
    """0 quando não há cache utilizável — é exatamente o valor que faz o
    handshake pedir a versão mais nova disponível na primeira vez."""
    cache = carregar_cache(caminho)
    return cache["versao"] if cache else 0


# --------------------------------------------------------------------------
# Orquestração (§4, os 4 passos do fluxo, mais o bundle de fábrica)
# --------------------------------------------------------------------------
def resolver_bundle(cliente: "api_client.ApiClient", versao_atual_no_servidor: int | None,
                    caminho_cache: Path, log: Callable[[str], None] = print) -> dict[str, Any]:
    """Decide o bundle desta execução:

    1. Se o handshake apontou uma versão mais nova que a local, tenta baixar.
    2. Bundle baixado e válido → grava no cache, usa ele.
    3. Bundle baixado mas inválido, ou download falhou → mantém a versão em
       cache (se houver) e avisa.
    4. Sem cache utilizável e sem bundle novo → cai para o bundle de fábrica
       embutido, avisando que está rodando com regras não confirmadas
       pelo servidor.
    """
    cache = carregar_cache(caminho_cache)
    versao_local = cache["versao"] if cache else 0

    if versao_atual_no_servidor is not None and versao_atual_no_servidor > versao_local:
        try:
            resp = cliente.get_regras(versao_local)
        except api_client.ApiError as e:
            log(f"  regras: não foi possível buscar a versão {versao_atual_no_servidor} "
                f"({e}) — mantendo a versão {versao_local or '(nenhuma)'}")
            resp = None

        if resp is not None:
            erros = validar_bundle(resp.get("conteudo"))
            if erros:
                log(f"  regras: bundle versão {resp.get('versao')} recebido da API é "
                    f"inválido ({'; '.join(erros)}) — mantendo a versão "
                    f"{versao_local or '(nenhuma)'}")
            else:
                salvar_cache(caminho_cache, resp["versao"], resp.get("publicadaEm"), resp["conteudo"])
                cache = {"versao": resp["versao"], "conteudo": resp["conteudo"]}
                log(f"  regras: atualizado para a versão {resp['versao']}")

    if cache is not None:
        return cache["conteudo"]

    log("  regras: sem cache local e sem contato bem-sucedido com a API ainda "
        "— usando o bundle de fábrica embutido nesta instalação")
    return BUNDLE_FABRICA
