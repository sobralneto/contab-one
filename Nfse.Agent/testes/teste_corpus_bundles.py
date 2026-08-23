#!/usr/bin/env python3
"""
Roda `regras.validar_bundle()` contra o corpus compartilhado em
`fixtures/bundles/` (manifest.json + arquivos JSON) e confere cada veredito
esperado.

O mesmo corpus é lido pelo teste .NET (ContabOne.Api.Tests/BundleCorpusTest.cs)
contra o validador C# — se os dois validadores divergirem, um dos testes
falha. O veredito compara CAMPOS problemáticos (primeira palavra de cada
mensagem, sem aspas), não o texto completo: o detalhe do erro de regex difere
entre as engines Python e .NET.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import regras
from _harness import Suite, rodar

PASTA_CORPUS = Path(__file__).resolve().parent / "fixtures" / "bundles"


def _campo_da_mensagem(mensagem: str) -> str:
    """Primeira palavra da mensagem, sem aspas — o identificador do campo
    problemático ('portal.urlLogin', "'portal'" -> 'portal', ...)."""
    return mensagem.strip().strip("'").split()[0]


def teste_corpus_bundles(s: Suite, _tmp: Path) -> None:
    manifest = json.loads((PASTA_CORPUS / "manifest.json").read_text(encoding="utf-8"))
    casos = manifest["casos"]
    s.check(len(casos) >= 8, "o corpus tem pelo menos os casos essenciais")

    for caso in casos:
        arquivo = caso["arquivo"]
        esperado = set(caso["campos"])
        conteudo = json.loads((PASTA_CORPUS / arquivo).read_text(encoding="utf-8"))

        erros = regras.validar_bundle(conteudo)
        obtido = {_campo_da_mensagem(m) for m in erros}

        s.check(obtido == esperado,
                f"{arquivo}: campos problemáticos {sorted(obtido)} == {sorted(esperado)}")


def teste_corpus_bundle_fabrica_sempre_na_lista(s: Suite, _tmp: Path) -> None:
    """O bundle embutido no agente precisa continuar passando no próprio
    validador (espelho do assert de BUNDLE_FABRICA em regras.py)."""
    s.check(regras.validar_bundle(regras.BUNDLE_FABRICA) == [],
            "BUNDLE_FABRICA continua válido contra o validador")


def main() -> Suite:
    s = Suite("teste_corpus_bundles")
    with tempfile.TemporaryDirectory(prefix="nfse-teste-corpus-") as tmp_str:
        tmp = Path(tmp_str)
        for nome, fn in list(globals().items()):
            if nome.startswith("teste_") and callable(fn):
                print(f"-- {nome}")
                fn(s, tmp)
    return s


if __name__ == "__main__":
    rodar(main)
