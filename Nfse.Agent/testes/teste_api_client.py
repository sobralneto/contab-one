#!/usr/bin/env python3
"""
Testa api_client.py: as seis chamadas HTTP contra um fake local (sucesso,
401, 500, 404 em /regras, timeout, conexão recusada), a política de retry, e
as funções puras de CNPJ (mascarar_cnpj/hash_cnpj) e comparação de versão.

Ver PLANO_SAAS_AGENTE.md §8. Cem por cento offline — localhost apenas.
"""

from __future__ import annotations

import hashlib
import hmac
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_client
from _fake_api import FakeAgentAPI, ServidorBuracoNegro, handshake_padrao, porta_fechada
from _harness import Suite, rodar

CHAVE_TESTE = "nfse_aaaaaaaa_" + "b" * 32


def _cliente_rapido(url: str, *, timeout: float = 2.0) -> api_client.ApiClient:
    """Sessão sem retry — os testes de caminho de erro não precisam esperar
    o backoff da política de produção pra provar que o erro certo é
    levantado; isso é testado à parte, por introspecção (ver teste_retry)."""
    sessao = api_client._sessao_com_retry(total=0)
    return api_client.ApiClient(url, CHAVE_TESTE, timeout=timeout, sessao=sessao)


def teste_handshake_sucesso(s: Suite) -> None:
    with FakeAgentAPI() as fake:
        fake.handshake_resposta = handshake_padrao(regrasVersaoAtual=7)
        cliente = _cliente_rapido(fake.url)
        resp = cliente.handshake(regras_versao_local=3, versao_agente="2.0.0")

        s.check(resp["podeExecutar"] is True, "handshake: podeExecutar propagado")
        s.check(resp["regrasVersaoAtual"] == 7, "handshake: regrasVersaoAtual propagado")
        s.check(resp["hmacCnpjKey"] == "chave-hmac-de-teste", "handshake: hmacCnpjKey propagado")

        metodo, caminho, corpo = fake.requisicoes[-1]
        s.check(metodo == "POST" and caminho == "/api/agent/handshake", "handshake: rota correta")
        s.check(corpo == {"versaoAgente": "2.0.0", "regrasVersaoLocal": 3, "so": sys.platform},
               "handshake: corpo da requisição no formato esperado (camelCase, 'so' = sys.platform)")


def teste_handshake_401(s: Suite) -> None:
    with FakeAgentAPI() as fake:
        # "nfse_lixo_invalido" tem o formato certo mas não é a chave
        # cadastrada no fake — espelha uma chave revogada/nunca existiu na
        # API real (formato válido, só não encontrada no banco).
        fake.chave_valida = CHAVE_TESTE
        cliente = api_client.ApiClient(fake.url, "nfse_lixo_invalido", timeout=2,
                                       sessao=api_client._sessao_com_retry(total=0))
        s.check_raises(api_client.ApiCredenciaisInvalidas, lambda: cliente.handshake(0),
                       "handshake com chave inválida levanta ApiCredenciaisInvalidas (nunca ApiIndisponivel)")


def teste_handshake_500(s: Suite) -> None:
    with FakeAgentAPI() as fake:
        fake.handshake_status = 500
        cliente = _cliente_rapido(fake.url)
        s.check_raises(api_client.ApiIndisponivel, lambda: cliente.handshake(0),
                       "handshake com HTTP 500 levanta ApiIndisponivel")


def teste_regras_200_304_404(s: Suite) -> None:
    with FakeAgentAPI() as fake:
        cliente = _cliente_rapido(fake.url)

        fake.regras_resposta = {"versao": 5, "publicadaEm": "2026-01-01T00:00:00Z",
                                "conteudo": {"portal": {}, "parsing": {}}}
        resp = cliente.get_regras(3)
        s.check(resp is not None and resp["versao"] == 5, "regras: 200 devolve o bundle")

        fake.regras_resposta = None  # o fake devolve 304 quando não setado
        s.check(cliente.get_regras(5) is None, "regras: 304 devolve None (sem levantar)")

        fake.regras_status = 404
        s.check_raises(api_client.RegraNaoPublicada, lambda: cliente.get_regras(0),
                       "regras: 404 levanta RegraNaoPublicada (não ApiIndisponivel — não é rede fora do ar)")


