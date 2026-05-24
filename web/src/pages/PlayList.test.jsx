import { describe, expect, test } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen } from '@testing-library/react'

import PlayList from './PlayList'
import { installMockFetch, jsonResponse } from '../test/mockFetch'

describe('PlayList', () => {
  test('shows play entry without API response', () => {
    installMockFetch({
      '/api/games': async () => jsonResponse({ detail: 'down' }, { status: 500 }),
    })

    render(<MemoryRouter><PlayList /></MemoryRouter>)

    expect(screen.getByRole('heading', { name: '玩游戏' })).toBeInTheDocument()
    expect(screen.getByText('奶牛摆放谜题')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '开始游戏' })).toHaveAttribute(
      'href',
      '/play/cow-puzzle?tab=start',
    )
  })
})
