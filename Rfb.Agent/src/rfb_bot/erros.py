"""Exceções do robô, sempre associadas a uma etapa nomeada do fluxo."""

from __future__ import annotations


class ErroRobo(Exception):
    """Erro base do robô."""


class ErroEtapa(ErroRobo):
    """Falha em uma etapa nomeada do fluxo.

    Carregar o nome da etapa permite que o log e o CSV digam exatamente
    onde o robô parou (ex.: "Clicar em 'Representar'").
    """

    def __init__(self, etapa: str, detalhe: str) -> None:
        self.etapa = etapa
        self.detalhe = detalhe
        super().__init__(f"[{etapa}] {detalhe}")


class ErroSessao(ErroEtapa):
    """A sessão do portal caiu ou o certificado não foi aceito."""


class ErroRepresentacao(ErroEtapa):
    """Falha técnica ao trocar a representação para o CNPJ do cliente."""


class ErroSemProcuracao(ErroRepresentacao):
    """O portal recusou a representação por falta de procuração válida.

    Condição de **negócio**, não falha do robô: a procuração do escritório
    para aquele CNPJ nunca existiu, venceu ou foi revogada. O runner trata
    como resultado válido (``status: sem_procuracao``) para não soar alarme
    de robô quebrado, mas registra no CSV para o contador providenciar.

    Mensagem confirmada contra o portal real em 2026-08-29: "Sua
    autorização como procurador não permite acesso a este serviço."
    """

    def __init__(self, mensagem_portal: str) -> None:
        self.mensagem_portal = mensagem_portal
        super().__init__("Representar cliente", mensagem_portal)


class ErroCnpjInvalido(ErroRepresentacao):
    """O portal recusou o CNPJ digitado -- condição de dado, não de acesso.

    Distinto de :class:`ErroSemProcuracao`: aqui o problema é a linha da
    planilha (CNPJ inexistente ou com dígito verificador errado, comum em
    valores de exemplo como "12.345.678/0001-99" esquecidos numa lista
    real), não a falta de procuração. Misturar os dois status faria o
    contador procurar uma procuração que nunca foi o problema.

    Mensagem confirmada contra o portal real em 2026-08-29: "CNPJ inválido."
    """

    def __init__(self, mensagem_portal: str) -> None:
        self.mensagem_portal = mensagem_portal
        super().__init__("Representar cliente", mensagem_portal)


class ErroRepresentacaoDivergente(ErroRepresentacao):
    """A sessão não está representando o CNPJ pretendido.

    Rede de segurança mais importante do robô. Criar uma credencial sob a
    representação errada gera uma Chave Secreta **do escritório (ou de outro
    cliente)** e a grava no CSV sob o nome deste cliente -- pior do que
    falhar, porque o resultado fica plausível e errado, e depois entrega
    acesso de API de um contribuinte a quem não deveria tê-lo.
    """

    def __init__(self, esperado: str, detalhe: str) -> None:
        self.esperado = esperado
        super().__init__(
            "Conferir representação ativa",
            f"a sessão não confirmou a representação de {esperado}: {detalhe}. "
            "Nenhuma credencial foi criada para este cliente.",
        )


class ErroCredencial(ErroEtapa):
    """A API de credenciais respondeu fora do esperado."""


class ErroLimiteRequisicoes(ErroCredencial):
    """O portal aplicou rate limit (429) e as tentativas se esgotaram."""
