import levelPack from './cowPuzzleLevels.json' with { type: 'json' }

export const REGION_COLORS = [
  '#68b7ff',
  '#f59ac2',
  '#ffd166',
  '#56c6a9',
  '#a0d468',
  '#ff8a5c',
  '#9b8cff',
  '#63d4e8',
  '#f0a85b',
  '#8dc5ff',
]

export const levels = levelPack.levels

export function getLevelsBySize(size) {
  return levels.filter(level => level.size === Number(size) && level.verified && level.unique)
}

export function getLevelBySize(size) {
  return getLevelsBySize(size)[0] || levels[0]
}

export function getRandomLevelBySize(size, currentId = null) {
  const pool = getLevelsBySize(size)
  if (pool.length === 0) return levels[0]
  const candidates = pool.length > 1 ? pool.filter(level => level.id !== currentId) : pool
  return candidates[Math.floor(Math.random() * candidates.length)]
}

export function createEmptyMarks(size) {
  return Array.from({ length: size }, () => Array(size).fill(false))
}

export function toggleMark(marks, row, col) {
  return marks.map((line, r) =>
    line.map((value, c) => (r === row && c === col ? !value : value)),
  )
}

export function marksFromSolution(size, solution) {
  const marks = createEmptyMarks(size)
  for (const [row, col] of solution) {
    marks[row][col] = true
  }
  return marks
}

export function selectedCells(marks) {
  const cells = []
  marks.forEach((line, row) => {
    line.forEach((marked, col) => {
      if (marked) cells.push({ row, col })
    })
  })
  return cells
}

export function evaluateBoard(level, marks) {
  const size = level.size
  const cells = selectedCells(marks)
  const conflicts = new Set()
  const violations = []
  const regionCells = new Map()
  const rowCells = new Map()
  const colCells = new Map()

  function addConflict(a, b) {
    conflicts.add(`${a.row}:${a.col}`)
    if (b) conflicts.add(`${b.row}:${b.col}`)
  }

  for (const cell of cells) {
    const region = level.grid[cell.row][cell.col]
    if (!regionCells.has(region)) regionCells.set(region, [])
    if (!rowCells.has(cell.row)) rowCells.set(cell.row, [])
    if (!colCells.has(cell.col)) colCells.set(cell.col, [])
    regionCells.get(region).push(cell)
    rowCells.get(cell.row).push(cell)
    colCells.get(cell.col).push(cell)
  }

  for (const [region, group] of regionCells.entries()) {
    if (group.length > 1) {
      group.forEach(cell => addConflict(cell))
      violations.push({
        rule: 'region',
        cells: group.map(cell => `${cell.row}:${cell.col}`),
        message: `区域 ${region + 1} 已放置 ${group.length} 头`,
      })
    }
  }

  for (const [row, group] of rowCells.entries()) {
    if (group.length > 1) {
      group.forEach(cell => addConflict(cell))
      violations.push({
        rule: 'row-column',
        cells: group.map(cell => `${cell.row}:${cell.col}`),
        message: `第 ${row + 1} 行已放置 ${group.length} 头`,
      })
    }
  }

  for (const [col, group] of colCells.entries()) {
    if (group.length > 1) {
      group.forEach(cell => addConflict(cell))
      violations.push({
        rule: 'row-column',
        cells: group.map(cell => `${cell.row}:${cell.col}`),
        message: `第 ${col + 1} 列已放置 ${group.length} 头`,
      })
    }
  }

  for (let i = 0; i < cells.length; i += 1) {
    for (let j = i + 1; j < cells.length; j += 1) {
      const a = cells[i]
      const b = cells[j]
      if (Math.abs(a.row - b.row) <= 1 && Math.abs(a.col - b.col) <= 1) {
        addConflict(a, b)
        violations.push({
          rule: 'adjacent',
          cells: [`${a.row}:${a.col}`, `${b.row}:${b.col}`],
          message: `第 ${a.row + 1} 行第 ${a.col + 1} 列与第 ${b.row + 1} 行第 ${b.col + 1} 列相邻`,
        })
      }
    }
  }

  const complete = cells.length === size
  const solved =
    complete &&
    conflicts.size === 0 &&
    regionCells.size === size &&
    rowCells.size === size &&
    colCells.size === size

  return {
    selected: cells.length,
    complete,
    solved,
    conflicts,
    violations,
    regionCounts: new Map([...regionCells].map(([key, value]) => [key, value.length])),
    rowCounts: new Map([...rowCells].map(([key, value]) => [key, value.length])),
    colCounts: new Map([...colCells].map(([key, value]) => [key, value.length])),
    remaining: Math.max(0, size - cells.length),
  }
}

export function validateLevel(level) {
  const size = level.size
  const errors = []
  if (!Array.isArray(level.grid) || level.grid.length !== size) {
    errors.push('grid size mismatch')
  }
  if (!Array.isArray(level.solution) || level.solution.length !== size) {
    errors.push('solution size mismatch')
  }
  if (!level.verified) errors.push('level is not marked verified')
  if (!level.unique) errors.push('level is not marked unique')
  const colors = new Set(level.grid.flat())
  for (let color = 0; color < size; color += 1) {
    if (!colors.has(color)) errors.push(`missing color ${color}`)
  }
  const marks = marksFromSolution(size, level.solution)
  const result = evaluateBoard(level, marks)
  if (!result.solved) errors.push('provided solution is not solved')
  return errors
}
