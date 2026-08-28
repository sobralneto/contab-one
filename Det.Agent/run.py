#!/usr/bin/env python
"""Ponto de entrada do robô DET, sem precisar instalar o pacote.

Serve tanto para rodar do código-fonte quanto como entry point do
executável gerado por ``build.py``.

Uso:
    python run.py
    python run.py --empresa 12345678000199
    python run.py --dump --empresa 12345678000199
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite ``import det_bot`` sem `pip install -e .`. Congelado pelo
# PyInstaller isso é desnecessário (o pacote já vai embutido) e o caminho
# nem existiria -- daí a guarda.
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from det_bot.runner import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
