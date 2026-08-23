#!/usr/bin/env python3
"""
Testa a fila local de pendências (PLANO_SAAS_AGENTE.md §5.3) e
enviar_relatorio_execucao: envio nunca pode derrubar a execução, falhas
viram pendência, pendências são reenviadas (ou descartadas se muito
antigas/corrompidas) na próxima execução.
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_client
from _fake_api import FakeAgentAPI, porta_fechada
from _harness import Suite, rodar

CHAVE_TESTE = "nfse_aaaaaaaa_" + "b" * 32

CLIENTES = [{"codigo": "0001", "nome": "Empresa Um", "cnpjMascarado": "11.111.***/**11",
            "cnpjHash": "hash1", "certificadoValidade": None, "certificadoNomeArquivo": "a.pfx"}]
METRICAS = [{"cliente_codigo": "0001", "tipo": "recebidas", "competencia": "2026-06",
            "qtd_baixadas": 2, "qtd_puladas": 0, "qtd_falhas": 0, "duracao_ms": 500}]


def _cliente_rapido(url: str) -> api_client.ApiClient:
    return api_client.ApiClient(url, CHAVE_TESTE, timeout=1,
                                sessao=api_client._sessao_com_retry(total=0))


def teste_relatorio_com_sucesso_nao_grava_pendencia(s: Suite, tmp: Path) -> None:
    pasta = tmp / "pend1"
    with FakeAgentAPI() as fake:
        cliente = _cliente_rapido(fake.url)
        api_client.enviar_relatorio_execucao(
            cliente, pasta, clientes=CLIENTES, metricas=METRICAS,
            status="Sucesso", mensagem_erro=None, log=lambda *_a: None,
        )
        rotas = [caminho for _, caminho, _ in fake.requisicoes]
        s.check(rotas == ["/api/agent/clientes", "/api/agent/execucoes",
                          "/api/agent/execucoes/exec-1/metricas", "/api/agent/execucoes/exec-1/finalizar"],
               f"ordem das chamadas: upsert -> abrir -> métricas -> finalizar (veio {rotas!r})")
    s.check(not pasta.exists() or not list(pasta.glob("*.json")),
           "sucesso não deixa nenhuma pendência gravada")


def teste_relatorio_falho_grava_pendencia_e_nao_lanca(s: Suite, tmp: Path) -> None:
    pasta = tmp / "pend2"
    cliente = _cliente_rapido(porta_fechada())  # API inacessível
    avisos = []
    try:
        api_client.enviar_relatorio_execucao(
            cliente, pasta, clientes=CLIENTES, metricas=METRICAS,
            status="Parcial", mensagem_erro="1 falha", log=avisos.append,
        )
    except Exception as e:  # nunca deveria chegar aqui
        s.check(False, f"enviar_relatorio_execucao propagou uma exceção ({e}) — nunca pode fazer isso")
        return
    s.check(True, "enviar_relatorio_execucao não lançou mesmo com a API inacessível")
    arquivos = list(pasta.glob("*.json"))
    s.check(len(arquivos) == 1, f"exatamente uma pendência gravada (achei {len(arquivos)})")
    s.check(any("tentado de novo" in a for a in avisos), "um aviso claro foi logado (não um erro silencioso)")

    conteudo = json.loads(arquivos[0].read_text(encoding="utf-8"))
    s.check(conteudo["clientes"] == CLIENTES, "pendência preserva o payload de clientes original")
    s.check(conteudo["metricas"] == METRICAS, "pendência preserva as métricas originais")
    s.check(conteudo["status"] == "Parcial", "pendência preserva o status")
    s.check("criado_em" in conteudo, "pendência tem timestamp de criação")


def teste_pendencia_e_reenviada_com_sucesso_e_apagada(s: Suite, tmp: Path) -> None:
    pasta = tmp / "pend3"
    pasta.mkdir()
    documento = {"criado_em": datetime.now(timezone.utc).isoformat(),
                "clientes": CLIENTES, "metricas": METRICAS,
                "status": "Sucesso", "mensagemErro": None}
    arquivo = pasta / "20260101T000000000000.json"
    arquivo.write_text(json.dumps(documento), encoding="utf-8")

    with FakeAgentAPI() as fake:
        cliente = _cliente_rapido(fake.url)
        api_client.reenviar_pendencias(cliente, pasta, log=lambda *_a: None)
        s.check(any(c == "/api/agent/clientes" for _, c, _ in fake.requisicoes),
               "reenviar_pendencias realmente chamou a API")
    s.check(not arquivo.exists(), "pendência enviada com sucesso é apagada")


def teste_pendencia_falha_de_novo_continua_na_fila(s: Suite, tmp: Path) -> None:
    pasta = tmp / "pend4"
    pasta.mkdir()
    documento = {"criado_em": datetime.now(timezone.utc).isoformat(),
                "clientes": CLIENTES, "metricas": METRICAS,
                "status": "Sucesso", "mensagemErro": None}
    arquivo = pasta / "20260101T000000000001.json"
    arquivo.write_text(json.dumps(documento), encoding="utf-8")

    cliente = _cliente_rapido(porta_fechada())
    api_client.reenviar_pendencias(cliente, pasta, log=lambda *_a: None)
    s.check(arquivo.exists(), "pendência que falhou de novo continua na fila (não é apagada)")


def teste_pendencia_antiga_e_descartada(s: Suite, tmp: Path) -> None:
    pasta = tmp / "pend5"
    pasta.mkdir()
    antiga = datetime.now(timezone.utc) - timedelta(days=31)
    documento = {"criado_em": antiga.isoformat(), "clientes": CLIENTES,
                "metricas": METRICAS, "status": "Sucesso", "mensagemErro": None}
    arquivo = pasta / "velha.json"
    arquivo.write_text(json.dumps(documento), encoding="utf-8")

    # nem precisa de servidor — nunca deveria tentar enviar uma pendência velha demais
    cliente = _cliente_rapido(porta_fechada())
    api_client.reenviar_pendencias(cliente, pasta, log=lambda *_a: None)
    s.check(not arquivo.exists(), "pendência com mais de 30 dias é descartada, não reenviada")


def teste_pendencia_corrompida_e_descartada(s: Suite, tmp: Path) -> None:
    pasta = tmp / "pend6"
    pasta.mkdir()
    arquivo = pasta / "corrompida.json"
    arquivo.write_text("{{{ não é json", encoding="utf-8")

    cliente = _cliente_rapido(porta_fechada())
    api_client.reenviar_pendencias(cliente, pasta, log=lambda *_a: None)
    s.check(not arquivo.exists(), "pendência corrompida é descartada, não trava a fila inteira")


def teste_reenviar_pendencias_pasta_inexistente_nao_lanca(s: Suite, tmp: Path) -> None:
    cliente = _cliente_rapido(porta_fechada())
    try:
        api_client.reenviar_pendencias(cliente, tmp / "nunca-existiu", log=lambda *_a: None)
        s.check(True, "pasta de pendências inexistente: não lança")
    except Exception as e:
        s.check(False, f"não deveria lançar ({e})")


def teste_traduzir_metricas_ignora_codigo_sem_id(s: Suite, _tmp: Path) -> None:
    linhas = api_client._traduzir_metricas(
        [{"cliente_codigo": "9999", "tipo": "recebidas", "competencia": "2026-06",
          "qtd_baixadas": 1, "qtd_puladas": 0, "qtd_falhas": 0, "duracao_ms": 10}],
        mapa_codigo_para_id={"0001": "id-0001"},  # "9999" não está no mapa
    )
    s.check(linhas == [], "métrica de um código sem id retornado pelo upsert é descartada, não quebra o envio")


def main() -> Suite:
    s = Suite("teste_pendencias")
    with tempfile.TemporaryDirectory(prefix="nfse-teste-pend-") as tmp_str:
        tmp = Path(tmp_str)
        for nome, fn in list(globals().items()):
            if nome.startswith("teste_") and callable(fn):
                print(f"-- {nome}")
                fn(s, tmp)
    return s


if __name__ == "__main__":
    rodar(main)
