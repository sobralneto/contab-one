#!/usr/bin/env python3
"""
Fixture compartilhada pelos testes desta pasta — NÃO é um arquivo de teste
(não roda nada sozinho, `executar_tudo.py` o ignora de propósito). Implementa
o suficiente do contrato real de /api/agent/* (ContabOne.Api/Features/Agent/
AgentEndpoints.cs) num http.server local, pra exercitar api_client.py e
regras.py sem precisar de um Postgres/dotnet de verdade rodando.

Continua com o espírito das suítes antigas descritas em HANDOFF.md: cem por
cento offline, localhost apenas, sem exigir nenhum serviço externo.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import api_client

# Mesma chave literal que todo teste_*.py desta pasta usa para o próprio
# ApiClient — precisa ser a mesma que cifra aqui, senão avaliar_licenca()
# nunca consegue decifrar de volta o que o fake "mandou".
CHAVE_TESTE_PADRAO = "nfse_aaaaaaaa_" + "b" * 32


def _cifrar_configuracao(chave_api: str, configuracao: dict) -> str:
    """Espelha ConfiguracaoCipher.Cifrar (ContabOne.Api) e
    api_client.decifrar_configuracao: AES-256-GCM, envelope
    base64(nonce[12] ‖ ciphertext ‖ tag). Só existe aqui — o agente de
    verdade nunca cifra, só decifra; é a API real quem cifra em produção."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    chave = api_client._derivar_chave_configuracao(chave_api)
    nonce = os.urandom(12)
    ciphertext = AESGCM(chave).encrypt(nonce, json.dumps(configuracao).encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def handshake_padrao(chave_api: str = CHAVE_TESTE_PADRAO, **overrides) -> dict:
    # `configuracao=None` simula a API antiga, que não envia o campo — o
    # agente trata ausência como "sem configuração remota" (compatibilidade
    # para trás, design.md §7 / requisito "Falha ao decifrar..." de
    # handshake-agente). `configuracao=...` (dict) é cifrado com chave_api
    # antes de entrar na resposta, como a API real faz.
    configuracao = overrides.pop("configuracao", {})
    base = {
        "escritorio": {"id": "11111111-1111-1111-1111-111111111111", "nome": "Escritório Teste"},
        "status": "Ativo",
        "podeExecutar": True,
        "mensagem": None,
        "plano": {"maxClientes": 50, "permiteEmitidas": True},
        "regrasVersaoAtual": 1,
        "agenteVersaoMinima": "2.0.0",
        "hmacCnpjKey": "chave-hmac-de-teste",
    }
    if configuracao is not None:
        base["configuracaoCifrada"] = _cifrar_configuracao(chave_api, configuracao)
    base.update(overrides)
    return base


class FakeAgentAPI:
    """
        with FakeAgentAPI() as api:
            cliente = api_client.ApiClient(api.url, "nfse_aaaaaaaa_" + "b" * 32, timeout=2)
            ...
            print(api.requisicoes)  # [(metodo, caminho, corpo_json), ...]
    """

    def __init__(self):
        self.handshake_resposta: dict | None = handshake_padrao()
        self.handshake_status = 200
        self.regras_status: int | None = None  # None => decide sozinho (304 se regras_resposta é None)
        self.regras_resposta: dict | None = None
        self.clientes_resposta: dict | None = None  # None => monta upsert automático
        # None = aceita qualquer chave com o formato "nfse_..." (default
        # permissivo, bom pros testes de caminho feliz); setar para uma
        # chave específica simula "só esta chave está cadastrada" — qualquer
        # outra (mesmo com o formato certo) leva 401, como a API de verdade
        # faz para uma chave com formato válido mas não encontrada no banco.
        self.chave_valida: str | None = None
        self.requisicoes: list[tuple[str, str, dict | None]] = []
        self._contador_execucao = 0
        self._servidor: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    # -- ciclo de vida --------------------------------------------------
    def iniciar(self) -> "FakeAgentAPI":
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_a):  # silencia o log padrão no stdout do teste
                pass

            def _corpo(self) -> dict | None:
                tam = int(self.headers.get("Content-Length", 0) or 0)
                bruto = self.rfile.read(tam) if tam else b""
                return json.loads(bruto) if bruto else None

            def _responder(self, status: int, corpo: dict | None = None) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                if corpo is not None:
                    self.wfile.write(json.dumps(corpo).encode("utf-8"))

            def do_POST(self):
                self._rotear("POST")

            def do_GET(self):
                self._rotear("GET")

            def _rotear(self, metodo: str) -> None:
                partes = urlsplit(self.path)
                caminho = partes.path
                query = parse_qs(partes.query)
                corpo = self._corpo() if metodo == "POST" else None
                fake.requisicoes.append((metodo, caminho, corpo))

                chave = self.headers.get("X-Api-Key", "")
                chave_ok = (chave.startswith("nfse_") if fake.chave_valida is None
                           else chave == fake.chave_valida)
                if not chave_ok:
                    self._responder(401)
                    return

                if metodo == "POST" and caminho == "/api/agent/handshake":
                    self._responder(fake.handshake_status, fake.handshake_resposta)
                    return

                if metodo == "GET" and caminho == "/api/agent/regras":
                    if fake.regras_status is not None:
                        self._responder(fake.regras_status, fake.regras_resposta)
                        return
                    if fake.regras_resposta is None:
                        self._responder(304)
                        return
                    self._responder(200, fake.regras_resposta)
                    return

                if metodo == "POST" and caminho == "/api/agent/execucoes":
                    fake._contador_execucao += 1
                    self._responder(200, {"execucaoId": f"exec-{fake._contador_execucao}"})
                    return

                if metodo == "POST" and caminho.startswith("/api/agent/execucoes/") \
                        and caminho.endswith("/metricas"):
                    qtd = len((corpo or {}).get("metricas", []))
                    self._responder(200, {"recebidas": qtd})
                    return

                if metodo == "POST" and caminho.startswith("/api/agent/execucoes/") \
                        and caminho.endswith("/finalizar"):
                    self._responder(200, {"status": "ok"})
                    return

                if metodo == "POST" and caminho == "/api/agent/clientes":
                    if fake.clientes_resposta is not None:
                        self._responder(200, fake.clientes_resposta)
                        return
                    lista = (corpo or {}).get("clientes", [])
                    mapeados = [{"codigo": c["codigo"], "id": f"id-{c['codigo']}"} for c in lista]
                    self._responder(200, {"atualizados": 0, "novos": len(lista), "clientes": mapeados})
                    return

                self._responder(404, {"erro": "rota desconhecida no fake"})

        self._servidor = HTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._servidor.serve_forever, daemon=True)
        self._thread.start()
        return self

    def parar(self) -> None:
        if self._servidor is not None:
            self._servidor.shutdown()
            self._servidor.server_close()

    @property
    def url(self) -> str:
        assert self._servidor is not None, "chame iniciar() primeiro"
        return f"http://127.0.0.1:{self._servidor.server_port}"

    def __enter__(self) -> "FakeAgentAPI":
        return self.iniciar()

    def __exit__(self, *_exc) -> None:
        self.parar()


