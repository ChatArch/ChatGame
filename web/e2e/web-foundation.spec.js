import { expect, test } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const uploadFixture = path.resolve(__dirname, '../../src/chatgame/web_static/examples/cow-puzzle-6.png')

function watchConsole(page) {
  const errors = []
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text())
  })
  page.on('pageerror', error => errors.push(error.message))
  return errors
}

test('navigation pages render without browser console errors', async ({ page }) => {
  const errors = watchConsole(page)

  await page.goto('/')
  await expect(page).toHaveURL(/\/play$/)
  await expect(page.getByRole('heading', { name: '玩游戏' })).toBeVisible()

  await page.getByRole('link', { name: '解游戏' }).click()
  await expect(page).toHaveURL(/\/solve$/)
  await expect(page.getByRole('heading', { name: '解游戏' })).toBeVisible()
  await expect(page.getByRole('link', { name: '自动求解' })).toHaveAttribute('href', '/solve/cow-puzzle?tab=solver')

  await page.getByRole('link', { name: '接入游戏' }).click()
  await expect(page).toHaveURL(/\/contribute$/)
  await expect(page.getByRole('heading', { name: '接入新游戏向导' })).toBeVisible()

  expect(errors).toEqual([])
})

test('play page supports fixed sizes, click effects and step-by-step demo solution', async ({ page }) => {
  const errors = watchConsole(page)

  await page.goto('/play/cow-puzzle?tab=start')
  await expect(page.getByLabel(/8 x 8 .*奶牛摆放棋盘/)).toBeVisible()

  const firstCell = page.getByRole('button', { name: /第 1 行第 1 列/ })
  await firstCell.click()
  await expect(firstCell).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('button', { name: /第 1 行第 4 列/ })).toHaveAttribute('style', /34, 92, 170/)
  await expect(page.getByRole('button', { name: /第 4 行第 1 列/ })).toHaveAttribute('style', /37, 137, 103/)
  await expect(page.getByRole('button', { name: /第 5 行第 2 列/ })).toHaveAttribute('style', /130, 92, 195/)
  await expect(page.getByRole('button', { name: /第 2 行第 2 列/ })).toHaveAttribute('style', /216, 64, 50/)

  await page.getByRole('button', { name: '6x6' }).click()
  await expect(page.getByLabel(/6 x 6 .*奶牛摆放棋盘/)).toBeVisible()

  await page.getByRole('button', { name: '10x10' }).click()
  await expect(page.getByLabel(/10 x 10 .*奶牛摆放棋盘/)).toBeVisible()

  await page.getByRole('button', { name: '8x8' }).click()
  await expect(page.getByLabel(/8 x 8 .*奶牛摆放棋盘/)).toBeVisible()

  await page.getByRole('button', { name: '6x6' }).click()
  await page.getByRole('button', { name: '演示解' }).click()
  await page.waitForTimeout(120)
  const earlyCount = await page.locator('[aria-pressed="true"]').count()
  expect(earlyCount).toBeGreaterThan(0)
  expect(earlyCount).toBeLessThan(6)
  await expect(page.locator('[aria-pressed="true"]')).toHaveCount(6, { timeout: 4_000 })
  await expect(page.getByRole('status')).toContainText('恭喜过关')

  expect(errors).toEqual([])
})

test('solver solves the packaged 10x10 sample and displays an annotated image', async ({ page }) => {
  const errors = watchConsole(page)

  await page.goto('/solve/cow-puzzle?tab=solver')
  await page.getByRole('button', { name: /10 x 10 示例/ }).click()
  await expect(page.getByAltText('预览')).toBeVisible()
  await expect(page.getByRole('button', { name: '求解', exact: true })).toBeEnabled()

  await page.getByRole('button', { name: '求解', exact: true }).click()
  await expect(page.locator('strong').filter({ hasText: /^(唯一解|多解提示)$/ })).toBeVisible({ timeout: 90_000 })
  await expect(page.getByAltText('标注结果')).toHaveAttribute('src', /^data:image\/png;base64,/)

  expect(errors).toEqual([])
})

test('solver upload path finishes with a result or explicit error instead of hanging', async ({ page }) => {
  const errors = watchConsole(page)

  await page.goto('/solve/cow-puzzle?tab=solver')
  await page.locator('input[type="file"]').setInputFiles(uploadFixture)
  await expect(page.getByAltText('预览')).toBeVisible()

  await page.getByRole('button', { name: '求解', exact: true }).click()
  await expect(page.getByText(/唯一解|多解提示|无解|搜索超限|无法读取|识别/)).toBeVisible({ timeout: 90_000 })
  await expect(page.getByRole('button', { name: '求解', exact: true })).toBeEnabled()

  expect(errors).toEqual([])
})

test('docs API failure falls back to built-in strategy content', async ({ page }) => {
  const errors = watchConsole(page)
  await page.route('**/api/games/cow-puzzle/docs', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: 'not json' })
  })

  await page.goto('/solve/cow-puzzle?tab=strategy')
  await expect(page.getByRole('heading', { name: '玩法与攻略' })).toBeVisible()
  await expect(page.getByText(/在彩色棋盘上放置奶牛/)).toBeVisible()
  await expect(page.getByText('加载中…')).toHaveCount(0)

  expect(errors).toEqual([])
})
