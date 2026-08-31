"""Orquestração: CLI, laço por cliente e resumo da execução.

Um único navegador serve todo o lote: a identidade é uma só (o certificado
do escritório) e o que muda entre clientes é apenas a representação dentro
do portal. Cada cliente fica isolado em try/except -- a falha de um não
interrompe os demais -- e o código de saída reflete o resultado agregado,
o que permite ao Agendador de Tarefas disparar alerta.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Any

from playwright.sync_api import BrowserContext, Error as ErroPlaywright, Page, sync_playwright

from . import __version__
from .credenciais import Sessao, consultar, criar
from .erros import ErroCnpjInvalido, ErroEtapa, ErroRobo, ErroSemProcuracao, ErroSessao
from .fontes import carregar_clientes
from .localizadores import clicar_se_existir
from .log import AVISO, FALHA, SUCESSO, configurar_logging, obter_logger, salvar_evidencia
from .navegador import (
    abrir_contexto,
    fechar_contexto,
    limpar_perfil,
    pagina_ativa,
    resumo_ambiente,
)
from .portal import garantir_sessao, representar
from .saida import (
    STATUS_CNPJ_INVALIDO,
    STATUS_CRIADA,
    STATUS_ERRO,
    STATUS_JA_POSSUIA,
    STATUS_SEM_PROCURACAO,
    STATUS_SIMULADO,
    preparar_csv,
    registrar,
)
from .settings import FONTE_EXCEL, MODOS_CERTIFICADO, RAIZ_PADRAO, Cliente, Config

# Códigos de saída para o agendador.
SAIDA_OK = 0
SAIDA_PARCIAL = 1
SAIDA_TOTAL = 2
SAIDA_CONFIG = 3


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rfb-bot",
        description=(
            "Gera credenciais (Chaves Secretas) no Portal Nacional de Tributação "
            "sobre Consumo para cada CNPJ representado como Procurador."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c", "--config", default="config.toml",
        help="Caminho do TOML de configuração.",
    )
    parser.add_argument(
        "--cliente", action="append", metavar="CNPJ",
        help="Processa apenas este CNPJ (repetível).",
    )
    parser.add_argument(
        "--clientes-arquivo", metavar="XLSX",
        help=(
            "Le a lista de clientes desta planilha (coluna A=CNPJ, B=Nome) "
            "em vez da fonte configurada em --config."
        ),
    )
    parser.add_argument(
        "-o", "--saida", metavar="CSV",
        help="Sobrescreve o caminho do CSV de saída.",
    )
    parser.add_argument(
        "--modo-certificado", choices=MODOS_CERTIFICADO,
        help="Sobrescreve o modo de fornecimento do certificado.",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Executa sem interface. Incompatível com o modo 'manual'.",
    )
    parser.add_argument(
        "--manter-aberto", action="store_true",
        help="Não fecha o navegador ao final (útil para inspeção).",
    )
    parser.add_argument(
        "--login", action="store_true",
        help=(
            "Somente autentica e grava a sessão no perfil persistente. "
            "Use na primeira execução, com o navegador visível."
        ),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help=(
            "Representa e consulta as credenciais existentes, mas não cria "
            "nenhuma. Use para conferir quem já tem chave antes do lote real."
        ),
    )
    parser.add_argument(
        "--dump", action="store_true",
        help="Grava screenshot + HTML do portal para calibrar seletores, e encerra.",
    )
    parser.add_argument(
        "--limpar-perfil", action="store_true",
        help="Apaga o perfil do Chrome (força novo login) e encerra.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Log em DEBUG.")
    parser.add_argument(
        "--sem-pausa", action="store_true",
        help="Não espera ENTER ao terminar (use no Agendador de Tarefas).",
    )
    parser.add_argument("--version", action="version", version=f"rfb-bot {__version__}")
    return parser


def aplicar_argumentos(cfg: Config, args: argparse.Namespace) -> None:
    """Sobrepõe a configuração de arquivo com os argumentos da linha de comando."""
    if args.saida:
        cfg.saida_csv = args.saida
    if args.modo_certificado:
        cfg.modo_certificado = args.modo_certificado
    if args.headless:
        cfg.headless = True
    if args.manter_aberto:
        cfg.fechar_navegador = False
    cfg.validar()


# ---------------------------------------------------------------------- #
# Cliente
# ---------------------------------------------------------------------- #
def processar_cliente(
    page: Page,
    cfg: Config,
    sessao: Sessao,
    cliente: Cliente,
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Representa o cliente, garante a credencial e grava a linha do CSV.

    O CSV é escrito **dentro** desta função, e não ao final do lote: a
    credencial já existe no portal no instante em que o POST retorna, e um
    lote interrompido depois disso deixaria o operador sem o segredo de uma
    chave que já foi emitida.
    """
    log = obter_logger(cliente.cnpj_digitos)
    inicio = time.monotonic()
    resultado: dict[str, Any] = {
        "cnpj": cliente.cnpj_formatado,
        "nome_credencial": cliente.nome_credencial,
        "status": STATUS_ERRO,
        "detalhe": "",
    }

    log.info("-" * 66)
    log.info("Cliente: %s | %s", cliente.nome_credencial, cliente.cnpj_formatado)

    try:
        representar(page, cfg, cliente, log)

        existente = consultar(page, cfg, sessao, log)
        if existente is not None:
            resultado["status"] = STATUS_JA_POSSUIA
            resultado["detalhe"] = f"clientId {existente['clientId']}"
            log.info("%s Ja possui credencial (clientId %s): pulado.",
                     AVISO, existente["clientId"])
            registrar(
                cfg.caminho_csv, log,
                cnpj=cliente.cnpj_formatado,
                nome_credencial=cliente.nome_credencial,
                status=STATUS_JA_POSSUIA,
                client_id=existente["clientId"],
                observacao="credencial preexistente, nao sobrescrita",
            )
            return resultado

        if args.dry_run:
            resultado["status"] = STATUS_SIMULADO
            log.info("%s --dry-run: criacao da credencial nao executada.", AVISO)
            registrar(
                cfg.caminho_csv, log,
                cnpj=cliente.cnpj_formatado,
                nome_credencial=cliente.nome_credencial,
                status=STATUS_SIMULADO,
                observacao="sem credencial; criacao suprimida por --dry-run",
            )
            return resultado

        credencial = criar(page, cfg, sessao, cliente, log)
        resultado["status"] = STATUS_CRIADA
        resultado["detalhe"] = f"clientId {credencial['clientId']}"
        registrar(
            cfg.caminho_csv, log,
            cnpj=cliente.cnpj_formatado,
            nome_credencial=cliente.nome_credencial,
            status=STATUS_CRIADA,
            client_id=credencial["clientId"],
            client_secret=credencial["clientSecret"],
        )

    except ErroSemProcuracao as exc:
        # Condição de negócio esperada: o escritório não tem (mais)
        # procuração para este CNPJ. Reportada com status próprio para não
        # soar como robô quebrado, mas com a mensagem exata do portal.
        resultado["status"] = STATUS_SEM_PROCURACAO
        resultado["detalhe"] = exc.mensagem_portal
        log.warning("%s Sem procuracao para %s: %s",
                    AVISO, cliente.cnpj_formatado, exc.mensagem_portal)
        registrar(
            cfg.caminho_csv, log,
            cnpj=cliente.cnpj_formatado,
            nome_credencial=cliente.nome_credencial,
            status=STATUS_SEM_PROCURACAO,
            observacao=exc.mensagem_portal,
        )
    except ErroCnpjInvalido as exc:
        # Também condição de dado, não falha do robô: a linha da planilha
        # tem um CNPJ que o próprio portal rejeita (dígito verificador
        # errado ou inexistente). Status próprio para não misturar com
        # "sem procuracao" -- o contador precisa corrigir a planilha, não
        # renovar procuração nenhuma.
        resultado["status"] = STATUS_CNPJ_INVALIDO
        resultado["detalhe"] = exc.mensagem_portal
        log.warning("%s CNPJ invalido para %s: %s",
                    AVISO, cliente.cnpj_formatado, exc.mensagem_portal)
        registrar(
            cfg.caminho_csv, log,
            cnpj=cliente.cnpj_formatado,
            nome_credencial=cliente.nome_credencial,
            status=STATUS_CNPJ_INVALIDO,
            observacao=exc.mensagem_portal,
        )
    except ErroEtapa as exc:
        resultado["detalhe"] = f"{exc.etapa}: {exc.detalhe}"
        log.error("%s Cliente %s interrompido na etapa '%s': %s",
                  FALHA, cliente.cnpj_formatado, exc.etapa, exc.detalhe)
        _registrar_falha(cfg, log, cliente, resultado["detalhe"])
    except ErroPlaywright as exc:
        resultado["detalhe"] = f"Navegador: {type(exc).__name__}: {exc}"
        log.exception("%s Erro do Playwright no cliente %s.", FALHA, cliente.cnpj_formatado)
        _registrar_falha(cfg, log, cliente, resultado["detalhe"])
    except Exception as exc:  # noqa: BLE001 - rede de segurança do laço
        resultado["detalhe"] = f"Inesperado: {type(exc).__name__}: {exc}"
        log.exception("%s Erro inesperado no cliente %s.", FALHA, cliente.cnpj_formatado)
        _registrar_falha(cfg, log, cliente, resultado["detalhe"])
    finally:
        if (resultado["status"] in (STATUS_ERRO, STATUS_SEM_PROCURACAO, STATUS_CNPJ_INVALIDO)
                and not page.is_closed()):
            salvar_evidencia(
                page, cfg.dir_debug, resultado["status"],
                prefixo=cliente.cnpj_digitos,
            )
        resultado["duracao_s"] = round(time.monotonic() - inicio, 1)

    return resultado


