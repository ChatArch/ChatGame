import { vi } from 'vitest'

export const uniqueSolveResult = {
  n: 6,
  solution_status: 'unique',
  solution_count: 1,
  solution_count_limit: 2,
  message: '已找到唯一解。',
  steps: [{ step: 1, row: 0, col: 0, color_id: 0, color_name: '蓝' }],
  grid: [[0]],
  grid_bbox: [0, 0, 10, 10],
  image_width: 100,
  image_height: 100,
  annotated_image: 'iVBORw0KGgo=',
  elapsed_ms: 12,
}

export const multipleSolveResult = {
  ...uniqueSolveResult,
  solution_status: 'multiple',
  solution_count: 2,
  message: '当前截图存在多个合法解，已先给出其中一个；建议确认关卡是否应为唯一解。',
}

export function jsonResponse(body, init = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
}

export function imageResponse() {
  return new Response(new Uint8Array([137, 80, 78, 71]), {
    status: 200,
    headers: { 'Content-Type': 'image/png' },
  })
}

export function installMockFetch(overrides = {}) {
  const calls = []
  globalThis.fetch = vi.fn(async (input, options = {}) => {
    const url = String(input)
    calls.push({ url, options })

    const override = overrides[url] || overrides.default
    if (override) {
      return override(input, options)
    }

    if (url === '/api/games') {
      return jsonResponse({
        games: [
          {
            id: 'cow-puzzle',
            name: '奶牛摆放谜题',
            description: '色块区域约束 · 行列唯一 · 无相邻',
          },
        ],
      })
    }

    if (url === '/api/games/cow-puzzle/docs') {
      return jsonResponse({ rules: '# 远端玩法', strategy: '# 远端攻略' })
    }

    if (url.startsWith('/examples/')) {
      return imageResponse()
    }

    if (url === '/api/solve') {
      return jsonResponse(uniqueSolveResult)
    }

    return jsonResponse({})
  })
  return calls
}
