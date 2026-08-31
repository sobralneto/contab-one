#!/usr/bin/env python3
"""
Regressão do miolo de coleta (nfse.py) depois da mudança pra agente. O
plano é explícito: "as suítes atuais têm que continuar passando sem
alteração — se alguma quebrar, é sinal de que a mudança vazou para o miolo
de coleta" (PLANO_SAAS_AGENTE.md §8).

As suítes originais (teste_nfse.py, teste_controle.py, teste_interrupcao.py
— ver HANDOFF.md §Testes) viviam no scratchpad de sessões anteriores e não
estão disponíveis nesta sessão para "somar" de verdade. Este arquivo
reconstrói os cenários mais importantes que elas cobriam, descritos em
HANDOFF.md, focando no que esta sessão mexeu por perto: os literais que
viraram globais reatribuíveis (LISTAGENS, MAX_DIAS_FILTRO, PARAM_PAGINA,
URL_NOTAS, as três regex) precisam continuar se comportando EXATAMENTE como
antes enquanto aplicar_regras() não for chamado — é o modo legado, e é o
que a grande maioria dos clientes vai continuar usando.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import nfse
from _harness import Suite, rodar

HTML_RECEBIDAS = """
<table><tbody>
<tr>
  <td>05/06/26</td><td>12.345.678/0001-90 EMPRESA X</td><td>06/2026</td>
  <td>1.234,56</td>
  <td><img data-original-title="NFS-e Gerada" src="/img/tb-gerada.svg"></td>
  <td><a href="/Notas/Download/NFSe/{chave}">baixar</a></td>