def _registrar_falha(
    cfg: Config, log: logging.Logger, cliente: Cliente, detalhe: str
) -> None:
    """Grava a falha no CSV, sem deixar que um erro de escrita apague o original."""
    try:
        registrar(
            cfg.caminho_csv, log,
            cnpj=cliente.cnpj_formatado,
            nome_credencial=cliente.nome_credencial,
            status=STATUS_ERRO,
            observacao=detalhe[:500],
        )
    except OSError as exc:
        log.error("%s Falha ao gravar a linha de erro no CSV: %s", FALHA, exc)


# ---------------------------------------------------------------------- #
# Execução
# ---------------------------------------------------------------------- #
def _calibrar(page: Page, cfg: Config, log: logging.Logger) -> None:
    """Grava evidência da home e da sidebar aberta, para ajustar seletores."""
    salvar_evidencia(page, cfg.dir_debug, "portal-home", prefixo="dump")
    if clicar_se_existir(page, cfg.sel("abrir_representar"), "abrir sidebar",
                         cfg.timeout_padrao_ms, log):
        page.wait_for_timeout(1_500)
    salvar_evidencia(page, cfg.dir_debug, "sidebar-representar", prefixo="dump")
    log.info("%s Evidencias em %s. Ajuste a secao [seletores] do config.toml.",
             SUCESSO, cfg.dir_debug)


