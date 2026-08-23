import { test, expect } from '@playwright/test'
import { criarEscritorioViaApi, CREDENCIAIS, login, prepararSeed, sufixoUnico } from './helpers'

test.describe('Gerar chave de agente', () => {
  test('7.5 a chave completa é exibida uma única vez, com o aviso, e o agente aparece na lista com apenas o prefixo da ferramenta escolhida', async ({ page }) => {
    await prepararSeed()
    // Escritório próprio (sem limite de agentes) — os compartilhados do seed
    // já estouraram o limite com execuções anteriores.
    const nomeEsc = `Escritório Agente ${sufixoUnico()}`
    await criarEscritorioViaApi(nomeEsc)
    await login(page, CREDENCIAIS.admin.email, CREDENCIAIS.admin.senha)

    await page.goto('/agentes')
    await page.click('text=Gerar nova chave')

    // Escolhe a ferramenta e, como admin, o escritório (ambos required, com
    // placeholder disabled no de escritório)
    await expect(page.locator('.modal-card')).toContainText('Nova chave de agente')
    await page.locator('.modal-form select[name="produto"]').selectOption('Det')
    await page.locator('.modal-form select[name="escritorio"]').selectOption({ label: nomeEsc })
    await page.click('.modal-form button[type="submit"]')

    // Modal da chave: aviso de exibição única + chave completa, com o prefixo
    // da ferramenta escolhida (e não `nfse_` fixo)
    await expect(page.locator('.chave-aviso')).toContainText('apenas uma vez')
    const chaveCompleta = (await page.locator('.chave-valor').textContent())?.trim() ?? ''
    expect(chaveCompleta).toMatch(/^det_[0-9a-f]{8}_[0-9a-f]{32}$/)

    // Fecha o modal — a chave NÃO é exibida de novo
    await page.click('.modal-actions .btn-secondary')
    await expect(page.locator('.chave-valor')).toHaveCount(0)

    // O agente aparece na lista com apenas o prefixo, marcado com a ferramenta
    const prefixo = chaveCompleta.split('_')[1]
    await expect(page.locator('.data-table')).toContainText(`det_${prefixo}_…`)
    await expect(page.locator('.data-table .produto-chip').first()).toContainText('DET')
  })
})
