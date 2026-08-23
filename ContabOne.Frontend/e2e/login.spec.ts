import { test, expect } from '@playwright/test'
import { CREDENCIAIS, login, prepararSeed } from './helpers'

test.describe('Login', () => {
  test('7.1 credenciais válidas entram, o dashboard carrega e o cookie de refresh sobrevive ao reload', async ({ page }) => {
    await prepararSeed()
    await login(page, CREDENCIAIS.admin.email, CREDENCIAIS.admin.senha)

    // Dashboard carrega os KPIs
    await expect(page.locator('.kpi-card').first()).toBeVisible()

    // O cookie de refresh (HttpOnly) sobrevive ao reload — o bootstrap restaura a sessão
    await page.reload()
    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.locator('.kpi-card').first()).toBeVisible()
  })

  test('7.2 credenciais inválidas mostram erro e permanecem na tela de login', async ({ page }) => {
    await prepararSeed()
    await page.goto('/login')
    await page.fill('#email', CREDENCIAIS.admin.email)
    await page.fill('#password', 'senha-errada')
    await page.click('.btn-login')

    await expect(page.locator('.login-error')).toBeVisible()
    await expect(page).toHaveURL(/\/login/)
  })
})