def _processar_lote(
    contexto: BrowserContext,
    page: Page,
    cfg: Config,
    clientes: list[Cliente],
    args: argparse.Namespace,
    log: logging.Logger,
) -> list[dict[str, Any]]:
    sessao = Sessao(contexto, cfg)
    garantir_sessao(page, cfg, log)

    if args.login:
        log.info("%s Sessao autenticada e persistida em %s.", SUCESSO, cfg.dir_perfil)
        return []
    if args.dump:
        _calibrar(page, cfg, log)
        return []

    preparar_csv(cfg.caminho_csv, log)
    resultados: list[dict[str, Any]] = []
    for indice, cliente in enumerate(clientes):
        page = pagina_ativa(contexto, page)
        resultados.append(processar_cliente(page, cfg, sessao, cliente, args))
        if indice < len(clientes) - 1 and cfg.pausa_entre_clientes_s > 0:
            # Espaça as trocas de representação: em lote grande, uma rajada
            # de mudanças de papel é o que mais provavelmente atrai o rate
            # limit do portal.
            time.sleep(cfg.pausa_entre_clientes_s)
    return resultados


def executar(args: argparse.Namespace) -> int:
    """Ponto de entrada lógico: carrega config, roda o laço e resume."""
    # O logging sobe antes da configuração: a leitura do TOML já produz
    # avisos que precisam ir para o arquivo de log.
    log = configurar_logging(
        Config().dir_logs, logging.DEBUG if args.verbose else logging.INFO
    )
    try:
        cfg = Config.carregar(args.config)
        if args.clientes_arquivo:
            # O arquivo recebido muda a cada execucao: sobrepoe a fonte do
            # TOML em vez de exigir editar 'fonte_clientes' toda vez.
            cfg.fonte_clientes = FONTE_EXCEL
            cfg.clientes_arquivo = args.clientes_arquivo
        cfg.clientes = carregar_clientes(cfg, log)
        aplicar_argumentos(cfg, args)
        clientes = cfg.clientes_ativos(args.cliente)
    except ErroRobo as exc:
        log.error("%s Erro de configuracao: %s", FALHA, exc)
        return SAIDA_CONFIG

    cfg.preparar_diretorios()
    log.info("rfb-bot %s | %d cliente(s) | modo_certificado=%s | %s",
             __version__, len(clientes), cfg.modo_certificado, resumo_ambiente())

    for suspeito in cfg.cnpjs_suspeitos():
        log.warning(
            "%s CNPJ %s nao passa no digito verificador. Se estiver errado, o "
            "robo vai representar outra empresa.",
            AVISO, suspeito.cnpj_formatado,
        )

    if args.limpar_perfil:
        limpar_perfil(cfg, log)
        return SAIDA_OK

    if not clientes and not (args.login or args.dump):
        log.warning("%s Nenhum cliente ativo no config.toml (todos com "
                    "ativo=false).", AVISO)
        return SAIDA_CONFIG

    with sync_playwright() as pw:
        try:
            contexto, page = abrir_contexto(pw, cfg, log)
        except ErroRobo as exc:
            log.error("%s %s", FALHA, exc)
            return SAIDA_CONFIG
        try:
            resultados = _processar_lote(contexto, page, cfg, clientes, args, log)
        except ErroSessao as exc:
            log.error("%s %s", FALHA, exc)
            return SAIDA_TOTAL
        finally:
            fechar_contexto(contexto, cfg, log)

    if not resultados:
        return SAIDA_OK
    return _resumir(resultados, cfg, log)


