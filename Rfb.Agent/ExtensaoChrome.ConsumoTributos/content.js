// content.js
// Automação de "Trocar Representação" no portal consumo.tributos.gov.br
// para uma lista de CNPJs.
//
// IMPORTANTE — leia antes de usar:
// 1) Esta extensão NUNCA tenta resolver o CAPTCHA. Quando um captcha aparece,
//    a automação PARA sozinha e espera você resolver manualmente e clicar em
//    "Continuar" no painel. Isso é proposital: contornar captcha/anti-bot não
//    é algo que deva ser automatizado. Na prática o captcha não aparece toda
//    vez (parece depender de velocidade/quantidade de tentativas), mas quando
//    aparecer o script para sozinho.
// 2) Os seletores abaixo foram conferidos ao vivo no DevTools (não são
//    suposição): o botão que abre o menu é #avatar-dropdown-trigger, o
//    formulário é a div #formularioRepresentacao, o campo de CNPJ é
//    #input-representar-cpfcnpj, o seletor de perfil é um <ng-select
//    class="brx-input"> (biblioteca ng-select — precisa do trio de eventos
//    mousedown+mouseup+click para abrir, um .click() simples não funciona),
//    e a mensagem de erro aparece em <span class="mensagemErro">. Ainda assim,
//    é uma SPA e esses detalhes podem mudar em atualizações do portal — se
//    algo parar de funcionar, use o DevTools para conferir de novo.
// 3) Teste primeiro com 1 CNPJ antes de rodar a lista inteira.

