import { describe, expect, test } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen } from '@testing-library/react'

import SolveList from './SolveList'
import { installMockFetch, jsonResponse } from '../test/mockFetch'

describe('SolveList', () => {
  test('shows solve entry without API response', () => {
    installMockFetch({
      '/api/games': async () => jsonResponse({ detail: 'down' }, { status: 500 }),
    })

    render(<MemoryRouter><SolveList /></MemoryRouter>)

    expect(screen.getByRole('heading', { name: '解游戏' })).toBeInTheDocument()
    expect(screen.getByText('奶牛摆放谜题')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '自动求解' })).toHaveAttribute(
      'href',
      '/solve/cow-puzzle?tab=solver',
    )
  })
})
