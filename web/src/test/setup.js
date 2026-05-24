import '@testing-library/jest-dom/vitest'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
  vi.useRealTimers()
})

if (!URL.createObjectURL) {
  URL.createObjectURL = vi.fn(() => 'blob:chatgame-preview')
}

if (!URL.revokeObjectURL) {
  URL.revokeObjectURL = vi.fn()
}
