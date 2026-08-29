#!/usr/bin/env python
"""Ponto de entrada do robô de credenciais, sem precisar instalar o pacote.

Uso:
    python run.py --login          # primeira execucao: apresenta o certificado
    python run.py --dump           # grava HTML do portal para calibrar seletores
    python run.py --dry-run        # so consulta quem ja tem credencial
    python run.py                  # gera as credenciais do config.toml
    python run.py --cliente 07467651000135
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite ``import rfb_bot`` sem `pip install -e .`. Congelado pelo
# PyInstaller isso é desnecessário (o pacote já vai embutido) e o caminho
# nem existiria -- daí a guarda.
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from rfb_bot.runner import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
