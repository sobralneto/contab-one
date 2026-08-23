#!/usr/bin/env python3
"""
Download das NFS-e recebidas e emitidas — Portal Nacional NFS-e.

Tudo por mTLS com o certificado A1, sem navegador e sem captcha:
  1. Autentica em https://certificado.nfse.gov.br/EmissorNacional/Certificado
  2. Lista as notas do período em /Notas/Recebidas e /Notas/Emitidas
  3. Exporta a relação de cada listagem para CSV
  4. Baixa o XML pela API oficial da Sefin Nacional:
     GET https://sefin.nfse.gov.br/sefinnacional/nfse/{chave}
  5. Gera o DANFSe v2.0 (PDF) conforme a NT nº 008/2026 — ver danfse.py

Processa todos os certificados da pasta configurada, um por empresa, e organiza
a saída em {codigo}_{nome}/{ano-mes}/Recebidas|Emitidas.

Duas restrições do portal que a ferramenta trata sozinha:
  * o filtro aceita no máximo 31 dias por consulta — períodos maiores são
    quebrados em janelas;
  * a listagem pagina de 15 em 15 pelo parâmetro `pg`.

Cada cliente tem um `_controle.json` na raiz da pasta dele, guardando:
  * se o backfill (a primeira busca, desde `primeira_busca_desde` no
    config.toml) já foi concluído, por listagem — só depois que os downloads
    daquele período terminam sem falha, nunca logo após a busca, para uma
    interrupção não deixar meses órfãos;
  * as chaves de nota cujo XML já foi obtido, para não rebaixar mesmo que o
    arquivo tenha sido movido/arquivado para fora da pasta depois.

Uso:
    python nfse.py                       # mês corrente, todas as empresas
    python nfse.py --mes 2026-06
    python nfse.py --empresa 0001 --tipos recebidas
    python nfse.py --somente-lista
"""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import html as html_mod
import json
import os
import re
import sys
import time
import tomllib
import traceback
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import NoReturn
from urllib.parse import quote, urlsplit

try:
    import requests
    from requests_pkcs12 import Pkcs12Adapter
except ImportError as _e:  # pragma: no cover
    # Só acontece rodando o nfse.py cru sem `pip install -r requirements.txt`
    # (no .exe as dependências vêm embutidas). Isso executa ANTES do bloco
    # __main__ no fim do arquivo, então a pausa de lá não alcança este ponto
    # — por isso a pausa é repetida aqui, mesmo sem log() ainda definido.
    print(f"Dependências faltando: {_e}\nRode: python -m pip install -r requirements.txt")
    if sys.platform == "win32":
        try:
            input("\nPressione ENTER para fechar...")
        except (EOFError, OSError):
            pass
    sys.exit(1)

try:
    # A ferramenta virou o agente do SaaS (PLANO_SAAS_AGENTE.md) — estes dois
    # módulos são tão parte do programa quanto o próprio nfse.py agora, ao
    # contrário de danfse (que continua opcional/degradável por design — ver
    # o try/except ImportError dentro de gerar_pdf()). Se faltarem, é um
    # pacote incompleto, não uma dependência de rede.
    import api_client
    import regras
except ImportError as _e:  # pragma: no cover
    print(f"Arquivo do programa ausente ou corrompido: {_e}\n"
          f"Reinstale a ferramenta a partir do pacote original.")
    if sys.platform == "win32":
        try:
            input("\nPressione ENTER para fechar...")
        except (EOFError, OSError):
            pass
    sys.exit(1)


def pasta_base() -> Path:
    """Onde ficam config.toml, certificados e notas.

    Empacotado como .exe, é a pasta do próprio executável — assim o usuário
    edita o config e larga os certificados ao lado do programa.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


RAIZ = pasta_base()

# --------------------------------------------------------------------------
# Constantes do portal
# --------------------------------------------------------------------------
ORIGEM_CERTIFICADO = "https://certificado.nfse.gov.br"
ORIGEM_SEFIN = "https://sefin.nfse.gov.br"
URL_LOGIN_CERTIFICADO = f"{ORIGEM_CERTIFICADO}/EmissorNacional/Certificado"
URL_NOTAS = "https://www.nfse.gov.br/EmissorNacional/Notas"
URL_API_NFSE = f"{ORIGEM_SEFIN}/sefinnacional/nfse"

# O portal rejeita filtros com mais de 31 dias (devolve "Nenhum registro
# encontrado" em vez de erro) e pagina de 15 em 15 pelo parâmetro `pg`.
MAX_DIAS_FILTRO = 31
PARAM_PAGINA = "pg"
MAX_PAGINAS = 500
PAUSA_API = 0.25

# Cada listagem tem sua rota, seus parâmetros e suas colunas.
LISTAGENS = {
    "recebidas": {
        "rota": "Recebidas",
        "executar": True,  # só Recebidas tem esse campo no formulário
        "pasta": "Recebidas",
        "colunas": ["geracao", "emitida_por", "competencia", "preco_servico", "situacao"],
    },
    "emitidas": {
        "rota": "Emitidas",
        "executar": False,
        "pasta": "Emitidas",
        "colunas": ["geracao", "emitida_para", "competencia", "municipio_emissor",
                    "preco_servico", "situacao"],
    },
}

# Padrões de parsing do HTML da listagem. Módulo-globais (em vez de literais
# inline em extrair_notas()/total_registros()) para que aplicar_regras()
# possa substituí-los por um bundle vindo da API — ver PLANO_SAAS_AGENTE.md
# §4. Os valores abaixo são o padrão de fábrica; nunca mudam sozinhos.
REGEX_CHAVE = re.compile(r"/Notas/Download/NFSe/(\d{40,60})")
REGEX_LINHA = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
REGEX_TOTAL_REGISTROS = re.compile(r"Total de\s*(\d+)\s*registros?")

PADRAO_CERTIFICADO = re.compile(
    r"^(?P<codigo>[^_]+)_(?P<cnpj>\d{11,14})_(?P<nome>.+?)_s\.(?P<senha>[^_]*)_v\.(?P<validade>[\d.]+)$"
)
# Mesmo padrão, mas sem a senha e a validade no nome — quando a senha vem do
# config.toml (senha_padrao ou [senhas]) em vez do arquivo.
PADRAO_CERTIFICADO_SEM_SENHA = re.compile(
    r"^(?P<codigo>[^_]+)_(?P<cnpj>\d{11,14})_(?P<nome>.+)$"
)
ENV_SENHA = "NFSE_PFX_SENHA"

# Arquivo de controle, um por empresa, na raiz da pasta do cliente. Registra
# as notas já baixadas (para não rebaixar) e se a primeira busca completa
# (backfill) já foi concluída.
NOME_CONTROLE = "_controle.json"
DATA_BACKFILL_PADRAO = "2026-01-01"

CONFIG_PADRAO = {
    "pasta_certificados": "certificados",
    "pasta_saida": "notas",
    "tipos": ["recebidas", "emitidas"],
    "gerar_pdf": True,
    # Data da primeira busca de um cliente ainda sem histórico baixado.
    "primeira_busca_desde": DATA_BACKFILL_PADRAO,
    # Tamanho, em dias, do período padrão de busca quando nenhuma flag de data
    # é passada (--mes/--inicio/--fim) — retroage a partir de hoje. Separado de
    # MAX_DIAS_FILTRO (o limite técnico do portal por consulta): pode ser maior
    # que ele, já que coletar()/janelas() quebram qualquer período em janelas
    # de MAX_DIAS_FILTRO dias de qualquer forma. Configurável por escritório
    # via config.toml ou pela tela de configuração do SaaS (handshake, ver
    # aplicar_configuracao_remota).
    "dias_busca_padrao": MAX_DIAS_FILTRO,
    # Seção opcional — ausente/incompleta = modo legado (roda exatamente como
    # antes desta ferramenta virar um agente, zero chamada de rede além do
    # portal). Ver carregar_config().
    "api": {},
}
TOLERANCIA_OFFLINE_PADRAO = 7


def preparar_console() -> None:
    """Faz o console do Windows aceitar acentos.

    O prompt do Windows abre em code page 850/1252; sem isso, "Período" e
    "Início" saem embaralhados no .exe.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


