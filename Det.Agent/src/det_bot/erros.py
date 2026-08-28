"""Exceções específicas do robô, sempre associadas a uma etapa do fluxo."""

from __future__ import annotations


class ErroRobo(Exception):
    """Erro base do robô."""


class ErroEtapa(ErroRobo):
    """Falha ocorrida em uma etapa nomeada do fluxo de automação.

    Carregar o nome da etapa permite que o log e o JSON de saída informem
    exatamente onde o robô parou (ex.: "Clicar em 'Entrar com gov.br'").
    """

    def __init__(self, etapa: str, detalhe: str) -> None:
        self.etapa = etapa
        self.detalhe = detalhe
        super().__init__(f"[{etapa}] {detalhe}")


class ErroAutenticacao(ErroEtapa):
    """Falha durante o login no gov.br (certificado, timeout, recusa)."""


class ErroLeitura(ErroEtapa):
    """Falha na navegação ou na extração de dados da Caixa Postal."""


class ErroEmpregadorDivergente(ErroLeitura):
    """A tela em leitura pertence a outro CNPJ que não o da empresa alvo.

    Rede de segurança de última linha, distinta da confirmação feita logo
    após a troca de perfil: confirmado contra o portal real em 2026-08-22
    que o perfil pode **reverter para o do escritório** entre a troca e a
    leitura (o caso observado envolveu o fallback de navegação por URL
    direta, que recarrega a SPA). Sem esta checagem o robô lê a caixa
    postal do escritório e a grava sob o nome do cliente -- pior que
    falhar, porque o relatório fica plausível e errado.
    """

    def __init__(self, esperado: str, encontrado: str) -> None:
        self.esperado = esperado
        self.encontrado = encontrado
        super().__init__(
            "Conferir empregador na tela",
            f"a tela exibe o empregador {encontrado or '(nao identificado)'}, "
            f"mas a empresa consultada e {esperado}. Nenhuma mensagem foi "
            "atribuida a esta empresa.",
        )


class ErroSemProcuracao(ErroAutenticacao):
    """O portal recusou a troca de perfil por falta de procuração válida.

    Diferente de uma falha técnica (seletor quebrado, timeout, sessão
    caída), esta é uma condição de **negócio** esperada: a procuração do
    escritório para aquele CNPJ nunca existiu, venceu ou foi revogada. O
    runner trata isso como um resultado válido (``status: sem_procuracao``),
    não como falha -- não deve soar alarme de robô quebrado, mas precisa
    aparecer no relatório para o contador providenciar a renovação.
    """

    def __init__(self, mensagem_portal: str) -> None:
        self.mensagem_portal = mensagem_portal
        super().__init__("Selecionar perfil", mensagem_portal)
