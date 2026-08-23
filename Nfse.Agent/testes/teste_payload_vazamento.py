#!/usr/bin/env python3
"""
"Vale um teste automatizado que faz asserção sobre isso — o payload não pode
conter nenhum desses campos. É o tipo de invariante que se perde numa
refatoração distraída." (PLANO_SAAS_AGENTE.md §6/§8)

Este teste já pegou um bug real ao ser escrito (não depois): a primeira
versão de _montar_payload_clientes() mandava o nome de arquivo ORIGINAL do
certificado como certificadoNomeArquivo — e no padrão de nome recomendado
(codigoEmpresa_CNPJ_NomeEmpresa_s.SENHA_v.DD.MM.AAAA.pfx) esse nome de
arquivo contém o CNPJ completo E a senha em texto claro. Corrigido em
nfse.py (_nome_arquivo_sanitizado) antes deste teste ser escrito de verdade.

Nota sobre ".pfx" especificamente: o campo certificadoNomeArquivo continua
terminando em ".pfx" de propósito (identifica qual certificado é, sem
revelar nada — a extensão sozinha não é segredo; ver PLANO_SAAS_AGENTE.md
§6, cujo próprio exemplo de payload mostra "certificadoNomeArquivo":
"0001_...pfx"). O que este teste proíbe de verdade é o CONTEÚDO sensível: a
senha, o CNPJ completo, e o nome de arquivo ORIGINAL (não o sanitizado).
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_client
import nfse
from _harness import Suite, rodar

HMAC_KEY = "chave-hmac-do-escritorio-de-teste"

# Um certificado no padrão COMPLETO recomendado — é exatamente esse padrão
# que embute CNPJ e senha no nome do arquivo (ver docstring acima).
SENHA_SECRETA = "MinhaSenhaSuperSecreta!2027"
CNPJ_COMPLETO = "54283546000126"
NOME_ARQUIVO_ORIGINAL = (
    f"0001_{CNPJ_COMPLETO}_Empresa Secreta LTDA_s.{SENHA_SECRETA}_v.04.03.2027.pfx"
)

# E um certificado fora do padrão (só o fallback: código = tudo antes do
# primeiro "_", resto vira "nome") — cobre o outro ramo de ler_certificado.
NOME_ARQUIVO_FORA_DO_PADRAO = "0099_algumacoisa_que_nao_seguiu_o_padrao.pfx"


def _empresas_de_teste(tmp: Path) -> list[nfse.Empresa]:
    e1 = nfse.ler_certificado(tmp / NOME_ARQUIVO_ORIGINAL)
    e2 = nfse.ler_certificado(tmp / NOME_ARQUIVO_FORA_DO_PADRAO)
    return [e1, e2]


def teste_ler_certificado_realmente_capturou_a_senha(s: Suite, tmp: Path) -> None:
    """Pré-condição do teste: se o parsing não capturasse a senha (ex.:
    alguém já tivesse mudado o regex), o teste de vazamento abaixo passaria
    por motivo errado — sem nunca ter testado nada de verdade."""
    e1 = nfse.ler_certificado(tmp / NOME_ARQUIVO_ORIGINAL)
    s.check(e1.senha == SENHA_SECRETA, "pré-condição: ler_certificado extraiu a senha do nome do arquivo")
    s.check(e1.cnpj == CNPJ_COMPLETO, "pré-condição: ler_certificado extraiu o CNPJ completo do nome do arquivo")


def teste_payload_de_clientes_nao_vaza_segredos(s: Suite, tmp: Path) -> None:
    empresas = _empresas_de_teste(tmp)
    payload = nfse._montar_payload_clientes(empresas, HMAC_KEY)
    texto = json.dumps(payload, ensure_ascii=False)

    s.check(SENHA_SECRETA not in texto, "a senha em texto claro não aparece em nenhum campo do payload")
    s.check(CNPJ_COMPLETO not in texto,
           "o CNPJ completo (14 dígitos seguidos) não aparece — só a versão mascarada/hash")
    s.check(NOME_ARQUIVO_ORIGINAL not in texto,
           "o nome de arquivo ORIGINAL (que embute CNPJ+senha) nunca é enviado")
    s.check(NOME_ARQUIVO_FORA_DO_PADRAO not in texto,
           "o nome de arquivo original também não vaza no caso fora-do-padrão")

    # positivo: confirma que o payload ainda é útil (não ficou tudo em branco)
    s.check(any(c["codigo"] == "0001" for c in payload), "o código da empresa continua no payload")
    s.check(all(c["cnpjMascarado"].startswith("54.283.") for c in payload if c["codigo"] == "0001"),
           "a versão MASCARADA do CNPJ (não a completa) continua no payload, como esperado")
    s.check(all(c["certificadoNomeArquivo"].endswith(".pfx") for c in payload),
           "certificadoNomeArquivo continua identificável (mantém a extensão) sem ser o nome original")


def teste_hash_cnpj_nao_e_reversivel_por_inspecao(s: Suite, _tmp: Path) -> None:
    h = api_client.hash_cnpj(CNPJ_COMPLETO, HMAC_KEY)
    s.check(CNPJ_COMPLETO not in h, "o hash não contém o CNPJ original em nenhum trecho reconhecível")
    s.check(len(h) == 64, "hash é SHA-256 em hex (64 caracteres) — não é o CNPJ codificado de forma óbvia")


def teste_metricas_nao_carregam_conteudo_de_nota(s: Suite, _tmp: Path) -> None:
    """As métricas nunca tiveram acesso ao conteúdo do XML pra começo de
    conversa (só contam sucesso/pulo/falha) — este teste é o fio de
    segurança pra uma mudança futura não introduzir isso por engano."""
    metricas = [{"cliente_codigo": "0001", "tipo": "recebidas", "competencia": "2026-06",
                "qtd_baixadas": 3, "qtd_puladas": 0, "qtd_falhas": 0, "duracao_ms": 900}]
    linhas = api_client._traduzir_metricas(metricas, {"0001": "id-0001"})
    texto = json.dumps(linhas, ensure_ascii=False)

    marcadores_de_nota = ["<?xml", "<InfNFSe", "<NFSe", "%PDF-", "nfseXmlGZipB64"]
    for marcador in marcadores_de_nota:
        s.check(marcador not in texto, f"payload de métricas não contém marcador de conteúdo de nota: {marcador!r}")

    campos_esperados = {"clienteId", "tipo", "competencia", "qtdBaixadas", "qtdPuladas", "qtdFalhas", "duracaoMs"}
    s.check(set(linhas[0].keys()) == campos_esperados,
           f"payload de métrica só tem os campos esperados (veio {set(linhas[0].keys())!r})")


def main() -> Suite:
    s = Suite("teste_payload_vazamento")
    tmp = Path(__file__).resolve().parent  # só usado para montar Path(nome_arquivo); nada é escrito em disco
    for nome, fn in list(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            print(f"-- {nome}")
            fn(s, tmp)
    return s


if __name__ == "__main__":
    rodar(main)
