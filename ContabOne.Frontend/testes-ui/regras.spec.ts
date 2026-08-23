import { test, expect, type Page } from '@playwright/test'

/**
 * Verificação da mudança `visualizar-editar-regras` (tasks 5.1–5.5).
 *
 * Requer o stack rodando:
 *   - API .NET em http://localhost:5139 (com seed dev: admin@nfse.local / Admin123!)
 *   - Vite dev server em http://localhost:5173
 */

const BASE = 'http://localhost:5173'

async function login(page: Page, email = 'admin@nfse.local', senha = 'Admin123!') {
  await page.goto(`${BASE}/login`)
  await page.fill('#email', email)
  await page.fill('#password', senha)
  await page.click('.btn-login')
  await page.waitForURL(/\/dashboard/)
}

async function irParaRegras(page: Page) {
  await page.goto(`${BASE}/admin/regras`)
  await page.waitForSelector('.regra-row')
}

test.describe('Tela de regras — visualizar e editar', () => {
  test.use({ permissions: ['clipboard-read', 'clipboard-write'] })

  test('5.1 — expande linha do histórico e mostra JSON formatado', async ({ page }) => {
    await login(page)
    await irParaRegras(page)

    const row = page.locator('.regra-row').first()
    await row.click()

    const pre = page.locator('.json-pre')
    await expect(pre).toBeVisible()
    const texto = (await pre.innerText()).trim()
    // conteúdo JSON visível, formatado em múltiplas linhas
    expect(texto).toContain('"portal"')
    expect(texto).toContain('"urlLogin"')
    expect(texto.split('\n').length).toBeGreaterThan(5)

    // recolhe ao clicar de novo
    await row.click()
    await expect(pre).not.toBeVisible()
  })

  test('5.2 — Copiar JSON copia para o clipboard e mostra "Copiado!"', async ({ page }) => {
    await login(page)
    await irParaRegras(page)

    const row = page.locator('.regra-row').first()
    await row.click()
    const pre = page.locator('.json-pre')
    await expect(pre).toBeVisible()
    const textoFormatado = (await pre.innerText()).trim()

    await page.locator('.detalhe-actions button', { hasText: 'Copiar JSON' }).click()
    await expect(page.locator('.copiado-msg')).toBeVisible()

    const clipboard = await page.evaluate(() => navigator.clipboard.readText())
    expect(JSON.parse(clipboard)).toEqual(JSON.parse(textoFormatado))
  })

  test('5.3 — Carregar no editor e publicar nova versão', async ({ page }) => {
    await login(page)
    await irParaRegras(page)

    const versaoAtual = Number.parseInt(
      (await page.locator('.regra-row').first().locator('.col-versao').innerText()).replace(/[^\d]/g, ''),
      10,
    )

    const row = page.locator('.regra-row').first()
    await row.click()
    const pre = page.locator('.json-pre')
    await expect(pre).toBeVisible()
    const textoFormatado = (await pre.innerText()).trim()

    await page.locator('.detalhe-actions button', { hasText: 'Carregar no editor' }).click()

    // O editor já vem pré-preenchido com a versão ativa (RegrasView.carregar),
    // então carregar por cima SEMPRE pede confirmação — o mesmo modal que o
    // 5.4 exercita. Sem confirmar aqui, o overlay fica aberto e intercepta os
    // cliques seguintes.
    const confirmacaoCarregar = page.locator('.modal-card')
    await expect(confirmacaoCarregar).toBeVisible()
    await confirmacaoCarregar.locator('.btn-danger').click()
    await expect(confirmacaoCarregar).toHaveCount(0)

    // JSON carregado no editor — o design especifica que o editor recebe a
    // string crua da API (não formatada); comparar por valor parseado.
    const textarea = page.locator('.json-editor')
    await expect.poll(() => textarea.inputValue()).not.toBe('')
    expect(JSON.parse((await textarea.inputValue()).trim())).toEqual(JSON.parse(textoFormatado))

    // edita um campo e publica (independe do valor atual do maxDiasFiltro —
    // cada execução do teste publica uma versão nova, o valor muda)
    const alterado = textoFormatado.replace(/"maxDiasFiltro": \d+/, '"maxDiasFiltro": 45')
    expect(alterado).not.toBe(textoFormatado)
    await textarea.fill(alterado)
    await page.locator('.editor-actions .btn-primary').click()

    // modal de confirmação de publicação
    const modal = page.locator('.modal-card')
    await expect(modal).toBeVisible()
    await modal.locator('.btn-danger').click()

    // nova versão aparece no histórico
    const nova = page.locator('.regra-row', { hasText: `v${versaoAtual + 1}` })
    await expect(nova).toBeVisible()
    await expect(page.locator('.regra-row').first()).toContainText(`v${versaoAtual + 1}`)
  })

  test('5.4 — confirmação antes de sobrescrever editor com texto', async ({ page }) => {
    await login(page)
    await irParaRegras(page)

    // digita algo no editor
    const textarea = page.locator('.json-editor')
    await textarea.fill('{ "rascunho": "nao publicar" }')

    // tenta carregar uma versão no editor
    const row = page.locator('.regra-row').first()
    await row.click()
    await expect(page.locator('.json-pre')).toBeVisible()
    await page.locator('.detalhe-actions button', { hasText: 'Carregar no editor' }).click()

    // modal de confirmação aparece
    const modal = page.locator('.modal-card')
    await expect(modal).toBeVisible()
    await expect(modal).toContainText('substituir')

    // cancelar mantém o rascunho
    await modal.locator('.btn-secondary').click()
    await expect(textarea).toHaveValue('{ "rascunho": "nao publicar" }')

    // confirmar substitui
    await page.locator('.detalhe-actions button', { hasText: 'Carregar no editor' }).click()
    await expect(modal).toBeVisible()
    await modal.locator('.btn-danger').click()
    await expect(textarea).not.toHaveValue('{ "rascunho": "nao publicar" }')
    expect((await textarea.inputValue()).trim().startsWith('{')).toBe(true)
  })

  test('5.5 — papel não-PlatformAdmin é redirecionado para /dashboard', async ({ page }) => {
    await login(page, 'escritorio@nfse.local', 'Admin123!')

    await page.goto(`${BASE}/admin/regras`)
    await page.waitForURL(/\/dashboard/)
    await expect(page.locator('.regra-row')).toHaveCount(0)
  })
})
