import { describe, expect, test, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import NavBar from './NavBar'
import { installMockFetch, jsonResponse } from '../test/mockFetch'

describe('NavBar', () => {
  test('renders primary navigation links and guest identity without dead login', async () => {
    installMockFetch({
      '/api/auth/bootstrap': () => jsonResponse({
        auth_available: false,
        identity: 'guest',
        authenticated: false,
        login_url: null,
      }),
    })
    render(<MemoryRouter><NavBar /></MemoryRouter>)

    expect(screen.getByRole('link', { name: '玩游戏' })).toHaveAttribute('href', '/play')
    expect(screen.getByRole('link', { name: '解游戏' })).toHaveAttribute('href', '/solve')
    expect(screen.getByRole('link', { name: '接入游戏' })).toHaveAttribute('href', '/contribute')
    await screen.findByText('访客')
    expect(screen.queryByRole('link', { name: '登录' })).not.toBeInTheDocument()
  })

  test('shows configured login entry and logs out with csrf', async () => {
    const calls = installMockFetch({
      '/api/auth/bootstrap': () => jsonResponse({
        auth_available: true,
        identity: 'authenticated',
        authenticated: true,
        csrf_token: 'csrf-token',
        login_url: '/login',
        logout_url: '/api/auth/logout',
        user: { user_id: 'acct-solver', display_name: 'Puzzle Solver', role: 'user' },
      }),
      '/api/auth/logout': () => jsonResponse({ authenticated: false }),
    })

    render(<MemoryRouter><NavBar /></MemoryRouter>)

    await screen.findByText('已登录：Puzzle Solver')
    await userEvent.click(screen.getByRole('button', { name: '退出' }))

    await waitFor(() => expect(screen.getByText('访客')).toBeInTheDocument())
    const logout = calls.find((call) => call.url === '/api/auth/logout')
    expect(logout.options.method).toBe('POST')
    expect(logout.options.credentials).toBe('same-origin')
    expect(logout.options.headers).toEqual({ 'x-csrf-token': 'csrf-token' })
  })

  test('configured guest login preserves current route and can cancel navigation', async () => {
    installMockFetch({
      '/api/auth/bootstrap': () => jsonResponse({
        auth_available: true,
        identity: 'guest',
        authenticated: false,
        csrf_token: null,
        login_url: '/login',
        user: null,
      }),
    })
    window.confirm = vi.fn(() => false)

    render(
      <MemoryRouter initialEntries={['/solve/cow-puzzle?tab=solver']}>
        <Routes>
          <Route path="*" element={<NavBar />} />
        </Routes>
      </MemoryRouter>,
    )

    const login = await screen.findByRole('link', { name: '登录' })
    expect(login).toHaveAttribute('href', '/login?next=%2Fsolve%2Fcow-puzzle%3Ftab%3Dsolver')
    await userEvent.click(login)
    expect(window.confirm).toHaveBeenCalled()
  })
})
