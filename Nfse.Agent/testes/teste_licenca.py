#!/usr/bin/env python3
"""
Testa o núcleo do licenciamento (PLANO_SAAS_AGENTE.md §3): a carência
offline, o cache assinado, e o caso mais importante de todos — que uma
chave rejeitada (401) NUNCA herda a carência offline, mesmo com um cache
local perfeitamente válido sentado ali do lado. Ver §8.
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_client
from _fake_api import FakeAgentAPI, handshake_padrao, porta_fechada
from _harness import Suite, rodar

CHAVE_TESTE = "nfse_aaaaaaaa_" + "b" * 32


def _cliente_offline(url: str) -> api_client.ApiClient:
    return api_client.ApiClient(url, CHAVE_TESTE, timeout=0.5,
                                sessao=api_client._sessao_com_retry(total=0))


def teste_online_sucesso_propaga_campos(s: Suite, tmp: Path) -> None:
    with FakeAgentAPI() as fake:
        fake.handshake_resposta = handshake_padrao(
            regrasVersaoAtual=9, hmacCnpjKey="chave-hmac-9",
            plano={"maxClientes": 10, "permiteEmitidas": False},
        )
        cliente = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        d = api_client.avaliar_licenca(cliente, 0, tmp / "cache1.json", tolerancia_dias=7)
        s.check(d.pode_executar is True, "online + podeExecutar:true => pode_executar True")
        s.check(d.modo == "online", "online: modo == 'online'")
        s.check(d.regras_versao_atual == 9, "online: regras_versao_atual propagado")
        s.check(d.hmac_cnpj_key == "chave-hmac-9", "online: hmac_cnpj_key propagado")
        s.check(d.plano == {"maxClientes": 10, "permiteEmitidas": False}, "online: plano propagado")
        s.check((tmp / "cache1.json").exists(), "online: grava o cache local mesmo tendo respondido ao vivo")


def teste_online_bloqueado_pelo_servidor(s: Suite, tmp: Path) -> None:
    with FakeAgentAPI() as fake:
        fake.handshake_resposta = handshake_padrao(
            podeExecutar=False, status="Inadimplente",
            mensagem="Assinatura suspensa por inadimplência. Regularize para continuar.",
        )
        cliente = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        d = api_client.avaliar_licenca(cliente, 0, tmp / "cache2.json", tolerancia_dias=7)
        s.check(d.pode_executar is False, "podeExecutar:false => pode_executar False")
        s.check(d.modo == "bloqueado", "bloqueado pelo servidor: modo == 'bloqueado'")
        s.check("inadimpl" in (d.mensagem or "").lower(), "a mensagem do servidor chega até a decisão")


def teste_401_nunca_herda_carencia_mesmo_com_cache_valido(s: Suite, tmp: Path) -> None:
    """O teste mais importante deste arquivo. Um cache fresco e válido não
    pode servir de desculpa pra continuar rodando com uma chave que acabou
    de ser explicitamente rejeitada — senão revogar uma chave (ou suspender
    um escritório inadimplente) levaria até tolerancia_offline_dias pra
    surtir efeito, o que anularia o propósito da revogação."""
    caminho = tmp / "cache_401.json"
    with FakeAgentAPI() as fake:
        cliente_bom = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        d1 = api_client.avaliar_licenca(cliente_bom, 0, caminho, tolerancia_dias=7)
        s.check(d1.pode_executar is True, "pré-condição: primeiro handshake com chave válida passa")
        s.check(caminho.exists(), "pré-condição: cache válido foi gravado")

        # A partir daqui só CHAVE_TESTE é aceita — simula a chave usada
        # abaixo tendo sido revogada (formato válido, mas rejeitada no servidor).
        fake.chave_valida = CHAVE_TESTE
        cliente_revogado = api_client.ApiClient(fake.url, "nfse_bbbbbbbb_" + "c" * 32, timeout=2)
        d2 = api_client.avaliar_licenca(cliente_revogado, 0, caminho, tolerancia_dias=7)
        s.check(d2.pode_executar is False,
               "chave revogada é bloqueada AGORA, mesmo com um cache de horas atrás ainda dentro da carência")
        s.check(d2.modo == "bloqueado", "401: modo == 'bloqueado', nunca 'offline'")


def teste_offline_com_cache_valido_roda(s: Suite, tmp: Path) -> None:
    caminho = tmp / "cache3.json"
    resposta = handshake_padrao(regrasVersaoAtual=4, hmacCnpjKey="k4")
    api_client.salvar_cache_licenca(caminho, resposta, CHAVE_TESTE)

    cliente = _cliente_offline(porta_fechada())  # ninguém escutando => ApiIndisponivel
    d = api_client.avaliar_licenca(cliente, 0, caminho, tolerancia_dias=7)
    s.check(d.pode_executar is True, "API fora do ar + cache válido e recente => continua rodando")
    s.check(d.modo == "offline", "modo == 'offline'")
    s.check(d.regras_versao_atual == 4, "offline: ainda expõe regras_versao_atual do cache")
    s.check(d.dias_offline == 0, "offline: dias_offline calculado (0 pro cache recém-gravado)")


def teste_offline_com_cache_vencido_bloqueia(s: Suite, tmp: Path) -> None:
    caminho = tmp / "cache4.json"
    resposta = handshake_padrao()
    api_client.salvar_cache_licenca(caminho, resposta, CHAVE_TESTE)

    # "adianta" o relógio escrevendo obtida_em manualmente pro passado, mas
    # recalculando a assinatura certa — testa a carência, não a assinatura.
    documento = json.loads(caminho.read_text(encoding="utf-8"))
    payload = documento["payload"]
    payload["obtida_em"] = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    assinatura = api_client._assinar_payload(payload, CHAVE_TESTE)
    caminho.write_text(json.dumps({"payload": payload, "assinatura": assinatura}), encoding="utf-8")

    cliente = _cliente_offline(porta_fechada())
    d = api_client.avaliar_licenca(cliente, 0, caminho, tolerancia_dias=7)
    s.check(d.pode_executar is False, "cache com 10 dias > carência de 7 dias => bloqueia")
    s.check(d.dias_offline == 10, "dias_offline reflete a idade real do cache")


def teste_offline_com_cache_adulterado_e_tratado_como_sem_cache(s: Suite, tmp: Path) -> None:
    """O cenário do §3.2: abrir o _agente_cache.json num editor de texto e
    trocar 'podeExecutar' pra true (ou adiantar o timestamp) não pode
    funcionar — a assinatura para de bater e o cache vira, na prática, como
    se não existisse."""
    caminho = tmp / "cache5.json"
    api_client.salvar_cache_licenca(caminho, handshake_padrao(podeExecutar=False), CHAVE_TESTE)

    documento = json.loads(caminho.read_text(encoding="utf-8"))
    documento["payload"]["podeExecutar"] = True  # adulteração manual, sem recalcular a assinatura
    caminho.write_text(json.dumps(documento), encoding="utf-8")

    s.check(api_client.carregar_cache_licenca(caminho, CHAVE_TESTE) is None,
           "carregar_cache_licenca: assinatura não bate => None (cache tratado como inexistente)")

    cliente = _cliente_offline(porta_fechada())
    d = api_client.avaliar_licenca(cliente, 0, caminho, tolerancia_dias=7)
    s.check(d.pode_executar is False,
           "avaliar_licenca com cache adulterado e API fora do ar => bloqueia (não usa o valor editado)")


def teste_offline_sem_cache_nenhum_bloqueia(s: Suite, tmp: Path) -> None:
    cliente = _cliente_offline(porta_fechada())
    d = api_client.avaliar_licenca(cliente, 0, tmp / "nunca-existiu.json", tolerancia_dias=7)
    s.check(d.pode_executar is False, "sem cache e API fora do ar => bloqueia, nunca assume êxito")
    s.check(d.modo == "bloqueado", "sem cache: modo == 'bloqueado'")


def teste_offline_cache_ja_dizia_bloqueado_continua_bloqueado(s: Suite, tmp: Path) -> None:
    caminho = tmp / "cache6.json"
    api_client.salvar_cache_licenca(
        caminho, handshake_padrao(podeExecutar=False, mensagem="Conta cancelada."), CHAVE_TESTE,
    )
    cliente = _cliente_offline(porta_fechada())
    d = api_client.avaliar_licenca(cliente, 0, caminho, tolerancia_dias=7)
    s.check(d.pode_executar is False,
           "cache válido (dentro da carência) cuja última resposta já era bloqueada continua bloqueado offline")
    s.check(d.mensagem == "Conta cancelada.", "a mensagem do último handshake bem-sucedido é preservada")


def teste_cache_assinatura_muda_se_payload_muda(s: Suite, tmp: Path) -> None:
    a = api_client._assinar_payload({"x": 1}, "chave")
    b = api_client._assinar_payload({"x": 2}, "chave")
    c = api_client._assinar_payload({"x": 1}, "outra-chave")
    s.check(a != b, "assinatura muda se o conteúdo do payload muda")
    s.check(a != c, "assinatura muda se a chave muda")
    s.check(a == api_client._assinar_payload({"x": 1}, "chave"), "assinatura é determinística")


def teste_cache_roundtrip_chave_errada_nao_le(s: Suite, tmp: Path) -> None:
    caminho = tmp / "cache7.json"
    api_client.salvar_cache_licenca(caminho, handshake_padrao(), CHAVE_TESTE)
    s.check(api_client.carregar_cache_licenca(caminho, CHAVE_TESTE) is not None,
           "cache lido de volta com a chave certa")
    s.check(api_client.carregar_cache_licenca(caminho, "outra-chave-qualquer") is None,
           "cache NÃO é aceito com uma chave de API diferente da que assinou")


def teste_cache_corrompido_e_tratado_como_ausente(s: Suite, tmp: Path) -> None:
    caminho = tmp / "cache8.json"
    caminho.write_text("isto não é um JSON válido {{{", encoding="utf-8")
    s.check(api_client.carregar_cache_licenca(caminho, CHAVE_TESTE) is None,
           "JSON corrompido no cache => tratado como se não existisse, não levanta exceção")


def main() -> Suite:
    s = Suite("teste_licenca")
    with tempfile.TemporaryDirectory(prefix="nfse-teste-licenca-") as tmp_str:
        tmp = Path(tmp_str)
        for nome, fn in list(globals().items()):
            if nome.startswith("teste_") and callable(fn):
                print(f"-- {nome}")
                fn(s, tmp)
    return s


if __name__ == "__main__":
    rodar(main)
