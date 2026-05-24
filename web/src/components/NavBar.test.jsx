import { describe, expect, test } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen } from '@testing-library/react'

import NavBar from './NavBar'

describe('NavBar', () => {
  test('renders primary navigation links', () => {
    render(<MemoryRouter><NavBar /></MemoryRouter>)

    expect(screen.getByRole('link', { name: '玩游戏' })).toHaveAttribute('href', '/play')
    expect(screen.getByRole('link', { name: '解游戏' })).toHaveAttribute('href', '/solve')
    expect(screen.getByRole('link', { name: '接入游戏' })).toHaveAttribute('href', '/contribute')
  })
})