PASTA_LOGS = RAIZ / "logs"


def _arquivo_log_hoje() -> Path:
    return PASTA_LOGS / f"nfse_{date.today():%Y-%m-%d}.log"


def _escrever_no_arquivo(texto: str) -> None:
    """Acrescenta texto ao log do dia. Uma falha aqui (disco cheio, pasta sem
    permissão) nunca pode derrubar a execução real — só o log em si se perde."""
    try:
        PASTA_LOGS.mkdir(parents=True, exist_ok=True)
        with _arquivo_log_hoje().open("a", encoding="utf-8") as f:
            f.write(texto)
    except OSError:
        pass


def log(msg: str) -> None:
    """Imprime no console E grava no arquivo de log do dia (logs/nfse_AAAA-MM-DD.log).

    Um arquivo por dia — cada execução é registrada, então um erro que passou
    rápido demais na tela para ser lido continua disponível depois.
    """
    linha = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(linha, flush=True)
    _escrever_no_arquivo(linha + "\n")


def log_excecao(contexto: str, exc: BaseException) -> None:
    """Como log(), mas para uma exceção: linha curta no console (não assusta
    quem não é programador com um traceback na tela), e o traceback completo
    só no arquivo — é o detalhe que faltava para diagnosticar depois."""
    log(f"{contexto}: {type(exc).__name__}: {exc}")
    _escrever_no_arquivo("".join(traceback.format_exception(exc)) + "\n")


def erro_fatal(msg: str, codigo: int = 1) -> NoReturn:
    """Substitui sys.exit(str) em todo erro de configuração/entrada: grava no
    log (console + arquivo) antes de sair, e sempre com código de saída
    inteiro — sys.exit(str) por si só imprime a mensagem no stderr, mas some
    do arquivo de log e, se não for capturado como SystemExit, pula direto a
    pausa final (SystemExit não é subclasse de Exception).

    `codigo` é 1 por padrão (todo call site existente continua igual). O
    licenciamento do agente usa 3 deliberadamente, para ser distinguível de
    um erro de configuração comum em scripts que olham o exit code (ver
    PLANO_SAAS_AGENTE.md §3.2)."""
    log(msg)
    sys.exit(codigo)


# --------------------------------------------------------------------------
# Configuração
# --------------------------------------------------------------------------
def carregar_config(caminho: Path) -> dict:
    """Lê o config.toml, completando com os padrões o que faltar."""
    config = dict(CONFIG_PADRAO)
    if caminho.exists():
        try:
            config.update(tomllib.loads(caminho.read_text(encoding="utf-8")))
        except tomllib.TOMLDecodeError as e:
            # A causa mais comum, de longe, para quem não programa: colar um
            # caminho do Windows numa string entre aspas duplas. TOML trata
            # \ como início de escape, então "C:\Users\..." quebra (\U não é
            # um escape válido) — mas o erro do parser não deixa isso óbvio.
            erro_fatal(
                f"Erro de sintaxe em {caminho.name}: {e}\n"
                f"    Dica: se o valor tem um caminho do Windows (ex.: C:\\Users\\...),\n"
                f"    a contrabarra simples quebra o TOML dentro de aspas duplas. Use:\n"
                f"        pasta_saida = 'C:\\Users\\...'    (aspas simples = texto literal)\n"
                f"        pasta_saida = \"C:/Users/...\"    (barra normal, funciona no Windows)\n"
                f"        pasta_saida = \"C:\\\\Users\\\\...\"  (contrabarra duplicada)"
            )
    else:
        log(f"{caminho.name} não encontrado — usando os valores padrão.")

    tipos = [t.strip().lower() for t in config.get("tipos", []) if str(t).strip()]
    invalidos = [t for t in tipos if t not in LISTAGENS]
    if invalidos:
        erro_fatal(f"Valor inválido em 'tipos' no {caminho.name}: {invalidos}. "
                   f"Use: {list(LISTAGENS)}")
    config["tipos"] = tipos or list(LISTAGENS)

    bruta = str(config.get("primeira_busca_desde", DATA_BACKFILL_PADRAO)).strip()
    try:
        config["primeira_busca_desde"] = datetime.strptime(bruta, "%Y-%m-%d").date()
    except ValueError:
        erro_fatal(f"Valor inválido em 'primeira_busca_desde' no {caminho.name}: {bruta!r}. "
                   f"Use o formato AAAA-MM-DD.")

    try:
        config["dias_busca_padrao"] = int(config.get("dias_busca_padrao", MAX_DIAS_FILTRO))
    except (TypeError, ValueError):
        erro_fatal(f"Valor inválido em 'dias_busca_padrao' no {caminho.name}: "
                   f"{config.get('dias_busca_padrao')!r}. Use um número inteiro de dias.")
    if config["dias_busca_padrao"] <= 0:
        erro_fatal(f"'dias_busca_padrao' no {caminho.name} precisa ser maior que zero.")

    # [api] ausente ou com 'url'/'chave' vazios = modo legado (roda igual a
    # antes desta ferramenta virar um agente, nenhuma chamada de rede além
    # do portal). Só liga o modo agente quando os dois estão preenchidos —
    # um [api] pela metade nunca deve disparar handshake silenciosamente.
    api_cfg = dict(config.get("api") or {})
    tem_url, tem_chave = bool(api_cfg.get("url")), bool(api_cfg.get("chave"))
    if tem_url or tem_chave:
        if not (tem_url and tem_chave):
            erro_fatal(f"[api] no {caminho.name} está incompleto: preencha 'url' e 'chave' "
                       f"os dois, ou nenhum (para rodar em modo legado, sem SaaS).")
        try:
            api_cfg["tolerancia_offline_dias"] = int(
                api_cfg.get("tolerancia_offline_dias", TOLERANCIA_OFFLINE_PADRAO))
        except (TypeError, ValueError):
            erro_fatal(f"Valor inválido em 'api.tolerancia_offline_dias' no {caminho.name}: "
                       f"{api_cfg.get('tolerancia_offline_dias')!r}. Use um número inteiro de dias.")
        if api_cfg["tolerancia_offline_dias"] <= 0:
            erro_fatal(f"'api.tolerancia_offline_dias' no {caminho.name} precisa ser maior que zero.")
    else:
        api_cfg = {}
    config["api"] = api_cfg

    return config


def resolver_pasta(valor: str) -> Path:
    """Caminhos relativos no config partem da pasta do script."""
    caminho = Path(valor).expanduser()
    return caminho if caminho.is_absolute() else (RAIZ / caminho)


# --------------------------------------------------------------------------
# Configuração remota do escritório (handshake) — §6 do PLANO_SAAS_AGENTE
# --------------------------------------------------------------------------
# Chaves que a plataforma pode informar e que o agente aceita aplicar. O que
# NÃO está aqui nunca entra no config: pasta_certificados, senhas e
# senha_padrao são segredo/caminho de máquina, não configuração de plataforma.
#
# A regra que mais importa: valor remoto inválido é DESCARTADO com aviso em
# log, nunca erro_fatal(). Um primeira_busca_desde digitado errado na tela não
# pode derrubar todos os agentes do escritório na próxima execução — dado
# vindo da rede não é confiável o bastante para matar o processo (mesmo
# princípio de regras.validar_bundle).

