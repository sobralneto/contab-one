#!/usr/bin/env python3
"""
Geração do DANFSe v2.0 conforme a Nota Técnica nº 008, de 05/05/2026
(SE/CGNFS-e) — "Especificações Técnicas do DANFSe".

O que a NT 008 determina e está implementado aqui:
  * modelo do Anexo I: ordem e disposição obrigatórias dos blocos (2.2.4);
  * A4 retrato, página única, margens de 0,15 a 0,20 cm (2.2, 2.2.1, 2.2.2);
  * borda da página com 1 pt e linhas divisórias com 0,5 pt (2.2.3);
  * sombreamento cinza claro (5%) no cabeçalho, nos títulos de bloco e nos
    campos "Emitente da NFS-e" e "Valor Líquido da NFS-e + IBS/CBS" (2.2.3);
  * fontes Arial nos títulos e Microsoft Sans Serif nos conteúdos, em preto
    sólido: 7 pt negrito caixa alta nos títulos de bloco, 6 pt negrito nos
    títulos de campo (7 pt caixa alta no bloco de identificação) e 7 pt normal
    nos conteúdos (2.4 a 2.4.4);
  * cabeçalho com a logomarca oficial à esquerda, "DANFSe v2.0" ao centro em
    Arial 9 pt negrito e município/ambiente à direita (2.4.3);
  * QR Code de 1,52 x 1,52 cm em X 17,48 cm / Y 1,67 cm, apontando para
    https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave={chave} (2.4.3);
  * aviso "NFS-e SEM VALIDADE JURÍDICA" em vermelho quando tpAmb = 2 (2.4.3);
  * supressão dos blocos Tomador/Destinatário/Intermediário/Tributação
    Municipal quando não se aplicam, com a frase padrão, e realocação do
    espaço para a Descrição do Serviço (2.3.1 a 2.3.3).

A NT 008 também informa (item 1) que a API de geração do DANFSe
(adn.nfse.gov.br/danfse) foi suspensa em 1º de julho de 2026 — gerar o
documento localmente a partir do XML passou a ser o caminho previsto.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

NS = "{http://www.sped.fazenda.gov.br/nfse}"
URL_CONSULTA = "https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave="


def _pasta_recursos() -> Path:
    """Pasta da logomarca e da tabela IBGE.

    Empacotado com PyInstaller, os dois arquivos ficam embutidos e são
    extraídos em tempo de execução para sys._MEIPASS.
    """
    import sys

    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


RAIZ = _pasta_recursos()

# --------------------------------------------------------------------------
# Medidas — a NT 008 especifica tudo em centímetros
# --------------------------------------------------------------------------
CM = 28.3465
LARGURA, ALTURA = 21.0 * CM, 29.7 * CM  # A4 retrato (2.2.1)
MARGEM = 0.175 * CM  # entre 0,15 e 0,20 cm (2.2.2)
ESQ = 0.30 * CM  # início do corpo impresso
LARG_CORPO = 20.40 * CM
COL = [ESQ + i * 5.105 * CM for i in range(4)]  # 4 colunas de ~5,09 cm
FIM = ESQ + LARG_CORPO

ESP_BORDA, ESP_LINHA = 1.0, 0.5  # (2.2.3)
CINZA_5 = HexColor("#F2F2F2")  # sombreamento 5% de densidade
VERMELHO = HexColor("#FF0000")  # M100/Y100

# alturas de linha da NT (item 2.4.5)
H_ID = 0.69 * CM  # bloco de identificação
H_LINHA = 0.645 * CM  # demais blocos

# tamanhos de fonte mínimos (2.4.1 a 2.4.4)
T_BLOCO, T_ROTULO, T_ROTULO_ID, T_CONTEUDO = 7, 6, 7, 7
T_CABECALHO, T_MUNICIPIO, T_AMBIENTE, T_QR = 9, 8, 6, 6


def _registrar_fontes() -> tuple[str, str, str]:
    """Arial para títulos e Microsoft Sans Serif para conteúdos (2.4).

    Fora do Windows cai para as fontes internas do reportlab — o documento
    continua válido, só não usa exatamente as famílias da NT.
    """
    pastas = [Path("C:/Windows/Fonts"), Path.home() / "AppData/Local/Microsoft/Windows/Fonts"]
    arquivos = {"Arial": "arial.ttf", "Arial-Bold": "arialbd.ttf", "MSSansSerif": "micross.ttf"}
    achadas = {}
    for nome, arquivo in arquivos.items():
        for pasta in pastas:
            caminho = pasta / arquivo
            if caminho.exists():
                try:
                    pdfmetrics.registerFont(TTFont(nome, str(caminho)))
                    achadas[nome] = nome
                except Exception:
                    pass
                break
    return (
        achadas.get("Arial", "Helvetica"),
        achadas.get("Arial-Bold", "Helvetica-Bold"),
        achadas.get("MSSansSerif", "Helvetica"),
    )


F_TITULO, F_TITULO_N, F_CONTEUDO = _registrar_fontes()

# --------------------------------------------------------------------------
# Tabelas de domínio do leiaute nacional
# --------------------------------------------------------------------------
TP_EMIT = {"1": "Prestador", "2": "Tomador", "3": "Intermediário"}
C_STAT = {"100": "NFS-e gerada", "101": "NFS-e cancelada", "102": "NFS-e substituída"}
FINALIDADE = {
    "1": "NFS-e regular",
    "2": "NFS-e complementar",
    "3": "NFS-e de ajuste",
    "4": "NFS-e de decisão judicial ou administrativa",
}
OP_SIMPLES = {
    "1": "Não optante",
    "2": "Optante - Microempreendedor Individual (MEI)",
    "3": "Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP)",
}
REG_AP_SN = {
    "1": "Regime de apuração dos tributos federais e municipal pelo Simples Nacional",
    "2": "Regime de apuração dos tributos federais pelo SN e ISSQN por fora do SN",
    "3": "Regime de apuração dos tributos federais e municipal por fora do SN",
}
TRIB_ISSQN = {
    "1": "Operação tributável",
    "2": "Exportação de serviço",
    "3": "Não incidência",
    "4": "Imunidade",
}
RET_ISSQN = {"1": "Não retido", "2": "Retido pelo tomador", "3": "Retido pelo intermediário"}
REG_ESP = {
    "0": "Nenhum",
    "1": "Ato cooperado",
    "2": "Estimativa",
    "3": "Microempresa municipal",
    "4": "Notário ou registrador",
    "5": "Profissional autônomo",
    "6": "Sociedade de profissionais",
}
AMBIENTE = {"1": "Produção", "2": "Homologação"}
AMB_GERADOR = {"1": "Prefeitura", "2": "Sistema Nacional NFS-e", "3": "Prefeitura em ambiente nacional"}

_MUNICIPIOS: dict[str, str] | None = None


def _municipios() -> dict[str, str]:
    global _MUNICIPIOS
    if _MUNICIPIOS is None:
        try:
            _MUNICIPIOS = json.loads((RAIZ / "municipios_ibge.json").read_text(encoding="utf-8"))
        except Exception:
            _MUNICIPIOS = {}
    return _MUNICIPIOS


# --------------------------------------------------------------------------
# Leitura e formatação
# --------------------------------------------------------------------------
def _txt(elemento, caminho: str) -> str:
    if elemento is None:
        return ""
    achado = elemento.find("/".join(NS + p for p in caminho.split("/")))
    return (achado.text or "").strip() if achado is not None else ""


def _no(elemento, caminho: str):
    if elemento is None:
        return None
    return elemento.find("/".join(NS + p for p in caminho.split("/")))


def _ou_traco(valor: str) -> str:
    return valor if valor else "-"


def _limitar(texto: str, maximo: int) -> str:
    """A NT manda completar com reticências quando o campo estoura (2.4.5)."""
    return texto if len(texto) <= maximo else texto[: maximo - 3].rstrip() + "..."


def _doc(numero: str) -> str:
    d = "".join(filter(str.isdigit, numero))
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    return numero or "-"


def _fone(numero: str) -> str:
    d = "".join(filter(str.isdigit, numero))
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return numero or "-"


def _cep(numero: str) -> str:
    d = "".join(filter(str.isdigit, numero))
    return f"{d[:2]}.{d[2:5]}-{d[5:]}" if len(d) == 8 else (numero or "")


def _data(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso[:10]).strftime("%d/%m/%Y")
    except ValueError:
        return iso or "-"


def _data_hora(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        return iso or "-"


def _valor(bruto: str) -> str:
    """Conteúdo dos campos monetários; o 'R$' já vem no rótulo, como no modelo."""
    if not bruto:
        return "-"
    try:
        return f"{float(bruto):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    except ValueError:
        return bruto


def _pct(bruto: str) -> str:
    if not bruto:
        return "-"
    try:
        return f"{float(bruto):.2f}".replace(".", ",")
    except ValueError:
        return bruto


def _cod_trib_nac(codigo: str) -> str:
    d = "".join(filter(str.isdigit, codigo))
    return f"{d[:2]}.{d[2:4]}.{d[4:6]}" if len(d) == 6 else codigo


def _municipio_uf(codigo: str, alternativo: str = "") -> str:
    """'Município / UF' — a NT manda concatenar nome e sigla (2.4.5)."""
    nome = _municipios().get((codigo or "").strip(), "")
    if nome:
        return nome.replace(" - ", " / ")
    return alternativo or "-"


def _ibge_cep(codigo: str, cep: str) -> str:
    """'Código IBGE / CEP' — campos concatenados (2.4.5)."""
    partes = [p for p in ((codigo or "").strip(), _cep(cep)) if p]
    return " / ".join(partes) or "-"


def _endereco(no) -> str:
    partes = [_txt(no, "xLgr"), _txt(no, "nro"), _txt(no, "xCpl"), _txt(no, "xBairro")]
    return _limitar(", ".join(p for p in partes if p and p != "0"), 77) or "-"


# --------------------------------------------------------------------------
# Desenho
# --------------------------------------------------------------------------
class _Folha:
    """Canvas com origem no topo e a grade de 4 colunas da NT 008."""

    def __init__(self, destino: Path):
        self.c = canvas.Canvas(str(destino), pagesize=(LARGURA, ALTURA))
        self.y = 0.30 * CM

    def _py(self, topo: float) -> float:
        return ALTURA - topo

    def borda(self) -> None:
        self.c.setLineWidth(ESP_BORDA)
        self.c.rect(MARGEM, MARGEM, LARGURA - 2 * MARGEM, ALTURA - 2 * MARGEM)
        self.c.setLineWidth(ESP_LINHA)

    def regua(self, topo: float | None = None) -> None:
        self.c.setLineWidth(ESP_LINHA)
        t = self.y if topo is None else topo
        self.c.line(ESQ, self._py(t), FIM, self._py(t))

    def sombra(self, x: float, topo: float, largura: float, altura: float) -> None:
        self.c.setFillColor(CINZA_5)
        self.c.rect(x, self._py(topo + altura), largura, altura, stroke=0, fill=1)
        self.c.setFillColor(HexColor("#000000"))

    def escrever(self, x: float, topo: float, texto: str, fonte: str, tamanho: float,
                 cor=None, centro: float | None = None) -> None:
        self.c.setFont(fonte, tamanho)
        self.c.setFillColor(cor or HexColor("#000000"))
        if centro is not None:
            self.c.drawCentredString(centro, self._py(topo), texto)
        else:
            self.c.drawString(x, self._py(topo), texto)
        self.c.setFillColor(HexColor("#000000"))

    def quebrar(self, texto: str, largura: float, fonte: str, tamanho: float) -> list[str]:
        linhas, atual = [], ""
        for palavra in str(texto).split():
            teste = f"{atual} {palavra}".strip()
            if self.c.stringWidth(teste, fonte, tamanho) <= largura:
                atual = teste
            else:
                if atual:
                    linhas.append(atual)
                while self.c.stringWidth(palavra, fonte, tamanho) > largura and len(palavra) > 1:
                    corte = len(palavra)
                    while corte > 1 and self.c.stringWidth(palavra[:corte], fonte, tamanho) > largura:
                        corte -= 1
                    linhas.append(palavra[:corte])
                    palavra = palavra[corte:]
                atual = palavra
        if atual:
            linhas.append(atual)
        return linhas or [""]

    # -- uma faixa de campos da grade
    def faixa(self, campos: list[tuple], altura: float = H_LINHA, bloco: str = "",
              rotulo_id: bool = False, sombrear_primeiro: bool = False,
              sombrear_ultimo: bool = False, nova_secao: bool = False) -> None:
        """Desenha uma linha de campos.

        Cada campo é (rótulo, valor) ou (rótulo, valor, colunas). Quando `bloco`
        vem preenchido, ele é o título do bloco: fica na primeira coluna, em
        caixa alta e com sombreamento, conforme 2.2.3 e 2.4.1.

        A régua horizontal só é traçada no início de um bloco. No Anexo I não
        há linha entre as faixas de um mesmo bloco — é o que mantém livre a
        área do QR Code, que fica ao lado das faixas de identificação.
        """
        if bloco or nova_secao:
            self.regua()
        topo = self.y
        # o título do bloco ocupa a primeira coluna; os campos começam na segunda
        indice = 1 if bloco else 0
        itens = []
        for campo in campos:
            rotulo, valor = campo[0], campo[1]
            cols = campo[2] if len(campo) > 2 else 1
            x = COL[min(indice, 3)]
            fim = COL[min(indice + cols, 3)] + (5.105 * CM if indice + cols >= 4 else 0)
            itens.append((rotulo, valor, x, min(fim, FIM) - x - 4))
            indice += cols

        # o sombreamento vai antes do texto, senão cobre o que já foi escrito
        if bloco or sombrear_primeiro:
            self.sombra(ESQ, topo, COL[1] - ESQ, altura)
        if sombrear_ultimo:
            self.sombra(COL[3], topo, FIM - COL[3], altura)
        if bloco:
            self.escrever(ESQ + 2, topo + 0.24 * CM, bloco.upper(), F_TITULO_N, T_BLOCO)

        for rotulo, valor, x, largura in itens:
            if rotulo:
                self.escrever(
                    x + 2, topo + 0.24 * CM,
                    rotulo.upper() if rotulo_id else rotulo,
                    F_TITULO_N, T_ROTULO_ID if rotulo_id else T_ROTULO,
                )
            if valor not in ("", None):
                texto = self.quebrar(valor, largura, F_CONTEUDO, T_CONTEUDO)[0]
                self.escrever(x + 2, topo + 0.54 * CM, texto, F_CONTEUDO, T_CONTEUDO)
        self.y += altura

    def caixa_texto(self, rotulo: str, conteudo: str, altura: float,
                    nova_secao: bool = False) -> None:
        """Bloco de texto livre (Descrição do Serviço, Informações Complementares)."""
        if nova_secao:
            self.regua()
        topo = self.y
        self.escrever(ESQ + 2, topo + 0.24 * CM, rotulo, F_TITULO_N, T_ROTULO)
        disponivel = int((altura - 0.30 * CM) / (0.32 * CM))
        linhas = self.quebrar(conteudo or "-", FIM - ESQ - 4, F_CONTEUDO, T_CONTEUDO)
        if len(linhas) > disponivel > 0:
            linhas = linhas[:disponivel]
            linhas[-1] = linhas[-1][:-3] + "..."
        for i, linha in enumerate(linhas):
            self.escrever(ESQ + 2, topo + 0.54 * CM + i * 0.32 * CM, linha, F_CONTEUDO, T_CONTEUDO)
        self.y += altura

    def faixa_aviso(self, texto: str, altura: float = H_LINHA) -> None:
        """Bloco suprimido: só a frase padrão da NT (2.3.1)."""
        self.regua()
        self.escrever(ESQ + 2, self.y + 0.42 * CM, texto, F_TITULO_N, T_BLOCO)
        self.y += altura

    def salvar(self) -> None:
        self.c.save()


# --------------------------------------------------------------------------
# Montagem do DANFSe
# --------------------------------------------------------------------------
def _cabecalho(f: _Folha, inf, dps, municipio_emit: str) -> None:
    altura = 1.16 * CM
    f.sombra(ESQ, 0.30 * CM, LARG_CORPO, altura)

    logo = RAIZ / "logo_nfse.png"
    if logo.exists():
        try:
            f.c.drawImage(
                ImageReader(str(logo)), 0.49 * CM, f._py(0.44 * CM + 0.85 * CM),
                width=4.00 * CM, height=0.85 * CM, mask="auto", preserveAspectRatio=True,
            )
        except Exception:
            pass

    centro = (5.41 * CM + 15.62 * CM) / 2
    f.escrever(0, 0.62 * CM, "DANFSe v2.0", F_TITULO_N, T_CABECALHO, centro=centro)
    f.escrever(0, 0.94 * CM, "Documento Auxiliar da NFS-e", F_TITULO_N, T_CABECALHO, centro=centro)
    if _txt(dps, "tpAmb") == "2":  # produção restrita (2.4.3)
        f.escrever(0, 1.26 * CM, "NFS-e SEM VALIDADE JURÍDICA", F_TITULO_N, T_CABECALHO,
                   cor=VERMELHO, centro=centro)

    x = 15.62 * CM
    for i, linha in enumerate(f.quebrar(f"Município: {municipio_emit}", 5.0 * CM,
                                        F_CONTEUDO, T_MUNICIPIO)[:2]):
        f.escrever(x, 0.56 * CM + i * 0.28 * CM, linha, F_CONTEUDO, T_MUNICIPIO)
    f.escrever(x, 1.13 * CM,
               f"Ambiente Gerador: {AMB_GERADOR.get(_txt(inf, 'ambGer'), '-')}",
               F_CONTEUDO, T_AMBIENTE)
    f.escrever(x, 1.38 * CM,
               f"Tipo de Ambiente: {AMBIENTE.get(_txt(dps, 'tpAmb'), '-')}",
               F_CONTEUDO, T_AMBIENTE)
    f.y = 1.48 * CM


def _qrcode(f: _Folha, chave: str) -> None:
    lado = 1.52 * CM  # dimensão mínima da NT (2.4.3)
    widget = qr.QrCodeWidget(URL_CONSULTA + chave)
    x0, y0, x1, y1 = widget.getBounds()
    desenho = Drawing(lado, lado, transform=[lado / (x1 - x0), 0, 0, lado / (y1 - y0), 0, 0])
    desenho.add(widget)
    renderPDF.draw(desenho, f.c, 17.48 * CM, f._py(1.67 * CM + lado))

    aviso = ("A autenticidade desta NFS-e pode ser verificada pela leitura deste código QR "
             "ou pela consulta da chave de acesso no portal nacional da NFS-e")
    for i, linha in enumerate(f.quebrar(aviso, 4.72 * CM, F_CONTEUDO, T_QR)[:3]):
        f.escrever(15.80 * CM, 3.56 * CM + i * 0.22 * CM, linha, F_CONTEUDO, T_QR)


def _bloco_pessoa(f: _Folha, titulo: str, no_pessoa, endereco, com_im: bool = True) -> None:
    """Prestador, Tomador, Destinatário e Intermediário têm o mesmo formato."""
    f.faixa(
        [
            ("CNPJ / CPF / NIF", _doc(_txt(no_pessoa, "CNPJ") or _txt(no_pessoa, "CPF")
                                      or _txt(no_pessoa, "NIF"))),
            ("Indicador Municipal (Inscrição)", _ou_traco(_txt(no_pessoa, "IM")) if com_im else ""),
            ("Telefone", _fone(_txt(no_pessoa, "fone"))),
        ],
        bloco=titulo,
    )
    f.faixa(
        [
            ("Nome / Nome Empresarial", _limitar(_ou_traco(_txt(no_pessoa, "xNome")), 77), 2),
            ("Município / Sigla UF", _municipio_uf(_txt(endereco, "endNac/cMun")
                                                   or _txt(endereco, "cMun"))),
            ("Código IBGE / CEP", _ibge_cep(_txt(endereco, "endNac/cMun") or _txt(endereco, "cMun"),
                                            _txt(endereco, "endNac/CEP") or _txt(endereco, "CEP"))),
        ]
    )
    f.faixa(
        [
            ("Endereço", _endereco(endereco), 2),
            ("E-mail", _limitar(_ou_traco(_txt(no_pessoa, "email")), 77), 2),
        ]
    )


def gerar(xml: bytes, destino: Path, canhoto: bool = True) -> Path:
    """Gera o DANFSe v2.0 a partir do XML da NFS-e. Devolve o caminho do PDF."""
    raiz = ET.fromstring(xml)
    inf = raiz.find(f"{NS}infNFSe")
    if inf is None:
        raise ValueError("XML sem elemento infNFSe — não é uma NFS-e")

    chave = (inf.get("Id") or "").removeprefix("NFS")
    dps = _no(inf, "DPS/infDPS")
    emit = _no(inf, "emit")
    ender_emit = _no(emit, "enderNac")
    prest = _no(dps, "prest")
    toma = _no(dps, "toma")
    interm = _no(dps, "interm")
    dest = _no(dps, "dest")
    serv = _no(dps, "serv")
    val_nfse = _no(inf, "valores")
    val_dps = _no(dps, "valores")
    trib = _no(val_dps, "trib")
    ibscbs = _no(dps, "IBSCBS")

    municipio_emit = _municipio_uf(_txt(ender_emit, "cMun"), _txt(inf, "xLocEmi"))

    f = _Folha(destino)
    f.borda()
    _cabecalho(f, inf, dps, municipio_emit)

    # ---- Dados de identificação da NFS-e (rótulos em caixa alta, 7 pt)
    # a régua aqui é a que separa o cabeçalho do bloco de identificação
    f.faixa([("Chave de Acesso da NFS-e", chave, 3)], altura=0.79 * CM,
            rotulo_id=True, nova_secao=True)
    f.faixa(
        [
            ("Número da NFS-e", _ou_traco(_txt(inf, "nNFSe"))),
            ("Competência da NFS-e", _data(_txt(dps, "dCompet"))),
            ("Data e Hora da Emissão da NFS-e", _data_hora(_txt(inf, "dhProc"))),
        ],
        altura=H_ID, rotulo_id=True,
    )
    f.faixa(
        [
            ("Número da DPS", _ou_traco(_txt(dps, "nDPS"))),
            ("Série da DPS", _ou_traco(_txt(dps, "serie").lstrip("0"))),
            ("Data e Hora da Emissão da DPS", _data_hora(_txt(dps, "dhEmi"))),
        ],
        altura=H_ID, rotulo_id=True,
    )
    f.faixa(
        [
            ("Emitente da NFS-e", TP_EMIT.get(_txt(dps, "tpEmit"), "-")),
            ("Situação da NFS-e", _limitar(C_STAT.get(_txt(inf, "cStat"), _ou_traco(_txt(inf, "cStat"))), 37)),
            ("Finalidade", _limitar(FINALIDADE.get(_txt(ibscbs, "finNFSe"), "-"), 37)),
        ],
        altura=H_ID, rotulo_id=True, sombrear_primeiro=True,  # campo sombreado (2.2.3)
    )
    _qrcode(f, chave)

    # ---- Prestador / Fornecedor
    # A identificação completa do prestador fica em infNFSe/emit; o nó
    # DPS/infDPS/prest traz só o documento e o regime tributário.
    _bloco_pessoa(f, "Prestador / Fornecedor", emit if emit is not None else prest, ender_emit)
    f.faixa(
        [
            ("Simples Nacional na Data de Competência",
             _limitar(OP_SIMPLES.get(_txt(dps, "prest/regTrib/opSimpNac"), "-"), 37)),
            ("Regime de Apuração Tributária pelo SN",
             _limitar(REG_AP_SN.get(_txt(dps, "prest/regTrib/regApTribSN"), "-"), 77), 3),
        ]
    )

    # ---- Tomador / Adquirente, Destinatário e Intermediário (2.3.1 e 2.3.2)
    sobra = 0.0
    if toma is not None:
        _bloco_pessoa(f, "Tomador / Adquirente", toma, _no(toma, "end"))
    else:
        f.faixa_aviso("TOMADOR/ADQUIRENTE DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e")
        sobra += 2 * H_LINHA

    if dest is not None:
        _bloco_pessoa(f, "Destinatário da Operação", dest, _no(dest, "end"), com_im=False)
    elif toma is not None:
        f.faixa_aviso("O DESTINATÁRIO É O PRÓPRIO TOMADOR/ADQUIRENTE DA OPERAÇÃO")
        sobra += 2 * H_LINHA
    else:
        f.faixa_aviso("DESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e")
        sobra += 2 * H_LINHA

    if interm is not None:
        _bloco_pessoa(f, "Intermediário da Operação", interm, _no(interm, "end"))
    else:
        f.faixa_aviso("INTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e")
        sobra += 2 * H_LINHA

    # ---- Serviço prestado
    trib_mun = _txt(inf, "xTribMun")
    f.faixa(
        [
            ("Código de Tributação Nacional / Municipal",
             " / ".join(p for p in (_cod_trib_nac(_txt(serv, "cServ/cTribNac")),
                                    _txt(serv, "cServ/cTribMun")) if p) or "-"),
            ("Código da NBS", _ou_traco(_txt(serv, "cServ/cNBS"))),
            ("Local da Prestação / Sigla UF / País",
             _municipio_uf(_txt(serv, "locPrest/cLocPrestacao"), _txt(inf, "xLocPrestacao"))),
        ],
        bloco="Serviço Prestado",
    )
    # "SE xTribMun <> '' ENTAO Descrição Municipal SENAO Descrição Nacional" (Anexo I)
    f.caixa_texto("Descrição do Código de Tributação Nacional / Municipal",
                  trib_mun or _txt(inf, "xTribNac"), 0.62 * CM)
    # O espaço liberado pelos blocos suprimidos vai para a Descrição do Serviço
    # (2.3.1); o que sobrar disso desce para as Informações Complementares.
    f.caixa_texto("Descrição do Serviço", _txt(serv, "cServ/xDescServ"),
                  1.10 * CM + min(sobra, 1.9 * CM))

    # ---- Tributação municipal (ISSQN)
    if _txt(trib, "tribMun/tribISSQN"):
        f.faixa(
            [
                ("Tipo de Tributação do ISSQN",
                 TRIB_ISSQN.get(_txt(trib, "tribMun/tribISSQN"), "-")),
                ("Município / Sigla UF / País de Incidência do ISSQN",
                 _municipio_uf(_txt(inf, "cLocIncid"), _txt(inf, "xLocIncid")), 2),
            ],
            bloco="Tributação Municipal (ISSQN)",
        )
        f.faixa(
            [
                ("Regime Especial de Tributação do ISSQN",
                 REG_ESP.get(_txt(dps, "prest/regTrib/regEspTrib"), "-")),
                ("Tipo de Imunidade do ISSQN", _ou_traco(_txt(trib, "tribMun/tpImunidade"))),
                ("Suspensão da Exigibilidade do ISSQN",
                 "Sim" if _txt(trib, "tribMun/tpSusp") else "Não"),
                ("Número Processo Suspensão", _ou_traco(_txt(trib, "tribMun/nProcesso"))),
            ]
        )
        f.faixa(
            [
                ("Benefício Municipal", _ou_traco(_txt(trib, "tribMun/BM/nBM"))),
                ("Cálculo do BM", _ou_traco(_txt(trib, "tribMun/BM/vRedBCBM"))),
                ("Total Deduções/Reduções", _valor(_txt(val_dps, "vDedRed/vDR"))),
                ("Desconto Incondicionado", _valor(_txt(val_dps, "vDescCondIncond/vDescIncond"))),
            ]
        )
        f.faixa(
            [
                ("BC ISSQN  R$", _valor(_txt(val_nfse, "vBC"))),
                ("Alíquota Aplicada  %", _pct(_txt(val_nfse, "pAliqAplic"))),
                ("Retenção do ISSQN", RET_ISSQN.get(_txt(trib, "tribMun/tpRetISSQN"), "-")),
                ("ISSQN Apurado  R$", _valor(_txt(val_nfse, "vISSQN"))),
            ]
        )
    else:
        f.faixa_aviso("TRIBUTAÇÃO MUNICIPAL (ISSQN) - OPERAÇÃO NÃO SUJEITA AO ISSQN")

    # ---- Tributação federal (exceto CBS)
    f.faixa(
        [
            ("IRRF  R$", _valor(_txt(trib, "tribFed/vRetIRRF"))),
            ("Contribuição Previdenciária - Retida  R$", _valor(_txt(trib, "tribFed/vRetCP"))),
            ("Contribuições Sociais - Retidas  R$", _valor(_txt(trib, "tribFed/vRetCSLL")), 2),
        ],
        bloco="Tributação Federal (Exceto CBS)",
    )
    f.faixa(
        [
            ("PIS - Débito Apuração Própria  R$", _valor(_txt(trib, "tribFed/piscofins/vPis"))),
            ("COFINS - Débito Apuração Própria  R$", _valor(_txt(trib, "tribFed/piscofins/vCofins"))),
            ("Descrição Contrib. Sociais - Retidas", "-", 2),
        ]
    )

    # ---- Tributação IBS / CBS (leiaute da reforma tributária)
    g = _no(ibscbs, "gIBSCBS")
    f.faixa(
        [
            ("CST / cClassTrib",
             " / ".join(p for p in (_txt(g, "CST"), _txt(g, "cClassTrib")) if p) or "-"),
            ("Indicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF",
             _ou_traco(_txt(g, "indOperacao")), 3),
        ],
        bloco="Tributação IBS / CBS",
    )
    f.faixa(
        [
            ("Exclusões e Reduções da Base de Cálculo  R$", _valor(_txt(g, "gIBSCBSValores/vExclusao"))),
            ("Base de Cálculo Após Exclusões e Reduções  R$", _valor(_txt(g, "gIBSCBSValores/vBC"))),
            ("Red. Alíquota IBS / Red. Alíquota CBS  %", "-"),
            ("Alíquota - IBS UF / IBS Mun  %", "-"),
        ]
    )
    f.faixa(
        [
            ("Alíq. Efetiva Municipal - IBS  %", _pct(_txt(g, "gIBSMun/pIBSMun"))),
            ("Valor Apurado Municipal - IBS  R$", _valor(_txt(g, "gIBSMun/vIBSMun"))),
            ("Alíq. Efetiva Estadual - IBS  %", _pct(_txt(g, "gIBSUF/pIBSUF"))),
            ("Valor Apurado Estadual - IBS  R$", _valor(_txt(g, "gIBSUF/vIBSUF"))),
        ]
    )
    f.faixa(
        [
            ("Valor Total Apurado - IBS  R$", _valor(_txt(g, "vIBS"))),
            ("Alíquota - CBS  %", _pct(_txt(g, "gCBS/pCBS"))),
            ("Alíquota Efetiva - CBS  %", _pct(_txt(g, "gCBS/pCBSEfet"))),
            ("Valor Total Apurado - CBS  R$", _valor(_txt(g, "gCBS/vCBS"))),
        ]
    )

    # ---- Valor total da NFS-e
    f.faixa(
        [
            ("Valor da Operação / Serviço  R$", _valor(_txt(val_dps, "vServPrest/vServ"))),
            ("Desconto Incondicionado  R$", _valor(_txt(val_dps, "vDescCondIncond/vDescIncond"))),
            ("Desconto Condicionado  R$", _valor(_txt(val_dps, "vDescCondIncond/vDescCond")), 2),
        ],
        altura=H_ID, bloco="Valor Total da NFS-e",
    )
    f.faixa(
        [
            ("Total das Retenções (ISSQN / Federais)  R$", _valor(_txt(val_nfse, "vTotalRetFed"))),
            ("Valor Líquido da NFS-e  R$", _valor(_txt(val_nfse, "vLiq"))),
            ("Total do IBS/CBS  R$", _valor(_txt(g, "vTotIBSCBS"))),
            ("Valor Líquido da NFS-e + IBS/CBS  R$", _valor(_txt(val_nfse, "vLiq"))),
        ],
        altura=H_ID,
        sombrear_ultimo=True,  # campo sombreado por exigência do item 2.2.3
    )

    # ---- Informações complementares
    f.regua()
    topo_info = f.y
    f.sombra(ESQ, topo_info, LARG_CORPO, 0.39 * CM)
    f.escrever(ESQ + 2, topo_info + 0.27 * CM, "INFORMAÇÕES COMPLEMENTARES", F_TITULO_N, T_BLOCO)
    f.y += 0.39 * CM

    complementares = []
    for rotulo, caminho in (("Imóvel", "serv/infoCompl/imovel"), ("Obra", "serv/infoCompl/obra"),
                            ("Evento", "serv/infoCompl/evento")):
        if _no(dps, caminho) is not None:
            complementares.append(f"{rotulo}: " + " ".join(
                (e.text or "").strip() for e in _no(dps, caminho).iter() if (e.text or "").strip()))
    if info := _txt(serv, "infoCompl/xInfComp"):
        complementares.append(info)
    totais = _totais_aproximados(trib)
    if totais:
        complementares.append(totais)

    fim_info = (28.10 * CM) if canhoto else (29.05 * CM)
    for i, linha in enumerate(_quebrar_lista(f, complementares, fim_info - f.y)):
        f.escrever(ESQ + 2, f.y + 0.26 * CM + i * 0.32 * CM, linha, F_CONTEUDO, T_CONTEUDO)
    f.y = fim_info

    # ---- Canhoto (opcional, item 2.1.13)
    if canhoto:
        f.faixa(
            [
                ("Data Cientificação", ""),
                ("Identificação e Assinatura", ""),
                ("Nº NFS-e / Chave NFS-e", f"{_txt(inf, 'nNFSe')} / {chave}", 2),
            ],
            altura=H_ID, nova_secao=True,
        )
        f.regua()

    f.salvar()
    return destino


def _totais_aproximados(trib) -> str:
    """Totais aproximados dos tributos (Lei nº 12.741/2012) — vão nas
    informações complementares, conforme o Anexo I. O leiaute admite valor em
    R$, percentual por esfera ou o percentual único do Simples Nacional."""
    if sn := _txt(trib, "totTrib/pTotTribSN"):
        return f"Totais Aproximados dos Tributos cfe. Lei nº 12.741/2012: Simples Nacional: {_pct(sn)}%"
    base = "Totais Aproximados dos Tributos cfe. Lei nº 12.741/2012: "
    if _txt(trib, "totTrib/pTotTrib/pTotTribFed"):
        return base + "; ".join(
            f"{r}: {_pct(_txt(trib, f'totTrib/pTotTrib/pTotTrib{t}'))}%"
            for r, t in (("Federais", "Fed"), ("Estaduais", "Est"), ("Municipais", "Mun"))
        )
    if _txt(trib, "totTrib/vTotTrib/vTotTribFed"):
        return base + "; ".join(
            f"{r}: R$ {_valor(_txt(trib, f'totTrib/vTotTrib/vTotTrib{t}'))}"
            for r, t in (("Federais", "Fed"), ("Estaduais", "Est"), ("Municipais", "Mun"))
        )
    return ""


def _quebrar_lista(f: _Folha, itens: list[str], altura: float) -> list[str]:
    linhas: list[str] = []
    for item in itens:
        linhas.extend(f.quebrar(item, FIM - ESQ - 4, F_CONTEUDO, T_CONTEUDO))
    cabem = max(int((altura - 0.26 * CM) / (0.32 * CM)), 0)
    if len(linhas) > cabem:
        linhas = linhas[:cabem]
        if linhas:
            linhas[-1] = linhas[-1][:-3] + "..."
    return linhas


def gerar_de_arquivo(caminho_xml: Path, destino: Path | None = None, canhoto: bool = True) -> Path:
    caminho_xml = Path(caminho_xml)
    destino = destino or caminho_xml.with_suffix(".pdf")
    return gerar(caminho_xml.read_bytes(), destino, canhoto=canhoto)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        sys.exit("uso: python danfse.py nota.xml [saida.pdf]")
    saida = gerar_de_arquivo(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    print(f"gerado: {saida}")
