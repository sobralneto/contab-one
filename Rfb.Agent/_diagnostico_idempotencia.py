"""Script de diagnostico TEMPORARIO -- nao faz parte do robo.

Investiga por que GET /api/v1/credenciais respondeu "sem credencial" para
um CNPJ que ja tem uma criada. So observa trafego de rede (nenhum POST);
nao cria nada. Apagar depois de usar.
"""
import sys, json, logging
sys.path.insert(0, "src")

from playwright.sync_api import sync_playwright
from rfb_bot.settings import Config
from rfb_bot.navegador import abrir_contexto, fechar_contexto
from rfb_bot.portal import garantir_sessao, representar
from rfb_bot.credenciais import Sessao
from rfb_bot.log import configurar_logging

cfg = Config.carregar("config.toml")
cfg.fonte_clientes = "toml"
cfg.clientes = []
cfg.headless = False
cfg.fechar_navegador = False
log = configurar_logging(cfg.dir_logs)

from rfb_bot.settings import Cliente
cliente = Cliente(cnpj="07467651000135", nome_credencial="DIAGNOSTICO")

requisicoes = []

with sync_playwright() as pw:
    contexto, page = abrir_contexto(pw, cfg, log)
    contexto.on("request", lambda r: requisicoes.append((r.method, r.url)) if "credencial-api-beta" in r.url else None)

    try:
        garantir_sessao(page, cfg, log)
        representar(page, cfg, cliente, log)
    except Exception:
        page.screenshot(path="debug/_diag_falha.png", full_page=True)
        print("URL no momento da falha:", page.url)
        raise

    print("\n=== Requisicoes para credencial-api-beta apos representar + navegar ===")
    for metodo, url in requisicoes:
        print(f"{metodo:6} {url}")

    print("\n=== GET /api/v1/credenciais MANUAL (mesma pagina) ===")
    sessao = Sessao(contexto, cfg)
    r1 = page.request.get(cfg.url_api_credenciais, headers=sessao.cabecalhos())
    print("status:", r1.status)
    print("corpo:", r1.text()[:500])

    print("\n=== Recarregando a pagina nova-credencial/tls e repetindo ===")
    page.goto(cfg.url_nova_credencial, wait_until="domcontentloaded", timeout=cfg.timeout_navegacao_ms)
    page.wait_for_timeout(3000)
    print("=== Requisicoes apos reload ===")
    for metodo, url in requisicoes[len(requisicoes)-10:]:
        print(f"{metodo:6} {url}")

    sessao2 = Sessao(contexto, cfg)
    r2 = page.request.get(cfg.url_api_credenciais, headers=sessao2.cabecalhos())
    print("\nstatus (2a consulta, mesma sessao apos reload):", r2.status)
    print("corpo:", r2.text()[:500])

    fechar_contexto(contexto, cfg, log)
