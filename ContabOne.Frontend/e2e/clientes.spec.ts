import { test, expect } from '@playwright/test'
import { CREDENCIAIS, login, prepararSeed, sufixoUnico } from './helpers'

test.describe('Cadastrar cliente', () => {
  test('7.3 escritório cria um cliente com código único e ele aparece na listagem', async ({ page }) => {
    await prepararSeed()
    await login(page, CREDENCIAIS.escritorio.email, CREDENCIAIS.escritorio.senha)

    const codigo = 'e2e' + sufixoUnico()
    const nome = `Cliente E2E ${sufixoUnico()}`

    await page.goto('/clientes')
    await page.click('text=Novo cliente')
    await page.fill('input[placeholder="00.000.000/0000-00"]', '') // CNPJ opcional — só confirma o foco do modal
    await page.locator('.modal-form input').nth(0).fill(codigo) // Código
    await page.locator('.modal-form input').nth(1).fill(nome) // Nome
    await page.click('.modal-form button[type="submit"]')

    // O modal fecha e o cliente aparece na tabela
    await expect(page.locator('.modal-overlay')).toHaveCount(0)
    await expect(page.locator('.data-table')).toContainText(codigo)
    await expect(page.locator('.data-table')).toContainText(nome)
  })

  test('7.4 código repetido no mesmo escritório é rejeitado com mensagem', async ({ page }) => {
    await prepararSeed()
    await login(page, CREDENCIAIS.escritorio.email, CREDENCIAIS.escritorio.senha)

    const codigo = 'dup' + sufixoUnico()

    await page.goto('/clientes')
    // cria o primeiro
    await page.click('text=Novo cliente')
    await page.locator('.modal-form input').nth(0).fill(codigo)
    await page.locator('.modal-form input').nth(1).fill('Cliente Original')
    await page.click('.modal-form button[type="submit"]')
    await expect(page.locator('.modal-overlay')).toHaveCount(0)
    await expect(page.locator('.data-table')).toContainText(codigo)

    // tenta o mesmo código de novo
    await page.click('text=Novo cliente')
    await page.locator('.modal-form input').nth(0).fill(codigo)
    await page.locator('.modal-form input').nth(1).fill('Cliente Duplicado')
    await page.click('.modal-form button[type="submit"]')

    // o modal continua aberto com a mensagem de erro
    await expect(page.locator('.modal-overlay')).toHaveCount(1)
    await expect(page.locator('.erro-modal')).toBeVisible()
  })
})
