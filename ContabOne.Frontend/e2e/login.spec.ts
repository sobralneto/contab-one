import { test, expect } from '@playwright/test'
import { CREDENCIAIS, login, prepararSeed } from './helpers'

test.describe('Login', () => {
  test('7.1 credenciais válidas entram no hub, a visão geral do NFS-e carrega e o cookie de refresh sobrevive ao reload', async ({ page }) => {
    await prepararSeed()
    await login(page, CREDENCIAIS.admin.email, CREDENCIAIS.admin.senha)

    // Login pousa no hub — o card da ferramenta é o que confirma que o
    // catálogo da sessão carregou.
    await expect(page.locator('.ferramenta-card', { hasText: 'NFS-e' }).first()).toBeVisible()

    await page.goto('/f/nfse')
    await expect(page.locator('.kpi-card').first()).toBeVisible()

    // O cookie de refresh (HttpOnly) sobrevive ao reload — o bootstrap restaura a sessão
    await page.reload()
    await expect(page).toHaveURL(/\/f\/nfse/)
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

  test('7.7 endereços anteriores (de quando só existia o NFS-e) continuam chegando na tela certa', async ({ page }) => {
    await prepararSeed()
    await login(page, CREDENCIAIS.admin.email, CREDENCIAIS.admin.senha)

    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/f\/nfse$/)
    await expect(page.locator('.kpi-card').first()).toBeVisible()

    // /execucoes segue redirect pro NFS-e (era a única ferramenta quando o
    // endereço nasceu). /clientes e /agentes NÃO são redirect: nunca
    // dependeram de qual ferramenta está na URL, então continuam sendo o
    // próprio endereço canônico.
    await page.goto('/execucoes')
    await expect(page).toHaveURL(/\/f\/nfse\/execucoes$/)
  })
})
