"""Carregamento e validação da configuração do robô.

A configuração vive em um JSON externo (``config/empresas.json``) para que
seletores, URLs e parâmetros possam ser ajustados sem tocar no código --
requisito importante em portais governamentais, que mudam layout sem aviso.

Os **segredos e a lista de trabalho** ficam fora desse JSON: a senha do
certificado e os CNPJs a consultar vêm do ``.env`` (ver :mod:`det_bot.fontes`).
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .erros import ErroRobo
from .seletores import SELETORES_PADRAO

# Modos de fornecimento do certificado digital ao navegador.
MODO_MANUAL = "manual"          # operador escolhe o certificado na janela do Chrome
MODO_POLITICA = "politica_chrome"  # política AutoSelectCertificateForUrls
MODO_PFX = "playwright_pfx"     # Playwright injeta o .pfx na camada TLS
MODOS_CERTIFICADO = (MODO_MANUAL, MODO_POLITICA, MODO_PFX)

# Origens da lista de empresas. Hoje só a planilha Excel; "api" entra aqui
# quando a integração existir (ver det_bot.fontes).
FONTE_EXCEL = "excel"
FONTES_EMPRESAS = (FONTE_EXCEL,)

def _raiz_do_projeto() -> Path:
    """Pasta que contém ``config/``, ``certificado/``, ``empresas/``, ``resultado/``.

    Rodando do código-fonte é a raiz do repositório
    (``<raiz>/src/det_bot/settings.py`` -> ``parents[2]``).

    **Congelado pelo PyInstaller é outra coisa:** ``__file__`` aponta para a
    pasta temporária onde o ``--onefile`` se descompacta (``sys._MEIPASS``),
    que é apagada ao sair. Usar essa pasta faria o robô procurar o
    certificado e a planilha dentro do temporário -- e gravar o resultado
    lá, onde o usuário nunca acharia. Ao lado do ``.exe`` é o único lugar
    que o operador enxerga e onde ele deposita os arquivos.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


RAIZ_PADRAO = _raiz_do_projeto()

# Convenções fixas de onde os arquivos de entrada moram, para que o operador
# só precise depositar o arquivo certo no lugar certo -- sem editar o JSON a
# cada renovação de certificado ou a cada planilha nova recebida.
DIR_CERTIFICADO_PADRAO = "certificado"
EMPRESAS_ARQUIVO_PADRAO = "empresas/empresas.xlsx"


# ---------------------------------------------------------------------- #
# CNPJ
# ---------------------------------------------------------------------- #
def normalizar_cnpj(valor: str | None) -> str:
    """Reduz o CNPJ aos 14 dígitos, aceitando qualquer pontuação."""
    return re.sub(r"\D", "", valor or "")


def formatar_cnpj(valor: str | None) -> str:
    """Devolve 00.000.000/0000-00; se não tiver 14 dígitos, devolve como veio."""
    d = normalizar_cnpj(valor)
    if len(d) != 14:
        return valor or ""
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


# Pesos do módulo 11 para os dígitos verificadores do CNPJ. Escritos por
# extenso de propósito: a forma "esperta" de gerá-los por aritmética modular
# é fácil de errar por um, e o sintoma seria rejeitar CNPJ bom em silêncio.
_PESOS_DV1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_PESOS_DV2 = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def cnpj_valido(valor: str | None) -> bool:
    """Confere os dois dígitos verificadores do CNPJ.

    Serve para pegar erro de digitação no ``.env`` antes de o robô consultar
    a empresa errada -- ou travar numa tela de erro do portal.
    """
    d = normalizar_cnpj(valor)
    if len(d) != 14 or len(set(d)) == 1:
        return False
    for pesos in (_PESOS_DV1, _PESOS_DV2):
        soma = sum(int(d[i]) * peso for i, peso in enumerate(pesos))
        resto = soma % 11
        esperado = 0 if resto < 2 else 11 - resto
        if int(d[len(pesos)]) != esperado:
            return False
    return True


