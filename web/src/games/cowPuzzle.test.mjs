import { describe, expect, test } from 'vitest'

import {
  createEmptyMarks,
  evaluateBoard,
  getLevelBySize,
  getLevelsBySize,
  getRandomLevelBySize,
  levels,
  marksFromSolution,
  toggleMark,
  validateLevel,
} from './cowPuzzle.js'

describe('cowPuzzle rules', () => {
  test('built-in levels are structurally valid and their provided solution wins', () => {
    for (const level of levels) {
      expect(validateLevel(level)).toEqual([])
      expect(evaluateBoard(level, marksFromSolution(level.size, level.solution)).solved).toBe(true)
    }
  })

  test('size selection returns the matching level', () => {
    expect(getLevelBySize(6).id).toBe('meadow-6-a')
    expect(getLevelBySize(8).id).toBe('meadow-8-a')
    expect(getLevelBySize(10).id).toBe('meadow-10-a')
    expect(getLevelsBySize(8)).toHaveLength(3)
  })

  test('random level selection avoids the current level when possible', () => {
    const next = getRandomLevelBySize(6, 'meadow-6-a')

    expect(next.size).toBe(6)
    expect(next.id).not.toBe('meadow-6-a')
  })

  test('one click toggles a mark without mutating the previous board', () => {
    const level = getLevelBySize(6)
    const empty = createEmptyMarks(level.size)
    const next = toggleMark(empty, 0, 0)

    expect(empty[0][0]).toBe(false)
    expect(next[0][0]).toBe(true)
    expect(evaluateBoard(level, next).selected).toBe(1)
  })

  test('illegal row and adjacency state reports conflicts', () => {
    const level = getLevelBySize(6)
    let marks = createEmptyMarks(level.size)
    marks = toggleMark(marks, 0, 0)
    marks = toggleMark(marks, 0, 1)

    const result = evaluateBoard(level, marks)
    expect(result.solved).toBe(false)
    expect(result.conflicts.has('0:0')).toBe(true)
    expect(result.conflicts.has('0:1')).toBe(true)
    expect(result.violations.some(violation => violation.rule === 'row-column')).toBe(true)
    expect(result.violations.some(violation => violation.rule === 'adjacent')).toBe(true)
  })

  test('complete solved state is recognized', () => {
    const level = getLevelBySize(8)
    const result = evaluateBoard(level, marksFromSolution(level.size, level.solution))

    expect(result.complete).toBe(true)
    expect(result.solved).toBe(true)
    expect(result.remaining).toBe(0)
  })
})
