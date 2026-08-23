import { test, expect } from '@playwright/test'
import { criarEscritorioViaApi, CREDENCIAIS, login, prepararSeed, sufixoUnico } from './helpers'

test.describe('Gerar chave de agente', () => {
  test('7.5 a chave completa é exibida uma única vez, com o aviso, e o agente aparece na lista com apenas o prefixo', async ({ page }) => {
    await prepararSeed()
    // Escritório próprio (sem limite de agentes) — os compartilhados do seed
    // já estouraram o limite com execuções anteriores.
    const nomeEsc = `Escritório Agente ${sufixoUnico()}`
    await criarEscritorioViaApi(nomeEsc)
    await login(page, CREDENCIAIS.admin.email, CREDENCIAIS.admin.senha)

    await page.goto('/agentes')
    await page.click('text=Gerar nova chave')

    // Admin: seleciona o escritório antes de gerar (modal de seleção — o
    // select é required e o placeholder é disabled)
    await expect(page.locator('.modal-card')).toContainText('Nova chave de agente')
    await page.locator('.modal-form select').selectOption({ label: nomeEsc })
    await page.click('.modal-form button[type="submit"]')

    // Modal da chave: aviso de exibição única + chave completa
    await expect(page.locator('.chave-aviso')).toContainText('apenas uma vez')
    const chaveCompleta = (await page.locator('.chave-valor').textContent())?.trim() ?? ''
    expect(chaveCompleta).toMatch(/^nfse_[0-9a-f]{8}_[0-9a-f]{32}$/)

    // Fecha o modal — a chave NÃO é exibida de novo
    await page.click('.modal-actions .btn-secondary')
    await expect(page.locator('.chave-valor')).toHaveCount(0)

    // O agente aparece na lista com apenas o prefixo
    const prefixo = chaveCompleta.split('_')[1]
    await expect(page.locator('.data-table')).toContainText(`nfse_${prefixo}_…`)
  })
})
