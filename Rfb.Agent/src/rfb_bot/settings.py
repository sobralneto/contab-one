"""Carregamento e validação da configuração do robô.

A configuração vive em um ``config.toml`` externo -- seletores, URLs, lista
de clientes e parâmetros podem ser ajustados sem tocar no código, requisito
importante em um portal em beta que muda de layout sem aviso.

O **segredo** (senha do .pfx) fica fora do TOML: vem do ``.env``, para que
o arquivo de configuração possa ser copiado e discutido sem vazar nada.
"""

from __future__ import annotations

import os
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .erros import ErroRobo
from .seletores import SELETORES_PADRAO

# Modos de fornecimento do certificado digital ao navegador.
MODO_MANUAL = "manual"       # operador escolhe o certificado no diálogo do Chrome
MODO_PFX = "playwright_pfx"  # Playwright injeta o .pfx na camada TLS
MODOS_CERTIFICADO = (MODO_MANUAL, MODO_PFX)

# Origem da lista de clientes: os blocos [[clientes]] do próprio config.toml
# (prático para poucos casos) ou uma planilha Excel (ver rfb_bot.fontes).
FONTE_TOML = "toml"
FONTE_EXCEL = "excel"
FONTES_CLIENTES = (FONTE_TOML, FONTE_EXCEL)

URL_PORTAL_PADRAO = "https://consumo.tributos.gov.br/"
BASE_CREDENCIAL_PADRAO = "https://consumo.tributos.gov.br/servico/credencial-api-beta"
# Rota da SPA aberta após a troca de representação. O POST de criação é
# feito por API, mas a página precisa ser carregada mesmo assim: é ela que
# renova o estado da sessão para o serviço de credencial (e é de onde o
# robô fareja o cabeçalho Authorization -- ver credenciais.Sessao).
ROTA_NOVA_CREDENCIAL = "/credenciais-acesso/nova-credencial/tls"

# Os 3 serviços obrigatórios de toda credencial testada. Ficam como padrão
# no código para que o config.toml possa ser mínimo, mas continuam
# sobrescrevíveis: se o portal passar a exigir um quarto, é uma linha de
# TOML, não um deploy.
SERVICOS_PADRAO = (
    "f3ddfabd-aeb4-4fab-b0c3-e0675d34f016",
    "0b216f6f-5768-4250-9c60-8b17be9abc04",
    "8c8c17eb-9f1e-4297-8a6f-a430bc38fbef",
)


def _raiz_do_projeto() -> Path:
    """Pasta que contém ``config.toml``, ``certificado/``, ``resultado/``.

    Rodando do código-fonte é a raiz do projeto
    (``<raiz>/src/rfb_bot/settings.py`` -> ``parents[2]``).

    **Congelado pelo PyInstaller é outra coisa:** ``__file__`` aponta para a
    pasta temporária onde o ``--onefile`` se descompacta, que é apagada ao
    sair. Usar essa pasta faria o robô procurar o certificado no temporário
    -- e gravar o CSV lá, onde o operador nunca acharia.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


RAIZ_PADRAO = _raiz_do_projeto()

DIR_CERTIFICADO_PADRAO = "certificado"


# ---------------------------------------------------------------------- #
# CNPJ
# ---------------------------------------------------------------------- #
def normalizar_documento(valor: str | None) -> str:
    """Reduz CPF/CNPJ aos dígitos, aceitando qualquer pontuação."""
    return re.sub(r"\D", "", valor or "")


def formatar_cnpj(valor: str | None) -> str:
    """Devolve 00.000.000/0000-00; se não tiver 14 dígitos, devolve como veio."""
    d = normalizar_documento(valor)
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

    Pega erro de digitação no config.toml antes de o robô representar a
    empresa errada -- ou travar numa tela de erro do portal.
    """
    d = normalizar_documento(valor)
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
# Cliente
# ---------------------------------------------------------------------- #
@dataclass(slots=True)
class Cliente:
    """Uma empresa cliente para a qual será gerada uma Chave Secreta.

    O **CNPJ é a chave**: é ele que o robô digita na troca de representação
    para assumir a procuração. ``nome_credencial`` é o campo "Nome" da
    credencial no portal -- é o que o contador vê depois na tela do cliente.
    """

    cnpj: str
    nome_credencial: str
    ativo: bool = True

    def __post_init__(self) -> None:
        if not normalizar_documento(self.cnpj):
            raise ErroRobo(f"Cliente sem CNPJ utilizavel: {self.cnpj!r}")
        if not (self.nome_credencial or "").strip():
            raise ErroRobo(
                f"Cliente {self.cnpj_formatado} sem 'nome_credencial' no config.toml."
            )
        self.nome_credencial = self.nome_credencial.strip()

    @property
    def cnpj_digitos(self) -> str:
        return normalizar_documento(self.cnpj)

    @property
    def cnpj_formatado(self) -> str:
        return formatar_cnpj(self.cnpj)


