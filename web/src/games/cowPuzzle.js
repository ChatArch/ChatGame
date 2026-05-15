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

export function getLevelBySize(size) {
  return levels.find(level => level.size === Number(size)) || levels[0]
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
  const regionCounts = new Map()
  const rowCounts = new Map()
  const colCounts = new Map()

  function addConflict(a, b) {
    conflicts.add(`${a.row}:${a.col}`)
    if (b) conflicts.add(`${b.row}:${b.col}`)
  }

  for (const cell of cells) {
    const region = level.grid[cell.row][cell.col]
    regionCounts.set(region, (regionCounts.get(region) || 0) + 1)
    rowCounts.set(cell.row, (rowCounts.get(cell.row) || 0) + 1)
    colCounts.set(cell.col, (colCounts.get(cell.col) || 0) + 1)
  }

  for (const cell of cells) {
    const region = level.grid[cell.row][cell.col]
    if (regionCounts.get(region) > 1 || rowCounts.get(cell.row) > 1 || colCounts.get(cell.col) > 1) {
      addConflict(cell)
    }
  }

  for (let i = 0; i < cells.length; i += 1) {
    for (let j = i + 1; j < cells.length; j += 1) {
      const a = cells[i]
      const b = cells[j]
      if (Math.abs(a.row - b.row) <= 1 && Math.abs(a.col - b.col) <= 1) {
        addConflict(a, b)
      }
    }
  }

  const complete = cells.length === size
  const solved =
    complete &&
    conflicts.size === 0 &&
    regionCounts.size === size &&
    rowCounts.size === size &&
    colCounts.size === size

  return {
    selected: cells.length,
    complete,
    solved,
    conflicts,
    regionCounts,
    rowCounts,
    colCounts,
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
  const colors = new Set(level.grid.flat())
  for (let color = 0; color < size; color += 1) {
    if (!colors.has(color)) errors.push(`missing color ${color}`)
  }
  const marks = marksFromSolution(size, level.solution)
  const result = evaluateBoard(level, marks)
  if (!result.solved) errors.push('provided solution is not solved')
  return errors
}