def teste_execucao_metricas_finalizar_tipos_como_inteiro(s: Suite) -> None:
    """O ponto central deste teste: TipoNota/StatusExecucao vão como inteiro
    no JSON, não como string — não há JsonStringEnumConverter registrado na
    API (conferido em Program.cs nesta sessão). Ver o comentário no topo de
    api_client.py."""
    with FakeAgentAPI() as fake:
        cliente = _cliente_rapido(fake.url)
        execucao_id = cliente.abrir_execucao(versao_agente="2.0.0")
        s.check(execucao_id == "exec-1", "abrir_execucao: devolve o execucaoId do corpo")

        cliente.enviar_metricas(execucao_id, [
            {"clienteId": "id-0001", "tipo": api_client.TIPO_NOTA["recebidas"], "competencia": "2026-06",
             "qtdBaixadas": 3, "qtdPuladas": 1, "qtdFalhas": 0, "duracaoMs": 1200},
        ])
        _, _, corpo_metricas = fake.requisicoes[-1]
        tipo_enviado = corpo_metricas["metricas"][0]["tipo"]
        s.check(tipo_enviado == 0 and isinstance(tipo_enviado, int),
               f"metricas: 'tipo' vai como inteiro 0 (recebidas), não 'recebidas' (veio {tipo_enviado!r})")

        cliente.finalizar_execucao(execucao_id, "Parcial", "algumas notas falharam")
        _, _, corpo_final = fake.requisicoes[-1]
        s.check(corpo_final["status"] == 1 and isinstance(corpo_final["status"], int),
               f"finalizar: 'status' vai como inteiro 1 (Parcial), não a string (veio {corpo_final['status']!r})")
        s.check(corpo_final["mensagemErro"] == "algumas notas falharam", "finalizar: mensagemErro propagada")


def teste_upsert_clientes_mapa_codigo_id(s: Suite) -> None:
    with FakeAgentAPI() as fake:
        cliente = _cliente_rapido(fake.url)
        mapa = cliente.upsert_clientes([
            {"codigo": "0001", "nome": "Empresa Um", "cnpjMascarado": "11.111.***/**11",
             "cnpjHash": "hash1", "certificadoValidade": "2027-01-01", "certificadoNomeArquivo": "a.pfx"},
            {"codigo": "0002", "nome": "Empresa Dois", "cnpjMascarado": "22.222.***/**22",
             "cnpjHash": "hash2", "certificadoValidade": None, "certificadoNomeArquivo": "b.pfx"},
        ])
        s.check(mapa == {"0001": "id-0001", "0002": "id-0002"},
               f"upsert_clientes: devolve o mapa codigo->id do servidor (veio {mapa!r})")


def teste_conexao_recusada(s: Suite) -> None:
    cliente = _cliente_rapido(porta_fechada(), timeout=2)
    s.check_raises(api_client.ApiIndisponivel, lambda: cliente.handshake(0),
                   "conexão recusada levanta ApiIndisponivel")


def teste_timeout(s: Suite) -> None:
    with ServidorBuracoNegro() as buraco:
        cliente = _cliente_rapido(buraco.url, timeout=0.3)
        inicio = time.monotonic()
        s.check_raises(api_client.ApiIndisponivel, lambda: cliente.handshake(0),
                       "timeout de leitura levanta ApiIndisponivel")
        s.check(time.monotonic() - inicio < 5,
               "timeout: falha rápido (não ficou preso esperando pra sempre)")


def teste_politica_de_retry_configurada(s: Suite) -> None:
    """Não exercita o retry de verdade (seria lento) — só confirma que a
    sessão padrão está configurada como o plano pede (§7 Fase 1): retry com
    backoff em erro de conexão/timeout/5xx, inclusive em POST."""
    sessao = api_client._sessao_com_retry()
    adaptador = sessao.get_adapter("https://qualquercoisa.example")
    retry = adaptador.max_retries
    s.check(retry.total == 3, "retry: total configurado (3 por padrão)")
    s.check(retry.backoff_factor == 0.5, "retry: backoff configurado (0.5 por padrão)")
    s.check(500 in retry.status_forcelist and 503 in retry.status_forcelist,
           "retry: 5xx está na lista de status que disparam retry")
    s.check(retry.allowed_methods is None, "retry: POST também é tentado de novo (não só métodos idempotentes)")


