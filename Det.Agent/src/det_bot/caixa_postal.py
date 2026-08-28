"""Navegação até a Caixa Postal do DET e extração das mensagens não lidas.

Estrutura real do portal (confirmada contra produção em 2026-08-21, não
documentada publicamente em lugar nenhum): a listagem **não é uma
``<table>``** -- é uma sequência de ``div.tabela.mensagens.linha-dividida``
dentro de ``div.form-group.tabela_mensagens``, com os campos identificados
por classe CSS (``.tipo``, ``.origem``, ``.hora``, ``.titulo``), não por
posição de coluna. Datas vêm abreviadas em português ("21 jul 26"), e a
paginação usa um botão com id fixo (``#btn-next-page``).

Por instrução do usuário, o robô só processa quando há mensagens não lidas.
Em vez de extrair tudo e filtrar depois, ele aciona o **filtro nativo do
próprio portal** ("Exibir apenas não lidas") -- mais confiável que inferir
"lida/não lida" de um ícone, e evita trabalho (e giro de arquivos em
``dados/``) quando não há nada novo para aquele cliente.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Any

from playwright.sync_api import Error as ErroPlaywright, Locator, Page
from playwright.sync_api import TimeoutError as TimeoutPlaywright

from .erros import ErroEmpregadorDivergente, ErroLeitura
from .localizadores import (
    aguardar_ocioso,
    clicar_primeiro,
    clicar_se_existir,
    esta_habilitado,
    primeiro_visivel,
)
from .log import AVISO, SUCESSO, etapa, normalizar
from .settings import Config, Empresa, formatar_cnpj, normalizar_cnpj

# Meses abreviados como o portal exibe ("21 jul 26"). As chaves já estão sem
# acento porque o texto passa por `normalizar()` antes de casar.
_MESES_PT = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}
_RX_DATA_PTBR = re.compile(r"(\d{1,2})\s+([a-z]{3})\s+(\d{2,4})")
# "Caixa de Entrada (3)" -- o número é o de NÃO LIDAS, não o total da aba.
_RX_CONTADOR = re.compile(r"\((\d+)\)")
# Confirmado contra o portal real: o dia corrente aparece como texto
# relativo em vez de "dd mmm aa" -- "Hoje" (e, por simetria de UX, "Ontem"
# para o dia anterior, embora só o primeiro tenha sido visto em produção).
_RELATIVOS = {"hoje": 0, "ontem": 1}


def _data_ptbr_para_iso(texto: str) -> str | None:
    """Converte 'dd mmm aa' (ex.: '21 jul 26') ou 'Hoje'/'Ontem' em ISO-8601.

    O portal não mostra hora na listagem, só dentro da mensagem aberta --
    por isso o resultado fica à meia-noite. ``data_envio`` preserva o texto
    original para quem precisar do valor exato exibido na tela.
    """
    normalizado = normalizar(texto)

    for palavra, dias_atras in _RELATIVOS.items():
        if palavra in normalizado.split():
            data = datetime.now().date() - timedelta(days=dias_atras)
            return datetime(data.year, data.month, data.day).isoformat()

    m = _RX_DATA_PTBR.search(normalizado)
    if not m:
        return None
    dia, mes_abrev, ano = m.groups()
    mes = _MESES_PT.get(mes_abrev)
    if not mes:
        return None
    ano_completo = int(ano) if len(ano) == 4 else 2000 + int(ano)
    try:
        return datetime(ano_completo, mes, int(dia)).isoformat()
    except ValueError:
        return None


def _contador_nao_lidas(texto: str) -> int | None:
    """Extrai o N de 'Caixa de Entrada (N)'; None se o padrão não casar."""
    m = _RX_CONTADOR.search(texto or "")
    return int(m.group(1)) if m else None


# Extração de todas as linhas de mensagem visíveis em uma só ida ao DOM.
JS_EXTRAIR_LINHAS = """
(container) => {
  const txt = (el) => el ? (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim() : '';
  const linhas = Array.from(container.querySelectorAll(':scope > .tabela.mensagens.linha-dividida'));
  return linhas.map((linha) => {
    const campo = (classe) => txt(linha.querySelector('.' + classe));
    const icones = Array.from(linha.querySelectorAll('i[class*="fa-"]'))
      .flatMap(i => Array.from(i.classList).filter(c => c.startsWith('fa-')));
    return {
      tipo: campo('tipo'),
      origem: campo('origem'),
      hora: campo('hora'),
      titulo: campo('titulo'),
      icones,
      texto: txt(linha),
    };
  });
}
"""


def _linha_para_mensagem(linha: dict[str, Any], pagina: int) -> dict[str, Any] | None:
    """Converte uma linha crua (JS) no registro final da mensagem.

    O campo ``situacao`` reflete o ícone da própria linha (útil se o robô
    algum dia ler sem o filtro aplicado); no fluxo normal, com o filtro
    "apenas não lidas" ativo, toda linha que chega aqui já é não lida.
    """
    if not (linha.get("texto") or "").strip():
        return None

    icones = linha.get("icones") or []
    lida = "fa-envelope-open" in icones

    return {
        "id_mensagem": None,  # o portal nao expoe link/id na listagem
        "tipo": (linha.get("tipo") or "").strip() or None,
        "remetente": (linha.get("origem") or "").strip() or None,
        "data_envio": (linha.get("hora") or "").strip() or None,
        "data_envio_iso": _data_ptbr_para_iso(linha.get("hora") or ""),
        "assunto": (linha.get("titulo") or "").strip() or None,
        "situacao": "Lida" if lida else "Nao lida",
        "corpo": None,  # preenchido por _ler_corpo_mensagem, se habilitado
        "pagina": pagina,
        "hash_linha": hashlib.sha1(
            normalizar(linha.get("texto") or "").encode("utf-8")
        ).hexdigest()[:16],
    }


def _hash_pagina(brutas: list[dict[str, Any]]) -> str:
    """Assinatura da página inteira -- usada para detectar troca real."""
    junto = "|".join(normalizar(l.get("texto") or "") for l in brutas)
    return hashlib.sha1(junto.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------- #
# Navegação
# ---------------------------------------------------------------------- #
def abrir_caixa_postal(page: Page, cfg: Config, log: logging.Logger) -> Page:
    """Chega à Caixa Postal pelo menu; se não der, tenta a URL direta."""
    clicar_se_existir(page, cfg.sel("abrir_menu"), "Abrir menu lateral", 4_000, log)

    try:
        clicar_primeiro(
            page, cfg.sel("menu_caixa_postal"), "Caixa Postal",
            cfg.timeout_padrao_ms, log,
        )
        aguardar_ocioso(page, cfg.sel("carregando"), cfg.timeout_padrao_ms)
        if _chegou(page, cfg):
            return page
        log.warning("%s Menu clicado, mas a Caixa Postal nao apareceu. Tentando URL direta.",
                    AVISO)
    except (LookupError, ErroPlaywright) as exc:
        log.warning("%s Navegacao pelo menu falhou (%s). Tentando URL direta.",
                    AVISO, exc)

    for url in cfg.urls_caixa_postal:
        try:
            log.info("Tentando URL direta da Caixa Postal: %s", url)
            page.goto(url, wait_until="domcontentloaded", timeout=cfg.timeout_navegacao_ms)
            aguardar_ocioso(page, cfg.sel("carregando"), cfg.timeout_padrao_ms)
            if _chegou(page, cfg):
                return page
        except (ErroPlaywright, TimeoutPlaywright) as exc:
            log.debug("URL %s nao serviu: %s", url, exc)

    raise ErroLeitura(
        "Abrir Caixa Postal",
        "nao foi possivel localizar a Caixa Postal nem pelo menu nem "
        f"pelas URLs {cfg.urls_caixa_postal}",
    )


_RX_CNPJ_NA_TELA = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")


def _cnpj_do_empregador(page: Page, cfg: Config) -> str:
    """CNPJ exibido na faixa "Empregador: ..."; vazio se não der para ler."""
    for spec in cfg.sel("faixa_empregador"):
        try:
            alvo, _ = primeiro_visivel(page, [spec], 3_000)
            texto = alvo.inner_text(timeout=2_000) or ""
        except (LookupError, ErroPlaywright, TimeoutError):
            continue
        achado = _RX_CNPJ_NA_TELA.search(texto)
        if achado:
            return achado.group(0)
    return ""


def confirmar_empregador_na_tela(
    page: Page, cfg: Config, empresa: Empresa, log: logging.Logger
) -> None:
    """Aborta a leitura se a tela não pertencer à empresa esperada.

    Conferir na troca de perfil não basta: confirmado contra o portal real
    em 2026-08-22 que o perfil pode reverter para o do escritório entre a
    troca e a leitura. Como a faixa "Empregador:" é renderizada em toda tela
    autenticada, ela é a única prova, no momento da leitura, de quem são os
    dados na tela.

    Divergência é erro; **não conseguir ler** o CNPJ é apenas aviso -- o
    portal pode mudar o layout da faixa, e travar toda execução por isso
    seria pior que seguir com ``perfil_confirmado`` já refletindo a dúvida.
    """
    encontrado = _cnpj_do_empregador(page, cfg)
    if not encontrado:
        log.warning(
            "%s Nao foi possivel ler a faixa 'Empregador:' para conferir de "
            "quem sao os dados em tela. Seguindo com a leitura -- confira o "
            "seletor 'faixa_empregador' se isso se repetir.", AVISO,
        )
        return

    if normalizar_cnpj(encontrado) != empresa.cnpj_digitos:
        raise ErroEmpregadorDivergente(
            esperado=empresa.cnpj_formatado,
            encontrado=formatar_cnpj(encontrado),
        )

    log.info("%s Empregador em tela confere: %s", SUCESSO, encontrado)


def _chegou(page: Page, cfg: Config) -> bool:
    """A aba 'Caixa de Entrada' aparecer é a confirmação de chegada.

    Não exige que haja mensagens: uma caixa sem nenhuma (lida ou não) é um
    estado legítimo, não uma falha de navegação.
    """
    try:
        primeiro_visivel(page, cfg.sel("aba_caixa_entrada"), 8_000)
        return True
    except (LookupError, ErroPlaywright):
        return False


# ---------------------------------------------------------------------- #
# Filtro de não lidas
# ---------------------------------------------------------------------- #
def contar_nao_lidas(page: Page, cfg: Config, log: logging.Logger) -> int | None:
    """Lê 'Caixa de Entrada (N)'; devolve None se o padrão não for lido.

    Best-effort, usado só para decidir o nível de log -- quem realmente
    decide se há trabalho a fazer é :func:`aplicar_filtro_nao_lidas` seguido
    da checagem de linhas na tela, não este número.
    """
    try:
        alvo, _ = primeiro_visivel(page, cfg.sel("contador_nao_lidas"), 5_000)
        texto = alvo.inner_text(timeout=3_000)
    except (LookupError, ErroPlaywright, TimeoutError):
        return None
    return _contador_nao_lidas(texto)


def aplicar_filtro_nao_lidas(page: Page, cfg: Config, log: logging.Logger) -> bool:
    """Restringe a listagem às não lidas, via filtro nativo do portal.

    Best-effort: se o link não existir (layout mudou), segue sem filtrar --
    melhor ler mensagens além do necessário do que travar a execução por um
    seletor. Devolve se o filtro foi de fato acionado.
    """
    aplicado = clicar_se_existir(
        page, cfg.sel("filtro_nao_lidas"), "Exibir apenas nao lidas", 6_000, log
    )
    if aplicado:
        log.info("Filtro 'Exibir apenas nao lidas' aplicado.")
    else:
        log.warning(
            "%s Filtro 'Exibir apenas nao lidas' nao encontrado; a listagem "
            "pode trazer mensagens ja lidas.", AVISO,
        )
    return aplicado


# ---------------------------------------------------------------------- #
# Corpo da mensagem (painel de detalhe)
# ---------------------------------------------------------------------- #
def _texto_painel(page: Page, cfg: Config) -> str:
    """Texto atual do painel de detalhe; string vazia se ele não existir."""
    try:
        painel, _ = primeiro_visivel(page, cfg.sel("painel_mensagem"), 2_000,
                                     estado="attached")
        return (painel.inner_text(timeout=2_000) or "").strip()
    except (LookupError, ErroPlaywright, TimeoutError):
        return ""


def _ler_corpo_mensagem(
    page: Page, linha: Locator, cfg: Config, log: logging.Logger
) -> str | None:
    """Clica na linha e devolve o texto completo do painel de detalhe.

    Best-effort: o corpo é um extra sobre o que a listagem já dá (assunto,
    remetente, data) -- se o painel não existir ou não atualizar a tempo, a
    mensagem ainda sai no resultado, só sem ``corpo``. Antes do clique, o
    painel mostra apenas o texto de instrução "Para visualizar uma
    mensagem, clique nela.", e é a MUDANÇA de conteúdo (não só a presença
    de texto) que confirma que o clique abriu esta mensagem específica.
    """
    antes = _texto_painel(page, cfg)
    try:
        linha.scroll_into_view_if_needed(timeout=3_000)
        linha.click(timeout=8_000)
    except (ErroPlaywright, TimeoutError) as exc:
        log.debug("Nao foi possivel clicar na linha para ler o corpo (%s).", exc)
        return None

    for _ in range(16):  # ~8s aguardando o painel atualizar
        atual = _texto_painel(page, cfg)
        if atual and normalizar(atual) != normalizar(antes):
            return atual
        page.wait_for_timeout(500)

    log.debug("Painel de detalhe nao mudou apos o clique; corpo nao capturado.")
    return None


def _coletar_pagina(
    page: Page, cfg: Config, container: Locator, pagina: int,
    vistos: set[str], log: logging.Logger,
) -> list[dict[str, Any]]:
    """Extrai as mensagens novas da página, abrindo cada uma se configurado.

    Não confia numa contagem de linhas fixa: **reconsulta o DOM a cada
    clique**. Motivo -- confirmado com um caso de teste que reproduz o
    portal: abrir uma mensagem tende a marcá-la como lida, e isso pode
    fazer um item da *próxima* página "subir" para preencher a vaga na
    página atual. Uma estratégia de índices fixos (mesmo em ordem reversa)
    perde esse item, porque ele só passa a existir na página depois que o
    laço já passou pela posição onde ele aparece. Reconsultar a cada
    iteração -- sempre pegando o ÚLTIMO item ainda não visto -- é o que
    torna a coleta correta independente de quanto a lista se realinha.
    """
    if not cfg.ler_corpo_mensagens:
        # Sem cliques não há realinhamento: uma leitura em lote já é exata
        # e muito mais rápida.
        brutas = container.evaluate(JS_EXTRAIR_LINHAS)
        registros = [_linha_para_mensagem(l, pagina) for l in brutas]
        return [r for r in registros if r and r["hash_linha"] not in vistos]

    coletados: dict[str, dict[str, Any]] = {}
    linhas = container.locator(":scope > .tabela.mensagens.linha-dividida")

    for _ in range(200):  # proteção contra laço infinito, não um limite normal
        brutas = container.evaluate(JS_EXTRAIR_LINHAS)
        if not brutas:
            break

        indice_pendente = None
        registro_pendente = None
        for indice in range(len(brutas) - 1, -1, -1):
            registro = _linha_para_mensagem(brutas[indice], pagina)
            if not registro:
                continue
            h = registro["hash_linha"]
            if h in vistos or h in coletados:
                continue
            indice_pendente, registro_pendente = indice, registro
            break

        if registro_pendente is None:
            # Nenhum item novo na leitura mais recente: a página estabilizou.
            break

        registro_pendente["corpo"] = _ler_corpo_mensagem(
            page, linhas.nth(indice_pendente), cfg, log
        )
        coletados[registro_pendente["hash_linha"]] = registro_pendente
    else:
        log.warning("%s Limite de iteracoes atingido lendo corpos da pagina %d.",
                    AVISO, pagina)

    return list(coletados.values())


# ---------------------------------------------------------------------- #
# Extração
# ---------------------------------------------------------------------- #
def _avancar_pagina(page: Page, cfg: Config, container: Locator,
                    assinatura_atual: str, log: logging.Logger) -> bool:
    """Clica em "próxima página" e confirma que o conteúdo mudou.

    Retorna ``False`` quando não há próxima página ou quando o conteúdo não
    muda -- proteção contra laço infinito caso o botão não desabilite na
    última página.
    """
    try:
        clicar_primeiro(
            page, cfg.sel("proxima_pagina"), "Proxima pagina", 6_000, log,
            predicado=esta_habilitado,
        )
    except (LookupError, ErroPlaywright):
        log.info("Sem proxima pagina habilitada; fim da varredura.")
        return False

    aguardar_ocioso(page, cfg.sel("carregando"), cfg.timeout_padrao_ms)

    for _ in range(20):  # ~10s aguardando a lista efetivamente trocar
        try:
            atual, _spec = primeiro_visivel(page, cfg.sel("tabela_mensagens"), 5_000,
                                            estado="attached")
            brutas = atual.evaluate(JS_EXTRAIR_LINHAS)
            if _hash_pagina(brutas) != assinatura_atual:
                return True
        except (LookupError, ErroPlaywright):
            pass
        page.wait_for_timeout(500)

    log.warning("%s Conteudo nao mudou apos avancar a pagina; encerrando a varredura.",
                AVISO)
    return False


def extrair_mensagens(
    page: Page, cfg: Config, empresa: Empresa, log: logging.Logger
) -> dict[str, Any]:
    """Lê as mensagens não lidas da Caixa Postal; percorre paginação se houver.

    Se, após o filtro nativo do portal, não sobrar nenhuma linha na tela, a
    leitura termina ali -- não é erro, é o caso comum quando não há nada
    novo para aquele cliente.
    """
    kw = {"page": page, "dir_debug": cfg.dir_debug, "prefixo_evidencia": empresa.id,
          "tipo_erro": ErroLeitura}

    mensagens: list[dict[str, Any]] = []
    vistos: set[str] = set()
    paginas_lidas = 0

    with etapa("Ler a Caixa Postal", log, **kw):
        # Antes de qualquer coleta: a tela em frente é mesmo desta empresa?
        confirmar_empregador_na_tela(page, cfg, empresa, log)

        contador = contar_nao_lidas(page, cfg, log)
        if contador is not None:
            log.info("Portal reporta %d mensagem(ns) nao lida(s) na Caixa de Entrada.",
                     contador)

        aplicar_filtro_nao_lidas(page, cfg, log)
        aguardar_ocioso(page, cfg.sel("carregando"), cfg.timeout_padrao_ms)

        for pagina in range(1, cfg.max_paginas + 1):
            aguardar_ocioso(page, cfg.sel("carregando"), cfg.timeout_padrao_ms)
            try:
                # "attached", não "visible": o container fica com altura
                # zero (e portanto invisível para o Playwright) quando não
                # há nenhuma mensagem -- e "nenhuma mensagem" é o resultado
                # normal quando não há nada não lido, não uma falha.
                container, spec = primeiro_visivel(
                    page, cfg.sel("tabela_mensagens"), cfg.timeout_padrao_ms, log,
                    estado="attached",
                )
            except (LookupError, ErroPlaywright) as exc:
                if pagina == 1:
                    raise
                log.debug("Container de mensagens sumiu na pagina %d (%s).", pagina, exc)
                break
            if pagina == 1:
                log.info("Lista de mensagens localizada via seletor: %s", spec)

            if not container.evaluate(JS_EXTRAIR_LINHAS):
                if pagina == 1:
                    log.info("Nenhuma mensagem nao lida; leitura concluida sem coleta.")
                break

            paginas_lidas = pagina
            registros_pagina = _coletar_pagina(page, cfg, container, pagina, vistos, log)

            for registro in registros_pagina:
                vistos.add(registro["hash_linha"])
                mensagens.append(registro)
            log.info("Pagina %d: %d mensagem(ns) nova(s). Acumulado: %d",
                     pagina, len(registros_pagina), len(mensagens))

            # A assinatura para decidir "a página mudou" é tirada DEPOIS da
            # coleta, não antes: quando `ler_corpo_mensagens` está ativo, os
            # cliques já podem ter alterado o conteúdo desta mesma página
            # (ver a docstring de `_coletar_pagina`) -- comparar contra um
            # estado anterior aos cliques falsamente pareceria "mudou".
            assinatura_atual = _hash_pagina(container.evaluate(JS_EXTRAIR_LINHAS))
            if not _avancar_pagina(page, cfg, container, assinatura_atual, log):
                break
        else:
            log.warning("%s Limite de %d paginas atingido; pode haver mais mensagens.",
                        AVISO, cfg.max_paginas)

    return {
        "url_caixa_postal": page.url,
        "nao_lidas_reportadas_pelo_portal": contador,
        "paginas_lidas": paginas_lidas,
        "total_mensagens": len(mensagens),
        "mensagens": mensagens,
    }


def dump_diagnostico(page: Page, cfg: Config, empresa: Empresa,
                     log: logging.Logger) -> None:
    """Grava screenshot + HTML da tela atual (modo ``--dump``).

    Usado para calibrar os seletores contra o layout real do portal sem
    precisar rodar o fluxo inteiro no escuro.
    """
    from .log import salvar_evidencia

    salvar_evidencia(page, cfg.dir_debug, "dump-caixa-postal", prefixo=empresa.id)
    try:
        n = page.locator(".tabela.mensagens.linha-dividida").count()
        log.info("Diagnostico: %d linha(s) de mensagem na tela | url=%s", n, page.url)
    except ErroPlaywright:
        pass