def aplicar_configuracao_remota(config: dict, remota: dict | None, *,
                                tipos_por_cli: bool = False,
                                sem_pdf: bool = False,
                                log: Callable[[str], None] = print) -> None:
    """Aplica a configuração recebida no handshake por cima da local.

    Precedência (design.md, Decisão 6): flag de CLI > configuração remota >
    config.toml > padrão. As flags da CLI já foram aplicadas em main() antes
    do handshake — quando `tipos_por_cli`/`sem_pdf` é True, a chave remota
    correspondente é ignorada (quem digitou está depurando; o servidor não
    sobrescreve).

    `remota` None (API antiga sem o bloco) = nada a aplicar.
    """
    if not remota:
        return

    # tipos: "recebidas,emitidas" → lista
    if not tipos_por_cli:
        bruto = remota.get("tipos")
        if bruto is not None:
            candidatos = [t.strip().lower() for t in str(bruto).split(",") if t.strip()]
            invalidos = [t for t in candidatos if t not in LISTAGENS]
            if candidatos and not invalidos:
                config["tipos"] = candidatos
                log(f"  configuração remota: tipos = {', '.join(candidatos)}")
            else:
                log(f"  AVISO: configuração remota com 'tipos' inválido ({bruto!r}) "
                    f"— mantendo os tipos locais")

    # primeira_busca_desde: "AAAA-MM-DD" → date
    bruto = remota.get("primeira_busca_desde")
    if bruto is not None:
        try:
            config["primeira_busca_desde"] = datetime.strptime(str(bruto).strip(), "%Y-%m-%d").date()
            log(f"  configuração remota: primeira_busca_desde = {config['primeira_busca_desde']}")
        except ValueError:
            log(f"  AVISO: configuração remota com 'primeira_busca_desde' inválido "
                f"({bruto!r}) — mantendo a data local")

    # pasta_saida: caminho que precisa dar para criar a pasta NESTA máquina —
    # um caminho válido para um escritório pode ser inválido para outro.
    bruto = remota.get("pasta_saida")
    if bruto is not None and str(bruto).strip():
        candidato = str(bruto).strip()
        try:
            resolver_pasta(candidato).mkdir(parents=True, exist_ok=True)
            config["pasta_saida"] = candidato
            log(f"  configuração remota: pasta_saida = {candidato}")
        except OSError:
            log(f"  AVISO: configuração remota com 'pasta_saida' inutilizável nesta "
                f"máquina ({candidato!r}) — mantendo a pasta local")

    # gerar_pdf: "true"/"false"
    if not sem_pdf:
        bruto = remota.get("gerar_pdf")
        if bruto is not None:
            if str(bruto).strip().lower() == "true":
                config["gerar_pdf"] = True
                log("  configuração remota: gerar_pdf = true")
            elif str(bruto).strip().lower() == "false":
                config["gerar_pdf"] = False
                log("  configuração remota: gerar_pdf = false")
            else:
                log(f"  AVISO: configuração remota com 'gerar_pdf' inválido ({bruto!r}) "
                    f"— mantendo o valor local")

    # dias_busca_padrao: inteiro positivo — tamanho do período padrão (sem
    # --mes/--inicio/--fim), ver resolver_periodo().
    bruto = remota.get("dias_busca_padrao")
    if bruto is not None:
        try:
            valor = int(str(bruto).strip())
            if valor <= 0:
                raise ValueError
            config["dias_busca_padrao"] = valor
            log(f"  configuração remota: dias_busca_padrao = {valor}")
        except ValueError:
            log(f"  AVISO: configuração remota com 'dias_busca_padrao' inválido "
                f"({bruto!r}) — mantendo o valor local")


def aplicar_limites_do_plano(config: dict, plano: dict | None, *,
                             log: Callable[[str], None] = print) -> None:
    """Aplica o teto comercial do plano sobre os tipos configurados.

    plano é o bloco `plano` do handshake: {"maxClientes": N, "permiteEmitidas":
    bool}. None (handshake sem plano) = nenhuma restrição adicional. O limite
    corta ACIMA de tudo — configuração remota, local e até a CLI pedindo
    emitidas não vencem o plano. Aplicado no agente, não no servidor (ver
    design.md Non-Goals) — contornável por quem edita o .exe, aceito.
    """
    if not plano or plano.get("permiteEmitidas") is not False:
        return
    tipos = config.get("tipos") or []
    if "emitidas" in tipos:
        config["tipos"] = [t for t in tipos if t != "emitidas"]
        log("  AVISO: plano do escritório não cobre notas emitidas — "
            "descartadas desta execução (configuração/CLI pedindo emitidas ignoradas)")


# --------------------------------------------------------------------------
# Certificados / empresas
# --------------------------------------------------------------------------
@dataclass
class Empresa:
    codigo: str
    cnpj: str
    nome: str
    senha: str
    validade: date | None
    pfx: Path

    @property
    def pasta(self) -> str:
        """Nome da pasta da empresa: {codigo}_{nome}, sem caracteres proibidos."""
        limpo = re.sub(r'[<>:"/\\|?*]', "-", self.nome).strip(" .")
        return f"{self.codigo}_{limpo}"

    @property
    def rotulo(self) -> str:
        return f"{self.codigo} - {self.nome}"


def ler_certificado(pfx: Path) -> Empresa:
    """Extrai os dados da empresa do nome do arquivo.

    Padrão completo: codigoEmpresa_CNPJ_NomeEmpresa_s.SENHA_v.DD.MM.AAAA.pfx

    A senha e a validade são opcionais no nome — sem elas, a senha sai do
    config.toml (senha_padrao ou [senhas]). O que nunca pode falhar é o
    código: é a chave usada para achar a pasta do cliente e a senha certa
    no config, então mesmo um arquivo totalmente fora do padrão recebe um
    código sensato (o texto antes do primeiro "_").
    """
    m = PADRAO_CERTIFICADO.match(pfx.stem)
    if m:
        validade = None
        try:
            validade = datetime.strptime(m["validade"], "%d.%m.%Y").date()
        except ValueError:
            pass
        return Empresa(codigo=m["codigo"], cnpj=m["cnpj"], nome=m["nome"].strip(),
                       senha=m["senha"], validade=validade, pfx=pfx)

    m = PADRAO_CERTIFICADO_SEM_SENHA.match(pfx.stem)
    if m:
        return Empresa(codigo=m["codigo"], cnpj=m["cnpj"], nome=m["nome"].strip(),
                       senha="", validade=None, pfx=pfx)

    codigo = pfx.stem.split("_", 1)[0].strip() or pfx.stem
    return Empresa(codigo=codigo, cnpj="", nome=pfx.stem, senha="",
                   validade=None, pfx=pfx)


def listar_empresas(pasta: Path, filtro: str | None = None) -> list[Empresa]:
    if not pasta.exists():
        erro_fatal(f"Pasta de certificados não encontrada: {pasta}\n"
                   f"Ajuste 'pasta_certificados' no config.toml.")
    arquivos = sorted(p for p in pasta.iterdir() if p.suffix.lower() in (".pfx", ".p12"))
    if not arquivos:
        erro_fatal(f"Nenhum certificado .pfx encontrado em {pasta}")

    empresas = [ler_certificado(p) for p in arquivos]
    if filtro:
        empresas = [e for e in empresas if e.codigo == filtro]
        if not empresas:
            erro_fatal(f"Nenhum certificado com o código {filtro!r} em {pasta}")
    return empresas