def teste_user_agent_versionado(s: Suite) -> None:
    with FakeAgentAPI() as fake:
        cliente = _cliente_rapido(fake.url)
        cliente.handshake(0)
        headers = cliente._headers()
        s.check(headers["User-Agent"] == f"nfse-agent/{api_client.VERSAO_AGENTE}",
               f"User-Agent inclui a versão do agente (veio {headers['User-Agent']!r})")
        s.check(headers["X-Api-Key"] == CHAVE_TESTE, "X-Api-Key: a chave configurada vai no header")


# ---- CNPJ (§6) -------------------------------------------------------------
def teste_mascarar_cnpj(s: Suite) -> None:
    s.check(api_client.mascarar_cnpj("54283546000126") == "54.283.***/**26",
           "mascarar_cnpj: caso normal, só dígitos")
    s.check(api_client.mascarar_cnpj("54.283.546/0001-26") == "54.283.***/**26",
           "mascarar_cnpj: tolera pontuação (remove antes de mascarar)")
    s.check(api_client.mascarar_cnpj("") == "", "mascarar_cnpj: vazio devolve vazio, não lança")
    s.check(api_client.mascarar_cnpj("123") == "123", "mascarar_cnpj: CNPJ curto devolve como veio (só dígitos)")
    s.check(api_client.mascarar_cnpj("1234567890123456789") == "1234567890123456789",
           "mascarar_cnpj: CNPJ longo demais também devolve como veio, não trunca nem lança")


def teste_hash_cnpj(s: Suite) -> None:
    esperado = hmac.new(b"chave-x", b"54283546000126", hashlib.sha256).hexdigest()
    s.check(api_client.hash_cnpj("54283546000126", "chave-x") == esperado,
           "hash_cnpj: HMAC-SHA256(cnpj, chave) em hex minúsculo — espelha CnpjHasher.Hash")
    s.check(api_client.hash_cnpj("54.283.546/0001-26", "chave-x") == esperado,
           "hash_cnpj: tolera pontuação (mesmo hash com ou sem máscara)")
    s.check(api_client.hash_cnpj("54283546000126", "chave-x") == api_client.hash_cnpj("54283546000126", "chave-x"),
           "hash_cnpj: estável entre chamadas (mesma entrada, mesmo resultado)")
    s.check(api_client.hash_cnpj("54283546000126", "chave-x") != api_client.hash_cnpj("54283546000126", "chave-y"),
           "hash_cnpj: chave diferente produz hash diferente")
    s.check(api_client.hash_cnpj("", "chave-x") == hmac.new(b"chave-x", b"", hashlib.sha256).hexdigest(),
           "hash_cnpj: CNPJ vazio não lança, produz o HMAC de uma string vazia")


def teste_versao_desatualizada(s: Suite) -> None:
    s.check(api_client.versao_desatualizada("1.9.0", "2.0.0") is True, "1.9.0 < 2.0.0")
    s.check(api_client.versao_desatualizada("2.0.0", "2.0.0") is False, "2.0.0 == 2.0.0 não é desatualizada")
    s.check(api_client.versao_desatualizada("2.1.0", "2.0.0") is False, "2.1.0 > 2.0.0 não é desatualizada")
    # Um lado ilegível = não dá pra comparar com confiança => não avisa, em
    # nenhuma das duas direções (nunca lança, e nunca finge saber a resposta).
    s.check(api_client.versao_desatualizada("2.0.0", "lixo-do-servidor") is False,
           "'mínima' malformada (dado de rede não confiável) não gera aviso espúrio")
    s.check(api_client.versao_desatualizada("lixo", "2.0.0") is False,
           "'atual' malformada também não gera aviso espúrio (mesmo não sendo o caso realista)")


def main() -> Suite:
    s = Suite("teste_api_client")
    for nome, fn in list(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            print(f"-- {nome}")
            fn(s)
    return s


if __name__ == "__main__":
    rodar(main)
