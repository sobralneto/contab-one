#!/usr/bin/env python3
"""
Roda todos os teste_*.py desta pasta, um por subprocess (isolamento total —
um teste que trava/vaza estado não contamina o próximo), e resume o
resultado. Uso:

    python testes/executar_tudo.py

Saída 0 se tudo passou, 1 caso contrário — dá pra usar como gate antes de
gerar o .exe (python build.py).
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent


def main() -> int:
    testes = sorted(p for p in PASTA.glob("teste_*.py"))
    if not testes:
        print("Nenhum teste_*.py encontrado.")
        return 1

    resultados: list[tuple[str, bool, float]] = []
    for teste in testes:
        print(f"\n{'=' * 70}\n{teste.name}\n{'=' * 70}")
        inicio = time.monotonic()
        r = subprocess.run([sys.executable, str(teste)], cwd=str(PASTA))
        duracao = time.monotonic() - inicio
        resultados.append((teste.name, r.returncode == 0, duracao))

    print(f"\n{'=' * 70}\nResumo\n{'=' * 70}")
    falhou = False
    for nome, ok, duracao in resultados:
        marca = "OK  " if ok else "FALHOU"
        print(f"  {marca}  {nome}  ({duracao:.1f}s)")
        falhou = falhou or not ok

    total = len(resultados)
    passou = sum(1 for _, ok, _ in resultados if ok)
    print(f"\n{passou}/{total} arquivos de teste passaram.")
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
