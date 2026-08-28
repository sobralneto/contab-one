"""Orquestração: CLI, laço por grupo/empresa e montagem do resultado final.

As empresas são agrupadas pelo **perfil de navegador**, e cada grupo roda
em um único Chrome: quem compartilha perfil compartilha a sessão gov.br, de
modo que um login serve para todos os clientes do grupo (caso do acesso com
o certificado do escritório contábil e procuração). Empresas com perfil
próprio formam grupos de um -- adequado a quem tem um certificado por
empresa.

Cada empresa continua isolada em try/except: a falha de um cliente não
interrompe a leitura dos demais. O código de saída do processo reflete o
resultado agregado, o que permite ao agendador (Task Scheduler / cron)
disparar alerta.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import (
    BrowserContext,
    Error as ErroPlaywright,
    Page,
    sync_playwright,
)

from . import __version__, relatorio
from .caixa_postal import abrir_caixa_postal, dump_diagnostico, extrair_mensagens
from .erros import ErroEmpregadorDivergente, ErroEtapa, ErroRobo, ErroSemProcuracao
from .fontes import montar_configuracao
from .govbr import autenticar, encerrar_sessao
from .log import AVISO, FALHA, SUCESSO, configurar_logging, obter_logger, salvar_evidencia
from .navegador import (
    abrir_contexto,
    fechar_contexto,
    limpar_perfil,
    pagina_ativa,
    resumo_ambiente,
)
from .saida import carimbo, salvar_resultado
from .settings import MODOS_CERTIFICADO, RAIZ_PADRAO, Config, Empresa

# Códigos de saída para o agendador.
SAIDA_OK = 0
SAIDA_PARCIAL = 1
SAIDA_TOTAL = 2
SAIDA_CONFIG = 3


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="det-bot",
        description=(
            "Robô de leitura da Caixa Postal do DET (Domicílio Eletrônico "
            "Trabalhista) com autenticação por certificado digital no gov.br."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c", "--config", default="config/empresas.json",
        help="Caminho do JSON de configuração.",
    )
    parser.add_argument(
        "-e", "--empresa", action="append", metavar="ID",
        help="Processa apenas esta empresa: id ou CNPJ (repetível).",
    )
    parser.add_argument(
        "--empresas-arquivo", metavar="XLSX",
        help=(
            "Le a lista de empresas desta planilha (coluna A=CNPJ, B=Nome) "
            "em vez da fonte configurada em --config."
        ),
    )
    parser.add_argument(
        "-o", "--saida", metavar="DIR",
        help="Sobrescreve o diretório de saída dos JSON.",
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
            "Use na primeira execução de cada perfil de navegador."
        ),
    )
    parser.add_argument(
        "--dump", action="store_true",
        help="Salva screenshot + HTML da Caixa Postal para calibrar seletores.",
    )
    parser.add_argument(
        "--limpar-perfil", action="store_true",
        help="Apaga o(s) perfil(is) do Chrome envolvido(s) e encerra.",
    )
    parser.add_argument(
        "--timeout-login", type=int, metavar="SEG",
        help="Segundos de espera pelo retorno autenticado do gov.br.",
    )
    parser.add_argument(
        "--sem-pausa", action="store_true",
        help="Nao espera ENTER ao terminar (use no Agendador de Tarefas).",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Log em DEBUG.")
    parser.add_argument("--version", action="version", version=f"det-bot {__version__}")
    return parser


def aplicar_argumentos(cfg: Config, args: argparse.Namespace) -> None:
    """Sobrepõe a configuração de arquivo com os argumentos da linha de comando."""
    if args.saida:
        cfg.dir_saida = Path(args.saida).resolve()
    if args.modo_certificado:
        cfg.modo_certificado = args.modo_certificado
    if args.headless:
        cfg.headless = True
    if args.manter_aberto:
        cfg.fechar_navegador = False
    if args.timeout_login:
        cfg.timeout_login_ms = args.timeout_login * 1000
    cfg.validar()


def _dados_empresa(empresa: Empresa) -> dict[str, Any]:
    return {
        "id": empresa.id,
        "nome": empresa.nome,
        "cnpj": empresa.cnpj_formatado,
        "cnpj_digitos": empresa.cnpj_digitos,
    }


def _resultado_base(empresa: Empresa) -> dict[str, Any]:
    return {
        "empresa": _dados_empresa(empresa),
        "status": "erro",
        "etapa_falha": None,
        "erro": None,
        "evidencias": {},
        "iniciado_em": datetime.now(timezone.utc).astimezone().isoformat(),
        # False ate que a troca de perfil seja confirmada na tela; a
        # integracao pode usar isso para decidir se confia no registro.
        "perfil_confirmado": False,
        # Preenchido quando o portal recusa a troca por falta de
        # procuração -- ver ErroSemProcuracao. None nos demais casos.
        "mensagem_portal": None,
        "total_mensagens": 0,
        "paginas_lidas": 0,
        "mensagens": [],
    }


def processar_empresa(
    contexto: BrowserContext,
    page: Page,
    cfg: Config,
    empresa: Empresa,
    args: argparse.Namespace,
) -> tuple[dict[str, Any], Page]:
    """Lê a Caixa Postal de uma empresa em um navegador já aberto.

    Devolve o resultado e a página ativa -- que pode ter mudado, se o
    gov.br abriu o fluxo em outra aba. Quem abre e fecha o navegador é
    :func:`processar_grupo`.
    """
    log = obter_logger(empresa.id)
    inicio = time.monotonic()
    resultado = _resultado_base(empresa)

    log.info("-" * 66)
    log.info("Empresa: %s | CNPJ %s", empresa.nome, empresa.cnpj_formatado)

    try:
        page, confirmado = autenticar(contexto, page, cfg, empresa, log)
        resultado["perfil_confirmado"] = confirmado

        if args.login:
            resultado["status"] = "ok"
            resultado["observacao"] = "modo --login: sessao gravada no perfil persistente"
            log.info("%s Sessao autenticada e persistida no perfil '%s'.",
                     SUCESSO, empresa.dir_perfil)
            return resultado, page

        page = abrir_caixa_postal(page, cfg, log)
        if args.dump:
            dump_diagnostico(page, cfg, empresa, log)

        coletado = extrair_mensagens(page, cfg, empresa, log)
        resultado.update(coletado)
        resultado["status"] = "ok"
        log.info("%s %d mensagem(ns) coletada(s) em %d pagina(s).",
                 SUCESSO, coletado["total_mensagens"], coletado["paginas_lidas"])

    except ErroSemProcuracao as exc:
        # Condição de negócio esperada, não uma falha do robô: o
        # escritório não tem (mais) procuração para este CNPJ. Reportado
        # com status próprio para não soar como robô quebrado, mas com a
        # mensagem exata do portal preservada para o contador agir.
        resultado["status"] = "sem_procuracao"
        resultado["etapa_falha"] = "Sem procuracao"
        resultado["mensagem_portal"] = exc.mensagem_portal
        log.warning("%s Empresa '%s' sem procuracao: %s",
                    AVISO, empresa.id, exc.mensagem_portal)
    except ErroEmpregadorDivergente as exc:
        # Nunca silenciar: significa que a tela lida era de OUTRO CNPJ. Os
        # dados desta empresa não foram obtidos, e nada foi atribuído a ela.
        resultado["etapa_falha"] = exc.etapa
        resultado["erro"] = exc.detalhe
        resultado["empregador_em_tela"] = exc.encontrado
        log.error(
            "%s Empresa '%s': a tela exibia o empregador %s. Leitura abortada "
            "para nao atribuir mensagens de outro CNPJ a esta empresa.",
            FALHA, empresa.id, exc.encontrado,
        )
    except ErroEtapa as exc:
        resultado["etapa_falha"] = exc.etapa
        resultado["erro"] = exc.detalhe
        log.error("%s Empresa '%s' interrompida na etapa '%s': %s",
                  FALHA, empresa.id, exc.etapa, exc.detalhe)
    except ErroRobo as exc:
        resultado["etapa_falha"] = "Preparacao do ambiente"
        resultado["erro"] = str(exc)
        log.error("%s Empresa '%s': %s", FALHA, empresa.id, exc)
    except ErroPlaywright as exc:
        resultado["etapa_falha"] = "Navegador"
        resultado["erro"] = f"{type(exc).__name__}: {exc}"
        log.exception("%s Erro do Playwright na empresa '%s'.", FALHA, empresa.id)
    except Exception as exc:  # noqa: BLE001 - rede de segurança do laço
        resultado["etapa_falha"] = "Inesperado"
        resultado["erro"] = f"{type(exc).__name__}: {exc}"
        log.exception("%s Erro inesperado na empresa '%s'.", FALHA, empresa.id)
    finally:
        # Evidência final de segurança: se falhou (ou ficou sem procuração)
        # e ainda há página viva, registra o estado da tela mesmo que a
        # etapa não tenha capturado -- útil para auditoria em ambos os casos.
        if resultado["status"] in ("erro", "sem_procuracao") and not resultado["evidencias"]:
            viva = next((p for p in contexto.pages if not p.is_closed()), None)
            if viva is not None:
                resultado["evidencias"] = salvar_evidencia(
                    viva, cfg.dir_debug, resultado["etapa_falha"] or "falha",
                    prefixo=f"{empresa.id}_final",
                )
        resultado["duracao_s"] = round(time.monotonic() - inicio, 1)

    return resultado, page


def processar_grupo(
    pw: Any, cfg: Config, grupo: list[Empresa], args: argparse.Namespace
) -> list[dict[str, Any]]:
    """Processa todas as empresas que dividem um perfil, em um só navegador.

    É aqui que mora a economia do agrupamento: no acesso com o certificado
    do escritório e procuração existe uma única identidade gov.br, então
    abrir um Chrome e autenticar uma vez por cliente seria repetir o mesmo
    login N vezes. Com
    o grupo, o certificado é apresentado uma vez e cada empresa seguinte
    custa apenas a troca de perfil dentro do DET.
    """
    perfil = grupo[0].dir_perfil
    compartilhado = len(grupo) > 1
    log = obter_logger(perfil if compartilhado else (grupo[0].id or perfil))

    log.info("=" * 66)
    if compartilhado:
        log.info("Perfil '%s' compartilhado por %d empresa(s): %s",
                 perfil, len(grupo), ", ".join(e.id for e in grupo))

    try:
        contexto, page = abrir_contexto(pw, cfg, grupo[0], log)
    except (ErroRobo, ErroPlaywright) as exc:
        # Sem navegador, nenhuma empresa do grupo pode ser lida: todas são
        # reportadas como falha, em vez de sumirem do relatório.
        log.error("%s Nao foi possivel abrir o navegador do perfil '%s': %s",
                  FALHA, perfil, exc)
        falhas = []
        for empresa in grupo:
            item = _resultado_base(empresa)
            item["etapa_falha"] = "Abrir navegador"
            item["erro"] = str(exc)
            item["duracao_s"] = 0.0
            falhas.append(item)
        return falhas

    resultados: list[dict[str, Any]] = []
    try:
        for indice, empresa in enumerate(grupo):
            item, page = processar_empresa(contexto, page, cfg, empresa, args)
            resultados.append(item)
            if indice < len(grupo) - 1 and cfg.pausa_entre_empresas_s > 0:
                time.sleep(cfg.pausa_entre_empresas_s)
    finally:
        # Sai do portal antes de fechar o navegador -- vale mesmo se o laço
        # acima falhou: a sessão aberta é a do certificado do escritório.
        # Blindado: estamos em `finally`, e uma exceção aqui mascararia o
        # erro real do laço e ainda deixaria o navegador aberto.
        try:
            encerrar_sessao(pagina_ativa(contexto, page), cfg, log)
        except Exception as exc:  # noqa: BLE001 - logout nunca derruba o fluxo
            log.warning("%s Falha ao encerrar a sessao no portal: %s", AVISO, exc)
        fechar_contexto(contexto, cfg, log)

    return resultados


def executar(args: argparse.Namespace) -> int:
    """Ponto de entrada lógico: carrega config, roda o laço e grava o JSON."""
    # O logging sobe antes da configuracao: a leitura do .env e da lista de
    # empresas ja produz avisos que precisam ir para o arquivo de log.
    log = configurar_logging(
        Config().dir_logs, logging.DEBUG if args.verbose else logging.INFO
    )
    try:
        cfg = montar_configuracao(args.config, log, empresas_arquivo=args.empresas_arquivo)
        aplicar_argumentos(cfg, args)
        empresas = cfg.empresas_ativas(args.empresa)
    except ErroRobo as exc:
        log.error("%s Erro de configuracao: %s", FALHA, exc)
        return SAIDA_CONFIG

    cfg.preparar_diretorios()
    log.info("det-bot %s | %d empresa(s) | modo_certificado=%s",
             __version__, len(empresas), cfg.modo_certificado)

    if args.limpar_perfil:
        # Empresas compartilham perfil: apagar uma vez por perfil, nao por empresa.
        for grupo in cfg.agrupar_por_perfil(empresas).values():
            limpar_perfil(cfg, grupo[0], log)
        return SAIDA_OK

    if not empresas:
        log.warning("%s Nenhuma empresa ativa para processar.", AVISO)
        return SAIDA_CONFIG

    marca = carimbo()
    resultado: dict[str, Any] = {
        "gerado_em": datetime.now(timezone.utc).astimezone().isoformat(),
        "versao_robo": __version__,
        "portal": cfg.url_portal,
        "modo_certificado": cfg.modo_certificado,
        "ambiente": resumo_ambiente(),
        "empresas": [],
    }

    grupos = cfg.agrupar_por_perfil(empresas)
    resultado["perfis"] = {p: [e.id for e in g] for p, g in grupos.items()}
    log.info("%d perfil(is) de navegador para %d empresa(s)", len(grupos), len(empresas))

    with sync_playwright() as pw:
        for indice, grupo in enumerate(grupos.values()):
            resultado["empresas"].extend(processar_grupo(pw, cfg, grupo, args))
            if indice < len(grupos) - 1 and cfg.pausa_entre_empresas_s > 0:
                time.sleep(cfg.pausa_entre_empresas_s)

    # "sem_procuracao" fica FORA de `falhas`: é uma condição de negócio
    # esperada (procuração vencida/revogada/nunca outorgada), não um sinal
    # de que o robô quebrou -- não deve disparar o mesmo alerta operacional.
    sucessos = [e for e in resultado["empresas"] if e["status"] == "ok"]
    sem_procuracao = [e for e in resultado["empresas"] if e["status"] == "sem_procuracao"]
    falhas = [e for e in resultado["empresas"]
              if e["status"] not in ("ok", "sem_procuracao")]
    resultado["resumo"] = {
        "empresas_processadas": len(resultado["empresas"]),
        "empresas_ok": len(sucessos),
        "empresas_sem_procuracao": len(sem_procuracao),
        "empresas_com_erro": len(falhas),
        "total_mensagens": sum(e["total_mensagens"] for e in resultado["empresas"]),
        "sem_perfil_confirmado": [
            e["empresa"]["cnpj"] for e in resultado["empresas"]
            if e["status"] == "ok" and not e.get("perfil_confirmado")
        ],
        "sem_procuracao": [
            {"empresa": e["empresa"]["cnpj"], "mensagem_portal": e["mensagem_portal"]}
            for e in sem_procuracao
        ],
        "falhas": [
            {"empresa": e["empresa"]["cnpj"], "etapa": e["etapa_falha"],
             "erro": e["erro"]}
            for e in falhas
        ],
    }

    salvar_resultado(resultado, cfg.dir_saida, log, marca)
    csv_gerado = relatorio.gerar(resultado, cfg.dir_resultado, log)

    log.info("=" * 66)
    log.info("Resumo: %d ok | %d sem procuracao | %d com erro | %d mensagem(ns) no total",
             len(sucessos), len(sem_procuracao), len(falhas),
             resultado["resumo"]["total_mensagens"])
    nao_confirmados = resultado["resumo"]["sem_perfil_confirmado"]
    if nao_confirmados:
        log.warning(
            "%s %d empresa(s) lidas sem confirmar o CNPJ na tela: %s. Os "
            "registros saem com perfil_confirmado=false.",
            AVISO, len(nao_confirmados), nao_confirmados,
        )
    for item in resultado["resumo"]["sem_procuracao"]:
        log.warning("%s %s -> sem procuracao: %s",
                    AVISO, item["empresa"], item["mensagem_portal"])
    for falha in resultado["resumo"]["falhas"]:
        log.error("%s %s -> etapa '%s': %s",
                  FALHA, falha["empresa"], falha["etapa"], falha["erro"])

    # Última linha do log de propósito: é o que o operador do executável
    # precisa levar da tela -- onde ficou o arquivo que ele veio buscar.
    if csv_gerado:
        log.info("%s Resultado em: %s", SUCESSO, csv_gerado)

    if not falhas:
        return SAIDA_OK
    return SAIDA_TOTAL if not sucessos and not sem_procuracao else SAIDA_PARCIAL


def _carregar_env() -> None:
    """Carrega o .env ao lado do executável/projeto (senhas nunca no JSON).

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
        logging.getLogger("det").exception("%s Erro nao tratado: %s", FALHA, exc)
        codigo = SAIDA_TOTAL

    if not args.sem_pausa:
        _pausar(codigo)
    return codigo


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
