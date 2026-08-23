#!/usr/bin/env python3
"""
Gera o executável nfse.exe, que roda em máquinas sem Python instalado.

    python -m pip install pyinstaller
    python build.py

O resultado vai para dist/nfse/:

    nfse.exe          o programa (logomarca e tabela IBGE embutidas)
    config.toml       configuração, editável pelo usuário
    certificados/     onde o usuário larga os .pfx
    LEIA-ME.txt       instruções curtas

É essa pasta inteira que se copia para o computador de destino. Nada de
instalar Python, nem dependências, nem runtime de navegador.

Requisitos da máquina de destino: Windows 64 bits. As fontes Arial e Microsoft
Sans Serif, exigidas pela NT 008 para o DANFSe, já vêm com o Windows.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DIST = RAIZ / "dist" / "nfse"
# O PyInstaller cria e apaga milhares de arquivos temporários. Fazer isso
# dentro de uma pasta do OneDrive dá PermissionError no meio do build, porque
# o sincronizador segura os arquivos — por isso a compilação acontece fora.
TRABALHO = Path(tempfile.gettempdir()) / "build-nfse"


def _versao_agente() -> str:
    """Lê VERSAO_AGENTE de api_client.py sem importar o módulo — build.py só
    precisa do PyInstaller instalado (ver docstring do arquivo); importar
    api_client.py de verdade puxaria requests/urllib3 junto, uma dependência
    que este script nunca precisou ter."""
    texto = (RAIZ / "api_client.py").read_text(encoding="utf-8")
    m = re.search(r'^VERSAO_AGENTE\s*=\s*"([^"]+)"', texto, re.M)
    return m.group(1) if m else "desconhecida"

LEIAME = """FERRAMENTA NFS-e
=================

Baixa os XML das notas recebidas e emitidas no Portal Nacional NFS-e e gera
o DANFSe (PDF) de cada uma. Nao precisa de Python nem de instalacao.

COMO USAR
---------
1. Coloque os certificados A1 (.pfx) na pasta "certificados". O nome do
   arquivo pode seguir este padrao (recomendado):

       codigoEmpresa_CNPJ_NomeEmpresa_s.SENHA_v.DD.MM.AAAA.pfx

   Exemplo:
       0001_54283546000126_EMPRESA EXEMPLO LTDA_s.123456_v.04.03.2027.pfx

   Mas nao precisa: se o certificado nao tiver a senha no nome, o programa
   usa a senha do "config.toml" (veja o passo 2). O nome so precisa comecar
   com um codigo antes do primeiro "_" - e o que identifica a empresa.

2. Abra o "config.toml" no Bloco de Notas. Se todos os certificados usam a
   MESMA senha, preencha uma vez so:

       senha_padrao = "a-senha-de-todos-os-certificados"

   O programa nunca pede senha na tela - se nenhum certificado tiver senha
   no nome nem no config, ele avisa e para, em vez de ficar esperando.

3. De um duplo clique em "nfse.exe".

Sem parametros, ele baixa tudo do dia 1o do mes atual ate hoje, de todas as
empresas que tiverem certificado na pasta.

A JANELA SO FECHA QUANDO VOCE APERTAR ENTER
--------------------------------------------
Em qualquer situacao - deu tudo certo ou deu erro - a janela preta espera
voce apertar ENTER antes de fechar. Se aparecer uma mensagem de erro, ela
fica na tela ate voce ler; nao tem risco de "piscar e sumir".

Se aparecer um erro e voce nao souber o que fazer, o arquivo dentro da pasta
"logs" (ex.: logs\\nfse_2026-07-26.log) tem a mesma mensagem guardada - abra
com o Bloco de Notas e mande para quem for te ajudar.

O CERTIFICADO NAO E INSTALADO NO WINDOWS
-----------------------------------------
O programa le o arquivo .pfx direto e usa em memoria, a cada execucao. Nada
e adicionado ao gerenciador de certificados do Windows.

OUTRAS OPCOES (prompt de comando, na pasta do programa)
-------------------------------------------------------
    nfse.exe --mes 2026-06              um mes fechado
    nfse.exe --inicio 01/05/2026 --fim 15/05/2026
    nfse.exe --empresa 0001             so uma empresa
    nfse.exe --tipos recebidas          so as recebidas
    nfse.exe --somente-lista            so os CSV, sem baixar
    nfse.exe --sem-pausa                nao espera ENTER (p/ tarefa agendada)
    nfse.exe --ajuda                    lista completa

