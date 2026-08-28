"""Persistência dos dados coletados em JSON.

São gerados dois níveis de arquivo:

* ``dados/det_<carimbo>.json`` -- consolidado da execução, com o resultado
  de todas as empresas e o resumo de erros;
* ``dados/empresas/<id>_<carimbo>.json`` -- um arquivo por empresa, formato
  conveniente para a integração consumir/reprocessar isoladamente.

A gravação é atômica (arquivo temporário + ``os.replace``) para que um
processo de integração jamais leia um JSON pela metade.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


def _gravar_atomico(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    descritor, temporario = tempfile.mkstemp(
        dir=str(caminho.parent), prefix=".tmp_", suffix=".json"
    )
    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
    except BaseException:
        Path(temporario).unlink(missing_ok=True)
        raise


def salvar_json(dados: dict[str, Any], caminho: Path) -> Path:
    """Grava o dicionário em JSON UTF-8 legível (acentos preservados)."""
    _gravar_atomico(caminho, json.dumps(dados, ensure_ascii=False, indent=2,
                                        default=str))
    return caminho


def carimbo() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def salvar_resultado(
    resultado: dict[str, Any],
    dir_saida: Path,
    log: logging.Logger,
    marca: str | None = None,
) -> dict[str, Path]:
    """Escreve o consolidado e os arquivos por empresa; devolve os caminhos."""
    marca = marca or carimbo()
    gerados: dict[str, Path] = {}

    consolidado = dir_saida / f"det_{marca}.json"
    salvar_json(resultado, consolidado)
    gerados["consolidado"] = consolidado
    log.info("JSON consolidado: %s", consolidado)

    for item in resultado.get("empresas", []):
        identificador = item.get("empresa", {}).get("id", "sem-id")
        caminho = dir_saida / "empresas" / f"{identificador}_{marca}.json"
        salvar_json(item, caminho)
        gerados[identificador] = caminho

    # Ponteiro estável para a última execução -- simplifica a integração,
    # que não precisa descobrir o carimbo mais recente.
    ultimo = dir_saida / "ultimo.json"
    salvar_json(resultado, ultimo)
    gerados["ultimo"] = ultimo

    return gerados