def pasta_da_empresa(saida: Path, empresa: Empresa) -> Path:
    """Devolve a pasta do cliente, reaproveitando a que já existir.

    A chave é o código da empresa — o prefixo antes do primeiro '_'. Se a razão
    social mudar no nome do certificado, o histórico continua na mesma pasta em
    vez de rachar em duas.
    """
    saida.mkdir(parents=True, exist_ok=True)
    existentes = sorted(
        p for p in saida.iterdir()
        if p.is_dir() and p.name.split("_", 1)[0].strip() == empresa.codigo
    )

    if not existentes:
        return saida / empresa.pasta

    if len(existentes) > 1:
        escolhida = max(existentes, key=lambda p: p.stat().st_mtime)
        log(f"  ATENÇÃO: {len(existentes)} pastas com o código {empresa.codigo} "
            f"({', '.join(p.name for p in existentes)}) — usando {escolhida.name}")
        return escolhida

    achada = existentes[0]
    if achada.name != empresa.pasta:
        log(f"  pasta existente reaproveitada: {achada.name} "
            f"(o certificado hoje diria {empresa.pasta})")
    return achada


# --------------------------------------------------------------------------
# Controle por empresa: histórico já buscado (backfill) e notas já baixadas
# --------------------------------------------------------------------------
# Um arquivo por cliente, na raiz da pasta dele — não por ano-mês, porque as
# duas coisas que ele guarda atravessam meses: se a busca histórica de cada
# listagem já foi feita, e quais chaves já foram obtidas (para não baixar de
# novo mesmo que o XML tenha sido movido/arquivado para fora da pasta).
def caminho_controle(pasta_empresa: Path) -> Path:
    return pasta_empresa / NOME_CONTROLE


def carregar_controle(pasta_empresa: Path) -> dict:
    """Lê o controle da empresa.

    Cliente novo (arquivo ainda não existe) ou controle corrompido devolvem a
    mesma estrutura em branco — o que, por si só, já sinaliza que o backfill
    ainda não foi feito para nenhuma listagem.
    """
    padrao = {"versao": 1, "backfill_concluido": {}, "notas_baixadas": {}}
    caminho = caminho_controle(pasta_empresa)
    if not caminho.exists():
        return padrao
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        log(f"  controle corrompido em {caminho.name} ({e}) — tratando como cliente novo")
        return padrao
    dados.setdefault("backfill_concluido", {})
    dados.setdefault("notas_baixadas", {})
    return dados


