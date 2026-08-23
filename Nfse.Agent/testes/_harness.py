#!/usr/bin/env python3
"""
Mini-harness compartilhado pelos testes desta pasta — não é um arquivo de
teste em si. Só para dar um formato consistente (contagem de asserts, saída
com código de erro se algo falhar) sem trazer pytest como dependência, no
mesmo espírito das suítes antigas descritas em HANDOFF.md §Testes.
"""

from __future__ import annotations

import sys
import traceback


class Suite:
    def __init__(self, nome: str):
        self.nome = nome
        self.total = 0
        self.falhas: list[str] = []

    def check(self, condicao: bool, descricao: str) -> None:
        self.total += 1
        if not condicao:
            self.falhas.append(descricao)
            print(f"  FALHOU: {descricao}")

    def check_raises(self, tipo_excecao, fn, descricao: str) -> None:
        self.total += 1
        try:
            fn()
        except tipo_excecao:
            return
        except Exception as e:  # exceção errada — também é falha, mas com detalhe
            self.falhas.append(f"{descricao} (levantou {type(e).__name__}, esperava {tipo_excecao.__name__})")
            print(f"  FALHOU: {descricao} (levantou {type(e).__name__}: {e})")
            return
        self.falhas.append(f"{descricao} (não levantou {tipo_excecao.__name__})")
        print(f"  FALHOU: {descricao} (não levantou nada)")

    def relatorio(self) -> int:
        print(f"\n{self.nome}: {self.total - len(self.falhas)}/{self.total} OK")
        if self.falhas:
            print(f"  {len(self.falhas)} falha(s):")
            for f in self.falhas:
                print(f"    - {f}")
            return 1
        return 0


def rodar(main_fn) -> None:
    """Executa main_fn() (que deve devolver um Suite) e sai com o código
    apropriado — inclusive em caso de exceção não tratada no próprio teste."""
    try:
        suite = main_fn()
    except Exception:
        print("ERRO INESPERADO rodando o teste:")
        traceback.print_exc()
        sys.exit(2)
    sys.exit(suite.relatorio())
