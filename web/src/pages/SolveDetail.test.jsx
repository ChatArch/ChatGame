import { describe, expect, test } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import SolveDetail from './SolveDetail'
import {
  installMockFetch,
  jsonResponse,
  multipleSolveResult,
  uniqueSolveResult,
} from '../test/mockFetch'

function renderSolveDetail(route = '/solve/cow-puzzle?tab=solver') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/solve/:id" element={<SolveDetail />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('SolveDetail', () => {
  test('renders solver controls and enables solving after selecting a sample', async () => {
    const user = userEvent.setup()
    installMockFetch()
    renderSolveDetail()

    const solveButton = screen.getByRole('button', { name: '求解' })
    expect(solveButton).toBeDisabled()

    const sample = screen.getByRole('button', { name: /10 x 10 示例/ })
    const classBefore = sample.className
    await user.click(sample)

    await waitFor(() => expect(screen.getByAltText('预览')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: '求解' })).toBeEnabled()
    expect(sample.className).not.toBe(classBefore)
  })

  test('shows unique solution result from solve API', async () => {
    const user = userEvent.setup()
    const calls = installMockFetch({
      '/api/solve': async () => jsonResponse(uniqueSolveResult),
    })
    renderSolveDetail()

    await user.click(screen.getByRole('button', { name: /6 x 6 示例/ }))
    await user.click(await screen.findByRole('button', { name: '求解' }))

    expect(await screen.findByText('唯一解')).toBeInTheDocument()
    expect(screen.getByText('已找到唯一解。')).toBeInTheDocument()
    expect(screen.getByAltText('标注结果')).toHaveAttribute('src', expect.stringContaining('data:image/png;base64,'))
    expect(calls.some(call => call.url === '/api/solve')).toBe(true)
  })

  test('shows multiple-solution warning from solve API', async () => {
    const user = userEvent.setup()
    installMockFetch({
      '/api/solve': async () => jsonResponse(multipleSolveResult),
    })
    renderSolveDetail()

    await user.click(screen.getByRole('button', { name: /8 x 8 示例/ }))
    await user.click(await screen.findByRole('button', { name: '求解' }))

    expect(await screen.findByText('多解提示')).toBeInTheDocument()
    expect(screen.getByText(/多个合法解/)).toBeInTheDocument()
  })

  test('shows solve errors and restores the solve button', async () => {
    const user = userEvent.setup()
    installMockFetch({
      '/api/solve': async () => jsonResponse({ detail: '无解，请检查截图是否清晰' }, { status: 422 }),
    })
    renderSolveDetail()

    await user.click(screen.getByRole('button', { name: /6 x 6 示例/ }))
    const solveButton = await screen.findByRole('button', { name: '求解' })
    await user.click(solveButton)

    expect(await screen.findByText('无解，请检查截图是否清晰')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '求解' })).toBeEnabled()
  })

  test('shows timeout errors and restores the solve button', async () => {
    const user = userEvent.setup()
    installMockFetch({
      '/api/solve': async () => {
        throw new Error('请求超时，请确认服务是否正常运行')
      },
    })
    renderSolveDetail()

    await user.click(screen.getByRole('button', { name: /6 x 6 示例/ }))
    await user.click(await screen.findByRole('button', { name: '求解' }))

    expect(await screen.findByText('请求超时，请确认服务是否正常运行')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '求解' })).toBeEnabled()
  })

  test('shows sample load errors without breaking upload controls', async () => {
    const user = userEvent.setup()
    installMockFetch({
      '/examples/cow-puzzle-10.png': async () => jsonResponse({ detail: 'missing' }, { status: 404 }),
    })
    renderSolveDetail()

    await user.click(screen.getByRole('button', { name: /10 x 10 示例/ }))

    expect(await screen.findByText('示例图加载失败')).toBeInTheDocument()
    expect(screen.getByText('拖拽或点击上传游戏截图')).toBeInTheDocument()
  })

  test('uploads a local image fixture and displays a result', async () => {
    const user = userEvent.setup()
    installMockFetch({
      '/api/solve': async () => jsonResponse(uniqueSolveResult),
    })
    const { container } = renderSolveDetail()

    const input = container.querySelector('input[type="file"]')
    const file = new File(['fake'], 'board.png', { type: 'image/png' })
    await user.upload(input, file)

    await waitFor(() => expect(screen.getByAltText('预览')).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: '求解' }))

    expect(await screen.findByText('唯一解')).toBeInTheDocument()
  })

  test('falls back to built-in docs when docs API fails', () => {
    installMockFetch({
      '/api/games/cow-puzzle/docs': async () => jsonResponse({ detail: 'down' }, { status: 500 }),
    })
    renderSolveDetail('/solve/cow-puzzle?tab=strategy')

    expect(screen.getByRole('heading', { name: '玩法与攻略' })).toBeInTheDocument()
    expect(screen.getByText(/在彩色棋盘上放置奶牛/)).toBeInTheDocument()
    expect(screen.queryByText('加载中…')).not.toBeInTheDocument()
  })
})