def porta_fechada() -> str:
    """URL de uma porta local que ninguém está escutando — conexão recusada
    quase instantânea, sem precisar esperar timeout."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    porta = s.getsockname()[1]
    s.close()
    return f"http://127.0.0.1:{porta}"


class ServidorBuracoNegro:
    """Aceita a conexão TCP mas nunca responde nada — força um timeout de
    leitura no cliente em vez de uma recusa de conexão. Usado só no teste de
    timeout; combine sempre com um `timeout=` curto no ApiClient do teste."""

    def __init__(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.listen(1)
        self._parar = False
        self._thread = threading.Thread(target=self._aceitar_e_ignorar, daemon=True)
        self._thread.start()

    def _aceitar_e_ignorar(self) -> None:
        self._socket.settimeout(0.2)
        while not self._parar:
            try:
                conn, _ = self._socket.accept()
                conn.settimeout(5)
                try:
                    conn.recv(65536)  # lê o request e não responde nada
                except OSError:
                    pass
            except socket.timeout:
                continue
            except OSError:
                break

    @property
    def url(self) -> str:
        porta = self._socket.getsockname()[1]
        return f"http://127.0.0.1:{porta}"

    def parar(self) -> None:
        self._parar = True
        try:
            self._socket.close()
        except OSError:
            pass

    def __enter__(self) -> "ServidorBuracoNegro":
        return self

    def __exit__(self, *_exc) -> None:
        self.parar()
