#!/usr/bin/env python3
"""
Testa regras.py: validação de esquema, cache local, e o fluxo de
resolver_bundle — sobretudo que um bundle inválido NUNCA substitui um bom
(PLANO_SAAS_AGENTE.md §4 e §8).
"""

from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_client
import regras
from _fake_api import FakeAgentAPI, porta_fechada
from _harness import Suite, rodar

CHAVE_TESTE = "nfse_aaaaaaaa_" + "b" * 32


def _bundle_valido() -> dict:
    return copy.deepcopy(regras.BUNDLE_FABRICA)


# ---- validar_bundle ---------------------------------------------------
def teste_bundle_fabrica_e_valido(s: Suite, _tmp: Path) -> None:
    s.check(regras.validar_bundle(regras.BUNDLE_FABRICA) == [], "BUNDLE_FABRICA não tem erros de esquema")


def teste_validar_bundle_nao_e_objeto(s: Suite, _tmp: Path) -> None:
    s.check(regras.validar_bundle("string qualquer") != [], "conteúdo que não é dict é inválido")
    s.check(regras.validar_bundle(None) != [], "conteúdo None é inválido")
    s.check(regras.validar_bundle([1, 2, 3]) != [], "conteúdo lista é inválido")


def teste_validar_bundle_campos_obrigatorios(s: Suite, _tmp: Path) -> None:
    casos = {
        "sem portal": lambda b: b.pop("portal"),
        "urlLogin não é https": lambda b: b["portal"].__setitem__("urlLogin", "http://inseguro"),
        "urlNotas ausente": lambda b: b["portal"].pop("urlNotas"),
        "maxDiasFiltro é string": lambda b: b["portal"].__setitem__("maxDiasFiltro", "31"),
        "maxDiasFiltro é bool": lambda b: b["portal"].__setitem__("maxDiasFiltro", True),
        "maxDiasFiltro fora da faixa": lambda b: b["portal"].__setitem__("maxDiasFiltro", 9999),
        "maxDiasFiltro zero": lambda b: b["portal"].__setitem__("maxDiasFiltro", 0),
        "paramPagina vazio": lambda b: b["portal"].__setitem__("paramPagina", ""),
        "listagens.recebidas sem rota": lambda b: b["portal"]["listagens"]["recebidas"].pop("rota"),
        "listagens.recebidas.executar não é bool": lambda b: b["portal"]["listagens"]["recebidas"].__setitem__("executar", "sim"),
        "listagens.emitidas.colunas vazia": lambda b: b["portal"]["listagens"]["emitidas"].__setitem__("colunas", []),
        "listagens.emitidas.colunas com não-string": lambda b: b["portal"]["listagens"]["emitidas"].__setitem__("colunas", [1, 2]),
        "sem parsing": lambda b: b.pop("parsing"),
        "regexChave ausente": lambda b: b["parsing"].pop("regexChave"),
        "regexLinha não compila": lambda b: b["parsing"].__setitem__("regexLinha", "(("),
        "regexTotalRegistros vazio": lambda b: b["parsing"].__setitem__("regexTotalRegistros", ""),
    }
    for descricao, mutar in casos.items():
        bundle = _bundle_valido()
        mutar(bundle)
        erros = regras.validar_bundle(bundle)
        s.check(len(erros) > 0, f"validar_bundle detecta: {descricao}")


# ---- cache local --------------------------------------------------------
def teste_cache_ausente(s: Suite, tmp: Path) -> None:
    s.check(regras.carregar_cache(tmp / "nao-existe.json") is None, "sem arquivo de cache => None")
    s.check(regras.versao_em_cache(tmp / "nao-existe.json") == 0, "sem cache => versão 0")


def teste_cache_roundtrip(s: Suite, tmp: Path) -> None:
    caminho = tmp / "cache.json"
    regras.salvar_cache(caminho, 5, "2026-01-01T00:00:00Z", _bundle_valido())
    cache = regras.carregar_cache(caminho)
    s.check(cache is not None and cache["versao"] == 5, "cache round-trip preserva a versão")
    s.check(regras.versao_em_cache(caminho) == 5, "versao_em_cache lê o round-trip")


def teste_cache_corrompido_ou_invalido(s: Suite, tmp: Path) -> None:
    c1 = tmp / "corrompido.json"
    c1.write_text("{{{ não é json", encoding="utf-8")
    s.check(regras.carregar_cache(c1) is None, "JSON corrompido => None")

    c2 = tmp / "sem_chaves.json"
    c2.write_text('{"outracoisa": 1}', encoding="utf-8")
    s.check(regras.carregar_cache(c2) is None, "JSON válido mas sem 'versao'/'conteudo' => None")

    c3 = tmp / "conteudo_invalido.json"
    bundle_quebrado = _bundle_valido()
    bundle_quebrado["portal"].pop("urlLogin")
    regras.salvar_cache(c3, 2, None, bundle_quebrado)
    s.check(regras.carregar_cache(c3) is None,
           "conteúdo gravado que não passa mais na validação (ex.: editado à mão) => None, tratado como ausente")


