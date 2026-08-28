#!/usr/bin/env python
"""Regera o CSV a partir de um JSON já coletado, sem consultar o portal.

A execução normal (``run.py`` / ``det.exe``) já grava o CSV sozinha em
``resultado/``. Este script serve para reprocessar uma execução antiga --
por exemplo, depois de corrigir a formatação do relatório.

    python tools/exportar_csv.py
    python tools/exportar_csv.py --entrada dados/det_20260822_175807.json
    python tools/exportar_csv.py --saida resultado/conferencia.csv

A lógica mora em ``det_bot.relatorio`` (o executável precisa dela embutida);
aqui é só a casca de linha de comando.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from det_bot.relatorio import coletar_linhas, escrever_csv, nome_arquivo  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "-e", "--entrada", default=str(RAIZ / "dados" / "ultimo.json"),
        help="JSON de origem (padrão: dados/ultimo.json).",
    )
    parser.add_argument(
        "-s", "--saida", default=None,
        help="CSV de destino (padrão: resultado/<hoje>_resultado-det.csv).",
    )
    args = parser.parse_args(argv)

    entrada = Path(args.entrada)
    if not entrada.is_file():
        print(f"[X] Arquivo nao encontrado: {entrada}", file=sys.stderr)
        return 1

    dados = json.loads(entrada.read_text(encoding="utf-8"))
    saida = Path(args.saida) if args.saida else RAIZ / "resultado" / nome_arquivo()

    linhas = coletar_linhas(dados)
    escrever_csv(linhas, saida)
    print(f"[OK] {len(linhas)} linha(s) exportada(s) para {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
