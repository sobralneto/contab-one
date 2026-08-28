#!/usr/bin/env python
"""Gera o arquivo .reg da política ``AutoSelectCertificateForUrls`` do Chrome.

Contexto
--------
No modo ``manual``, o Chrome abre um diálogo **nativo do Windows** pedindo
que o operador escolha o certificado. Esse diálogo está fora do DOM: o
Playwright não consegue clicar nele. Para rodar 100% desatendido usando os
certificados do repositório do Windows, a saída é instruir o próprio Chrome
a escolher sozinho, via política ``AutoSelectCertificateForUrls``.

Este script **apenas gera** o arquivo ``.reg``. Ele não altera o registro
do Windows -- a aplicação é um passo consciente do administrador:

    1. Revise o conteúdo gerado.
    2. Execute como Administrador:  reg import politica_certificado.reg
    3. Reinicie o Chrome.

Atenção: a política é **por máquina** (HKLM), não por perfil. Com mais de
uma empresa, ou você inclui uma entrada por CNPJ com filtros de SUBJECT
distintos (funciona quando cada URL/emissor é distinguível), ou reaplica a
política antes de cada empresa, ou usa o modo ``playwright_pfx``, que
resolve isso sem tocar no registro.

Uso
---
    python tools/gerar_politica_certificado.py --config config/empresas.json
    python tools/gerar_politica_certificado.py --cn "ACME LTDA:12345678000199"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

CHAVE = r"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Google\Chrome\AutoSelectCertificateForUrls"

# Origem do gov.br que executa o handshake com certificado de cliente.
PADRAO_URL = "https://certificado.sso.acesso.gov.br"


def montar_entrada(pattern: str, filtro: dict) -> str:
    """Monta o valor JSON de uma entrada da política, já escapado para .reg."""
    valor = json.dumps({"pattern": pattern, "filter": filtro}, ensure_ascii=False)
    # No formato .reg, aspas dentro de um valor string precisam de barra invertida.
    return valor.replace("\\", "\\\\").replace('"', '\\"')


def gerar_reg(filtros: list[dict], padrao_url: str) -> str:
    linhas = ["Windows Registry Editor Version 5.00", "", f"[{CHAVE}]"]
    for indice, filtro in enumerate(filtros, start=1):
        linhas.append(f'"{indice}"="{montar_entrada(padrao_url, filtro)}"')
    linhas.append("")
    return "\r\n".join(linhas)


def filtros_do_config(caminho: Path) -> list[dict]:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    filtros = []
    for empresa in dados.get("empresas", []):
        if not empresa.get("ativo", True):
            continue
        filtro = empresa.get("filtro_certificado")
        if filtro:
            filtros.append(filtro)
        else:
            print(
                f"[!] Empresa '{empresa.get('id')}' sem 'filtro_certificado'; ignorada.",
                file=sys.stderr,
            )
    return filtros


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-c", "--config", help="JSON de configuração do robô.")
    parser.add_argument(
        "--cn", action="append", metavar="CN",
        help="CN do titular do certificado (repetível). Ex.: 'ACME LTDA:12345678000199'.",
    )
    parser.add_argument("--url", default=PADRAO_URL, help="Padrão de URL da política.")
    parser.add_argument(
        "-o", "--saida", default=str(RAIZ / "politica_certificado.reg"),
        help="Arquivo .reg a gerar.",
    )
    args = parser.parse_args(argv)

    filtros: list[dict] = []
    if args.config:
        filtros.extend(filtros_do_config(Path(args.config)))
    for cn in args.cn or []:
        filtros.append({"SUBJECT": {"CN": cn}})

    if not filtros:
        parser.error("informe --config (com 'filtro_certificado') e/ou --cn.")

    destino = Path(args.saida)
    destino.write_text(gerar_reg(filtros, args.url), encoding="utf-8")

    print(f"[OK] Arquivo gerado: {destino}")
    print(f"     {len(filtros)} filtro(s) de certificado.")
    print()
    print("     Revise o conteudo e, como Administrador, execute:")
    print(f"         reg import \"{destino}\"")
    print("     Depois reinicie o Chrome. Para remover a politica:")
    print(f"         reg delete \"{CHAVE}\" /f")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
