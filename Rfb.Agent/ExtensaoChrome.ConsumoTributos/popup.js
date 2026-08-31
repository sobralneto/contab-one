// popup.js
// Apenas envia uma mensagem para o content script da aba ativa pedindo
// para mostrar/esconder o painel flutuante. Toda a lógica de automação
// vive em content.js, rodando na própria página.

const statusEl = document.getElementById('status');

document.getElementById('toggle').addEventListener('click', async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url || !tab.url.includes('consumo.tributos.gov.br')) {
      statusEl.textContent = 'Abra uma aba em consumo.tributos.gov.br primeiro.';
      return;
    }
    await chrome.tabs.sendMessage(tab.id, { type: 'TOGGLE_PAINEL' });
    window.close();
  } catch (err) {
    statusEl.textContent = 'Não consegui falar com a página. Recarregue a aba do portal e tente de novo.';
    console.error(err);
  }
});