# ---- resolver_bundle: instalação nova ------------------------------------
def teste_instalacao_nova_sem_versao_do_servidor_usa_fabrica(s: Suite, tmp: Path) -> None:
    with FakeAgentAPI() as fake:
        cliente = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        bundle = regras.resolver_bundle(cliente, None, tmp / "r1.json", log=lambda *_a: None)
        s.check(bundle == regras.BUNDLE_FABRICA, "sem versão do servidor conhecida => bundle de fábrica, sem tentar rede")
        s.check(fake.requisicoes == [], "não bateu na API quando não sabia se havia versão mais nova")


def teste_instalacao_nova_com_api_fora_do_ar_usa_fabrica(s: Suite, tmp: Path) -> None:
    cliente = api_client.ApiClient(porta_fechada(), CHAVE_TESTE, timeout=0.5,
                                   sessao=api_client._sessao_com_retry(total=0))
    bundle = regras.resolver_bundle(cliente, 5, tmp / "r2.json", log=lambda *_a: None)
    s.check(bundle == regras.BUNDLE_FABRICA,
           "instalação nova + API inacessível no primeiro contato => cai pro bundle de fábrica, não trava")


def teste_instalacao_nova_com_api_ok_baixa_e_cacheia(s: Suite, tmp: Path) -> None:
    novo_conteudo = _bundle_valido()
    novo_conteudo["portal"]["maxDiasFiltro"] = 20
    with FakeAgentAPI() as fake:
        fake.regras_resposta = {"versao": 3, "publicadaEm": "2026-02-01T00:00:00Z", "conteudo": novo_conteudo}
        cliente = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        caminho = tmp / "r3.json"
        bundle = regras.resolver_bundle(cliente, 3, caminho, log=lambda *_a: None)
        s.check(bundle["portal"]["maxDiasFiltro"] == 20, "bundle novo e válido é adotado")
        s.check(regras.versao_em_cache(caminho) == 3, "versão nova fica em cache pra próxima execução")


# ---- resolver_bundle: bundle inválido não substitui o bom (o cenário do §8) --
def teste_bundle_invalido_nao_substitui_o_bom(s: Suite, tmp: Path) -> None:
    caminho = tmp / "r4.json"
    bom = _bundle_valido()
    bom["portal"]["maxDiasFiltro"] = 31
    regras.salvar_cache(caminho, 1, "2026-01-01T00:00:00Z", bom)

    quebrado = _bundle_valido()
    quebrado["portal"].pop("urlApiXml")  # inválido de propósito
    avisos = []
    with FakeAgentAPI() as fake:
        fake.regras_resposta = {"versao": 2, "publicadaEm": "2026-03-01T00:00:00Z", "conteudo": quebrado}
        cliente = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        bundle = regras.resolver_bundle(cliente, 2, caminho, log=avisos.append)

    s.check(bundle["portal"]["maxDiasFiltro"] == 31, "continua servindo o bundle antigo (válido)")
    s.check(regras.versao_em_cache(caminho) == 1, "o cache em disco NÃO foi sobrescrito pelo bundle quebrado")
    s.check(any("inválido" in a for a in avisos), "um aviso claro foi logado sobre o bundle rejeitado")


def teste_304_mantem_cache_existente(s: Suite, tmp: Path) -> None:
    caminho = tmp / "r5.json"
    atual = _bundle_valido()
    regras.salvar_cache(caminho, 4, "2026-01-01T00:00:00Z", atual)
    with FakeAgentAPI() as fake:
        fake.regras_resposta = None  # fake devolve 304
        cliente = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        bundle = regras.resolver_bundle(cliente, 4, caminho, log=lambda *_a: None)
    s.check(bundle == atual, "versão local já é a atual (304) => usa o cache como está")


def teste_versao_local_ja_atual_nao_bate_na_api(s: Suite, tmp: Path) -> None:
    caminho = tmp / "r6.json"
    regras.salvar_cache(caminho, 7, None, _bundle_valido())
    with FakeAgentAPI() as fake:
        cliente = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        regras.resolver_bundle(cliente, 7, caminho, log=lambda *_a: None)  # servidor não tem versão mais nova
        s.check(fake.requisicoes == [], "quando a versão do servidor não é maior que a local, nem tenta buscar")


def teste_404_regra_nao_publicada_cai_para_cache_ou_fabrica(s: Suite, tmp: Path) -> None:
    with FakeAgentAPI() as fake:
        fake.regras_status = 404
        fake.regras_resposta = {"erro": "Nenhuma regra publicada"}
        cliente = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        bundle = regras.resolver_bundle(cliente, 1, tmp / "r7.json", log=lambda *_a: None)
    s.check(bundle == regras.BUNDLE_FABRICA,
           "404 (SaaS novo, nunca publicou regra) não é tratado como pânico — cai pro bundle de fábrica")


def main() -> Suite:
    s = Suite("teste_regras")
    with tempfile.TemporaryDirectory(prefix="nfse-teste-regras-") as tmp_str:
        tmp = Path(tmp_str)
        for nome, fn in list(globals().items()):
            if nome.startswith("teste_") and callable(fn):
                print(f"-- {nome}")
                fn(s, tmp)
    return s


if __name__ == "__main__":
    rodar(main)
