import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  createEmptyMarks,
  evaluateBoard,
  getLevelBySize,
  levels,
  marksFromSolution,
  toggleMark,
  validateLevel,
} from './cowPuzzle.js'

test('built-in levels are structurally valid and their provided solution wins', () => {
  for (const level of levels) {
    assert.deepEqual(validateLevel(level), [])
    assert.equal(evaluateBoard(level, marksFromSolution(level.size, level.solution)).solved, true)
  }
})

test('size selection returns the matching level', () => {
  assert.equal(getLevelBySize(6).id, 'meadow-6')
  assert.equal(getLevelBySize(8).id, 'meadow-8')
  assert.equal(getLevelBySize(10).id, 'meadow-10')
})

test('one click toggles a mark without mutating the previous board', () => {
  const level = getLevelBySize(6)
  const empty = createEmptyMarks(level.size)
  const next = toggleMark(empty, 0, 0)

  assert.equal(empty[0][0], false)
  assert.equal(next[0][0], true)
  assert.equal(evaluateBoard(level, next).selected, 1)
})

test('illegal row and adjacency state reports conflicts', () => {
  const level = getLevelBySize(6)
  let marks = createEmptyMarks(level.size)
  marks = toggleMark(marks, 0, 0)
  marks = toggleMark(marks, 0, 1)

  const result = evaluateBoard(level, marks)
  assert.equal(result.solved, false)
  assert.ok(result.conflicts.has('0:0'))
  assert.ok(result.conflicts.has('0:1'))
})

test('complete solved state is recognized', () => {
  const level = getLevelBySize(8)
  const result = evaluateBoard(level, marksFromSolution(level.size, level.solution))

  assert.equal(result.complete, true)
  assert.equal(result.solved, true)
  assert.equal(result.remaining, 0)
})
