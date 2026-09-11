import { describe, expect, test, vi } from 'vitest'

import { csrfHeaders, fetchAuthBootstrap, fetchJson, logoutAuth } from './api'

describe('fetchJson', () => {
  test('returns parsed JSON for successful responses', async () => {
    globalThis.fetch = vi.fn(async () => new Response(JSON.stringify({ ok: true }), { status: 200 }))

    await expect(fetchJson('/api/health')).resolves.toEqual({ ok: true })
  })

  test('uses backend detail for failed responses', async () => {
    globalThis.fetch = vi.fn(async () => new Response(JSON.stringify({ detail: '无解' }), { status: 422 }))

    await expect(fetchJson('/api/solve')).rejects.toThrow('无解')
  })

  test('reports invalid JSON responses', async () => {
    globalThis.fetch = vi.fn(async () => new Response('<html></html>', { status: 200 }))

    await expect(fetchJson('/api/bad')).rejects.toThrow('服务返回格式异常')
  })

  test('turns aborts into timeout errors', async () => {
    vi.useFakeTimers()
    globalThis.fetch = vi.fn((_path, { signal }) => new Promise((_resolve, reject) => {
      signal.addEventListener('abort', () => {
        reject(new DOMException('aborted', 'AbortError'))
      })
    }))

    const request = expect(fetchJson('/api/slow', {}, 10))
      .rejects.toThrow('请求超时，请确认服务是否正常运行')
    await vi.advanceTimersByTimeAsync(10)

    await request
  })

  test('auth helpers use same-origin credentials and csrf header', async () => {
    const calls = []
    globalThis.fetch = vi.fn(async (path, options = {}) => {
      calls.push({ path, options })
      return new Response(JSON.stringify({ ok: true }), { status: 200 })
    })

    await fetchAuthBootstrap()
    await logoutAuth({ csrf_token: 'csrf-token' })

    expect(calls[0]).toMatchObject({ path: '/api/auth/bootstrap', options: { credentials: 'same-origin' } })
    expect(calls[1].path).toBe('/api/auth/logout')
    expect(calls[1].options.method).toBe('POST')
    expect(calls[1].options.credentials).toBe('same-origin')
    expect(calls[1].options.headers).toEqual({ 'x-csrf-token': 'csrf-token' })
    expect(csrfHeaders(null)).toEqual({})
  })
})