def _resumir(resultados: list[dict[str, Any]], cfg: Config, log: logging.Logger) -> int:
    criadas = [r for r in resultados if r["status"] == STATUS_CRIADA]
    ja_possuiam = [r for r in resultados if r["status"] == STATUS_JA_POSSUIA]
    simuladas = [r for r in resultados if r["status"] == STATUS_SIMULADO]
    sem_procuracao = [r for r in resultados if r["status"] == STATUS_SEM_PROCURACAO]
    cnpj_invalido = [r for r in resultados if r["status"] == STATUS_CNPJ_INVALIDO]
    falhas = [r for r in resultados if r["status"] == STATUS_ERRO]

    log.info("=" * 66)
    log.info(
        "Resumo: %d criada(s) | %d ja possuia(m) | %d simulada(s) | "
        "%d sem procuracao | %d cnpj invalido | %d com erro",
        len(criadas), len(ja_possuiam), len(simuladas),
        len(sem_procuracao), len(cnpj_invalido), len(falhas),
    )
    for item in sem_procuracao:
        log.warning("%s %s -> sem procuracao: %s", AVISO, item["cnpj"], item["detalhe"])
    for item in cnpj_invalido:
        log.warning("%s %s -> cnpj invalido: %s", AVISO, item["cnpj"], item["detalhe"])
    for item in falhas:
        log.error("%s %s -> %s", FALHA, item["cnpj"], item["detalhe"])

    # Última linha de propósito: é o que o operador precisa levar da tela.
    log.info("%s Credenciais em: %s", SUCESSO, cfg.caminho_csv)

    if not falhas:
        return SAIDA_OK
    produtivo = criadas or ja_possuiam or simuladas or sem_procuracao or cnpj_invalido
    return SAIDA_PARCIAL if produtivo else SAIDA_TOTAL


def _carregar_env() -> None:
    """Carrega o .env ao lado do executável/projeto (senhas nunca no TOML).

    O caminho é explícito, e não relativo ao diretório de trabalho: um
    ``.exe`` disparado pelo Agendador de Tarefas herda um CWD arbitrário
    (tipicamente ``C:\\Windows\\System32``), e ali não há ``.env`` nenhum.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(RAIZ_PADRAO / ".env", override=False)


def _pausar(codigo: int) -> None:
    """Segura a janela até o ENTER -- só faz sentido em console interativo.

    Sem isso, o duplo clique no ``.exe`` abre e fecha a janela preta num
    piscar, levando junto a mensagem de erro que explicaria o problema.
    """
    try:
        if not sys.stdin or not sys.stdin.isatty():
            return
    except (ValueError, AttributeError):
        return
    try:
        input(f"\n[codigo de saida {codigo}] Pressione ENTER para fechar...")
    except (EOFError, KeyboardInterrupt):
        pass


def main(argv: list[str] | None = None) -> int:
    _carregar_env()
    args = montar_parser().parse_args(argv)
    try:
        codigo = executar(args)
    except KeyboardInterrupt:
        print(f"\n{AVISO} Execucao interrompida pelo operador.", file=sys.stderr)
        codigo = SAIDA_TOTAL
    except Exception as exc:  # noqa: BLE001 - ultima rede antes da janela fechar
        # No executável não há terminal que sobreviva ao processo: um
        # traceback impresso e perdido é indistinguível de "não fez nada".
        logging.getLogger("rfb").exception("%s Erro nao tratado: %s", FALHA, exc)
        codigo = SAIDA_TOTAL

    if not args.sem_pausa:
        _pausar(codigo)
    return codigo


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
