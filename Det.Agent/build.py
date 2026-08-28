#!/usr/bin/env python3
"""
Gera o executável det.exe, que roda em máquinas sem Python nem Node instalados.

    python -m pip install pyinstaller
    python build.py

O resultado vai para dist/det/:

    det.exe            o programa (Playwright + driver Node embutidos)
    config/            configuração, editável no Bloco de Notas
    certificado/       onde o usuário larga o .pfx do escritório
    empresas/          onde o usuário larga o empresas.xlsx
    .env.exemplo       modelo do arquivo com a senha do certificado
    LEIA-ME.txt        instruções curtas

É essa pasta inteira que se copia para o computador de destino.

O QUE A MÁQUINA DE DESTINO PRECISA TER
--------------------------------------
Windows 64 bits e **Google Chrome instalado**. O Chrome não é embutido de
propósito: a autenticação no gov.br é um handshake TLS com certificado de
cliente, conduzido pelo navegador junto à CryptoAPI do Windows -- é por isso
que o robô sobe o Chrome real (`channel="chrome"`) em vez do Chromium que o
Playwright normalmente baixa. Ver o cabeçalho de `navegador.py`.

Python e Node NÃO precisam estar instalados: o Node vem embutido: o
Playwright fala com o navegador através de um driver Node próprio
(`playwright/driver/node.exe`, ~100 MB), que o `--collect-all playwright`
empacota junto. Sem ele o .exe compila e falha só na hora de abrir o
navegador, na máquina do cliente -- por isso a checagem explícita mais
abaixo.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DIST = RAIZ / "dist" / "det"
# O PyInstaller cria e apaga milhares de arquivos temporários. Fazer isso
# dentro de uma pasta sincronizada (OneDrive) ou servida por IIS dá
# PermissionError no meio do build -- por isso a compilação acontece fora.
TRABALHO = Path(tempfile.gettempdir()) / "build-det"

LEIAME = """ROBO DET - Domicilio Eletronico Trabalhista
============================================

Le a Caixa Postal do DET de varias empresas, uma a uma, usando o certificado
digital do escritorio e a procuracao de cada cliente. Nao precisa de Python
nem de instalacao.

ANTES DE USAR (uma vez so)
--------------------------
1. CERTIFICADO: coloque o arquivo .pfx do escritorio na pasta
   "certificado". Pode ser um arquivo so - o programa acha sozinho,
   independente do nome. Quando renovar o certificado, troque o arquivo
   pelo novo; nao precisa mexer em configuracao.

2. SENHA: renomeie ".env.exemplo" para ".env", abra no Bloco de Notas e
   preencha a senha do certificado:

       DET_PFX_SENHA=asenhadocertificado

3. GOOGLE CHROME: precisa estar instalado na maquina. O programa abre o
   Chrome de verdade - e assim que o certificado digital funciona.

A CADA EXECUCAO
---------------
1. Coloque a planilha das empresas na pasta "empresas", com o nome
   empresas.xlsx. O formato e simples:

       Coluna A = CNPJ        Coluna B = Nome da empresa

   A primeira linha pode ser o cabecalho (CNPJ / Nome) ou ja o primeiro
   dado - o programa entende os dois casos.

2. De um duplo clique em "det.exe".

3. O resultado sai na pasta "resultado", num arquivo com a data do dia:

       resultado\\2026-08-22_resultado-det.csv

   E um CSV que abre no Excel com duplo clique, com as colunas
   CNPJ | Nome | Titulo | Mensagem.

TODA EMPRESA APARECE NO RESULTADO
----------------------------------
Mesmo quem nao tem mensagem nova aparece, com o titulo "Sem mensagens" -
assim voce sabe que ela foi consultada de verdade. Os outros casos:

    Sem procuracao   o escritorio nao tem (ou perdeu) a procuracao desse
                     CNPJ no DET. A mensagem traz o texto exato do portal.
    Erro             algo impediu a consulta (CNPJ invalido, portal fora
                     do ar, etc). A mensagem diz em que passo parou.

A JANELA SO FECHA QUANDO VOCE APERTAR ENTER
--------------------------------------------
Deu certo ou deu erro, a janela preta espera o ENTER. Nao tem risco de
"piscar e sumir" levando junto a mensagem de erro.

Se aparecer um erro e voce nao souber o que fazer, o arquivo dentro da
pasta "logs" tem a mesma mensagem guardada - abra com o Bloco de Notas e
mande para quem for te ajudar.

O CAPTCHA E O CERTIFICADO
-------------------------
O gov.br as vezes pede CAPTCHA no login. O programa nao resolve CAPTCHA:
ele avisa na tela e espera voce resolver na janela do Chrome que abriu.

Evite rodar varias vezes seguidas em poucos minutos - o gov.br passa a
recusar as tentativas de login. Se precisar repetir, espere uns 10 minutos.

OUTRAS OPCOES (prompt de comando, na pasta do programa)
-------------------------------------------------------
    det.exe --empresa 12345678000199    so uma empresa da planilha
    det.exe --empresas-arquivo outra.xlsx   usa outra planilha
    det.exe --sem-pausa                 nao espera ENTER (tarefa agendada)
    det.exe --dump                      salva print da tela p/ diagnostico
    det.exe --limpar-perfil             descarta o login salvo
    det.exe --help                      lista completa