</tr>
</tbody></table>
<div>Total de 1 registros</div>
"""


def _html(chave: str) -> str:
    return HTML_RECEBIDAS.format(chave=chave)


# ---- montar_url / janelas (modo legado = valores de fábrica) --------------
def teste_montar_url_usa_pg_nao_pagina(s: Suite) -> None:
    url = nfse.montar_url("recebidas", date(2026, 6, 1), date(2026, 6, 30), pagina=3)
    s.check("pg=3" in url, "paginação usa 'pg=', não 'pagina=' (bug histórico documentado em HANDOFF)")
    s.check("pagina=" not in url, "'pagina=' não aparece de jeito nenhum na URL")


def teste_montar_url_executar_so_em_recebidas(s: Suite) -> None:
    url_rec = nfse.montar_url("recebidas", date(2026, 6, 1), date(2026, 6, 30))
    url_emi = nfse.montar_url("emitidas", date(2026, 6, 1), date(2026, 6, 30))
    s.check("executar=1" in url_rec, "Recebidas exige executar=1")
    s.check("executar=1" not in url_emi, "Emitidas NÃO aceita executar=1 (devolveria vazio se tivesse)")


def teste_montar_url_sem_pagina_na_primeira(s: Suite) -> None:
    url = nfse.montar_url("recebidas", date(2026, 6, 1), date(2026, 6, 30))
    s.check("pg=" not in url, "página 1 não inclui o parâmetro pg= (só a partir da 2ª)")


def teste_janelas_31_dias_por_padrao(s: Suite) -> None:
    s.check(nfse.MAX_DIAS_FILTRO == 31, "pré-condição: MAX_DIAS_FILTRO é 31 no modo legado (fábrica)")
    faixas_30 = nfse.janelas(date(2026, 1, 1), date(2026, 1, 30))
    s.check(len(faixas_30) == 1, "30 dias cabe numa janela só")
    faixas_31 = nfse.janelas(date(2026, 1, 1), date(2026, 1, 31))
    s.check(len(faixas_31) == 1, "exatamente 31 dias ainda cabe numa janela só")
    faixas_32 = nfse.janelas(date(2026, 1, 1), date(2026, 2, 1))
    s.check(len(faixas_32) == 2, "32 dias já precisa de 2 janelas")
    s.check(faixas_32[0] == (date(2026, 1, 1), date(2026, 1, 31)), "primeira janela vai até o dia 31")
    s.check(faixas_32[1] == (date(2026, 2, 1), date(2026, 2, 1)), "segunda janela pega o dia restante")


def teste_janelas_data_invertida_para_com_erro(s: Suite) -> None:
    try:
        nfse.janelas(date(2026, 6, 30), date(2026, 6, 1))
        s.check(False, "deveria ter chamado erro_fatal (SystemExit) para início > fim")
    except SystemExit as e:
        s.check(e.code == 1, "data inicial depois da final: erro_fatal com código 1 (padrão)")


# ---- extrair_notas / total_registros --------------------------------------
def teste_extrair_notas_recebidas(s: Suite) -> None:
    chave = "5" * 44
    notas = nfse.extrair_notas(_html(chave), "recebidas")
    s.check(len(notas) == 1, "extrai exatamente 1 nota da tabela")
    nota = notas[0]
    s.check(nota["chave"] == chave, "chave extraída da URL de download")
    s.check(nota["situacao"] == "NFS-e Gerada", "situação lida do title/data-original-title do <img>")
    s.check(nota["emitida_por"] == "12.345.678/0001-90 EMPRESA X", "coluna emitida_por presente em Recebidas")
    s.check("municipio_emissor" not in nota, "coluna municipio_emissor NÃO existe em Recebidas (só Emitidas)")


def teste_extrair_notas_ignora_linha_sem_link_de_download(s: Suite) -> None:
    html = "<table><tr><td>lixo</td><td>sem link nenhum aqui</td></tr></table>"
    s.check(nfse.extrair_notas(html, "recebidas") == [], "linha sem /Notas/Download/NFSe/ é ignorada")


def teste_total_registros(s: Suite) -> None:
    s.check(nfse.total_registros("<div>Total de 42 registros</div>") == 42, "extrai o total de registros")
    s.check(nfse.total_registros("<div>Total de 1 registro</div>") == 1, "aceita singular ('registro')")
    s.check(nfse.total_registros("<div>nada aqui</div>") is None, "sem o texto, devolve None (não zero)")


# ---- ler_certificado -------------------------------------------------------
def teste_ler_certificado_padrao_completo(s: Suite) -> None:
    e = nfse.ler_certificado(Path("0001_54283546000126_EMPRESA EXEMPLO LTDA_s.123456_v.04.03.2027.pfx"))
    s.check(e.codigo == "0001", "código extraído")
    s.check(e.cnpj == "54283546000126", "CNPJ extraído")
    s.check(e.nome == "EMPRESA EXEMPLO LTDA", "nome extraído")
    s.check(e.senha == "123456", "senha extraída do nome do arquivo")
    s.check(e.validade == date(2027, 3, 4), "validade extraída (DD.MM.AAAA)")


def teste_ler_certificado_sem_senha_no_nome(s: Suite) -> None:
    e = nfse.ler_certificado(Path("0002_54283546000126_OUTRA EMPRESA.pfx"))
    s.check(e.codigo == "0002" and e.cnpj == "54283546000126", "padrão sem senha/validade ainda extrai código e CNPJ")
    s.check(e.senha == "", "sem senha no nome: fica vazio (vem do config.toml depois)")
    s.check(e.validade is None, "sem validade no nome: fica None")


def teste_ler_certificado_totalmente_fora_do_padrao(s: Suite) -> None:
    e = nfse.ler_certificado(Path("00097_LEJ CONTABIL_123456_v.09.12.2026.pfx"))
    s.check(e.codigo == "00097", "código é sempre o texto antes do primeiro '_', mesmo com o resto bagunçado")
    e2 = nfse.ler_certificado(Path("semunderscorenenhum.pfx"))
    s.check(e2.codigo == "semunderscorenenhum", "sem nenhum '_': o código vira o nome inteiro (nunca falha)")


# ---- senha_da_empresa: ordem de precedência --------------------------------
def teste_senha_precedencia(s: Suite) -> None:
    e_com_senha = nfse.Empresa("0001", "123", "X", senha="do-arquivo", validade=None, pfx=Path("x.pfx"))
    s.check(nfse.senha_da_empresa(e_com_senha, {"senha_padrao": "ignorada"}) == "do-arquivo",
           "senha do nome do arquivo tem prioridade sobre tudo")

    e_sem_senha = nfse.Empresa("0002", "123", "X", senha="", validade=None, pfx=Path("x.pfx"))
    s.check(nfse.senha_da_empresa(e_sem_senha, {"senhas": {"x.pfx": "da-secao"}, "senha_padrao": "padrao"})
           == "da-secao", "[senhas] pelo nome do arquivo vem antes de senha_padrao")
    s.check(nfse.senha_da_empresa(e_sem_senha, {"senhas": {"0002": "errado"}, "senha_padrao": "padrao"})
           == "padrao", "[senhas] por código (antigo) não casa mais — cai para senha_padrao")
    s.check(nfse.senha_da_empresa(e_sem_senha, {"senha_padrao": "padrao"}) == "padrao",
           "senha_padrao é usada quando não há [senhas] pro nome do arquivo")

    os.environ["NFSE_PFX_SENHA"] = "da-variavel-de-ambiente"
    try:
        s.check(nfse.senha_da_empresa(e_sem_senha, {}) == "da-variavel-de-ambiente",
               "variável de ambiente é o último recurso")
    finally:
        del os.environ["NFSE_PFX_SENHA"]

    try:
        nfse.senha_da_empresa(e_sem_senha, {})
        s.check(False, "sem nenhuma fonte de senha deveria levantar RuntimeError")
    except RuntimeError:
        s.check(True, "sem nenhuma fonte de senha: RuntimeError imediato (nunca um prompt)")


# ---- controle: round-trip, corrupção, dedup --------------------------------
def teste_controle_roundtrip(s: Suite, tmp: Path) -> None:
    pasta = tmp / "cliente1"
    controle = nfse.carregar_controle(pasta)
    s.check(controle == {"versao": 1, "backfill_concluido": {}, "notas_baixadas": {}},
           "cliente novo: estrutura em branco")

    nfse.registrar_nota(controle, "recebidas", "chaveA")
    nfse.marcar_backfill_concluido(controle, "recebidas")
    nfse.salvar_controle(pasta, controle)

    de_volta = nfse.carregar_controle(pasta)
    s.check(de_volta["notas_baixadas"]["recebidas"] == ["chaveA"], "nota registrada sobrevive ao round-trip")
    s.check(nfse.backfill_concluido(de_volta, "recebidas") is True, "backfill concluído sobrevive ao round-trip")
    s.check(nfse.backfill_concluido(de_volta, "emitidas") is False, "listagem não marcada continua False")


def teste_controle_corrompido_vira_cliente_novo(s: Suite, tmp: Path) -> None:
    pasta = tmp / "cliente2"
    pasta.mkdir()
    (pasta / "_controle.json").write_text("{{{ não é json", encoding="utf-8")
    controle = nfse.carregar_controle(pasta)
    s.check(controle == {"versao": 1, "backfill_concluido": {}, "notas_baixadas": {}},
           "controle corrompido é tratado como cliente novo, não lança")


def teste_controle_grava_atomico(s: Suite, tmp: Path) -> None:
    pasta = tmp / "cliente3"
    nfse.salvar_controle(pasta, {"versao": 1, "backfill_concluido": {}, "notas_baixadas": {}})
    s.check(not (pasta / "_controle.json.tmp").exists(), "arquivo .tmp não sobra depois de salvar (replace atômico)")
    s.check((pasta / "_controle.json").exists(), "_controle.json existe depois de salvar")


# ---- config.toml: [api] é obrigatório --------------------------------------
def teste_config_sem_api_e_erro(s: Suite, tmp: Path) -> None:
    caminho = tmp / "config.toml"
    caminho.write_text('pasta_saida = "notas"\n', encoding="utf-8")
    try:
        nfse.carregar_config(caminho)
        s.check(False, "config.toml sem [api] deveria dar erro_fatal")
    except SystemExit as e:
        s.check(e.code == 1, "sem [api]: erro_fatal com código 1 (erro de configuração comum)")


def teste_config_api_incompleto_e_erro(s: Suite, tmp: Path) -> None:
    caminho = tmp / "config_incompleto.toml"
    caminho.write_text('[api]\nurl = "https://x.example"\n', encoding="utf-8")  # sem 'chave'
    try:
        nfse.carregar_config(caminho)
        s.check(False, "[api] com só 'url' preenchido deveria dar erro_fatal")
    except SystemExit as e:
        s.check(e.code == 1, "[api] incompleto: erro_fatal com código 1 (erro de configuração comum)")


def teste_config_api_completo_liga_modo_agente(s: Suite, tmp: Path) -> None:
    caminho = tmp / "config_completo.toml"
    caminho.write_text(
        '[api]\nurl = "https://x.example"\nchave = "nfse_aaaaaaaa_' + "b" * 32 + '"\n',
        encoding="utf-8",
    )
    config = nfse.carregar_config(caminho)
    s.check(bool(config["api"]), "[api] completo: config['api'] é truthy (liga o modo agente)")
    s.check("tolerancia_offline_dias" not in config["api"],
           "tolerancia_offline_dias não é mais lido do config.toml — valor fixo no código")


def main() -> Suite:
    s = Suite("teste_regressao_coleta")
    with tempfile.TemporaryDirectory(prefix="nfse-teste-regressao-") as tmp_str:
        tmp = Path(tmp_str)
        for nome, fn in list(globals().items()):
            if not (nome.startswith("teste_") and callable(fn)):
                continue
            print(f"-- {nome}")
            if fn.__code__.co_argcount == 2:
                fn(s, tmp)
            else:
                fn(s)
    return s


if __name__ == "__main__":
    rodar(main)
