"""Geração do CSV de resultado -- o entregável que o contador realmente lê.

Uma linha por mensagem, colunas ``CNPJ | Nome | Título | Mensagem``. **Toda
empresa da lista aparece pelo menos uma vez**, mesmo sem mensagem nenhuma:
um relatório que só mostra quem deu problema não prova que as demais foram
de fato consultadas -- e foi exatamente essa omissão que já escondeu uma
empresa do relatório antes.

Vive dentro do pacote (e não em ``tools/``) porque o executável gerado por
``build.py`` precisa produzir o CSV sozinho, sem um segundo comando.
"""

from __future__ import annotations

import csv
import logging
from datetime import date
from pathlib import Path
from typing import Any

CABECALHO = ("CNPJ", "Nome", "Título", "Mensagem")
# ';' -- delimitador de lista padrão do Excel em pt-BR: abre certo com um
# duplo clique, sem passar pelo assistente de importação.
DELIMITADOR = ";"

TITULO_SEM_PROCURACAO = "Sem procuração"
TITULO_ERRO = "Erro"
TITULO_SEM_MENSAGENS = "Sem mensagens"


def nome_arquivo(dia: date | None = None) -> str:
    """``YYYY-MM-DD_resultado-det.csv`` -- ordena sozinho por data no Explorer."""
    return f"{(dia or date.today()).isoformat()}_resultado-det.csv"


def coletar_linhas(dados: dict[str, Any]) -> list[tuple[str, str, str, str]]:
    """Achata o JSON em ``(cnpj, nome, título, mensagem)``.

    Cada empresa rende pelo menos uma linha:

    * ``sem_procuracao`` -> a mensagem exata do portal, para o contador
      providenciar a renovação;
    * qualquer outro status != ``ok`` -> a falha, com a etapa em que parou;
    * ``ok`` sem mensagens -> "Sem mensagens", provando que foi consultada;
    * ``ok`` com mensagens -> uma linha por mensagem.
    """
    linhas: list[tuple[str, str, str, str]] = []
    for empresa in dados.get("empresas", []):
        dados_empresa = empresa.get("empresa", {})
        cnpj = dados_empresa.get("cnpj", "")
        nome = dados_empresa.get("nome") or ""
        status = empresa.get("status")

        if status == "sem_procuracao":
            linhas.append((
                cnpj, nome, TITULO_SEM_PROCURACAO,
                empresa.get("mensagem_portal") or "",
            ))
            continue

        if status != "ok":
            etapa = empresa.get("etapa_falha")
            erro = empresa.get("erro") or "Falha nao detalhada."
            linhas.append((
                cnpj, nome, TITULO_ERRO,
                f"[{etapa}] {erro}" if etapa else erro,
            ))
            continue

        mensagens = empresa.get("mensagens") or []
        if not mensagens:
            linhas.append((cnpj, nome, TITULO_SEM_MENSAGENS, ""))
            continue

        for msg in mensagens:
            linhas.append((
                cnpj, nome,
                msg.get("assunto") or "",
                msg.get("corpo") or "",
            ))
    return linhas


def escrever_csv(linhas: list[tuple[str, str, str, str]], saida: Path) -> Path:
    """Grava o CSV em UTF-8 com BOM (o Excel pt-BR exige o BOM p/ acentuação)."""
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo, delimiter=DELIMITADOR)
        escritor.writerow(CABECALHO)
        escritor.writerows(linhas)
    return saida


def gerar(
    resultado: dict[str, Any],
    dir_resultado: Path,
    log: logging.Logger,
    dia: date | None = None,
) -> Path | None:
    """Escreve ``resultado/<data>_resultado-det.csv``. ``None`` se falhar.

    Best-effort de propósito: o JSON consolidado já foi gravado quando isto
    roda, então um erro aqui (arquivo aberto no Excel, disco cheio) não pode
    derrubar a execução nem apagar o que já foi coletado.
    """
    destino = dir_resultado / nome_arquivo(dia)
    linhas = coletar_linhas(resultado)
    try:
        escrever_csv(linhas, destino)
    except OSError as exc:
        log.error(
            "Nao foi possivel gravar o CSV em %s: %s. Se o arquivo estiver "
            "aberto no Excel, feche-o e rode de novo.", destino, exc,
        )
        return None

    log.info("Resultado: %s (%d linha(s))", destino, len(linhas))
    return destino