def salvar_controle(pasta_empresa: Path, controle: dict) -> None:
    """Grava de forma atômica: escreve num arquivo à parte e substitui — uma
    interrupção no meio da escrita não corrompe o controle anterior."""
    pasta_empresa.mkdir(parents=True, exist_ok=True)
    destino = caminho_controle(pasta_empresa)
    tmp = destino.with_suffix(".tmp")
    tmp.write_text(json.dumps(controle, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(destino)


def notas_ja_registradas(controle: dict, tipo: str) -> set[str]:
    return set(controle.get("notas_baixadas", {}).get(tipo, []))


def registrar_nota(controle: dict, tipo: str, chave: str) -> None:
    lista = controle.setdefault("notas_baixadas", {}).setdefault(tipo, [])
    if chave not in lista:
        lista.append(chave)


def backfill_concluido(controle: dict, tipo: str) -> bool:
    return bool(controle.get("backfill_concluido", {}).get(tipo, False))


def marcar_backfill_concluido(controle: dict, tipo: str) -> None:
    controle.setdefault("backfill_concluido", {})[tipo] = True


def senha_da_empresa(empresa: Empresa, config: dict | None = None) -> str:
    """Senha do .pfx, em ordem de prioridade:

    1. nome do arquivo (padrão `_s.SENHA_`)
    2. config.toml, seção [senhas], pelo nome do arquivo do certificado
    3. config.toml, campo senha_padrao (uma senha para todos os certificados)
    4. variável de ambiente NFSE_PFX_SENHA

    A chave de [senhas] é o nome do arquivo (`empresa.pfx.name`), não o
    código extraído do nome — dessa forma a resolução de senha não depende
    de nenhuma convenção de nomenclatura de certificado (change
    agente-config-minima-cifrada, Decisão 1).

    Nunca há prompt no console. Detectar "há um humano esperando para
    digitar" de forma confiável não dá — em execução automatizada
    (agendador de tarefas, execução remota) isso já travou o processo
    esperando uma entrada que nunca chegaria. Sem senha configurada, o erro é
    imediato e explica o que fazer, em vez de ficar pendurado.

    O certificado nunca é instalado no Windows: ele é lido do arquivo .pfx e
    carregado em memória a cada execução, nunca gravado na loja do sistema.
    """
    if empresa.senha:
        return empresa.senha

    config = config or {}
    senhas = config.get("senhas") or {}
    if senha := senhas.get(empresa.pfx.name):
        return str(senha)

    if senha := config.get("senha_padrao"):
        return str(senha)

    if os.environ.get(ENV_SENHA):
        return os.environ[ENV_SENHA]

    raise RuntimeError(
        f"Sem senha para o certificado {empresa.pfx.name} (código {empresa.codigo}).\n"
        f"    Configure 'senha_padrao' no config.toml (uma senha para todos)\n"
        f"    ou adicione '{empresa.pfx.name}' à seção [senhas] do config.toml"
    )


# --------------------------------------------------------------------------
# Período
# --------------------------------------------------------------------------
def resolver_periodo(args: argparse.Namespace, config: dict) -> tuple[date, date]:
    if args.mes:
        try:
            ano, mes = (int(x) for x in args.mes.split("-"))
            primeiro = date(ano, mes, 1)
        except ValueError:
            erro_fatal("Formato inválido em --mes. Use AAAA-MM (ex.: 2026-06).")
        ultimo = (date(ano, 12, 31) if mes == 12
                  else date(ano, mes + 1, 1) - timedelta(days=1))
        return primeiro, min(ultimo, date.today())

    hoje = date.today()
    # Padrão sem nenhuma flag de data: janela de config["dias_busca_padrao"]
    # dias terminando hoje, não "mês corrente" — aproveita um período maior em
    # vez de encolher no início do mês. Valor configurável por escritório
    # (config.toml ou tela de configuração do SaaS via handshake, ver
    # aplicar_configuracao_remota) — deliberadamente independente de
    # MAX_DIAS_FILTRO, o limite técnico do portal por consulta: pode ser maior,
    # já que coletar()/janelas() quebram qualquer período em janelas de
    # MAX_DIAS_FILTRO dias de qualquer forma. main() só chama resolver_periodo()
    # depois de aplicar_configuracao_remota(), para já refletir um valor remoto.
    return (_ler_data(args.inicio, "--inicio")
            or (hoje - timedelta(days=config["dias_busca_padrao"] - 1)),
            _ler_data(args.fim, "--fim") or hoje)


def _ler_data(valor: str | None, rotulo: str) -> date | None:
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%d/%m/%Y").date()
    except ValueError:
        erro_fatal(f"Data inválida em {rotulo}: {valor!r}. Use DD/MM/AAAA.")


def janelas(inicio: date, fim: date, max_dias: int | None = None) -> list[tuple[date, date]]:
    """Divide o período em faixas que o portal aceita (MAX_DIAS_FILTRO dias).

    `max_dias` só existe para os testes poderem variar o limite sem mexer no
    global. Deliberadamente NÃO é `max_dias: int = MAX_DIAS_FILTRO` — um
    default de parâmetro é calculado uma vez, na definição da função; como
    aplicar_regras() pode reatribuir MAX_DIAS_FILTRO depois que o módulo já
    foi carregado, um default assim ficaria travado no valor de fábrica para
    sempre, ignorando qualquer bundle remoto que mude o limite.
    """
    if max_dias is None:
        max_dias = MAX_DIAS_FILTRO
    if inicio > fim:
        erro_fatal("A data inicial é posterior à data final.")
    faixas, atual = [], inicio
    while atual <= fim:
        ultimo = min(atual + timedelta(days=max_dias - 1), fim)
        faixas.append((atual, ultimo))
        atual = ultimo + timedelta(days=1)
    return faixas


def montar_url(tipo: str, inicio: date, fim: date, pagina: int = 1) -> str:
    cfg = LISTAGENS[tipo]
    url = f"{URL_NOTAS}/{cfg['rota']}?"
    if cfg["executar"]:
        url += "executar=1&"
    url += (f"busca=&datainicio={quote(inicio.strftime('%d/%m/%Y'), safe='')}"
            f"&datafim={quote(fim.strftime('%d/%m/%Y'), safe='')}")
    if pagina > 1:
        url += f"&{PARAM_PAGINA}={pagina}"
    return url


# --------------------------------------------------------------------------
# Regras vindas da API (PLANO_SAAS_AGENTE.md §4) — substitui os literais
# acima por um bundle remoto, cacheado, ou de fábrica (ver regras.py).
# --------------------------------------------------------------------------
def origens_mtls() -> set[str]:
    """As origens (scheme://host) onde o certificado A1 precisa ser
    apresentado — derivadas das URLs ativas em vez de uma lista solta à
    parte, para nunca divergir se um bundle remoto mudar um domínio."""
    origens = set()
    for url in (URL_LOGIN_CERTIFICADO, URL_NOTAS, URL_API_NFSE):
        partes = urlsplit(url)
        origens.add(f"{partes.scheme}://{partes.netloc}")
    return origens


def aplicar_regras(bundle: dict) -> None:
    """Substitui as constantes de protocolo do portal pelas do bundle
    resolvido (remoto, cache, ou fábrica — ver regras.resolver_bundle).
    Chamado uma vez em main(), antes de qualquer listagem/download.

    Só os campos que o bundle realmente descreve são sobrescritos. `pasta`
    (o nome da subpasta de saída, Recebidas/Emitidas) fica de fora
    deliberadamente: é uma decisão local de organização de arquivos, não um
    detalhe do protocolo do portal — não faz sentido vir de um bundle
    remoto, e mudar isso reorganizaria pastas de clientes já em produção.
    """
    global MAX_DIAS_FILTRO, PARAM_PAGINA, URL_LOGIN_CERTIFICADO, URL_NOTAS, URL_API_NFSE
    global REGEX_CHAVE, REGEX_LINHA, REGEX_TOTAL_REGISTROS

    portal = bundle.get("portal") or {}
    parsing = bundle.get("parsing") or {}

    URL_LOGIN_CERTIFICADO = portal.get("urlLogin", URL_LOGIN_CERTIFICADO)
    URL_NOTAS = portal.get("urlNotas", URL_NOTAS)
    URL_API_NFSE = portal.get("urlApiXml", URL_API_NFSE)
    MAX_DIAS_FILTRO = int(portal.get("maxDiasFiltro", MAX_DIAS_FILTRO))
    PARAM_PAGINA = portal.get("paramPagina", PARAM_PAGINA)

    for tipo, cfg in (portal.get("listagens") or {}).items():
        if tipo not in LISTAGENS or not isinstance(cfg, dict):
            continue  # o bundle pode descrever listagens que esta versão do agente não conhece
        LISTAGENS[tipo]["rota"] = cfg.get("rota", LISTAGENS[tipo]["rota"])
        LISTAGENS[tipo]["executar"] = bool(cfg.get("executar", LISTAGENS[tipo]["executar"]))
        LISTAGENS[tipo]["colunas"] = list(cfg.get("colunas", LISTAGENS[tipo]["colunas"]))

    if padrao := parsing.get("regexChave"):
        REGEX_CHAVE = re.compile(padrao)
    if padrao := parsing.get("regexLinha"):
        REGEX_LINHA = re.compile(padrao, re.S)
    if padrao := parsing.get("regexTotalRegistros"):
        REGEX_TOTAL_REGISTROS = re.compile(padrao)


# --------------------------------------------------------------------------
# Login
# --------------------------------------------------------------------------
def abrir_sessao(empresa: Empresa, config: dict | None = None) -> requests.Session:
    """Sessão HTTPS que apresenta o certificado A1 nos domínios do portal.

    O .pfx é lido do disco e carregado em memória — nada é instalado na loja
    de certificados do Windows.
    """
    sessao = requests.Session()
    adaptador = Pkcs12Adapter(pkcs12_filename=str(empresa.pfx),
                              pkcs12_password=senha_da_empresa(empresa, config))
    for origem in origens_mtls():
        sessao.mount(origem, adaptador)
    return sessao


def autenticar(sessao: requests.Session) -> None:
    r = sessao.get(URL_LOGIN_CERTIFICADO, timeout=60)
    if not r.ok or "/Login" in r.url:
        raise RuntimeError(
            "Falha na autenticação por certificado. Confira a senha do .pfx e a "
            f"validade do certificado. HTTP {r.status_code}, URL final: {r.url}"
        )


# --------------------------------------------------------------------------
# Listagem — parsing do HTML (funções puras, testáveis sem rede)
# --------------------------------------------------------------------------
def _texto(fragmento: str) -> str:
    limpo = re.sub(r"<[^>]+>", " ", fragmento)
    return re.sub(r"\s+", " ", html_mod.unescape(limpo)).strip()


def _formatar_documento(texto: str) -> str:
    """A máscara de CNPJ/CPF é aplicada por JS no portal; aqui é feita na mão."""

    def mascarar(m: re.Match[str]) -> str:
        d = m.group(1)
        if len(d) == 14:
            return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"

    return re.sub(r"^(\d{14}|\d{11})\b", mascarar, texto)


def _situacao(celula: str) -> str:
    """A situação é um <img> com o rótulo no title (ex.: 'NFS-e Gerada')."""
    if texto := _texto(celula):
        return texto
    if m := re.search(r'(?:data-original-title|title|alt)="([^"]+)"', celula):
        return html_mod.unescape(m.group(1))
    if m := re.search(r"/tb-([\w-]+)\.svg", celula):
        return m.group(1).replace("-", " ")
    return ""


def extrair_notas(html: str, tipo: str) -> list[dict]:
    """Extrai as notas da tabela de resultados da listagem."""
    colunas = LISTAGENS[tipo]["colunas"]
    notas: list[dict] = []
    for linha in REGEX_LINHA.findall(html):
        m = REGEX_CHAVE.search(linha)
        if not m:
            continue
        celulas = re.findall(r"<td[^>]*>(.*?)</td>", linha, re.S)
        if len(celulas) < len(colunas):
            continue
        nota = {"chave": m.group(1), "tipo": tipo}
        for i, coluna in enumerate(colunas):
            if coluna == "situacao":
                nota[coluna] = _situacao(celulas[i])
            elif coluna in ("emitida_por", "emitida_para"):
                nota[coluna] = _formatar_documento(_texto(celulas[i]))
            else:
                nota[coluna] = _texto(celulas[i])
        notas.append(nota)
    return notas


def total_registros(html: str) -> int | None:
    """Lê o 'Total de N registros' do rodapé — é o número que a paginação deve
    alcançar, e serve de conferência do que foi coletado."""
    m = REGEX_TOTAL_REGISTROS.search(re.sub(r"<[^>]+>", " ", html))
    return int(m.group(1)) if m else None


def mes_da_nota(nota: dict, padrao: date) -> str:
    """Pasta ano-mes: usa a data de geração da própria nota (DD/MM/AA)."""
    if m := re.match(r"(\d{2})/(\d{2})/(\d{2,4})", nota.get("geracao", "")):
        dia, mes, ano = m.groups()
        ano = f"20{ano}" if len(ano) == 2 else ano
        return f"{ano}-{mes}"
    return f"{padrao.year}-{padrao.month:02d}"


def coletar(sessao: requests.Session, tipo: str, inicio: date, fim: date) -> list[dict]:
    """Percorre janelas de 31 dias e todas as páginas de cada janela."""
    encontradas: dict[str, dict] = {}
    faixas = janelas(inicio, fim)
    if len(faixas) > 1:
        log(f"  período de {(fim - inicio).days + 1} dias dividido em "
            f"{len(faixas)} janelas (limite do portal: {MAX_DIAS_FILTRO} dias)")

    for ini_faixa, fim_faixa in faixas:
        pagina, esperado, vistos = 1, None, 0
        while pagina <= MAX_PAGINAS:
            r = sessao.get(montar_url(tipo, ini_faixa, fim_faixa, pagina), timeout=60)
            if not r.ok:
                raise RuntimeError(f"Listagem de {tipo} falhou: HTTP {r.status_code}")
            html = r.text

            if pagina == 1:
                esperado = total_registros(html)
            notas = extrair_notas(html, tipo)
            if not notas:
                break
            vistos += len(notas)
            for nota in notas:
                encontradas.setdefault(nota["chave"], nota)
            if esperado is not None and vistos >= esperado:
                break
            pagina += 1

        if esperado is not None and vistos < esperado:
            log(f"  ATENÇÃO: {ini_faixa:%d/%m} a {fim_faixa:%d/%m} declarou "
                f"{esperado} registros mas foram lidos {vistos}")

    return list(encontradas.values())


def salvar_csv(notas: list[dict], caminho: Path, tipo: str) -> None:
    colunas = ["chave"] + LISTAGENS[tipo]["colunas"]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=colunas, extrasaction="ignore")
        w.writeheader()
        w.writerows(notas)


# --------------------------------------------------------------------------
# Download do XML e geração do PDF
# --------------------------------------------------------------------------
def baixar_xml(sessao: requests.Session, chave: str, destino: Path,
               ja_registradas: set[str] | None = None) -> str:
    """Baixa o XML. Pula se o arquivo já existe OU se o controle da empresa
    já registrou essa chave como baixada antes — o segundo caso cobre a nota
    cujo XML foi movido/arquivado para fora da pasta depois de baixado: evita
    rebaixar, ao custo de não reconseguir aquele arquivo específico sem editar
    o controle na mão."""
    arquivo = destino / f"{chave}.xml"
    if arquivo.exists() and arquivo.stat().st_size > 0:
        return "pulado"
    if ja_registradas and chave in ja_registradas:
        return "pulado"

    try:
        r = sessao.get(f"{URL_API_NFSE}/{chave}", timeout=60)
        if not r.ok:
            log(f"  API respondeu HTTP {r.status_code} para {chave}")
            return "falha"
        conteudo = r.json()
    except (json.JSONDecodeError, ValueError) as e:
        log(f"  resposta da API não é JSON: {e}")
        return "falha"
    except Exception as e:
        log(f"  erro na chamada à API: {e}")
        return "falha"

    campo = conteudo.get("nfseXmlGZipB64")
    if not campo:
        log(f"  resposta sem nfseXmlGZipB64 (chaves: {list(conteudo)})")
        return "falha"
    try:
        xml = gzip.decompress(base64.b64decode(campo))
    except Exception as e:
        log(f"  falha ao descompactar o XML: {e}")
        return "falha"
    if not xml.lstrip().startswith(b"<?xml"):
        log("  conteúdo devolvido não é um XML")
        return "falha"

    destino.mkdir(parents=True, exist_ok=True)
    arquivo.write_bytes(xml)
    return "ok"


def gerar_pdf(caminho_xml: Path, destino_pdf: Path) -> str:
    """PDFs já existentes (inclusive baixados do portal) são preservados."""
    if destino_pdf.exists() and destino_pdf.stat().st_size > 0:
        return "pulado"
    try:
        import danfse

        danfse.gerar(caminho_xml.read_bytes(), destino_pdf)
        return "ok"
    except ImportError as e:
        # mostra o módulo que faltou de verdade, em vez de chutar
        log(f"  não foi possível carregar o gerador de PDF: {e}")
        if not getattr(sys, "frozen", False):
            log("  rode: python -m pip install -r requirements.txt")
        return "falha"
    except Exception as e:
        log(f"  falha ao gerar o PDF: {e}")
        destino_pdf.unlink(missing_ok=True)
        return "falha"


# --------------------------------------------------------------------------
# Processamento por empresa
# --------------------------------------------------------------------------
def processar_empresa(empresa: Empresa, config: dict, args: argparse.Namespace,
                      inicio: date, fim: date) -> tuple[dict, list[dict]]:
    """Devolve (resumo, metricas). `resumo` é o agregado de sempre (console);
    `metricas` é uma linha por (tipo, competência) — a granularidade que o
    dashboard web precisa (PLANO_SAAS_AGENTE.md §5.1). As duas são
    incrementadas juntas, nos mesmos pontos do código, para nunca divergir
    uma da outra."""
    resumo = {"xml": 0, "pdf": 0, "pulados": 0, "falhas": []}
    # chave (tipo, ano_mes) -> {"qtd_baixadas", "qtd_puladas", "qtd_falhas", "duracao_ms"}
    metricas: dict[tuple[str, str], dict] = {}

    if empresa.validade and empresa.validade < date.today():
        log(f"  ATENÇÃO: certificado venceu em {empresa.validade:%d/%m/%Y}")

    sessao = abrir_sessao(empresa, config)
    raiz_empresa: Path | None = None
    controle: dict | None = None
    try:
        autenticar(sessao)
        raiz_empresa = pasta_da_empresa(resolver_pasta(config["pasta_saida"]), empresa)
        controle = carregar_controle(raiz_empresa)

        for tipo in config["tipos"]:
            # Cliente sem backfill registrado ainda: estende o início da busca
            # até a data configurada (padrão 01/01/2026), sem trocar o fim
            # pedido.
            #
            # O backfill só é marcado concluído DEPOIS que os downloads do
            # período inteiro terminam sem falha — não logo após a listagem.
            # Se marcasse na listagem, uma interrupção no meio dos downloads
            # (ex.: baixou jan-mar e travou antes de abril) faria a próxima
            # execução voltar a pedir só o período original, e abril/maio
            # ficariam órfãos para sempre, sem nenhuma consulta futura
            # alcançá-los outra vez.
            pendente = not backfill_concluido(controle, tipo)
            tipo_inicio = min(inicio, config["primeira_busca_desde"]) if pendente else inicio
            if pendente and tipo_inicio < inicio:
                log(f"  {tipo}: cliente sem histórico registrado — buscando desde "
                    f"{tipo_inicio:%d/%m/%Y} (primeira consulta)")

            notas = coletar(sessao, tipo, tipo_inicio, fim)

            if not notas:
                # sem isso, "0 nota(s)" se confunde com erro de consulta
                log(f"  {tipo}: nenhuma nota encontrada no período "
                    f"{tipo_inicio:%d/%m/%Y} a {fim:%d/%m/%Y} (consulta OK)")
                # nada para baixar: a busca em si já cobriu o período inteiro
                if pendente:
                    marcar_backfill_concluido(controle, tipo)
                    salvar_controle(raiz_empresa, controle)
                continue
            log(f"  {tipo}: {len(notas)} nota(s)")

            ja_registradas = notas_ja_registradas(controle, tipo)

            # cada nota vai para a pasta do mês da sua própria geração
            por_mes: dict[str, list[dict]] = {}
            for nota in notas:
                por_mes.setdefault(mes_da_nota(nota, tipo_inicio), []).append(nota)

            falhas_neste_tipo = 0
            for ano_mes, lote in sorted(por_mes.items()):
                destino = raiz_empresa / ano_mes / LISTAGENS[tipo]["pasta"]
                destino.mkdir(parents=True, exist_ok=True)
                salvar_csv(lote, destino / f"notas-{ano_mes}.csv", tipo)
                if args.somente_lista:
                    log(f"    {ano_mes}/{LISTAGENS[tipo]['pasta']}: {len(lote)} nota(s) no CSV")
                    continue

                _inicio_lote = time.monotonic()
                m = metricas.setdefault((tipo, ano_mes),
                                        {"qtd_baixadas": 0, "qtd_puladas": 0, "qtd_falhas": 0})
                for nota in lote:
                    chave = nota["chave"]
                    status = baixar_xml(sessao, chave, destino, ja_registradas)
                    if status == "ok":
                        resumo["xml"] += 1
                        m["qtd_baixadas"] += 1
                        registrar_nota(controle, tipo, chave)
                    elif status == "pulado":
                        resumo["pulados"] += 1
                        m["qtd_puladas"] += 1
                        registrar_nota(controle, tipo, chave)
                    else:
                        resumo["falhas"].append(f"{chave} (XML)")
                        m["qtd_falhas"] += 1
                        falhas_neste_tipo += 1
                        continue

                    arquivo_xml = destino / f"{chave}.xml"
                    if config["gerar_pdf"] and not args.sem_pdf and arquivo_xml.exists():
                        st = gerar_pdf(arquivo_xml, destino / f"{chave}.pdf")
                        if st == "ok":
                            resumo["pdf"] += 1
                        elif st == "falha":
                            resumo["falhas"].append(f"{chave} (PDF)")
                            m["qtd_falhas"] += 1
                    if status != "pulado":
                        time.sleep(PAUSA_API)
                m["duracao_ms"] = round((time.monotonic() - _inicio_lote) * 1000)

                log(f"    {ano_mes}/{LISTAGENS[tipo]['pasta']}: {len(lote)} nota(s)")
                salvar_controle(raiz_empresa, controle)  # progresso salvo a cada mês

            # --somente-lista nunca baixa nada, então "concluir" o backfill
            # aqui deixaria o próximo run de verdade sem baixar o histórico.
            if pendente and not args.somente_lista and falhas_neste_tipo == 0:
                marcar_backfill_concluido(controle, tipo)
                salvar_controle(raiz_empresa, controle)
    finally:
        sessao.close()
        if raiz_empresa is not None and controle is not None:
            salvar_controle(raiz_empresa, controle)  # rede de segurança final

    linhas_metricas = [
        {"cliente_codigo": empresa.codigo, "tipo": tipo, "competencia": ano_mes, **valores}
        for (tipo, ano_mes), valores in metricas.items()
    ]
    return resumo, linhas_metricas


# --------------------------------------------------------------------------
# Programa principal
# --------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Baixa XML e DANFSe das NFS-e recebidas e emitidas (sem navegador).",
    )
    p.add_argument("--config", type=Path, default=RAIZ / "config.toml",
                   help="Arquivo de configuração (padrão: config.toml).")
    p.add_argument("--empresa", help="Processa só o certificado com esse código.")
    p.add_argument("--tipos", help="recebidas, emitidas ou os dois (sobrepõe o config).")
    p.add_argument("--inicio", help="Data inicial DD/MM/AAAA (padrão: dia 1 do mês atual).")
    p.add_argument("--fim", help="Data final DD/MM/AAAA (padrão: hoje).")
    p.add_argument("--mes", help="Atalho para um mês inteiro, formato AAAA-MM.")
    p.add_argument("--somente-lista", action="store_true",
                   help="Apenas exporta os CSV, sem baixar XML nem gerar PDF.")
    p.add_argument("--sem-pdf", action="store_true", help="Não gera os PDFs.")
    p.add_argument("--sem-pausa", action="store_true",
                   help="Não espera ENTER ao final. Use em tarefas agendadas.")
    p.add_argument("--ajuda", action="help", help="Mostra esta ajuda.")
    return p.parse_args()


