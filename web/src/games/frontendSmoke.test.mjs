import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import React from 'react'
import { renderToString } from 'react-dom/server'
import { createServer } from 'vite'

let vite
const h = React.createElement

before(async () => {
  vite = await createServer({
    appType: 'custom',
    logLevel: 'error',
    server: { hmr: false, middlewareMode: true },
  })
})

after(async () => {
  await vite?.close()
})

async function load(modulePath) {
  return vite.ssrLoadModule(modulePath)
}

test('solve list renders the supported game and navigation links without API data', async () => {
  const [{ MemoryRouter }, { default: SolveList }] = await Promise.all([
    load('/node_modules/react-router-dom/dist/index.mjs'),
    load('/src/pages/SolveList.jsx'),
  ])

  const html = renderToString(h(MemoryRouter, null, h(SolveList)))

  assert.match(html, /解游戏/)
  assert.match(html, /奶牛摆放谜题/)
  assert.match(html, /href="\/solve\/cow-puzzle\?tab=solver"/)
  assert.match(html, /自动求解/)
})

test('solve detail solver tab renders upload controls and sample buttons', async () => {
  const [{ MemoryRouter, Route, Routes }, { default: SolveDetail }] = await Promise.all([
    load('/node_modules/react-router-dom/dist/index.mjs'),
    load('/src/pages/SolveDetail.jsx'),
  ])

  const html = renderToString(
    h(
      MemoryRouter,
      { initialEntries: ['/solve/cow-puzzle?tab=solver'] },
      h(Routes, null, h(Route, { path: '/solve/:id', element: h(SolveDetail) })),
    ),
  )

  assert.match(html, /自动求解/)
  assert.match(html, /拖拽或点击上传游戏截图/)
  assert.match(html, /6 x 6 示例/)
  assert.match(html, /10 x 10 示例/)
  assert.match(html, /disabled=""/)
})

test('play detail start tab renders core game controls', async () => {
  const [{ MemoryRouter, Route, Routes }, { default: PlayDetail }] = await Promise.all([
    load('/node_modules/react-router-dom/dist/index.mjs'),
    load('/src/pages/PlayDetail.jsx'),
  ])

  const html = renderToString(
    h(
      MemoryRouter,
      { initialEntries: ['/play/cow-puzzle?tab=start'] },
      h(Routes, null, h(Route, { path: '/play/:id', element: h(PlayDetail) })),
    ),
  )

  assert.match(html, /重开/)
  assert.match(html, /演示解/)
  assert.match(html, /6<!-- -->x<!-- -->6/)
  assert.match(html, /8<!-- -->x<!-- -->8/)
  assert.match(html, /10<!-- -->x<!-- -->10/)
})