(() => {
  const STORAGE_KEY = 'trocaRepresentacaoState';

  // ---------- utilidades ----------

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  async function waitFor(fn, { timeout = 8000, interval = 200 } = {}) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      const value = await fn();
      if (value) return value;
      await sleep(interval);
    }
    return null;
  }

  function isVisible(el) {
    if (!el) return false;
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function textOf(el) {
    return (el.innerText || el.textContent || '').trim();
  }

  // Define valor em inputs controlados por framework (Angular/React), disparando
  // os eventos que esses frameworks escutam para atualizar o estado interno.
  function setNativeValue(input, value) {
    const proto = input.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    setter.call(input, value);
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function highlight(el) {
    if (!el) return;
    const prev = el.style.outline;
    el.style.outline = '2px solid #ff9800';
    setTimeout(() => { el.style.outline = prev; }, 600);
  }

  // Clique "simples" (basta para <button> nativos).
  function clickEl(el) {
    if (!el) return false;
    highlight(el);
    el.click();
    return true;
  }

  // Alguns widgets (ex.: ng-select) só abrem/reagem com a sequência completa
  // mousedown → mouseup → click. Um .click() sozinho não é suficiente para eles.
  function clickSequence(el) {
    if (!el) return false;
    highlight(el);
    ['mousedown', 'mouseup', 'click'].forEach((type) => {
      el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
    });
    return true;
  }

  // Digita caractere a caractere usando execCommand('insertText'), que dispara
  // eventos de input "reais" o bastante para máscaras (ex.: máscara de CNPJ) e
  // para o Angular Reactive Forms reconhecerem a mudança. Setar `.value`
  // direto + disparar 'input' manualmente NÃO é suficiente aqui.
  //
  // CUIDADO: execCommand('insertText') digita em QUALQUER QUE SEJA o elemento
  // com foco no momento — não necessariamente `input`. Se o foco não migrou de
  // verdade (ex.: um dropdown de outro campo ainda "prendendo" o foco), os
  // caracteres vazam para o campo errado silenciosamente. Por isso aqui a
  // gente força o foco com um clique de verdade (não só `.focus()`) e CONFERE
  // que `document.activeElement` é mesmo o input antes de digitar.
  // `clearMethod`:
  //  - 'native' (padrão) — limpa via setter nativo de .value + evento 'input'.
  //    Funciona bem para inputs "normais" (ex.: campo de CNPJ).
  //  - 'execCommand' — limpa via execCommand('selectAll')+('delete'), ou seja,
  //    simula um Ctrl+A + Delete de verdade. NECESSÁRIO para campos com
  //    componente de máscara próprio por trás (ex.: o <br-date-picker> do
  //    campo "Validade" da credencial): setar .value direto corrompe o
  //    estado interno do componente (confirmado ao vivo — produzia algo como
  //    "30/080/321031" em vez de "30/08/2031"). Use este modo sempre que o
  //    campo alvo for um desses componentes com máscara/estado próprios.
  // `charDelay`: pausa (ms) entre cada caractere digitado. Valor mais alto
  // dá mais tempo pra SPA (Angular reactive forms, máscaras, validação)
  // acompanhar cada tecla antes da próxima — útil se a página estiver
  // lenta/carregada. O padrão subiu de 25ms pra 40ms depois de um caso real
  // em que o campo de perfil ficava vazio na hora de confirmar (mesma causa
  // raiz: a SPA não tinha "processado" a digitação/seleção anterior a
  // tempo). Ver também a confirmação de seleção em selectPerfil().
  async function typeInto(input, text, { clearMethod = 'native', charDelay = 40 } = {}) {
    // O foco pode não "pegar" na primeira tentativa se o painel/acordeão
    // ainda estiver com a animação de abertura em andamento (visto ao vivo:
    // acontece só no primeiro CNPJ da lista, logo depois de abrir o menu de
    // representação pela primeira vez). Por isso tentamos algumas vezes com
    // uma pequena espera entre elas antes de desistir, em vez de abortar já
    // na primeira falha.
    let focado = false;
    for (let tentativa = 0; tentativa < 3 && !focado; tentativa++) {
      if (tentativa > 0) await sleep(300);
      clickSequence(input);
      input.focus();
      await sleep(150);
      focado = document.activeElement === input;
    }
    if (!focado) {
      throw new Error('O foco não foi para o campo esperado antes de digitar (document.activeElement é outro elemento) — abortando para não digitar no lugar errado.');
    }
    if (clearMethod === 'execCommand') {
      document.execCommand('selectAll', false, null);
      document.execCommand('delete', false, null);
    } else {
      setNativeValue(input, '');
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
    await sleep(150);
    for (const ch of text) {
      if (document.activeElement !== input) {
        throw new Error('O foco saiu do campo no meio da digitação — abortando para não digitar no lugar errado.');
      }
      document.execCommand('insertText', false, ch);
      await sleep(charDelay);
    }
    // Alguns componentes (ex.: <br-date-picker>, que ENVOLVE o <input> real e
    // é o verdadeiro dono do FormControl do Angular) só reavaliam sua própria
    // validade ao ver 'change'/'keyup' no input interno — sem isso o texto
    // aparece certo na tela, mas o componente pai continua marcado como
    // ng-invalid e o botão "Confirmar" nunca habilita. Confirmado ao vivo no
    // campo "Validade": sem estas duas linhas ficava preso em "Campo
    // obrigatório" mesmo com o valor certo digitado. Disparar aqui é
    // inofensivo para inputs simples (ex.: campo de CNPJ).
    input.dispatchEvent(new Event('change', { bubbles: true }));
    input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
    await sleep(50);
    input.dispatchEvent(new Event('blur', { bubbles: true }));
  }

  // ---------- deteção de captcha ----------

  // Heurística de captcha: procura iframes de provedores conhecidos, ou
  // texto típico de desafio visual em português. Nunca interage com o captcha,
  // só detecta a presença dele para pausar a automação.
  function detectCaptcha() {
    const iframeHints = ['captcha', 'hcaptcha', 'recaptcha', 'geetest', 'funcaptcha', 'arkose'];
    const iframes = Array.from(document.querySelectorAll('iframe'));
    const suspicious = iframes.find((f) => {
      const src = (f.getAttribute('src') || '').toLowerCase();
      return isVisible(f) && iframeHints.some((h) => src.includes(h));
    });
    if (suspicious) return true;

    const bodyText = document.body.innerText.toLowerCase();
    const hints = ['clique no animal', 'selecione as imagens', 'verificação de segurança', 'não sou um robô'];
    return hints.some((h) => bodyText.includes(h));
  }

  // ---------- seletores conferidos ao vivo no portal ----------

  const SEL = {
    trigger: '#avatar-dropdown-trigger', // botão do CNPJ/avatar no cabeçalho, abre o menu do usuário
    panel: '#formularioRepresentacao',   // div que contém todo o formulário de troca de representação
    cnpjInput: '#input-representar-cpfcnpj',
    ngSelect: 'ng-select',               // combobox de perfil (classe "brx-input"); só há um dentro do painel
    erroMsg: '.mensagemErro',
  };

  // O #formularioRepresentacao continua existindo no DOM mesmo fechado/colapsado
  // (o portal só troca classes/CSS, não remove o elemento) — por isso checar
  // "existe" não basta, é preciso checar se está de fato visível/expandido.
  function isReasonablyVisible(el, minHeight = 0) {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > minHeight;
  }

  async function openRepresentationMenuIfNeeded() {
    // 1) Garante que o menu do usuário (dropdown do cabeçalho) esteja aberto.
    //    Ele pode ter fechado sozinho (ex.: comportamento padrão de dropdown
    //    Bootstrap que fecha em qualquer clique fora dele).
    let panel = document.querySelector(SEL.panel);
    if (!isReasonablyVisible(panel)) {
      const trigger = document.querySelector(SEL.trigger);
      if (!trigger) return false;
      clickEl(trigger);
      panel = await waitFor(() => {
        const p = document.querySelector(SEL.panel);
        return isReasonablyVisible(p) ? p : null;
      }, { timeout: 4000 });
      if (!panel) return false;
    }

    // 2) Garante que a seção esteja EXPANDIDA. É um acordeão (botão
    //    button.expandir com aria-expanded) que some para ~20px de altura
    //    quando colapsado — bem menor que os ~200px com os campos visíveis.
    if (!isReasonablyVisible(panel, 80)) {
      const expandBtn = panel.querySelector('button.expandir');
      if (expandBtn) {
        clickSequence(expandBtn);
        await waitFor(() => isReasonablyVisible(document.querySelector(SEL.panel), 80), { timeout: 3000 });
        // A checagem de altura acima "pega" o painel assim que a transição de
        // abrir o acordeão COMEÇA a crescer além de 80px, não quando ela
        // termina — visto ao vivo causando falha de foco no campo de CNPJ
        // logo em seguida (primeiro CNPJ da lista). Um respiro extra deixa a
        // animação assentar antes de qualquer interação com os campos.
        await sleep(300);
      }
    }

    return isReasonablyVisible(document.querySelector(SEL.panel), 80);
  }

  function getPanelRoot() {
    return document.querySelector(SEL.panel) || document;
  }

  async function fillCnpj(panel, cnpj) {
    const input = await waitFor(() => panel.querySelector(SEL.cnpjInput));
    if (!input) throw new Error('Campo de CNPJ não encontrado (verifique SEL.cnpjInput em content.js).');

    // Se um ng-select de tentativa anterior ficou aberto, ele pode "prender" o
    // foco e fazer a digitação do CNPJ vazar para a caixa de busca dele. Fecha
    // qualquer dropdown de perfil aberto antes de mexer no campo de CNPJ.
    const ngSelect = panel.querySelector(SEL.ngSelect);
    if (ngSelect && ngSelect.classList.contains('ng-select-opened')) {
      const container = ngSelect.querySelector('.ng-select-container');
      if (container) { clickSequence(container); await sleep(200); }
    }

    const digitos = cnpj.replace(/\D/g, '');
    await typeInto(input, digitos);

    // Confere que o valor realmente foi para o campo certo (e não vazou para
    // outro lugar). O portal formata como XX.XXX.XXX/XXXX-XX.
    const valorFinal = input.value.replace(/\D/g, '');
    if (valorFinal !== digitos) {
      throw new Error(`O campo de CNPJ ficou com valor inesperado ("${input.value}") depois de digitar "${cnpj}" — provável vazamento de foco para outro campo.`);
    }
    return input;
  }

  async function selectPerfil(panel, perfilTexto) {
    const ngSelect = await waitFor(() => panel.querySelector(SEL.ngSelect));
    if (!ngSelect) throw new Error('Seletor de perfil (ng-select) não encontrado no painel.');

    const container = ngSelect.querySelector('.ng-select-container');
    if (!container) throw new Error('Container do ng-select não encontrado.');

    // O ng-select ABRE/FECHA (toggle) a cada clique no container. Se por algum
    // motivo ele já estiver aberto quando chegamos aqui (ex.: abriu sozinho ao
    // perder o foco do campo de CNPJ), clicar de novo iria FECHÁ-LO — daí a
    // extensão nunca achar as opções. Por isso checamos o estado antes de clicar.
    const isOpen = () => ngSelect.classList.contains('ng-select-opened') || !!panel.querySelector('.ng-option');

    const buscarOpcao = () => {
      const opts = Array.from(panel.querySelectorAll('.ng-option'));
      return opts.find((o) => textOf(o).toLowerCase() === perfilTexto.trim().toLowerCase()) || null;
    };

    // Lê o valor atualmente exibido no combobox FECHADO (ex.: "Procurador").
    // ng-select normalmente renderiza isso em ".ng-value-label" dentro do
    // container; se essa classe não existir nesta versão do componente,
    // cai para o texto visível do container (sem a caixa de busca).
    function lerValorExibido() {
      const label = container.querySelector('.ng-value-label');
      if (label) return textOf(label);
      const clone = container.cloneNode(true);
      const inputClone = clone.querySelector('input');
      if (inputClone) inputClone.remove();
      return textOf(clone);
    }

    // Relatado ao vivo pelo usuário: o CNPJ era válido, mas a representação
    // não habilitava porque o campo de perfil ficava vazio na hora de
    // clicar em "Representar". Ou seja, clicar na opção nem sempre é
    // suficiente — o clique pode "pegar" no DOM um instante antes do
    // Angular atualizar o texto exibido no combobox fechado. Por isso, além
    // de clicar, CONFIRMAMOS que o valor exibido realmente mudou para o
    // perfil escolhido antes de considerar concluído; se não confirmar,
    // tentamos mais uma vez (reabrindo o dropdown do zero).
    async function escolherEConfirmar() {
      if (!isOpen()) {
        clickSequence(container);
        await waitFor(() => isOpen(), { timeout: 2000 });
      }

      const option = await waitFor(buscarOpcao, { timeout: 3000 });
      if (!option) return { ok: false, motivo: 'opcao-nao-encontrada' };

      clickSequence(option);

      const confirmado = await waitFor(() => {
        const atual = lerValorExibido();
        return !!(atual && atual.trim().toLowerCase() === perfilTexto.trim().toLowerCase());
      }, { timeout: 3000, interval: 150 });

      return confirmado ? { ok: true } : { ok: false, motivo: 'selecao-nao-confirmada' };
    }

    let resultado = await escolherEConfirmar();
    if (!resultado.ok) {
      // Uma segunda tentativa cobre tanto "a lista fechou antes de eu achar
      // a opção" quanto "cliquei mas o texto exibido não atualizou a tempo".
      await sleep(400);
      resultado = await escolherEConfirmar();
    }

    if (!resultado.ok) {
      if (resultado.motivo === 'opcao-nao-encontrada') {
        const vistas = Array.from(panel.querySelectorAll('.ng-option')).map(textOf);
        throw new Error(
          `Opção de perfil "${perfilTexto}" não encontrada. Opções realmente vistas agora: `
          + (vistas.length ? vistas.join(', ') : '(nenhuma — o dropdown provavelmente não abriu; veja o comentário sobre toggle em selectPerfil())')
        );
      }
      throw new Error(
        `Cliquei na opção "${perfilTexto}" mas o campo continuou sem refletir a seleção (valor exibido: "${lerValorExibido() || '(vazio)'}") depois de 2 tentativas — provavelmente lentidão da página nesse momento.`
      );
    }

    return true;
  }

  async function clickRepresentar(panel) {
    // Existe também um botão "Representar" com classe "expandir" (é o
    // colapsável/acordeão do formulário, não o botão de submit) — por isso
    // filtramos por button.br-button, que é o botão de submit de verdade.
    const btn = await waitFor(() => {
      const candidates = Array.from(panel.querySelectorAll('button.br-button'));
      return candidates.find((b) => textOf(b).toLowerCase() === 'representar') || null;
    });
    if (!btn) throw new Error('Botão "Representar" (button.br-button) não encontrado.');
    clickEl(btn);
    return true;
  }

  // Ao clicar em "Representar" no formulário principal, o portal às vezes
  // abre um modal extra de confirmação — visto ao vivo com pelo menos DUAS
  // variantes de texto diferentes:
  //   - "Você está representando o CNPJ X. Deseja trocar a representação
  //     para o CNPJ Y?" (quando já havia outra representação ativa)
  //   - "Você tem certeza de que deseja representar o CNPJ Y?" (quando não
  //     havia troca, ex.: primeira representação)
  // Por isso NÃO casamos pelo texto do corpo (variável) e sim pelo título do
  // modal (id="altera-rep-titulo", texto "Representar"), que é igual nas
  // duas variantes — mesma estrutura de modal já tratada em
  // tentarRepresentarViaRecentes() (.modal-content, botão "Representar"
  // ligado a um hCaptcha invisível). Confirmado com o usuário: clicar em
  // "Representar" aqui é seguro. Como o botão usa hCaptcha invisível,
  // clickSequence() é obrigatório (clickEl() simples não dispara o fluxo do
  // widget — mesmo motivo já documentado no modal de "Recentes"). Depois de
  // clicar, esperamos ~5s (pedido explícito do usuário) pra troca efetivar
  // no backend antes de seguir para a geração da credencial.
  async function tratarModalConfirmacaoTroca() {
    const modal = await waitFor(() => {
      const m = Array.from(document.querySelectorAll('.modal-content')).find((x) => {
        if (!isVisible(x)) return false;
        const titulo = x.querySelector('#altera-rep-titulo, .modal-title');
        return titulo && textOf(titulo).trim().toLowerCase() === 'representar';
      });
      return m || null;
    }, { timeout: 2500, interval: 200 });

    if (!modal) return null; // não apareceu — segue o fluxo normal de detecção

    const confirmar = Array.from(modal.querySelectorAll('button')).find((b) => textOf(b).trim() === 'Representar');
    if (!confirmar) {
      return { type: 'erro', mensagem: 'Modal de confirmação de troca de representação apareceu, mas o botão "Representar" não foi encontrado nele.' };
    }
    clickSequence(confirmar);
    await sleep(5000);

    if (detectCaptcha()) return { type: 'captcha' };
    return { type: 'sucesso' };
  }

  // Depois de clicar em Representar, descobre o que aconteceu.
  async function detectOutcome(panel, cnpjInput) {
    const result = await waitFor(() => {
      if (detectCaptcha()) return { type: 'captcha' };

      const erroEl = panel.querySelector(SEL.erroMsg);
      if (erroEl && isVisible(erroEl) && textOf(erroEl)) {
        return { type: 'erro', mensagem: textOf(erroEl) };
      }

      // Sucesso: ao concluir, o formulário reseta e o campo de CNPJ volta a
      // ficar vazio (o painel também costuma fechar/recolher).
      const stillPanel = document.querySelector(SEL.panel);
      const input = stillPanel ? stillPanel.querySelector(SEL.cnpjInput) : null;
      if (!stillPanel || !input || input.value.trim() === '') return { type: 'sucesso' };

      return null;
    }, { timeout: 8000, interval: 300 });

    return result || { type: 'desconhecido', mensagem: 'Nenhum resultado claro em 8s — confira manualmente.' };
  }

  // ---------- reaproveitar representações já concedidas ----------
  //
  // Descoberta ao vivo (não estava no plano original): se um CNPJ JÁ foi
  // representado antes (grant já existe), o formulário normal de "Trocar
  // Representação" para de oferecer qualquer perfil — o ng-select mostra só
  // o placeholder "Não encontrado", porque não há nada novo para conceder.
  // Isso é esperado e vai acontecer sempre que a lista de CNPJs for
  // reprocessada (ex.: rodar nesta extensão de novo para gerar credenciais
  // depois de já ter trocado a representação antes) — sem este atalho, esses
  // CNPJs cairiam incorretamente como erro ("perfil não encontrado"), mesmo
  // sendo CNPJs válidos e já autorizados.
  //
  // O caminho certo, confirmado ao vivo, é a seção "Representações
  // Recentes" do mesmo painel: cada linha tem um botão de atalho
  // (button.br-button.circle) que reabre aquela representação com só uma
  // confirmação num modal (.modal-content) — sem escolher perfil de novo.
  // Se você já estiver representando aquele CNPJ no momento do clique, o
  // modal muda de figura e só avisa "Você já está representando o CNPJ X"
  // (com um botão "Cancelar" apenas) — tratamos isso também como sucesso.

  function getRecentesContainer() {
    const btn = Array.from(document.querySelectorAll('button.expandir'))
      .find((b) => textOf(b) === 'Representações Recentes');
    return btn ? btn.closest('.item-title').parentElement : null;
  }

  async function abrirRecentesSeNecessario() {
    let container = getRecentesContainer();
    if (!container) return null;
    if (!isReasonablyVisible(container, 40)) {
      const expandBtn = container.querySelector('button.expandir');
      if (expandBtn) {
        clickSequence(expandBtn);
        await waitFor(() => isReasonablyVisible(getRecentesContainer(), 40), { timeout: 3000 });
      }
    }
    return getRecentesContainer();
  }

  function encontrarAtalhoRecente(container, cnpj) {
    const digitos = cnpj.replace(/\D/g, '');
    const linhas = Array.from(container.querySelectorAll('.d-flex.align-items-center'));
    const linha = linhas.find((l) => (l.textContent || '').replace(/\D/g, '').includes(digitos));
    return linha ? linha.querySelector('button.br-button.circle') : null;
  }

  // Retorna null quando este CNPJ NÃO está em "Representações Recentes"
  // (é novo) — quem chamou deve então seguir para o formulário normal.
  // Quando está, retorna o resultado final (sucesso/captcha/erro) direto.
  async function tentarRepresentarViaRecentes(cnpj) {
    const container = await abrirRecentesSeNecessario();
    if (!container) return null;

    const atalho = encontrarAtalhoRecente(container, cnpj);
    if (!atalho) return null;

    clickSequence(atalho);
    const modal = await waitFor(() => {
      const m = Array.from(document.querySelectorAll('.modal-content'))
        .find((x) => isVisible(x) && /representar/i.test(textOf(x)));
      return m || null;
    }, { timeout: 4000 });

    if (!modal) {
      return { type: 'erro', mensagem: 'Cliquei no atalho de "Representações Recentes" mas nenhum modal de confirmação apareceu.' };
    }

    if (/já está representando/i.test(textOf(modal))) {
      // Já é a representação ativa agora — nada a fazer, conta como sucesso.
      const fechar = Array.from(modal.querySelectorAll('button')).find((b) => textOf(b) === 'Cancelar');
      if (fechar) clickSequence(fechar);
      return { type: 'sucesso' };
    }

    const confirmar = Array.from(modal.querySelectorAll('button')).find((b) => textOf(b) === 'Representar');
    if (!confirmar) {
      return { type: 'erro', mensagem: 'Modal de confirmação do atalho apareceu mas o botão "Representar" não foi encontrado.' };
    }
    // IMPORTANTE: este botão, diferente do "Representar" do formulário
    // principal, só reage à sequência completa mousedown+mouseup+click — um
    // clickEl() (.click() simples) NÃO fecha o modal nem confirma nada
    // (confirmado ao vivo: o modal ficava aberto pra sempre). Por isso
    // clickSequence() aqui, não clickEl().
    clickSequence(confirmar);

    const digitos = cnpj.replace(/\D/g, '');
    return waitFor(() => {
      if (detectCaptcha()) return { type: 'captcha' };
      const atualBtn = Array.from(document.querySelectorAll('button.expandir')).find((b) => textOf(b) === 'Representação Atual');
      if (!atualBtn) return null;
      const atualContainer = atualBtn.closest('.item-title').parentElement;
      if ((atualContainer.textContent || '').replace(/\D/g, '').includes(digitos)) {
        return { type: 'sucesso' };
      }
      return null;
    }, { timeout: 8000, interval: 300 });
  }

  // ---------- geração de credencial (Chaves Secretas / TLS) ----------
  //
  // Confirmado ao vivo: a credencial é por REPRESENTAÇÃO (não por login). Ou
  // seja, representando o CNPJ X e gerando uma credencial, ela fica associada
  // a X; ao trocar para o CNPJ Y e gerar de novo, é uma credencial NOVA e
  // diferente. Se já existir uma "Chaves Secretas" para aquela representação,
  // "Gerar Token" pula direto para a tela de visualização da existente (não
  // cria duplicata) — o código abaixo trata os dois casos.

  const URL_HOME = 'https://consumo.tributos.gov.br/';
  const URL_NOVA_CREDENCIAL = 'https://consumo.tributos.gov.br/servico/credencial-api-beta/credenciais-acesso/nova-credencial';

  const SEL_CRED = {
    nomeInput: 'input[placeholder="Digite um nome para identificar a credencial"]',
    validadeInput: 'input[placeholder="Validade"]',
  };

  // "Validade": 5 anos a partir de HOJE (data em que a extensão está rodando),
  // no formato DD/MM/AAAA que o campo espera.
  function dataValidadeEm5Anos() {
    const d = new Date();
    d.setFullYear(d.getFullYear() + 5);
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    return `${dd}/${mm}/${yyyy}`;
  }

  function encontrarCheckboxConsentimento() {
    function up(e, n) { let x = e; for (let i = 0; i < n && x.parentElement; i++) x = x.parentElement; return x; }
    const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
    return checkboxes.find((c) => /Autorizo a Receita Federal/i.test(up(c, 3).innerText || '')) || null;
  }

  // Lê um campo da tela "Visualizar Credencial" (Nome, Validade, Client Id,
  // Client Secret são todos renderizados como blocos .view-field).
  function lerCampoView(labelTexto) {
    const fields = Array.from(document.querySelectorAll('.view-field'));
    const field = fields.find((f) => {
      const l = f.querySelector('.view-field__label');
      return l && textOf(l).trim().toLowerCase() === labelTexto.trim().toLowerCase();
    });
    if (!field) return null;
    const valorEl = field.querySelector('.view-field__input span, .view-field__input');
    return valorEl ? textOf(valorEl).trim() : null;
  }

  // Nome do escritório/procurador logado, usado como "Nome" da credencial.
  // Só aparece dentro do painel do avatar (.item-username), então abrimos o
  // painel, lemos e fechamos de novo.
  async function capturarNomeEscritorio() {
    const trigger = document.querySelector(SEL.trigger);
    if (!trigger) return null;
    const jaAberto = !!document.querySelector('.item-username');
    if (!jaAberto) clickEl(trigger);
    const el = await waitFor(() => document.querySelector('.item-username'), { timeout: 3000 });
    const nome = el ? textOf(el) : null;
    if (!jaAberto && trigger) clickEl(trigger); // fecha de novo do jeito que achamos
    return nome;
  }

  // Baixa o CSV final (CNPJ, ClientId, ClientSecret) — tudo local, no
  // navegador do usuário; nada disso é enviado para lugar nenhum.
  function baixarCsv(resultados) {
    const linhas = ['CNPJ,ClientId,ClientSecret'];
    resultados.forEach((r) => {
      if (r.clientId && r.clientSecret) {
        linhas.push(`"${r.cnpj}","${r.clientId}","${r.clientSecret}"`);
      }
    });
    const csv = linhas.join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `credenciais-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }

  // ---------- painel flutuante (UI) ----------

  let panelEls = null;

  function ensureFloatingPanel() {
    if (panelEls) return panelEls;

    const host = document.createElement('div');
    host.style.position = 'fixed';
    host.style.top = '16px';
    host.style.right = '16px';
    host.style.zIndex = 2147483647;
    document.documentElement.appendChild(host);

    const shadow = host.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        .box {
          width: 320px;
          background: #fff;
          border: 1px solid #ccc;
          border-radius: 8px;
          box-shadow: 0 4px 16px rgba(0,0,0,.2);
          font-family: system-ui, Arial, sans-serif;
          font-size: 13px;
          color: #1a1a1a;
        }
        .head {
          display: flex; justify-content: space-between; align-items: center;
          padding: 8px 10px; background: #0b3d91; color: #fff; border-radius: 8px 8px 0 0;
          cursor: move;
        }
        .head button { background: none; border: none; color: #fff; cursor: pointer; font-size: 14px; }
        .body { padding: 10px; }
        textarea { width: 100%; box-sizing: border-box; min-height: 80px; font-family: monospace; font-size: 12px; }
        select, button.action { width: 100%; box-sizing: border-box; padding: 6px; margin-top: 6px; font-size: 13px; }
        .row { display: flex; gap: 6px; }
        .row button { flex: 1; }
        #log { margin-top: 8px; max-height: 200px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; padding: 6px; background: #fafafa; }
        .item { padding: 3px 2px; border-bottom: 1px solid #eee; }
        .item:last-child { border-bottom: none; }
        .ok { color: #157347; font-weight: 600; }
        .erro { color: #b02a37; font-weight: 600; }
        .captcha { color: #b8860b; font-weight: 600; }
        .info { color: #555; }
        label { display:block; font-weight: 600; margin-top: 6px; }
        .aviso { font-size: 11px; color: #8a5a00; background: #fff6e5; border: 1px solid #ffe1a6; border-radius: 4px; padding: 6px; margin-top: 6px; }
        button.secondary { background: #fff; border: 1px solid #0b3d91; color: #0b3d91; }
      </style>
      <div class="box">
        <div class="head">
          <strong>Representação + Credencial</strong>
          <button id="fechar" title="Fechar">✕</button>
        </div>
        <div class="body">
          <label>CNPJs (um por linha)</label>
          <textarea id="cnpjs" placeholder="12.345.678/0001-99&#10;11.345.572/0001-29&#10;07.467.651/0001-35"></textarea>
          <label>Perfil</label>
          <select id="perfil">
            <option value="Procurador">Procurador</option>
            <option value="Matriz">Matriz</option>
            <option value="Sucessor">Sucessor</option>
            <option value="Ente Federado">Ente Federado</option>
          </select>
          <div class="aviso">Para cada CNPJ: troca a representação e, se der certo, gera uma credencial "Chaves Secretas" nova (Nome = escritório logado, Validade = hoje + 5 anos). No final baixa um CSV com CNPJ, ClientId e ClientSecret. O CSV tem segredos em texto puro — guarde com cuidado e apague depois de importar.</div>
          <div class="row">
            <button class="action" id="iniciar">Iniciar</button>
            <button class="action" id="parar" disabled>Parar</button>
          </div>
          <button class="action" id="continuar" disabled>Continuar após CAPTCHA</button>
          <button class="action secondary" id="baixarCsv" disabled>Baixar CSV agora</button>
          <div id="log"></div>
        </div>
      </div>
    `;

    panelEls = {
      host,
      shadow,
      cnpjsEl: shadow.getElementById('cnpjs'),
      perfilEl: shadow.getElementById('perfil'),
      iniciarBtn: shadow.getElementById('iniciar'),
      pararBtn: shadow.getElementById('parar'),
      continuarBtn: shadow.getElementById('continuar'),
      baixarCsvBtn: shadow.getElementById('baixarCsv'),
      logEl: shadow.getElementById('log'),
    };

    shadow.getElementById('fechar').addEventListener('click', () => {
      host.style.display = 'none';
    });

    makeDraggable(host, shadow.querySelector('.head'));

    panelEls.iniciarBtn.addEventListener('click', onIniciar);
    panelEls.pararBtn.addEventListener('click', onParar);
    panelEls.continuarBtn.addEventListener('click', onContinuar);
    panelEls.baixarCsvBtn.addEventListener('click', async () => {
      const state = await getState();
      if (state && state.resultados && state.resultados.some((r) => r.clientId)) {
        baixarCsv(state.resultados);
      } else {
        log('info', 'Ainda não há nenhuma credencial coletada para baixar.');
      }
    });

    return panelEls;
  }

  function makeDraggable(host, handle) {
    let dragging = false, offX = 0, offY = 0;
    handle.addEventListener('mousedown', (e) => {
      dragging = true;
      offX = e.clientX - host.getBoundingClientRect().left;
      offY = e.clientY - host.getBoundingClientRect().top;
    });
    document.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      host.style.right = 'auto';
      host.style.left = `${e.clientX - offX}px`;
      host.style.top = `${e.clientY - offY}px`;
    });
    document.addEventListener('mouseup', () => { dragging = false; });
  }

  // ---------- estado / persistência ----------
  //
  // Cada CNPJ agora passa por VÁRIAS páginas (home → nova-credencial →
  // visualizar), e mudar de URL recarrega a extensão do zero. Por isso todo
  // o progresso mora em chrome.storage.local, com uma "fase" explícita, e a
  // função tick() é chamada de novo a cada carregamento de página para
  // continuar de onde parou — é uma máquina de estados simples, não um loop
  // único em memória (que morreria a cada navegação).
  //
  // fase:
  //   'representar'           -> troca a representação para cnpjs[index]
  //   'abrir-credencial'      -> na página de credenciais, clica "Gerar Token"
  //   'preencher-credencial'  -> preenche Nome/Validade/Consentimento e confirma
  //   'ler-credencial'        -> lê Client Id / Client Secret da tela de resultado
  //   'finalizado'            -> baixa o CSV e para

  async function getState() {
    const data = await chrome.storage.local.get(STORAGE_KEY);
    return data[STORAGE_KEY] || null;
  }

  async function setState(state) {
    await chrome.storage.local.set({ [STORAGE_KEY]: state });
  }

  async function clearState() {
    await chrome.storage.local.remove(STORAGE_KEY);
  }

  function estadoInicial(cnpjs, perfil) {
    return {
      cnpjs,
      perfil,
      index: 0,
      fase: 'representar',
      aguardarNaHome: false,
      officeName: null,
      resultados: [], // { cnpj, clientId?, clientSecret?, erro? }
      logs: [],
      waitingCaptcha: false,
      running: true,
    };
  }

  async function logPersist(state, kind, msg) {
    state.logs.push({ kind, msg });
    await setState(state);
    renderLogs(state);
  }

  function renderLogs(state) {
    const { logEl } = ensureFloatingPanel();
    logEl.innerHTML = '';
    (state.logs || []).forEach(({ kind, msg }) => {
      const div = document.createElement('div');
      div.className = `item ${kind}`;
      div.textContent = msg;
      logEl.appendChild(div);
    });
    logEl.scrollTop = logEl.scrollHeight;
  }

  function log(kind, msg) {
    // usado só para mensagens que não precisam ficar no estado (ex.: erro de
    // input do usuário antes mesmo de existir um estado)
    const { logEl } = ensureFloatingPanel();
    const div = document.createElement('div');
    div.className = `item ${kind}`;
    div.textContent = msg;
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function atualizarBotoes(state) {
    const { pararBtn, iniciarBtn, continuarBtn, baixarCsvBtn } = ensureFloatingPanel();
    pararBtn.disabled = !state.running || state.waitingCaptcha;
    iniciarBtn.disabled = !!state.running;
    continuarBtn.disabled = !state.waitingCaptcha;
    baixarCsvBtn.disabled = !(state.resultados && state.resultados.some((r) => r.clientId));
  }

  function marcarErroCnpjAtual(state, mensagem) {
    const cnpj = state.cnpjs[state.index];
    state.resultados.push({ cnpj, erro: mensagem });
    state.index += 1;
    state.fase = 'representar';
  }

  // ---------- fluxo principal (máquina de estados) ----------

  async function processarUmCnpj(cnpj, perfil) {
    const abriu = await openRepresentationMenuIfNeeded();
    if (!abriu) return { type: 'erro', mensagem: 'Não consegui abrir o menu de representação (ajuste o seletor no content.js).' };

    const panel = getPanelRoot();

    // Atalho: CNPJ já representado antes → usa "Representações Recentes" (ver
    // comentário em tentarRepresentarViaRecentes). Retorna null se este CNPJ
    // não está lá (é novo), e nesse caso seguimos pro formulário normal.
    const viaRecentes = await tentarRepresentarViaRecentes(cnpj);
    if (viaRecentes) return viaRecentes;

    const cnpjInput = await fillCnpj(panel, cnpj);
    await sleep(600); // dá tempo da SPA buscar/carregar os perfis disponíveis para este CNPJ
    await selectPerfil(panel, perfil); // já confirma internamente que a seleção "pegou" antes de retornar
    await sleep(400);
    await clickRepresentar(panel);

    // Se já havia outra representação ativa, pode aparecer um modal extra
    // pedindo confirmação da troca (ver comentário em
    // tratarModalConfirmacaoTroca()). Se não aparecer, segue a detecção normal.
    const modalResultado = await tratarModalConfirmacaoTroca();
    if (modalResultado) return modalResultado;

    return detectOutcome(panel, cnpjInput);
  }

  async function finalizar(state) {
    const okCount = state.resultados.filter((r) => r.clientId).length;
    const erroCount = state.resultados.filter((r) => r.erro).length;
    await logPersist(state, 'info', `Concluído: ${okCount} credencial(is) gerada(s), ${erroCount} com erro. Baixando CSV...`);
    if (okCount > 0) baixarCsv(state.resultados);
    state.running = false;
    state.fase = 'finalizado';
    await setState(state);
    atualizarBotoes(state);
  }

  // Chamada uma vez a cada carregamento de página (via restoreIfNeeded) e
  // recursivamente após cada passo que NÃO navega para outra URL.
  async function tick() {
    const state = await getState();
    if (!state || !state.running || state.waitingCaptcha) return;

    if (state.index >= state.cnpjs.length) {
      await finalizar(state);
      return;
    }

    const cnpj = state.cnpjs[state.index];

    // ----- fase: trocar representação -----
    if (state.fase === 'representar') {
      // Acabamos de voltar pra home depois de gerar uma credencial (ver fase
      // 'ler-credencial'). Espera 40s aqui, já na home carregada, antes de
      // mexer no próximo CNPJ — dá tempo da tela (menu do avatar, painel de
      // representação etc.) carregar por completo, em vez de esperar ainda
      // na tela da credencial anterior e navegar logo em seguida.
      if (state.aguardarNaHome) {
        state.aguardarNaHome = false;
        await setState(state);
        await logPersist(state, 'info', 'Aguardando 40s para a página carregar por completo antes do próximo CNPJ...');
        await sleep(40000);
      }

      await logPersist(state, 'info', `[${state.index + 1}/${state.cnpjs.length}] Trocando representação para ${cnpj}...`);

      let resultado;
      try {
        resultado = await processarUmCnpj(cnpj, state.perfil);
      } catch (err) {
        resultado = { type: 'erro', mensagem: err.message };
      }

      if (resultado.type === 'captcha') {
        await logPersist(state, 'captcha', `[${cnpj}] CAPTCHA detectado — resolva manualmente e clique em "Continuar após CAPTCHA".`);
        state.waitingCaptcha = true;
        await setState(state);
        atualizarBotoes(state);
        return;
      }

      if (resultado.type !== 'sucesso') {
        await logPersist(state, 'erro', `[${cnpj}] Erro na representação: ${resultado.mensagem || resultado.type}`);
        marcarErroCnpjAtual(state, resultado.mensagem || resultado.type);
        await setState(state);
        await sleep(600);
        return tick(); // próximo CNPJ, ainda estamos na mesma página (home)
      }

      await logPersist(state, 'ok', `[${cnpj}] Representação OK. Indo gerar a credencial...`);

      if (!state.officeName) {
        state.officeName = await capturarNomeEscritorio();
        if (!state.officeName) {
          await logPersist(state, 'erro', 'Não consegui ler o nome do escritório logado (.item-username) — usando um nome genérico.');
          state.officeName = 'Credencial gerada automaticamente';
        }
      }

      state.fase = 'abrir-credencial';
      await setState(state);
      await sleep(300);
      window.location.href = URL_NOVA_CREDENCIAL; // recarrega; tick() roda de novo no próximo load
      return;
    }

    // ----- fase: abrir a tela de "Nova Credencial" e clicar em "Gerar Token" -----
    if (state.fase === 'abrir-credencial') {
      const btn = await waitFor(() => {
        const bs = Array.from(document.querySelectorAll('button'));
        return bs.find((b) => textOf(b) === 'Gerar Token') || null;
      }, { timeout: 8000 });

      if (!btn) {
        await logPersist(state, 'erro', `[${cnpj}] Botão "Gerar Token" não encontrado na página de credenciais.`);
        marcarErroCnpjAtual(state, 'Botão "Gerar Token" não encontrado.');
        await setState(state);
        return tick();
      }

      // clickSequence() por precaução: descobrimos ao vivo que um botão de
      // confirmação MUITO parecido (o "Representar" do modal de
      // "Representações Recentes", alguns parágrafos abaixo) ignora
      // silenciosamente um clickEl() simples — sem erro nenhum, só não
      // acontece nada. Testamos "Gerar Token" manualmente (clique real do
      // mouse, não .click() sintético) e funcionou, mas não dá pra testar o
      // .click() sintético em si sem gerar mais credenciais reais só pra
      // isso — por segurança, usamos aqui o clique mais robusto
      // (mousedown+mouseup+click) em vez de assumir que se comporta como o
      // "Representar" do formulário principal (que usa clickEl() e está
      // confirmado ok em uso real).
      clickSequence(btn);
      await sleep(700);

      // Formulário vazio (credencial nova) ou já foi direto pra visualização
      // de uma credencial existente para esta representação?
      const formVazio = await waitFor(() => document.querySelector(SEL_CRED.nomeInput), { timeout: 2000 });
      state.fase = formVazio ? 'preencher-credencial' : 'ler-credencial';
      await setState(state);
      return tick();
    }

    // ----- fase: preencher Nome / Validade / Consentimento e confirmar -----
    if (state.fase === 'preencher-credencial') {
      try {
        const nomeInput = await waitFor(() => document.querySelector(SEL_CRED.nomeInput), { timeout: 4000 });
        if (!nomeInput) throw new Error('Campo "Nome" da credencial não encontrado.');
        await typeInto(nomeInput, state.officeName);

        const validadeInput = document.querySelector(SEL_CRED.validadeInput);
        if (!validadeInput) throw new Error('Campo "Validade" da credencial não encontrado.');
        // clearMethod: 'execCommand' — ver comentário em typeInto(); o campo
        // "Validade" usa um <br-date-picker> por trás, que corrompe o valor se
        // limparmos via setter nativo de .value.
        await typeInto(validadeInput, dataValidadeEm5Anos(), { clearMethod: 'execCommand' });
        await sleep(300);

        const consent = encontrarCheckboxConsentimento();
        if (!consent) throw new Error('Checkbox de consentimento não encontrado.');
        if (!consent.checked) clickSequence(consent);
        await sleep(300);

        const confirmarBtn = await waitFor(() => {
          const b = Array.from(document.querySelectorAll('button')).find((x) => textOf(x) === 'Confirmar' && !x.disabled);
          return b || null;
        }, { timeout: 4000 });
        if (!confirmarBtn) throw new Error('Botão "Confirmar" não habilitou (algum campo pode estar inválido).');

        // clickSequence() pelo mesmo motivo de precaução do "Gerar Token"
        // acima — ver comentário lá.
        clickSequence(confirmarBtn);
        await sleep(500);

        if (detectCaptcha()) {
          await logPersist(state, 'captcha', `[${cnpj}] CAPTCHA detectado ao confirmar a credencial — resolva manualmente e clique em "Continuar após CAPTCHA".`);
          state.waitingCaptcha = true;
          await setState(state);
          atualizarBotoes(state);
          return;
        }
      } catch (err) {
        await logPersist(state, 'erro', `[${cnpj}] Erro ao preencher a credencial: ${err.message}`);
        marcarErroCnpjAtual(state, err.message);
        await setState(state);
        return tick();
      }

      state.fase = 'ler-credencial';
      await setState(state);
      await sleep(1000);
      return tick();
    }

    // ----- fase: ler Client Id / Client Secret da tela de resultado -----
    if (state.fase === 'ler-credencial') {
      const campos = await waitFor(() => {
        const clientId = lerCampoView('Client Id');
        const clientSecret = lerCampoView('Client Secret');
        return (clientId && clientSecret) ? { clientId, clientSecret } : null;
      }, { timeout: 8000 });

      if (!campos) {
        await logPersist(state, 'erro', `[${cnpj}] Não consegui ler Client Id / Client Secret na tela de resultado.`);
        marcarErroCnpjAtual(state, 'Client Id/Secret não encontrados na tela.');
      } else {
        state.resultados.push({ cnpj, clientId: campos.clientId, clientSecret: campos.clientSecret });
        await logPersist(state, 'ok', `[${cnpj}] Credencial obtida com sucesso.`);
        state.index += 1;
        state.fase = 'representar';
        // Sinaliza pra fase 'representar' esperar a página assentar antes de
        // mexer no próximo CNPJ (ver comentário na fase 'representar').
        state.aguardarNaHome = true;
      }

      await setState(state);
      atualizarBotoes(state);

      if (state.index >= state.cnpjs.length) return tick(); // cai no finalizar()

      await sleep(500);
      window.location.href = URL_HOME; // volta pra home pra reabrir o menu de representação
      return;
    }
  }

  async function onIniciar() {
    const { cnpjsEl, perfilEl } = ensureFloatingPanel();
    const cnpjs = cnpjsEl.value.split('\n').map((s) => s.trim()).filter(Boolean);
    if (cnpjs.length === 0) {
      log('erro', 'Cole ao menos um CNPJ na caixa de texto.');
      return;
    }
    const perfil = perfilEl.value;
    const state = estadoInicial(cnpjs, perfil);
    await setState(state);
    atualizarBotoes(state);
    tick();
  }

  async function onParar() {
    const state = await getState();
    if (!state) return;
    state.running = false;
    await setState(state);
    atualizarBotoes(state);
    log('info', 'Execução marcada para parar (efetiva no próximo passo).');
  }

  async function onContinuar() {
    const state = await getState();
    if (!state) return;
    state.waitingCaptcha = false;
    await setState(state);
    atualizarBotoes(state);
    await logPersist(state, 'info', 'Retomando após CAPTCHA...');
    tick();
  }

  // Roda a cada carregamento de página: restaura a caixa de CNPJs/perfil,
  // repinta o log a partir do que está salvo, e continua a máquina de
  // estados se uma execução estava em andamento.
  async function restoreIfNeeded() {
    const state = await getState();
    if (!state) return;
    const { cnpjsEl, perfilEl } = ensureFloatingPanel();
    cnpjsEl.value = state.cnpjs.join('\n');
    perfilEl.value = state.perfil;
    renderLogs(state);
    atualizarBotoes(state);
    if (state.running && !state.waitingCaptcha) {
      await sleep(500); // dá um respiro pra página terminar de montar
      tick();
    }
  }

  // ---------- mensageria com popup.js ----------

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg && msg.type === 'TOGGLE_PAINEL') {
      const { host } = ensureFloatingPanel();
      host.style.display = host.style.display === 'none' ? 'block' : 'none';
    }
  });

  // Não abre o painel sozinho ao carregar a página — só cria e restaura
  // estado se havia uma execução em andamento.
  restoreIfNeeded();
})();