def _status_execucao(problemas: int, falhas: list, total: dict) -> str:
    """Sucesso/Parcial/Falha para o relatório à API (StatusExecucao no
    servidor). Parcial cobre qualquer mistura de sucesso e falha; Falha é
    reservado para quando nada funcionou apesar de haver falha registrada."""
    if problemas == 0 and not falhas:
        return "Sucesso"
    trabalho_feito = total["xml"] + total["pdf"] + total["pulados"]
    return "Falha" if trabalho_feito == 0 else "Parcial"


def _nome_arquivo_sanitizado(empresa: Empresa) -> str:
    """NUNCA o nome de arquivo original. No padrão recomendado do certificado
    (codigoEmpresa_CNPJ_NomeEmpresa_s.SENHA_v.DD.MM.AAAA.pfx), o nome do
    arquivo embute o CNPJ completo E a senha em texto claro — exatamente os
    dois campos que PLANO_SAAS_AGENTE.md §6 proíbe enviar. E no caso de um
    arquivo fora do padrão (ver ler_certificado), o texto antes do primeiro
    "_" pode ser qualquer coisa que alguém digitou, sem garantia nenhuma de
    que não seja sensível. Reconstruído a partir só do código (que já é
    enviado, sem mascarar, em 'codigo') e da extensão original."""
    return f"{empresa.codigo}{empresa.pfx.suffix}"