ONDE FICAM OS ARQUIVOS
----------------------
    resultado\\    o CSV que voce veio buscar
    dados\\        o mesmo conteudo em JSON (para integracao)
    logs\\         o que aconteceu em cada execucao
    debug\\        prints de tela quando algo falha
    perfis\\       a sessao do navegador (evita relogar toda hora)

ATENCAO - DADOS DE CLIENTE
---------------------------
As pastas "resultado", "dados" e "debug" contem mensagens e dados dos seus
clientes, e a pasta ".env" contem a senha do certificado. Proteja o acesso
a esta pasta (permissoes, nao compartilhar por e-mail).
"""

ENV_EXEMPLO = """# Renomeie este arquivo para .env (sem o .exemplo) e preencha.

# Senha do certificado .pfx que esta na pasta certificado/
DET_PFX_SENHA=
"""


def executar(comando: list[str]) -> None:
    print("$", " ".join(comando), flush=True)
    resultado = subprocess.run(comando, cwd=RAIZ)
    if resultado.returncode:
        sys.exit(f"Falhou: {' '.join(comando)}")


def _driver_playwright() -> Path:
    """Confere que o driver Node do Playwright existe antes de compilar.

    Sem ele o .exe compila normalmente e só quebra na máquina do cliente, na
    hora de abrir o navegador -- o pior momento possível para descobrir.
    """
    import playwright

    driver = Path(playwright.__file__).parent / "driver"
    node = driver / "node.exe"
    if not node.is_file():
        sys.exit(
            f"Driver do Playwright nao encontrado em {driver}.\n"
            "Rode: python -m pip install --force-reinstall playwright"
        )
    return driver


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        sys.exit("PyInstaller nao encontrado. Rode: python -m pip install pyinstaller")

    try:
        driver = _driver_playwright()
    except ImportError:
        sys.exit("Playwright nao encontrado. Rode: python -m pip install -r requirements.txt")

    tamanho_driver = sum(f.stat().st_size for f in driver.rglob("*") if f.is_file())
    print(f"Driver Playwright: {driver} ({tamanho_driver / 1024 / 1024:.0f} MB)")

    for pasta in (RAIZ / "build", RAIZ / "dist", TRABALHO):
        shutil.rmtree(pasta, ignore_errors=True)
    TRABALHO.mkdir(parents=True, exist_ok=True)

    executar([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "det",
        "--console",
        "--noconfirm",
        "--workpath", str(TRABALHO / "build"),
        "--distpath", str(TRABALHO / "dist"),
        "--specpath", str(TRABALHO),
        "--paths", str(RAIZ / "src"),
        # Traz o pacote inteiro do Playwright, incluindo driver/node.exe --
        # é o que dispensa Node na máquina de destino.
        "--collect-all", "playwright",
        # Importados pelo pacote mas não visíveis à análise estática do
        # PyInstaller a partir do entry point.
        "--hidden-import", "det_bot.relatorio",
        "--hidden-import", "openpyxl",
        "--hidden-import", "dotenv",
        # Nada de GUI/científico no pacote.
        "--exclude-module", "tkinter",
        "--exclude-module", "unittest",
        "--exclude-module", "pydoc",
        "--exclude-module", "numpy",
        "--exclude-module", "PIL",
        str(RAIZ / "run.py"),
    ])

    DIST.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TRABALHO / "dist" / "det.exe", DIST / "det.exe")

    # Config vai de fora, editável -- o .example, nunca o config real (que
    # pode conter caminhos e ajustes da máquina de desenvolvimento).
    (DIST / "config").mkdir(exist_ok=True)
    shutil.copy2(RAIZ / "config" / "empresas.example.json",
                 DIST / "config" / "empresas.json")

    # Pastas que o usuário preenche. Vão vazias, com um aviso dentro, para
    # que ele não precise adivinhar que elas devem existir.
    (DIST / "certificado").mkdir(exist_ok=True)
    (DIST / "certificado" / "COLOQUE-O-PFX-AQUI.txt").write_text(
        "Coloque aqui o arquivo .pfx do certificado do escritorio.\n"
        "Pode ser um arquivo so; o programa acha sozinho pelo nome.\n",
        encoding="utf-8",
    )
    (DIST / "empresas").mkdir(exist_ok=True)
    (DIST / "empresas" / "COLOQUE-O-EMPRESAS-XLSX-AQUI.txt").write_text(
        "Coloque aqui a planilha com o nome: empresas.xlsx\n"
        "Coluna A = CNPJ | Coluna B = Nome da empresa\n",
        encoding="utf-8",
    )

    (DIST / ".env.exemplo").write_text(ENV_EXEMPLO, encoding="utf-8")
    (DIST / "LEIA-ME.txt").write_text(LEIAME, encoding="utf-8")

    tamanho = (DIST / "det.exe").stat().st_size / 1024 / 1024
    print()
    print(f"Pronto: {DIST}")
    print(f"  det.exe  {tamanho:.1f} MB")
    print("Copie essa pasta inteira para o computador de destino.")
    print("A maquina de destino precisa ter o Google Chrome instalado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
