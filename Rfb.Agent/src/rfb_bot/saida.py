"""Gravação do CSV de saída, com permissão restrita.

O arquivo gerado aqui contém **segredos de produção em texto puro**: cada
``client_secret`` dá acesso de API à conta de um contribuinte real. Duas
consequências no código:

* o arquivo é criado com permissão restrita ao usuário atual, antes de
  qualquer linha ser escrita (criar aberto e apertar depois deixa uma
  janela em que outro usuário da máquina pode ler);
* a escrita é linha a linha, com ``flush``, para que uma interrupção no
  meio do lote não perca as credenciais já emitidas -- elas existem no
  portal de qualquer forma, e um CSV truncado seria a única cópia perdida.

Numa v2 isto vira um cofre (Vault/KeyVault/SOPS); só este módulo muda.
"""

from __future__ import annotations

import csv
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .log import AVISO

COLUNAS = (
    "gerado_em",
    "cnpj",
    "nome_credencial",
    "status",
    "client_id",
    "client_secret",
    "observacao",
)

# Status registrados no CSV.
STATUS_CRIADA = "criada"
STATUS_JA_POSSUIA = "ja_possuia"
STATUS_SEM_PROCURACAO = "sem_procuracao"
STATUS_ERRO = "erro"
STATUS_SIMULADO = "simulado"


def _restringir_permissao(caminho: Path, log: logging.Logger) -> None:
    """Deixa o arquivo legível apenas pelo usuário atual.

    No Windows, ``os.chmod`` só mexe no atributo somente-leitura e não
    restringe nada -- quem controla acesso ali é a ACL. Daí o ``icacls``:
    remove a herança do diretório (que normalmente concede leitura a
    Users/Authenticated Users) e concede acesso total só ao dono.
    """
    try:
        os.chmod(caminho, 0o600)
    except OSError as exc:
        log.warning("%s Nao foi possivel aplicar chmod 600 em %s (%s)",
                    AVISO, caminho.name, exc)

    if sys.platform != "win32":
        return

    usuario = os.getenv("USERNAME") or ""
    dominio = os.getenv("USERDOMAIN") or ""
    if not usuario:
        log.warning("%s USERNAME indefinido: ACL de %s nao foi restringida.",
                    AVISO, caminho.name)
        return
    conta = f"{dominio}\\{usuario}" if dominio else usuario
    try:
        resultado = subprocess.run(
            ["icacls", str(caminho), "/inheritance:r", "/grant:r", f"{conta}:F"],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        log.warning("%s Falha ao executar icacls em %s (%s)", AVISO, caminho.name, exc)
        return
    if resultado.returncode != 0:
        log.warning(
            "%s icacls nao restringiu %s (codigo %s). O arquivo tem segredos: "
            "confira as permissoes manualmente.",
            AVISO, caminho.name, resultado.returncode,
        )


def preparar_csv(caminho: Path, log: logging.Logger) -> None:
    """Cria o CSV com cabeçalho e permissão restrita, se ainda não existir."""
    if caminho.exists():
        return
    caminho.parent.mkdir(parents=True, exist_ok=True)
    # Criado vazio e apertado ANTES de receber conteúdo: a permissão só
    # protege o que for escrito depois dela.
    caminho.touch(mode=0o600)
    _restringir_permissao(caminho, log)
    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        csv.writer(arquivo, delimiter=";").writerow(COLUNAS)
    log.info("CSV de saida criado: %s", caminho)


def registrar(
    caminho: Path,
    log: logging.Logger,
    *,
    cnpj: str,
    nome_credencial: str,
    status: str,
    client_id: str = "",
    client_secret: str = "",
    observacao: str = "",
) -> None:
    """Acrescenta uma linha ao CSV e força a gravação em disco.

    O separador é ``;`` e a codificação ``utf-8-sig`` porque o destino é o
    Excel em português, que abre CSV com vírgula em coluna única.
    """
    preparar_csv(caminho, log)
    linha = [
        datetime.now().isoformat(timespec="seconds"),
        cnpj,
        nome_credencial,
        status,
        client_id,
        client_secret,
        observacao,
    ]
    with caminho.open("a", encoding="utf-8-sig", newline="") as arquivo:
        csv.writer(arquivo, delimiter=";").writerow(linha)
        arquivo.flush()
        os.fsync(arquivo.fileno())