def _montar_payload_clientes(empresas: list[Empresa], hmac_key: str) -> list[dict]:
    """Um registro por certificado encontrado nesta execução — nunca inclui
    o .pfx, a senha, nem o CNPJ completo (só mascarado + hash). Ver
    PLANO_SAAS_AGENTE.md §6."""
    return [
        {
            "codigo": e.codigo,
            "nome": e.nome,
            "cnpjMascarado": api_client.mascarar_cnpj(e.cnpj),
            "cnpjHash": api_client.hash_cnpj(e.cnpj, hmac_key),
            "certificadoValidade": e.validade.isoformat() if e.validade else None,
            "certificadoNomeArquivo": _nome_arquivo_sanitizado(e),
        }
        for e in empresas
    ]


def main() -> int:
    preparar_console()
    _escrever_no_arquivo(
        f"\n{'='*70}\nExecução iniciada em {datetime.now():%d/%m/%Y %H:%M:%S}\n{'='*70}\n"
    )
    args = parse_args()
    config = carregar_config(args.config)
    if args.tipos:
        tipos = [t.strip().lower() for t in args.tipos.split(",") if t.strip()]
        if invalidos := [t for t in tipos if t not in LISTAGENS]:
            erro_fatal(f"--tipos aceita apenas {list(LISTAGENS)}; recebido: {invalidos}")
        config["tipos"] = tipos

    # ---- agente SaaS: identidade e licenciamento ---------------------------
    # Roda antes de qualquer certificado ser tocado (PLANO_SAAS_AGENTE.md
    # §3.2). config["api"] só é truthy quando 'url' e 'chave' estão os dois
    # preenchidos (ver carregar_config) — sem [api] no config.toml, nada
    # nesta seção roda: é o modo legado (§9), idêntico ao comportamento de
    # antes desta ferramenta virar um agente, zero chamada de rede além do
    # próprio portal.
    api_cliente: api_client.ApiClient | None = None
    decisao: api_client.DecisaoLicenca | None = None
    if config["api"]:
        api_cliente = api_client.ApiClient(base_url=config["api"]["url"], chave=config["api"]["chave"])
        cache_licenca = RAIZ / api_client.NOME_CACHE_LICENCA
        cache_regras = RAIZ / regras.NOME_CACHE

        decisao = api_client.avaliar_licenca(
            api_cliente, regras.versao_em_cache(cache_regras), cache_licenca,
            config["api"]["tolerancia_offline_dias"], log=log,
        )
        if not decisao.pode_executar:
            erro_fatal(decisao.mensagem or "Execução não autorizada pelo servidor.", codigo=3)
        if decisao.modo == "offline":
            log(f"  AVISO: {decisao.mensagem}")
        if decisao.agente_versao_minima and api_client.versao_desatualizada(
                api_client.VERSAO_AGENTE, decisao.agente_versao_minima):
            # Avisa e segue — bloquear por versão travaria o cliente exatamente
            # no momento em que a rede/API já é o ponto frágil (§3.2).
            log(f"  AVISO: uma versão mais nova do agente está disponível (mínima "
                f"recomendada: {decisao.agente_versao_minima}, atual: "
                f"{api_client.VERSAO_AGENTE}) — continuando mesmo assim")

        # Só tenta rede de novo (regras/pendências) se o handshake desta
        # execução respondeu de fato — se já sabemos que estamos na carência
        # offline, repetir a mesma tentativa (com os mesmos retries) só
        # atrasaria o trabalho de verdade sem chance real de sucesso.
        versao_regras_servidor = decisao.regras_versao_atual if decisao.modo == "online" else None
        bundle = regras.resolver_bundle(api_cliente, versao_regras_servidor, cache_regras, log=log)
        aplicar_regras(bundle)

        # Configuração do escritório vem do handshake (ou do cache, em carência
        # offline — o cache guarda a última resposta intacta). Aplicada antes
        # de qualquer certificado ser tocado. Flags da CLI vencem (quem
        # digitou está depurando), o plano corta por cima de tudo.
        aplicar_configuracao_remota(
            config, decisao.configuracao,
            tipos_por_cli=bool(args.tipos), sem_pdf=bool(args.sem_pdf), log=log)
        aplicar_limites_do_plano(config, decisao.plano, log=log)

        if decisao.modo == "online":
            api_client.reenviar_pendencias(api_cliente, RAIZ / "_pendencias", log=log)

    # Depois de aplicar_configuracao_remota(): se o escritório configurou um
    # dias_busca_padrao diferente do local (config.toml), o período padrão
    # (sem --inicio/--fim/--mes) já nasce com a janela certa.
    inicio, fim = resolver_periodo(args, config)

    empresas = listar_empresas(resolver_pasta(config["pasta_certificados"]), args.empresa)
    saida = resolver_pasta(config["pasta_saida"])

    log(f"Período: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}  |  Listagens: {', '.join(config['tipos'])}")
    log(f"Empresas: {len(empresas)}  |  Saída: {saida}")

    total = {"xml": 0, "pdf": 0, "pulados": 0, "falhas": []}
    problemas = 0
    todas_metricas: list[dict] = []

    for empresa in empresas:
        log(f"— {empresa.rotulo}")
        try:
            resumo, metricas_empresa = processar_empresa(empresa, config, args, inicio, fim)
        except Exception as e:
            log_excecao(f"  ERRO ao processar {empresa.rotulo}", e)
            problemas += 1
            continue
        for chave in ("xml", "pdf", "pulados"):
            total[chave] += resumo[chave]
        total["falhas"].extend(resumo["falhas"])
        todas_metricas.extend(metricas_empresa)

    print()
    log(f"Concluído — {total['xml']} XML baixado(s), {total['pdf']} PDF gerado(s), "
        f"{total['pulados']} já existente(s), {len(total['falhas'])} falha(s).")
    if total["falhas"]:
        log("Falhas (rode de novo para tentar só elas):")
        for f in total["falhas"][:20]:
            log(f"  - {f}")
    log(f"Arquivos em: {saida}")

    # ---- agente SaaS: relatório desta execução -----------------------------
    # --somente-lista não baixa nada (só lista) — não há métrica de download
    # real pra reportar, e uma linha zerada no dashboard pareceria uma
    # execução que rodou e falhou em tudo, não uma que deliberadamente só
    # listou. enviar_relatorio_execucao() nunca lança: falha de rede aqui
    # vira aviso + pendência, nunca um exit code de erro (§5.3) — o trabalho
    # real já terminou antes desta seção.
    if api_cliente is not None and decisao is not None and not args.somente_lista:
        if decisao.hmac_cnpj_key:
            status = _status_execucao(problemas, total["falhas"], total)
            mensagem_erro = None
            if status != "Sucesso":
                mensagem_erro = "; ".join(total["falhas"][:5]) or f"{problemas} empresa(s) com erro"
            api_client.enviar_relatorio_execucao(
                api_cliente, RAIZ / "_pendencias",
                clientes=_montar_payload_clientes(empresas, decisao.hmac_cnpj_key),
                metricas=todas_metricas,
                status=status,
                mensagem_erro=mensagem_erro,
                log=log,
            )
        else:
            log("  AVISO: servidor não informou a chave de ofuscação de CNPJ neste "
                "handshake — relatório desta execução não foi enviado")

    return 2 if problemas else (1 if total["falhas"] else 0)