ONDE FICAM OS ARQUIVOS
----------------------
    notas/{codigo}_{empresa}/{ano-mes}/Recebidas/
    notas/{codigo}_{empresa}/{ano-mes}/Emitidas/

Rodar de novo no mesmo periodo nao baixa nada duas vezes - cada cliente tem
um arquivo "_controle.json" na raiz da pasta dele com as notas ja obtidas.

CLIENTE NOVO: A PRIMEIRA BUSCA VAI MAIS LONGE
----------------------------------------------
Na primeira vez que um certificado aparece (a pasta do cliente ainda nao
tem controle), o programa busca desde a data em "primeira_busca_desde" do
config.toml (padrao 01/01/2026) ate o fim pedido, mesmo que voce so tenha
pedido um mes - assim voce nao precisa lembrar de rodar manualmente com uma
data antiga para trazer o historico de um cliente novo.

CONEXAO COM O PAINEL WEB (OPCIONAL)
------------------------------------
Se o seu escritorio tem uma chave de acesso ao painel SaaS, abra o
"config.toml" e preencha a secao [api] (url e chave) - ela vem comentada
por padrao. Com isso preenchido, cada execucao passa a: validar a licenca
do escritorio, enviar a contagem de notas baixadas por cliente/mes (nunca o
conteudo das notas) e os dados dos certificados (nome, CNPJ ofuscado,
validade - nunca o .pfx nem a senha), e buscar regras de coleta
atualizadas do servidor.

Sem a secao [api] preenchida, o programa roda exatamente como sempre rodou,
sem nenhuma chamada de rede alem do proprio Portal Nacional NFS-e.

ATENCAO
-------
A senha do certificado fica no nome do arquivo ou no config.toml, em texto
simples. Quem tiver acesso a essa pasta tem a senha junto - proteja o
acesso a ela (permissoes da pasta, nao compartilhar por email, etc.).
"""


def executar(comando: list[str]) -> None:
    print("$", " ".join(comando), flush=True)
    resultado = subprocess.run(comando, cwd=RAIZ)
    if resultado.returncode:
        sys.exit(f"Falhou: {' '.join(comando)}")


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        sys.exit("PyInstaller não encontrado. Rode: python -m pip install pyinstaller")

    for pasta in (RAIZ / "build", RAIZ / "dist", TRABALHO):
        shutil.rmtree(pasta, ignore_errors=True)
    TRABALHO.mkdir(parents=True, exist_ok=True)

    # os dois recursos vão embutidos no .exe; o config fica de fora, editável
    executar([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "nfse",
        "--console",
        "--noconfirm",
        "--workpath", str(TRABALHO / "build"),
        "--distpath", str(TRABALHO / "dist"),
        "--specpath", str(TRABALHO),
        "--add-data", f"{RAIZ / 'municipios_ibge.json'}{';'}.",
        "--add-data", f"{RAIZ / 'logo_nfse.png'}{';'}.",
        # danfse é importado dinamicamente pela gerar_pdf() (e continua
        # opcional/degradável); api_client e regras são import de topo de nfse.py
        # (o PyInstaller já os pegaria sozinho) — hidden-import aqui é só reforço
        # explícito, barato e não faz mal duplicar.
        "--paths", str(RAIZ),
        "--hidden-import", "danfse",
        "--hidden-import", "api_client",
        "--hidden-import", "regras",
        "--hidden-import", "reportlab.graphics.barcode.qr",
        "--collect-submodules", "reportlab",
        # cryptography (decifragem do bloco `configuracao` do handshake em
        # api_client.py) traz submódulos nativos que o PyInstaller nem
        # sempre resolve sozinho — coleta explícita, mesmo padrão do reportlab.
        "--collect-all", "cryptography",
        # nada de tkinter/numpy/etc. no pacote
        "--exclude-module", "tkinter",
        "--exclude-module", "unittest",
        "--exclude-module", "pydoc",
        str(RAIZ / "nfse.py"),
    ])

    DIST.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TRABALHO / "dist" / "nfse.exe", DIST / "nfse.exe")
    shutil.copy2(RAIZ / "config.toml", DIST / "config.toml")
    (DIST / "certificados").mkdir(exist_ok=True)
    (DIST / "LEIA-ME.txt").write_text(LEIAME, encoding="utf-8")

    tamanho = (DIST / "nfse.exe").stat().st_size / 1024 / 1024
    print()
    print(f"Pronto: {DIST}")
    print(f"  nfse.exe  {tamanho:.1f} MB  (agente v{_versao_agente()})")
    print("Copie essa pasta inteira para o computador de destino.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
