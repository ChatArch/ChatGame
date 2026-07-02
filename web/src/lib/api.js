export const fallbackGames = [
  {
    id: 'cow-puzzle',
    name: '奶牛摆放谜题',
    description: '色块区域约束 · 行列唯一 · 无相邻',
    status: 'supported',
    badge: '已支持',
  },
]

export const fallbackDocs = {
  rules: `# 玩法说明\n\n在彩色棋盘上放置奶牛，需要同时满足三条规则：\n\n1. 每种颜色区域恰好 1 头牛。\n2. 每行、每列恰好 1 头牛。\n3. 任意两头牛不能在上下左右或斜对角相邻。`,
  strategy: `# 游戏攻略\n\n优先观察格子最少的颜色区域，再结合行列唯一和相邻禁放规则排除候选位置。`,
}

export async function fetchJson(path, options = {}, timeoutMs = 8000) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(path, { ...options, signal: controller.signal })
    const text = await response.text()
    let data = null

    if (text) {
      try {
        data = JSON.parse(text)
      } catch {
        throw new Error('服务返回格式异常')
      }
    }

    if (!response.ok) {
      throw new Error(data?.detail || `请求失败：${response.status}`)
    }
    return data
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('请求超时，请确认服务是否正常运行', { cause: error })
    }
    throw error
  } finally {
    window.clearTimeout(timeout)
  }
}