# ---------------------------------------------------------------------- #
# Empresa
# ---------------------------------------------------------------------- #
@dataclass(slots=True)
class Empresa:
    """Uma empresa cliente cuja Caixa Postal será lida.

    O **CNPJ é a chave**: é ele que o robô digita na troca de perfil do DET
    para assumir a procuração. O nome é apenas rótulo de log e de JSON.
    """

    cnpj: str
    nome: str | None = None
    id: str | None = None
    # Subdiretório do perfil persistente do Chrome. Normalmente vazio, para
    # herdar o perfil compartilhado do escritório.
    perfil_navegador: str | None = None
    ativo: bool = True

    def __post_init__(self) -> None:
        if not normalizar_cnpj(self.cnpj):
            raise ErroRobo(f"Empresa sem CNPJ utilizavel: {self.cnpj!r}")
        self.id = self.id or self.cnpj_digitos
        self.nome = self.nome or self.cnpj_formatado

    @property
    def cnpj_digitos(self) -> str:
        return normalizar_cnpj(self.cnpj)

    @property
    def cnpj_formatado(self) -> str:
        return formatar_cnpj(self.cnpj)

    @property
    def dir_perfil(self) -> str:
        """Subdiretório do perfil do Chrome usado por esta empresa."""
        return self.perfil_navegador or self.id or self.cnpj_digitos


