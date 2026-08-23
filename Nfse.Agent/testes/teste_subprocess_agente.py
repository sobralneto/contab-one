#!/usr/bin/env python3
"""
Testes de ponta a ponta via subprocess — exit code só dá pra observar de
fora do processo (mesma razão de teste_subprocess_pausa.py ter existido
antes, por HANDOFF.md §Testes). Cobre o item mais crítico do checklist:

  "bloqueio por inadimplência: podeExecutar: false -> sai com código 3 e
   não toca em nenhum .pfx" (PLANO_SAAS_AGENTE.md §8)

RAIZ em nfse.py é sempre a pasta do próprio script (não o cwd) — pra rodar
isolado sem escrever _agente_cache.json/_pendencias/logs dentro da pasta
real do projeto, cada teste copia nfse.py + api_client.py + regras.py pra
um diretório temporário e roda o processo de lá, exatamente como o
dist/nfse/ que build.py produz.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _fake_api import FakeAgentAPI, handshake_padrao
from _harness import Suite, rodar

RAIZ_REAL = Path(__file__).resolve().parent.parent
TIMEOUT_SUBPROCESSO = 30


def _agente_isolado(destino: Path) -> Path:
    """Copia só o necessário pro processo iniciar e chegar até o ponto de
    decisão de licenciamento (não danfse nem os recursos — o caminho
    bloqueado nunca chega perto deles)."""
    destino.mkdir(parents=True, exist_ok=True)
    for nome in ("nfse.py", "api_client.py", "regras.py"):
        shutil.copy2(RAIZ_REAL / nome, destino / nome)
    return destino / "nfse.py"


def _rodar(nfse_py: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(nfse_py), *args],
        cwd=str(nfse_py.parent),
        capture_output=True, text=True, timeout=TIMEOUT_SUBPROCESSO,
    )


def teste_ajuda_nao_toca_config_nem_rede(s: Suite, tmp: Path) -> None:
    nfse_py = _agente_isolado(tmp / "ajuda")
    r = _rodar(nfse_py, "--ajuda")
    s.check(r.returncode == 0, f"--ajuda sai com código 0 (veio {r.returncode}, stderr={r.stderr[:300]!r})")
    s.check("--somente-lista" in r.stdout, "--ajuda lista as opções conhecidas")
    # main() grava o cabeçalho "Execução iniciada" no log ANTES de parse_args()
    # rodar — pré-existente a esta sessão, não uma regressão; --ajuda não é
    # totalmente livre de efeito colateral, só não toca config/certificados/rede.
    s.check(not (nfse_py.parent / "_agente_cache.json").exists(),
           "--ajuda não chega a tentar nenhum handshake (não existe [api] pra ligar o modo agente aqui)")


def teste_bloqueio_por_inadimplencia_sai_codigo_3_sem_tocar_pfx(s: Suite, tmp: Path) -> None:
    pasta = _agente_isolado(tmp / "bloqueado").parent
    (pasta / "certificados").mkdir()
    pfx = pasta / "certificados" / "0001_54283546000126_EMPRESA_s.123456_v.04.03.2027.pfx"
    pfx.write_bytes(b"conteudo-fake-de-certificado-que-nunca-deve-ser-lido")
    mtime_antes = pfx.stat().st_mtime_ns
    conteudo_antes = pfx.read_bytes()

    with FakeAgentAPI() as fake:
        fake.handshake_resposta = handshake_padrao(
            podeExecutar=False, status="Inadimplente",
            mensagem="Assinatura suspensa por inadimplência. Regularize para continuar.",
        )
        chave = "nfse_aaaaaaaa_" + "b" * 32
        (pasta / "config.toml").write_text(
            f'pasta_certificados = "certificados"\npasta_saida = "notas"\n\n'
            f'[api]\nurl = "{fake.url}"\nchave = "{chave}"\n',
            encoding="utf-8",
        )
        r = _rodar(pasta / "nfse.py", "--sem-pausa")

    s.check(r.returncode == 3, f"handshake bloqueado: processo sai com código 3 (veio {r.returncode})")
    s.check("inadimpl" in (r.stdout + r.stderr).lower(),
           "a mensagem do servidor (inadimplência) chega até a saída do programa")
    s.check("EMPRESA" not in r.stdout and "0001" not in r.stdout,
           "o processo nunca chegou a listar/mencionar a empresa do certificado")
    s.check(not (pasta / "notas").exists(), "pasta de saída 'notas' nem chegou a ser criada")

    s.check(pfx.stat().st_mtime_ns == mtime_antes, "o arquivo .pfx não foi modificado (mtime igual)")
    s.check(pfx.read_bytes() == conteudo_antes, "o arquivo .pfx não foi modificado (conteúdo idêntico)")


def teste_chave_revogada_sai_codigo_3(s: Suite, tmp: Path) -> None:
    """401 (chave não cadastrada/revogada) também bloqueia com código 3 —
    mesmo contrato de saída que podeExecutar:false, do ponto de vista de
    quem só olha o exit code de fora (ex.: um agendador de tarefas)."""
    pasta = _agente_isolado(tmp / "revogado").parent
    (pasta / "certificados").mkdir()

    with FakeAgentAPI() as fake:
        fake.chave_valida = "nfse_aaaaaaaa_" + "b" * 32  # só essa é aceita
        (pasta / "config.toml").write_text(
            f'pasta_certificados = "certificados"\npasta_saida = "notas"\n\n'
            f'[api]\nurl = "{fake.url}"\nchave = "nfse_zzzzzzzz_' + "c" * 32 + '"\n',
            encoding="utf-8",
        )
        r = _rodar(pasta / "nfse.py", "--sem-pausa")

    s.check(r.returncode == 3, f"chave inválida: sai com código 3 (veio {r.returncode})")


def teste_modo_legado_sem_api_nao_bate_na_rede(s: Suite, tmp: Path) -> None:
    """Sem [api] no config.toml, o processo nem tenta abrir uma conexão —
    aqui isso é verificado apontando pra uma porta fechada teoricamente
    alcançável (só que nunca é: sem [api], o código que chamaria essa URL
    nem existe no caminho de execução) e confirmando que o processo segue
    até o erro ESPERADO (pasta de certificados vazia), não um erro de rede."""
    pasta = _agente_isolado(tmp / "legado").parent
    (pasta / "certificados").mkdir()  # existe, mas vazia
    (pasta / "config.toml").write_text(
        'pasta_certificados = "certificados"\npasta_saida = "notas"\n', encoding="utf-8",
    )
    r = _rodar(pasta / "nfse.py", "--sem-pausa")
    s.check(r.returncode == 1, f"modo legado, pasta de certificados vazia: erro de configuração comum, código 1 (veio {r.returncode})")
    s.check("certificado" in (r.stdout + r.stderr).lower(),
           "a mensagem de erro é sobre a pasta de certificados vazia, não sobre API/rede")


def main() -> Suite:
    s = Suite("teste_subprocess_agente")
    with tempfile.TemporaryDirectory(prefix="nfse-teste-subprocess-") as tmp_str:
        tmp = Path(tmp_str)
        for nome, fn in list(globals().items()):
            if nome.startswith("teste_") and callable(fn):
                print(f"-- {nome}")
                fn(s, tmp)
    return s


if __name__ == "__main__":
    rodar(main)
