import { act, fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import userEvent from '@testing-library/user-event'

import PlayDetail from './PlayDetail'
import { installMockFetch, jsonResponse } from '../test/mockFetch'
import { getLevelBySize } from '../games/cowPuzzle'

function renderPlayDetail(route = '/play/cow-puzzle?tab=start') {
  installMockFetch()
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/play/:id" element={<PlayDetail />} />
      </Routes>
    </MemoryRouter>,
  )
}

function selectedCells() {
  return screen.getAllByRole('button').filter(button => button.getAttribute('aria-pressed') === 'true')
}

describe('PlayDetail', () => {
  test('renders game controls for the start tab', () => {
    renderPlayDetail()

    expect(screen.getByLabelText(/8 x 8 A 奶牛摆放棋盘/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '6x6' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '8x8' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '10x10' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '重开' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '演示解' })).toBeInTheDocument()
  })

  test('switches board sizes and rebuilds board state', async () => {
    const user = userEvent.setup()
    renderPlayDetail()

    await user.click(screen.getByRole('button', { name: '6x6' }))
    expect(screen.getByLabelText(/6 x 6 .*奶牛摆放棋盘/)).toBeInTheDocument()
    expect(selectedCells()).toHaveLength(0)

    await user.click(screen.getByRole('button', { name: '10x10' }))
    expect(screen.getByLabelText(/10 x 10 .*奶牛摆放棋盘/)).toBeInTheDocument()
    expect(selectedCells()).toHaveLength(0)
  })

  test('selects and unselects a board cell', async () => {
    const user = userEvent.setup()
    renderPlayDetail()

    const cell = screen.getByRole('button', { name: /第 1 行第 1 列/ })
    await user.click(cell)
    expect(cell).toHaveAttribute('aria-pressed', 'true')

    await user.click(cell)
    expect(cell).toHaveAttribute('aria-pressed', 'false')
  })

  test('clicking a cell highlights affected row, column, region and adjacent cells', async () => {
    const user = userEvent.setup()
    renderPlayDetail()

    const cell = (row, col) => screen.getByRole('button', {
      name: new RegExp(`第 ${row + 1} 行第 ${col + 1} 列`),
    })

    await user.click(cell(0, 0))

    expect(cell(0, 3).style.boxShadow).toContain('34, 92, 170')
    expect(cell(3, 0).style.boxShadow).toContain('37, 137, 103')
    expect(cell(4, 1).style.boxShadow).toContain('130, 92, 195')
    expect(cell(1, 1).style.boxShadow).toContain('216, 64, 50')
  })

  test('restart clears selected cells', async () => {
    const user = userEvent.setup()
    renderPlayDetail()

    const cell = screen.getByRole('button', { name: /第 1 行第 1 列/ })
    await user.click(cell)
    expect(selectedCells()).toHaveLength(1)

    await user.click(screen.getByRole('button', { name: '重开' }))
    expect(selectedCells()).toHaveLength(0)
  })

  test('demo solution appears step by step with fake timers', async () => {
    vi.useFakeTimers()
    renderPlayDetail()

    fireEvent.click(screen.getByRole('button', { name: '演示解' }))
    expect(selectedCells()).toHaveLength(0)

    await act(async () => {
      vi.advanceTimersByTime(0)
    })
    expect(selectedCells().length).toBeGreaterThan(0)
    expect(selectedCells().length).toBeLessThan(8)

    await act(async () => {
      vi.advanceTimersByTime(260 * 8)
    })
    expect(selectedCells()).toHaveLength(8)
  })

  test('falls back to built-in rules when docs API fails', () => {
    installMockFetch({
      '/api/games/cow-puzzle/docs': async () => jsonResponse({ detail: 'down' }, { status: 500 }),
    })
    render(
      <MemoryRouter initialEntries={['/play/cow-puzzle?tab=rules']}>
        <Routes>
          <Route path="/play/:id" element={<PlayDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText(/在彩色棋盘上放置奶牛/)).toBeInTheDocument()
    expect(screen.queryByText('加载中…')).not.toBeInTheDocument()
  })

  test('shows a visible solved celebration when the provided solution is played', async () => {
    const user = userEvent.setup()
    renderPlayDetail()

    const board = screen.getByLabelText(/8 x 8 A 奶牛摆放棋盘/)
    const level = getLevelBySize(8)

    for (const [row, col] of level.solution) {
      await user.click(within(board).getByRole('button', {
        name: `第 ${row + 1} 行第 ${col + 1} 列，区域 ${level.grid[row][col] + 1}`,
      }))
    }

    expect(screen.getByRole('status')).toHaveTextContent('🎉')
    expect(screen.getByText('恭喜过关！')).toBeInTheDocument()
  })
})
