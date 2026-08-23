#!/usr/bin/env python3
"""
Cobre a aplicação da configuração remota do escritório (bloco `configuracao`
do handshake) e o teto do plano (`permiteEmitidas`) no agente — nfse.py §6 e
§9 do PLANO_SAAS_AGENTE.md / specs handshake-agente e configuracao-persistencia.

A regra central: valor remoto inválido é descartado com aviso em log, nunca
aborta a execução (design.md, Decisão 6) — dado vindo da rede não é confiável
o bastante para matar o processo.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_client
import nfse
from _fake_api import FakeAgentAPI, handshake_padrao, porta_fechada
from _harness import Suite, rodar

CHAVE_TESTE = "nfse_aaaaaaaa_" + "b" * 32


def _config_local() -> dict:
    """Config no formato que carregar_config produz (tipos normalizado para
    lista, primeira_busca_desde como date, gerar_pdf bool)."""
    return {
        "pasta_certificados": "certificados",
        "pasta_saida": "notas",
        "tipos": ["recebidas", "emitidas"],
        "gerar_pdf": True,
        "primeira_busca_desde": date(2026, 1, 1),
        "dias_busca_padrao": 31,
        "api": {},
    }


# ---- 8.2: remota sobrescreve a local nas chaves informadas; local supre o resto
def teste_remota_sobrescreve_e_local_suprime(s: Suite, tmp: Path) -> None:
    config = _config_local()
    pasta_remota = tmp / "saida-remota"
    avisos = []
    nfse.aplicar_configuracao_remota(config, {
        "tipos": "recebidas",
        "primeira_busca_desde": "2025-06-15",
        "pasta_saida": str(pasta_remota),
        "gerar_pdf": "false",
        "dias_busca_padrao": "60",
    }, log=avisos.append)

    s.check(config["tipos"] == ["recebidas"], "tipos remoto substitui o local")
    s.check(config["primeira_busca_desde"] == date(2025, 6, 15), "data remota aplicada")
    s.check(config["pasta_saida"] == str(pasta_remota), "pasta remota aplicada")
    s.check(config["gerar_pdf"] is False, "gerar_pdf remoto aplicado")
    s.check(config["dias_busca_padrao"] == 60, "dias_busca_padrao remoto aplicado")
    s.check(pasta_remota.exists(), "pasta remota criada (validação de caminho)")
    s.check(len(avisos) == 5, "cada chave aplicada registra log")


def teste_remota_ausente_mantem_local(s: Suite, tmp: Path) -> None:
    config = _config_local()
    nfse.aplicar_configuracao_remota(config, None, log=lambda *_a: None)
    s.check(config == _config_local(), "configuracao None (API antiga) não muda nada")


def teste_remota_vazia_mantem_local(s: Suite, tmp: Path) -> None:
    config = _config_local()
    nfse.aplicar_configuracao_remota(config, {}, log=lambda *_a: None)
    s.check(config == _config_local(), "configuracao {} não muda nada")


def teste_chaves_desconhecidas_sao_ignoradas(s: Suite, tmp: Path) -> None:
    config = _config_local()
    nfse.aplicar_configuracao_remota(config, {"chave_futura": "valor"}, log=lambda *_a: None)
    s.check(config == _config_local(), "chave que o agente não conhece é ignorada (aditivo)")


# ---- 8.3: valor remoto inválido é descartado com aviso; nunca aborta
def teste_data_malformada_descartada_com_aviso(s: Suite, tmp: Path) -> None:
    for bruta in ("31/12/2025", "2025-13-01", "ontem"):
        config = _config_local()
        avisos = []
        nfse.aplicar_configuracao_remota(config, {"primeira_busca_desde": bruta},
                                         log=avisos.append)
        s.check(config["primeira_busca_desde"] == date(2026, 1, 1),
                f"data remota inválida ({bruta!r}) mantém a local")
        s.check(any("primeira_busca_desde" in a and "AVISO" in a for a in avisos),
                f"aviso em log para {bruta!r}")


def teste_tipos_invalidos_descartados_com_aviso(s: Suite, tmp: Path) -> None:
    config = _config_local()
    avisos = []
    nfse.aplicar_configuracao_remota(config, {"tipos": "recebidas,inexistente"},
                                     log=avisos.append)
    s.check(config["tipos"] == ["recebidas", "emitidas"], "tipos com chave desconhecida mantém local")
    s.check(any("tipos" in a and "AVISO" in a for a in avisos), "aviso em log")


def teste_tipos_remoto_vazio_descartado(s: Suite, tmp: Path) -> None:
    config = _config_local()
    nfse.aplicar_configuracao_remota(config, {"tipos": "  ,,"}, log=lambda *_a: None)
    s.check(config["tipos"] == ["recebidas", "emitidas"], "tipos vazio não vira lista vazia")


def teste_gerar_pdf_invalido_descartado(s: Suite, tmp: Path) -> None:
    config = _config_local()
    avisos = []
    nfse.aplicar_configuracao_remota(config, {"gerar_pdf": "sim"}, log=avisos.append)
    s.check(config["gerar_pdf"] is True, "gerar_pdf inválido mantém o local")
    s.check(any("gerar_pdf" in a and "AVISO" in a for a in avisos), "aviso em log")


def teste_dias_busca_padrao_invalido_descartado(s: Suite, tmp: Path) -> None:
    for bruto in ("quinze", "0", "-5", "3.5"):
        config = _config_local()
        avisos = []
        nfse.aplicar_configuracao_remota(config, {"dias_busca_padrao": bruto}, log=avisos.append)
        s.check(config["dias_busca_padrao"] == 31, f"dias_busca_padrao inválido ({bruto!r}) mantém o local")
        s.check(any("dias_busca_padrao" in a and "AVISO" in a for a in avisos),
                f"aviso em log para {bruto!r}")


def teste_pasta_saida_inutilizavel_descartada(s: Suite, tmp: Path) -> None:
    # Cria um ARQUIVO e tenta usar a "pasta" abaixo dele — mkdir falha com
    # OSError, o mesmo que acontece com um caminho de outra máquina.
    arquivo = tmp / "nao-e-pasta"
    arquivo.write_text("x", encoding="utf-8")
    config = _config_local()
    avisos = []
    nfse.aplicar_configuracao_remota(config, {"pasta_saida": str(arquivo / "sub")},
                                     log=avisos.append)
    s.check(config["pasta_saida"] == "notas", "pasta inutilizável mantém a local")
    s.check(any("pasta_saida" in a and "AVISO" in a for a in avisos), "aviso em log")


# ---- 8.4: flag de CLI vence a configuração remota
def teste_cli_vence_remota(s: Suite, tmp: Path) -> None:
    config = _config_local()
    config["tipos"] = ["emitidas"]  # --tipos emitidas já aplicado em main()
    avisos = []
    nfse.aplicar_configuracao_remota(config, {"tipos": "recebidas"},
                                     tipos_por_cli=True, log=avisos.append)
    s.check(config["tipos"] == ["emitidas"], "CLI vence a remota para tipos")
    s.check(not any("tipos" in a for a in avisos), "nenhum aviso de tipos — chave nem foi considerada")


def teste_cli_sem_pdf_vence_remota(s: Suite, tmp: Path) -> None:
    config = _config_local()
    nfse.aplicar_configuracao_remota(config, {"gerar_pdf": "true"},
                                     sem_pdf=True, log=lambda *_a: None)
    s.check(config["gerar_pdf"] is True, "--sem-pdf não é revertido pela remota")


# ---- 8.5: plano sem permiteEmitidas corta acima de tudo
def teste_plano_sem_emitidas_remove_emitidas(s: Suite, tmp: Path) -> None:
    config = _config_local()  # local pede os dois tipos
    avisos = []
    nfse.aplicar_limites_do_plano(config, {"maxClientes": 10, "permiteEmitidas": False},
                                  log=avisos.append)
    s.check(config["tipos"] == ["recebidas"], "emitidas descartada pelo plano")
    s.check(any("emitidas" in a and "AVISO" in a for a in avisos), "aviso em log")


def teste_plano_sem_emitidas_vence_remota_e_cli(s: Suite, tmp: Path) -> None:
    # Ordem real de main(): remota aplicada, depois o plano corta por cima.
    config = _config_local()
    config["tipos"] = ["emitidas"]  # mesmo que a CLI tivesse pedido
    nfse.aplicar_configuracao_remota(config, {"tipos": "recebidas,emitidas"},
                                     tipos_por_cli=True, log=lambda *_a: None)
    nfse.aplicar_limites_do_plano(config, {"permiteEmitidas": False}, log=lambda *_a: None)
    s.check(config["tipos"] == [], "plano corta até o que a CLI pediu")


def teste_plano_com_emitidas_nao_restringe(s: Suite, tmp: Path) -> None:
    config = _config_local()
    nfse.aplicar_limites_do_plano(config, {"maxClientes": 10, "permiteEmitidas": True},
                                  log=lambda *_a: None)
    s.check(config["tipos"] == ["recebidas", "emitidas"], "plano com emitidas não restringe")


def teste_sem_plano_nao_restringe(s: Suite, tmp: Path) -> None:
    config = _config_local()
    nfse.aplicar_limites_do_plano(config, None, log=lambda *_a: None)
    s.check(config["tipos"] == ["recebidas", "emitidas"], "handshake sem plano não restringe")


# ---- 8.6: handshake sem bloco configuracao (API antiga) — comportamento atual
def teste_handshake_sem_configuracao_mantem_local(s: Suite, tmp: Path) -> None:
    with FakeAgentAPI() as fake:
        fake.handshake_resposta = handshake_padrao(configuracao=None)  # API antiga
        cliente = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        decisao = api_client.avaliar_licenca(cliente, 0, tmp / "lic.json")
    s.check(decisao.modo == "online", "handshake normal segue online")
    s.check(decisao.configuracao is None, "configuracao None = sem remota para aplicar")


# ---- 8.7: em carência offline, a configuração usada é a do cache de licença
def teste_offline_usa_configuracao_do_cache(s: Suite, tmp: Path) -> None:
    # O cache guarda o dicionário JÁ DECIFRADO (design.md, Decisão 4) — é
    # exatamente o que avaliar_licenca() grava depois de decifrar
    # `configuracaoCifrada` no caminho online; aqui simulamos esse resultado
    # diretamente, sem passar pelo handshake de verdade.
    caminho = tmp / "lic.json"
    resposta_cacheada = {**handshake_padrao(configuracao=None),
                         "configuracao": {"tipos": "emitidas", "gerar_pdf": "false"}}
    api_client.salvar_cache_licenca(caminho, resposta_cacheada, CHAVE_TESTE)

    cliente = api_client.ApiClient(porta_fechada(), CHAVE_TESTE, timeout=0.5,
                                   sessao=api_client._sessao_com_retry(total=0))
    decisao = api_client.avaliar_licenca(cliente, 0, caminho, tolerancia_dias=7)

    s.check(decisao.modo == "offline", "API fora do ar cai na carência offline")
    s.check(decisao.configuracao == {"tipos": "emitidas", "gerar_pdf": "false"},
            "configuração do cache (última resposta de handshake) é usada offline")

    config = _config_local()
    nfse.aplicar_configuracao_remota(config, decisao.configuracao, log=lambda *_a: None)
    s.check(config["tipos"] == ["emitidas"], "configuração do cache é aplicada de fato")


# ---- 8.8: falha ao decifrar a configuração remota nunca bloqueia a execução
# (handshake-agente, requisito "Falha ao decifrar a configuração remota não
# interrompe a execução" — change agente-config-minima-cifrada)
def teste_configuracao_cifrada_com_chave_diferente_e_descartada(s: Suite, tmp: Path) -> None:
    with FakeAgentAPI() as fake:
        # Cifrado com uma chave diferente da que o ApiClient do teste usa —
        # simula chave rotacionada/incompatível entre quem cifrou e quem
        # tenta decifrar.
        fake.handshake_resposta = handshake_padrao(
            chave_api="nfse_bbbbbbbb_" + "c" * 32,
            configuracao={"tipos": "emitidas"},
        )
        cliente = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        avisos = []
        decisao = api_client.avaliar_licenca(cliente, 0, tmp / "lic-chave-errada.json", log=avisos.append)

    s.check(decisao.modo == "online", "handshake em si funciona — só a configuração não decifra")
    s.check(decisao.pode_executar, "chave de cifragem incompatível não bloqueia a execução")
    s.check(decisao.configuracao is None, "configuração não decifrável vira None")
    s.check(any("AVISO" in a and "decifrar" in a for a in avisos), "aviso em log sobre a falha de decifragem")


def teste_configuracao_cifrada_corrompida_e_descartada(s: Suite, tmp: Path) -> None:
    with FakeAgentAPI() as fake:
        fake.handshake_resposta = handshake_padrao(configuracao=None)
        fake.handshake_resposta["configuracaoCifrada"] = "isto-nao-e-base64-valido!!"
        cliente = api_client.ApiClient(fake.url, CHAVE_TESTE, timeout=2)
        avisos = []
        decisao = api_client.avaliar_licenca(cliente, 0, tmp / "lic-corrompida.json", log=avisos.append)

    s.check(decisao.modo == "online", "handshake em si funciona — só a configuração não decifra")
    s.check(decisao.pode_executar, "payload cifrado corrompido não bloqueia a execução")
    s.check(decisao.configuracao is None, "payload corrompido vira None")
    s.check(any("AVISO" in a for a in avisos), "aviso em log sobre a falha de decifragem")


def main() -> Suite:
    s = Suite("teste_configuracao_remota")
    with tempfile.TemporaryDirectory(prefix="nfse-teste-config-") as tmp_str:
        tmp = Path(tmp_str)
        for nome, fn in list(globals().items()):
            if nome.startswith("teste_") and callable(fn):
                print(f"-- {nome}")
                fn(s, tmp)
    return s


if __name__ == "__main__":
    rodar(main)