# ---------------------------------------------------------------------- #
# Config
# ---------------------------------------------------------------------- #
@dataclass(slots=True)
class Config:
    """Configuração global de execução."""

    raiz: Path = RAIZ_PADRAO
    url_portal: str = URL_PORTAL_PADRAO
    base_credencial: str = BASE_CREDENCIAL_PADRAO

    # ------------------------------------------------------------------ #
    # Credencial
    # ------------------------------------------------------------------ #
    validade_anos: int = 5
    servicos_padrao: list[str] = field(default_factory=lambda: list(SERVICOS_PADRAO))
    consentimento_assinatura_qualificada: bool = True
    papel: str = "Procurador"

    # ------------------------------------------------------------------ #
    # Certificado -- um só, do escritório contábil, para todos os clientes
    # ------------------------------------------------------------------ #
    modo_certificado: str = MODO_PFX
    certificado_pfx: str | None = None
    # Nome da variável de ambiente com a senha do .pfx. A senha NUNCA fica
    # no TOML.
    certificado_senha_env: str = "RFB_PFX_SENHA"
    # Origens que exigem o certificado de cliente. É uma lista porque o
    # login pode terminar no host do portal ou no do gov.br, e o Playwright
    # só apresenta o .pfx à origem que casar exatamente.
    origens_certificado: list[str] = field(
        default_factory=lambda: [
            "https://consumo.tributos.gov.br",
            "https://certificado.sso.acesso.gov.br",
        ]
    )

    # ------------------------------------------------------------------ #
    # Saída e diretórios
    # ------------------------------------------------------------------ #
    saida_csv: str = "credenciais_geradas.csv"
    dir_perfil: Path = RAIZ_PADRAO / "perfil"
    dir_resultado: Path = RAIZ_PADRAO / "resultado"
    dir_debug: Path = RAIZ_PADRAO / "debug"
    dir_logs: Path = RAIZ_PADRAO / "logs"

    canal_navegador: str = "chrome"  # chrome | msedge | chromium
    headless: bool = False
    fechar_navegador: bool = True

    timeout_padrao_ms: int = 30_000
    timeout_navegacao_ms: int = 60_000
    # Tempo tolerado entre iniciar a autenticação e o portal responder
    # autenticado. Generoso: envolve handshake TLS, redirecionamentos
    # encadeados e, no modo manual, um diálogo humano.
    timeout_login_ms: int = 180_000
    # Delay entre clientes. Existe para não parecer ataque ao portal em
    # lotes grandes; ver `tentativas_api`/`espera_rate_limit_s` para o que
    # acontece quando ele não basta.
    pausa_entre_clientes_s: float = 2.0
    tentativas_api: int = 3
    espera_rate_limit_s: float = 15.0

    # ------------------------------------------------------------------ #
    # Origem da lista de clientes
    # ------------------------------------------------------------------ #
    fonte_clientes: str = FONTE_TOML
    # Coluna A = CNPJ, coluna B = Nome (vira `nome_credencial`). Caminho
    # relativo resolve a partir de `raiz`.
    clientes_arquivo: str | None = "empresas.xlsx"

    seletores: dict[str, list[str]] = field(default_factory=dict)
    clientes: list[Cliente] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Fábrica
    # ------------------------------------------------------------------ #
    @classmethod
    def carregar(cls, caminho: str | Path) -> Config:
        """Lê o ``config.toml`` aplicando os padrões do código."""
        cfg = cls()
        cfg.seletores = {k: list(v) for k, v in SELETORES_PADRAO.items()}

        arquivo = Path(caminho)
        if not arquivo.is_absolute():
            arquivo = (cfg.raiz / arquivo).resolve()
        if not arquivo.is_file():
            raise ErroRobo(
                f"Arquivo de configuracao nao encontrado: {arquivo}. "
                "Copie config.exemplo.toml para config.toml e preencha."
            )

        try:
            bruto = tomllib.loads(arquivo.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise ErroRobo(f"TOML invalido em {arquivo}: {exc}") from exc

        cfg._aplicar(bruto, base=arquivo.parent)
        return cfg

    def _aplicar(self, bruto: dict[str, Any], base: Path) -> None:
        geral = bruto.get("geral") or {}
        if not isinstance(geral, dict):
            raise ErroRobo("A secao [geral] do config.toml deve ser uma tabela.")

        simples = (
            "url_portal",
            "base_credencial",
            "validade_anos",
            "consentimento_assinatura_qualificada",
            "papel",
            "modo_certificado",
            "certificado_pfx",
            "certificado_senha_env",
            "fonte_clientes",
            "clientes_arquivo",
            "saida_csv",
            "canal_navegador",
            "headless",
            "fechar_navegador",
            "timeout_padrao_ms",
            "timeout_navegacao_ms",
            "timeout_login_ms",
            "pausa_entre_clientes_s",
            "tentativas_api",
            "espera_rate_limit_s",
        )
        for chave in simples:
            if chave in geral:
                setattr(self, chave, geral[chave])

        for chave in ("servicos_padrao", "origens_certificado"):
            if geral.get(chave):
                setattr(self, chave, list(geral[chave]))

        for chave in ("dir_perfil", "dir_resultado", "dir_debug", "dir_logs"):
            if geral.get(chave):
                caminho = Path(geral[chave])
                if not caminho.is_absolute():
                    caminho = base / caminho
                # `resolve()` achata o "config\..\resultado" dos caminhos
                # relativos: esse caminho vai para o log e é o que o
                # operador lê para achar o arquivo gerado.
                setattr(self, chave, caminho.resolve())

        # Seletores do TOML *substituem* a lista padrão daquela chave,
        # permitindo fixar o seletor exato quando o layout já é conhecido --
        # sem editar o código nem gerar novo executável.
        for chave, valores in (bruto.get("seletores") or {}).items():
            if not isinstance(valores, list) or not all(isinstance(v, str) for v in valores):
                raise ErroRobo(f"seletores.{chave} deve ser uma lista de strings.")
            self.seletores[chave] = list(valores)

        self.clientes = [
            Cliente(
                cnpj=str(item.get("cnpj", "")),
                nome_credencial=str(item.get("nome_credencial", "")),
                ativo=bool(item.get("ativo", True)),
            )
            for item in (bruto.get("clientes") or [])
        ]

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

        Sem ``certificado_pfx`` informado, procura sozinho o único ``*.pfx``
        dentro de ``certificado/``: o nome do arquivo muda a cada renovação
        (leva CNPJ e validade no nome), então depender da pasta em vez do
        nome exato evita editar o TOML todo ano.
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
                f"Pasta de certificado nao encontrada: {pasta}. Coloque ali o "
                ".pfx do escritorio, ou informe 'certificado_pfx' no config.toml."
            )
        candidatos = sorted(pasta.glob("*.pfx"))
        if not candidatos:
            raise ErroRobo(
                f"Nenhum arquivo .pfx encontrado em '{pasta}'. Coloque ali o "
                "certificado do escritorio."
            )
        if len(candidatos) > 1:
            raise ErroRobo(
                f"Mais de um .pfx em '{pasta}': {[c.name for c in candidatos]}. "
                "Deixe so o certificado valido ali, ou informe qual usar em "
                "'certificado_pfx' no config.toml."
            )
        return candidatos[0]

    def caminho_clientes_arquivo(self) -> Path:
        """Resolve o caminho da planilha de clientes, aceitando caminho relativo à raiz."""
        if not self.clientes_arquivo:
            raise ErroRobo(
                "fonte_clientes='excel' exige 'clientes_arquivo' no config.toml "
                "(ou --clientes-arquivo na linha de comando)."
            )
        caminho = Path(self.clientes_arquivo)
        if not caminho.is_absolute():
            caminho = (self.raiz / caminho).resolve()
        if not caminho.is_file():
            raise ErroRobo(f"Planilha de clientes nao encontrada em: {caminho}")
        return caminho

    # ------------------------------------------------------------------ #
    # URLs derivadas
    # ------------------------------------------------------------------ #
    @property
    def url_api_credenciais(self) -> str:
        return f"{self.base_credencial.rstrip('/')}/api/v1/credenciais"

    @property
    def url_nova_credencial(self) -> str:
        return f"{self.base_credencial.rstrip('/')}{ROTA_NOVA_CREDENCIAL}"

    @property
    def caminho_csv(self) -> Path:
        caminho = Path(self.saida_csv)
        if not caminho.is_absolute():
            caminho = (self.dir_resultado / caminho).resolve()
        return caminho

    # ------------------------------------------------------------------ #
    # Validação e utilidades
    # ------------------------------------------------------------------ #
    def validar(self) -> None:
        """Falha cedo em configurações incoerentes, antes de abrir o navegador."""
        if self.modo_certificado not in MODOS_CERTIFICADO:
            raise ErroRobo(
                f"modo_certificado invalido: '{self.modo_certificado}'. "
                f"Use um de {MODOS_CERTIFICADO}."
            )
        if self.headless and self.modo_certificado == MODO_MANUAL:
            raise ErroRobo(
                "modo_certificado 'manual' exige headless=false: a escolha do "
                "certificado acontece em um dialogo nativo do sistema."
            )
        if self.modo_certificado == MODO_PFX:
            self.caminho_certificado()  # levanta se ausente ou inexistente
            self.senha_certificado()    # levanta se a variavel nao existir
        if not isinstance(self.validade_anos, int) or self.validade_anos <= 0:
            raise ErroRobo(
                f"validade_anos deve ser um inteiro positivo, veio {self.validade_anos!r}."
            )
        if not self.servicos_padrao:
            raise ErroRobo(
                "servicos_padrao vazio: a credencial seria criada sem nenhum "
                "servico habilitado e nao serviria para nada."
            )
        if not isinstance(self.tentativas_api, int) or self.tentativas_api < 1:
            raise ErroRobo(
                f"tentativas_api deve ser >= 1, veio {self.tentativas_api!r}."
            )
        if self.fonte_clientes not in FONTES_CLIENTES:
            raise ErroRobo(
                f"fonte_clientes invalida: '{self.fonte_clientes}'. "
                f"Use um de {FONTES_CLIENTES}."
            )
        if not self.clientes:
            dica = (
                f"Confira a planilha '{self.clientes_arquivo}' (coluna A = "
                "CNPJ, coluna B = Nome)."
                if self.fonte_clientes == FONTE_EXCEL
                else "Adicione ao menos um bloco [[clientes]] com 'cnpj' e "
                "'nome_credencial' no config.toml."
            )
            raise ErroRobo(f"Nenhum cliente a processar. {dica}")

        vistos: dict[str, str] = {}
        for cliente in self.clientes:
            digitos = cliente.cnpj_digitos
            if len(digitos) != 14:
                raise ErroRobo(
                    f"CNPJ com {len(digitos)} digito(s), esperado 14: '{cliente.cnpj}'"
                )
            if digitos in vistos:
                raise ErroRobo(
                    f"CNPJ repetido na lista de clientes: {cliente.cnpj_formatado} "
                    f"('{vistos[digitos]}' e '{cliente.nome_credencial}')"
                )
            vistos[digitos] = cliente.nome_credencial

    def cnpjs_suspeitos(self) -> list[Cliente]:
        """Clientes cujo CNPJ não passa no dígito verificador.

        Não bloqueia a execução -- homologação costuma usar CNPJ fictício --,
        mas rende um aviso alto no log, porque o sintoma de um CNPJ errado é
        o robô gerar credencial para a empresa errada.
        """
        return [c for c in self.clientes if not cnpj_valido(c.cnpj)]

    def preparar_diretorios(self) -> None:
        for pasta in (self.dir_perfil, self.dir_resultado, self.dir_debug, self.dir_logs):
            pasta.mkdir(parents=True, exist_ok=True)

    def sel(self, chave: str, **substituicoes: str) -> list[str]:
        """Seletores candidatos de uma chave lógica, com ``{papel}`` resolvido.

        A substituição é textual, e não ``str.format``: os seletores são
        regex, e um quantificador como ``.{0,3}`` faria o ``format``
        levantar ``KeyError`` num seletor que não tem nada de errado.
        """
        valores = self.seletores.get(chave)
        if not valores:
            raise ErroRobo(f"Seletor '{chave}' nao configurado.")
        resolvidos = list(valores)
        for nome, valor in substituicoes.items():
            resolvidos = [v.replace("{" + nome + "}", valor) for v in resolvidos]
        return resolvidos

    def clientes_ativos(self, filtro: list[str] | None = None) -> list[Cliente]:
        """Clientes a processar, opcionalmente filtrados por CNPJ."""
        alvo = [c for c in self.clientes if c.ativo]
        if not filtro:
            return alvo

        digitos = {normalizar_documento(f) for f in filtro if normalizar_documento(f)}
        selecionados = [c for c in alvo if c.cnpj_digitos in digitos]
        if not selecionados:
            raise ErroRobo(
                f"Nenhum cliente ativo corresponde a {sorted(filtro)}. "
                f"Disponiveis: {[c.cnpj_formatado for c in alvo]}"
            )
        return selecionados
