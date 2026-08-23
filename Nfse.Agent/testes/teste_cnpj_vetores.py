#!/usr/bin/env python3
"""
Paridade do hash de CNPJ com o servidor: `api_client.hash_cnpj` (Python) e
`CnpjHasher.Hash` (C#) precisam produzir o MESMO hex para a mesma entrada —
se divergirem, o servidor deixa de reconhecer o mesmo cliente entre execuções
e duplica cadastros silenciosamente.

Os vetores vivem em `fixtures/cnpj_vetores.json`, lidos também pelo teste
.NET (ContabOne.Api.Tests/HashersTest.cs). Alterar um vetor de propósito deve
fazer AS DUAS suítes falharem (ver tarefa 4.7 do change).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_client
from _harness import Suite, rodar

PASTA_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _vetores() -> list[dict]:
    doc = json.loads((PASTA_FIXTURES / "cnpj_vetores.json").read_text(encoding="utf-8"))
    return doc["vetores"]


def teste_hash_reproduz_os_vetores(s: Suite, _tmp: Path) -> None:
    for vetor in _vetores():
        obtido = api_client.hash_cnpj(vetor["cnpj"], vetor["chave"])
        s.check(obtido == vetor["hash"],
                f"hash_cnpj({vetor['cnpj']}) == {vetor['hash']} (obtido {obtido})")


def teste_pontuacao_nao_altera_o_hash(s: Suite, _tmp: Path) -> None:
    """O hash é calculado sobre os dígitos apenas — '12.345.678/0001-90' e
    '12345678000190' precisam produzir o mesmo hex (o C# recebe o CNPJ já
    limpo; o agente limpa antes de hashear)."""
    s.check(
        api_client.hash_cnpj("12.345.678/0001-90", "outra-chave-42")
        == api_client.hash_cnpj("12345678000190", "outra-chave-42"),
        "pontuação é ignorada antes do hash")


def main() -> Suite:
    s = Suite("teste_cnpj_vetores")
    with tempfile.TemporaryDirectory(prefix="nfse-teste-cnpj-") as tmp_str:
        tmp = Path(tmp_str)
        for nome, fn in list(globals().items()):
            if nome.startswith("teste_") and callable(fn):
                print(f"-- {nome}")
                fn(s, tmp)
    return s


if __name__ == "__main__":
    rodar(main)