if __name__ == "__main__":
    # Lido direto do argv, não do argparse: precisa estar disponível mesmo se
    # main() falhar antes de terminar de interpretar os argumentos.
    _sem_pausa = "--sem-pausa" in sys.argv[1:]
    codigo = 0
    try:
        codigo = main()
    except SystemExit as e:
        # erro_fatal()/argparse chamam sys.exit, que levanta SystemExit — e
        # SystemExit NÃO é subclasse de Exception, então um `except Exception`
        # não pega isso: a mensagem seria impressa (ou, pior, perdida, se o
        # código for string) e o processo encerraria ANTES da pausa abaixo,
        # fechando a janela sem dar tempo de ler. Por isso é capturado aqui
        # explicitamente, e só então a pausa roda.
        if isinstance(e.code, str):
            log(e.code)  # replica o print-e-sai-com-1 que sys.exit(str) faria, mas passando por log() (grava também no arquivo)
            codigo = 1
        else:
            codigo = e.code if isinstance(e.code, int) else 0
    except KeyboardInterrupt:
        log("Interrompido pelo usuário (Ctrl+C).")
        codigo = 130
    except Exception as e:  # no .exe, um traceback cru fecharia a janela
        preparar_console()
        log_excecao("ERRO INESPERADO", e)
        codigo = 2
    finally:
        # Fecha só quando o usuário apertar ENTER — nunca sozinho, em nenhum
        # dos caminhos acima. --sem-pausa é a saída para tarefa agendada
        # (sem isso, um agendamento sem ninguém para apertar Enter travaria
        # para sempre); o try/except cobre o caso de stdin indisponível
        # mesmo sem a flag (ex.: tarefa agendada sem console) — não trava.
        if not _sem_pausa:
            try:
                input("\nPressione ENTER para fechar...")
            except (EOFError, OSError):
                pass
    sys.exit(codigo)
