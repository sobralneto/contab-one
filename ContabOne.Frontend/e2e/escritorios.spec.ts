import { test, expect } from '@playwright/test'
import { CREDENCIAIS, login, prepararSeed, sufixoUnico } from './helpers'

test.describe('Admin suspender escritório', () => {
  test('7.6 admin cria um escritório próprio para o teste, suspende, e o status reflete na listagem', async ({ page }) => {
    await prepararSeed()
    await login(page, CREDENCIAIS.admin.email, CREDENCIAIS.admin.senha)

    const nome = `Escritório E2E ${sufixoUnico()}`

    // Cria o próprio escritório (não suspende o semeado — bloquearia os
    // outros testes, design.md Decisão 6)
    await page.goto('/admin/escritorios')
    await page.click('text=Novo escritório')
    await page.locator('.modal-form input').nth(0).fill(nome)
    await page.click('.modal-form button[type="submit"]')
    await expect(page.locator('.modal-overlay')).toHaveCount(0)
    await expect(page.locator('.data-table')).toContainText(nome)

    // Edita e muda o status para Suspenso
    const linha = page.locator('.data-table tbody tr', { hasText: nome })
    await linha.locator('.btn-edit').first().click() // botão de editar
    await page.locator('.status-select').selectOption('Suspenso')
    await expect(page.locator('.modal-card')).toContainText('bloqueado no próximo handshake')

    // Mudança de status exige confirmação — o Salvar abre um segundo modal
    // (o de editar continua aberto embaixo; escopar pelo texto)
    await page.click('.modal-form button[type="submit"]')
    await expect(page.getByText('Alterar status do escritório')).toBeVisible()
    await page.click('.modal-actions .btn-danger')

    await expect(page.locator('.modal-overlay')).toHaveCount(0)
    await expect(page.locator('.data-table tbody tr', { hasText: nome })).toContainText('Suspenso')
  })
})