# ---------------------------------------------------------------------- #
# Config
# ---------------------------------------------------------------------- #
@dataclass(slots=True)
class Config:
    """Configuração global de execução."""

    raiz: Path = RAIZ_PADRAO
    url_portal: str = "https://det.sit.trabalho.gov.br/"
    urls_caixa_postal: list[str] = field(default_factory=list)
    padroes_url_autenticado: list[str] = field(default_factory=list)
    padroes_url_login: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Certificado -- um só, do escritório contábil, para todos os clientes
    # ------------------------------------------------------------------ #
    modo_certificado: str = MODO_PFX
    certificado_pfx: str | None = None
    # Nome da variável de ambiente com a senha do .pfx. A senha NUNCA fica
    # no JSON de configuração.
    certificado_senha_env: str = "DET_PFX_SENHA"
    # Origem que exige o certificado de cliente no fluxo gov.br. Fica
    # configurável porque é o host que o Playwright precisa casar para
    # apresentar o .pfx -- e porque permite apontar para um servidor de
    # teste ao validar o handshake.
    origem_certificado: str = "https://certificado.sso.acesso.gov.br"
    # Usado apenas no modo "politica_chrome".
    filtro_certificado: dict[str, Any] | None = None

    # Tipo de perfil a assumir na troca dentro do DET: o escritório entra
    # como procurador de cada empresa cliente.
    tipo_perfil_det: str = "Procurador"

    # Origem da lista de empresas.
    fonte_empresas: str = FONTE_EXCEL
    # Planilha usada quando fonte_empresas == "excel": coluna A = CNPJ,
    # coluna B = Nome. Caminho relativo resolve a partir de `raiz`. Padrão
    # fixo: a pasta "empresas/" sempre guarda o arquivo mais recente
    # recebido, sob o mesmo nome -- assim nao ha JSON para editar a cada
    # planilha nova.
    empresas_arquivo: str | None = EMPRESAS_ARQUIVO_PADRAO

    # Perfil de navegador herdado por empresas que não declaram o seu. Com
    # uma identidade gov.br única, o compartilhamento é o caso normal: um
    # login serve para todos os clientes.
    perfil_navegador_padrao: str | None = "escritorio"

    dir_perfis: Path = RAIZ_PADRAO / "perfis"
    dir_saida: Path = RAIZ_PADRAO / "dados"
    dir_debug: Path = RAIZ_PADRAO / "debug"
    dir_logs: Path = RAIZ_PADRAO / "logs"
    # Onde sai o CSV que o contador abre. Separado de `dir_saida` (JSON
    # técnico, uma pasta que enche de arquivos) justamente para ser a pasta
    # limpa que o usuário do executável olha.
    dir_resultado: Path = RAIZ_PADRAO / "resultado"

    canal_navegador: str = "chrome"  # chrome | msedge | chromium
    headless: bool = False
    fechar_navegador: bool = True

    timeout_padrao_ms: int = 30_000
    timeout_navegacao_ms: int = 60_000
    # Tempo tolerado entre iniciar a autenticação e o portal responder
    # autenticado. Generoso: envolve handshake TLS e redirecionamentos
    # encadeados do gov.br (e, no modo manual, um diálogo humano).
    timeout_login_ms: int = 180_000
    max_paginas: int = 30
    pausa_entre_empresas_s: float = 3.0
    # Clica em cada mensagem não lida para capturar o texto completo do
    # painel de detalhe. Mais lento (uma navegação por mensagem) -- desligar
    # deixa a leitura restrita aos metadados da listagem.
    ler_corpo_mensagens: bool = True

    seletores: dict[str, list[str]] = field(default_factory=dict)
    empresas: list[Empresa] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Fábrica
    # ------------------------------------------------------------------ #
    @classmethod
    def carregar(cls, caminho: str | Path | None = None) -> Config:
        """Carrega a configuração de um JSON, aplicando os padrões do código.

        Não valida: as empresas ainda não foram carregadas neste ponto (elas
        vêm do ``.env``). Quem monta tudo e valida é
        :func:`det_bot.fontes.montar_configuracao`.
        """
        cfg = cls()
        cfg.seletores = {k: list(v) for k, v in SELETORES_PADRAO.items()}
        # Confirmado contra o portal real 2026-08-21: a rota e uma palavra
        # so, sem hifen (componente Angular "app-caixapostal-page").
        cfg.urls_caixa_postal = [
            "https://det.sit.trabalho.gov.br/caixapostal",
        ]
        cfg.padroes_url_autenticado = [r"det\.sit\.trabalho\.gov\.br"]
        cfg.padroes_url_login = [
            r"sso\.acesso\.gov\.br",
            r"certificado\.sso\.acesso\.gov\.br",
            r"acesso\.gov\.br/login",
        ]

        if caminho is None:
            return cfg

        arquivo = Path(caminho)
        if not arquivo.is_file():
            raise ErroRobo(f"Arquivo de configuracao nao encontrado: {arquivo}")

        try:
            bruto = json.loads(arquivo.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ErroRobo(f"JSON invalido em {arquivo}: {exc}") from exc

        cfg._aplicar(bruto, base=arquivo.parent)
        return cfg

    def _aplicar(self, bruto: dict[str, Any], base: Path) -> None:
        """Sobrescreve os padrões com o conteúdo do JSON."""
        simples = (
            "url_portal",
            "modo_certificado",
            "certificado_pfx",
            "certificado_senha_env",
            "origem_certificado",
            "filtro_certificado",
            "tipo_perfil_det",
            "fonte_empresas",
            "empresas_arquivo",
            "perfil_navegador_padrao",
            "canal_navegador",
            "headless",
            "fechar_navegador",
            "timeout_padrao_ms",
            "timeout_navegacao_ms",
            "timeout_login_ms",
            "max_paginas",
            "pausa_entre_empresas_s",
            "ler_corpo_mensagens",
        )
        for chave in simples:
            if chave in bruto:
                setattr(self, chave, bruto[chave])

        for chave in ("urls_caixa_postal", "padroes_url_autenticado", "padroes_url_login"):
            if bruto.get(chave):
                setattr(self, chave, list(bruto[chave]))

        for chave in ("dir_perfis", "dir_saida", "dir_debug", "dir_logs", "dir_resultado"):
            if bruto.get(chave):
                caminho = Path(bruto[chave])
                if not caminho.is_absolute():
                    caminho = base / caminho
                # `resolve()` achata o "config\..\resultado" que sairia dos
                # caminhos relativos do JSON: esse caminho vai para o log e
                # é o que o operador lê para achar o arquivo gerado.
                setattr(self, chave, caminho.resolve())

        # Seletores do JSON *substituem* a lista padrão daquela chave,
        # permitindo fixar o seletor exato quando o layout já é conhecido.
        for chave, valores in (bruto.get("seletores") or {}).items():
            if chave.startswith("_"):  # chaves de comentário
                continue
            if not isinstance(valores, list) or not all(isinstance(v, str) for v in valores):
                raise ErroRobo(f"seletores['{chave}'] deve ser uma lista de strings.")
            self.seletores[chave] = list(valores)


    # ------------------------------------------------------------------ #
    # Segredos e certificado
    # ------------------------------------------------------------------ #
    def senha_certificado(self) -> str | None:
        """Lê a senha do .pfx da variável de ambiente configurada."""
        senha = os.getenv(self.certificado_senha_env)
        if not senha and self.modo_certificado == MODO_PFX:
            raise ErroRobo(
                f"Variavel de ambiente '{self.certificado_senha_env}' vazia ou "
                "nao definida. Preencha-a no arquivo .env."
            )
        return senha

    def caminho_certificado(self) -> Path:
        """Resolve o caminho do .pfx.

        Com ``certificado_pfx`` informado, usa exatamente esse caminho
        (relativo à raiz, se não for absoluto) -- útil para desambiguar se um
        dia houver mais de um .pfx na pasta. Sem ele, procura sozinho o
        único ``*.pfx`` dentro de ``certificado/``: o nome do arquivo muda a
        cada renovação (leva a validade no nome), então depender da pasta em
        vez do nome exato evita editar o JSON todo ano.
        """
        if self.certificado_pfx:
            caminho = Path(self.certificado_pfx)
            if not caminho.is_absolute():
                caminho = (self.raiz / caminho).resolve()
            if not caminho.is_file():
                raise ErroRobo(f"Certificado .pfx nao encontrado em: {caminho}")
            return caminho

        pasta = self.raiz / DIR_CERTIFICADO_PADRAO
        if not pasta.is_dir():
            raise ErroRobo(
                f"Pasta de certificado nao encontrada: {pasta}. Coloque ali "
                "o .pfx do escritorio, ou informe 'certificado_pfx' no "
                "config/empresas.json."
            )
        candidatos = sorted(pasta.glob("*.pfx"))
        if not candidatos:
            raise ErroRobo(
                f"Nenhum arquivo .pfx encontrado em '{pasta}'. Coloque ali o "
                "certificado do escritorio."
            )
        if len(candidatos) > 1:
            raise ErroRobo(
                f"Mais de um .pfx em '{pasta}': "
                f"{[c.name for c in candidatos]}. Deixe so o certificado "
                "valido ali, ou informe qual usar em 'certificado_pfx' no "
                "config/empresas.json."
            )
        return candidatos[0]

    def caminho_empresas_arquivo(self) -> Path:
        """Resolve o caminho da planilha de empresas, aceitando caminho relativo à raiz."""
        if not self.empresas_arquivo:
            raise ErroRobo(
                "fonte_empresas='excel' exige 'empresas_arquivo' no "
                "config/empresas.json (ou --empresas-arquivo na linha de comando)."
            )
        caminho = Path(self.empresas_arquivo)
        if not caminho.is_absolute():
            caminho = (self.raiz / caminho).resolve()
        if not caminho.is_file():
            raise ErroRobo(f"Planilha de empresas nao encontrada em: {caminho}")
        return caminho

    # ------------------------------------------------------------------ #
    # Validação e utilidades
    # ------------------------------------------------------------------ #
    def aplicar_perfil_padrao(self) -> None:
        """Faz as empresas sem perfil próprio herdarem o perfil do escritório."""
        if not self.perfil_navegador_padrao:
            return
        for empresa in self.empresas:
            if not empresa.perfil_navegador:
                empresa.perfil_navegador = self.perfil_navegador_padrao

    def validar(self) -> None:
        """Falha cedo em configurações incoerentes, antes de abrir o navegador."""
        if self.modo_certificado not in MODOS_CERTIFICADO:
            raise ErroRobo(
                f"modo_certificado invalido: '{self.modo_certificado}'. "
                f"Use um de {MODOS_CERTIFICADO}."
            )
        if self.fonte_empresas not in FONTES_EMPRESAS:
            raise ErroRobo(
                f"fonte_empresas invalida: '{self.fonte_empresas}'. "
                f"Use um de {FONTES_EMPRESAS}."
            )
        if self.headless and self.modo_certificado == MODO_MANUAL:
            raise ErroRobo(
                "modo_certificado 'manual' exige headless=false: a escolha do "
                "certificado acontece em um dialogo nativo do Windows."
            )
        if self.modo_certificado == MODO_PFX:
            self.caminho_certificado()  # levanta se ausente ou inexistente
            self.senha_certificado()    # levanta se a variavel nao existir

        if not self.empresas:
            raise ErroRobo(
                f"Nenhuma empresa a processar. Confira a planilha "
                f"'{self.empresas_arquivo}' (coluna A = CNPJ, coluna B = Nome)."
            )

        vistos: dict[str, str] = {}
        for empresa in self.empresas:
            digitos = empresa.cnpj_digitos
            if len(digitos) != 14:
                raise ErroRobo(
                    f"CNPJ com {len(digitos)} digito(s), esperado 14: '{empresa.cnpj}'"
                )
            if digitos in vistos:
                raise ErroRobo(
                    f"CNPJ repetido na lista: {empresa.cnpj_formatado} "
                    f"(ids '{vistos[digitos]}' e '{empresa.id}')"
                )
            vistos[digitos] = empresa.id or digitos

    def cnpjs_suspeitos(self) -> list[Empresa]:
        """Empresas cujo CNPJ não passa no dígito verificador.

        Não bloqueia a execução -- homologação costuma usar CNPJ fictício --,
        mas rende um aviso alto no log, porque o sintoma de um CNPJ errado é
        o robô consultar a empresa errada.
        """
        return [e for e in self.empresas if not cnpj_valido(e.cnpj)]

    def preparar_diretorios(self) -> None:
        for pasta in (self.dir_perfis, self.dir_saida, self.dir_debug,
                      self.dir_logs, self.dir_resultado):
            pasta.mkdir(parents=True, exist_ok=True)

    def sel(self, chave: str) -> list[str]:
        """Retorna a lista de seletores candidatos para uma chave lógica."""
        valores = self.seletores.get(chave)
        if not valores:
            raise ErroRobo(f"Seletor '{chave}' nao configurado.")
        return valores

    def empresas_ativas(self, filtro: list[str] | None = None) -> list[Empresa]:
        """Empresas a processar, opcionalmente filtradas por id ou CNPJ."""
        alvo = [e for e in self.empresas if e.ativo]
        if not filtro:
            return alvo

        desejados = {f.strip().lower() for f in filtro if f.strip()}
        digitos = {normalizar_cnpj(d) for d in desejados if normalizar_cnpj(d)}

        def combina(e: Empresa) -> bool:
            return (e.id or "").lower() in desejados or e.cnpj_digitos in digitos

        selecionadas = [e for e in alvo if combina(e)]
        if not selecionadas:
            raise ErroRobo(
                f"Nenhuma empresa ativa corresponde a {sorted(desejados)}. "
                f"Disponiveis: {[e.id for e in alvo]}"
            )
        return selecionadas

    @staticmethod
    def agrupar_por_perfil(empresas: list[Empresa]) -> dict[str, list[Empresa]]:
        """Agrupa empresas pelo perfil de navegador, preservando a ordem.

        Cada grupo é processado com **um único** navegador: uma abertura de
        Chrome e um login, em vez de um por empresa.
        """
        grupos: dict[str, list[Empresa]] = {}
        for empresa in empresas:
            grupos.setdefault(empresa.dir_perfil, []).append(empresa)
        return grupos
