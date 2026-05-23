import { useEffect, useRef, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import styles from './LibraryDetail.module.css'
import gameStyles from './PlayGame.module.css'
import {
  REGION_COLORS,
  createEmptyMarks,
  evaluateBoard,
  getLevelBySize,
  getRandomLevelBySize,
  toggleMark,
} from '../games/cowPuzzle'
import { fallbackDocs, fetchJson } from '../lib/api'

const SIZES = [6, 8, 10]

const RULES = [
  ['region', '每个颜色区域恰好 1 头'],
  ['row-column', '每行每列恰好 1 头'],
  ['adjacent', '任意两头不能相邻'],
]

export default function PlayDetail() {
  const { id } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'rules'
  const [docs, setDocs] = useState(fallbackDocs)
  const [level, setLevel] = useState(() => getLevelBySize(8))
  const [marks, setMarks] = useState(() => createEmptyMarks(8))
  const demoTimersRef = useRef([])

  useEffect(() => {
    let mounted = true
    fetchJson(`/api/games/${id}/docs`)
      .then(d => { if (mounted) setDocs({ ...fallbackDocs, ...d }) })
      .catch(() => {})
    return () => { mounted = false }
  }, [id])

  useEffect(() => () => {
    demoTimersRef.current.forEach(clearTimeout)
    demoTimersRef.current = []
  }, [])

  const result = evaluateBoard(level, marks)

  function stopDemo() {
    demoTimersRef.current.forEach(clearTimeout)
    demoTimersRef.current = []
  }

  function switchSize(size) {
    stopDemo()
    const nextLevel = getRandomLevelBySize(size)
    setLevel(nextLevel)
    setMarks(createEmptyMarks(nextLevel.size))
  }

  function restart() {
    stopDemo()
    const nextLevel = getRandomLevelBySize(level.size, level.id)
    setLevel(nextLevel)
    setMarks(createEmptyMarks(nextLevel.size))
  }

  function showSolution() {
    stopDemo()
    setMarks(createEmptyMarks(level.size))

    level.solution.forEach(([row, col], index) => {
      const timer = window.setTimeout(() => {
        setMarks(current => toggleMark(current, row, col))
      }, index * 260)
      demoTimersRef.current.push(timer)
    })
  }

  function onCellClick(row, col) {
    stopDemo()
    setMarks(current => toggleMark(current, row, col))
  }

  function effectStyle(influence) {
    if (!influence || influence.total === 0) return {}

    const shadows = []
    const totalIntensity = Math.min(influence.total, 12)
    const sinkDepth = Math.min(14, totalIntensity * 1.35)
    const borderWidth = Math.min(5, 1 + totalIntensity * 0.22)
    const regionAlpha = Math.min(0.16 + influence.region * 0.08, 0.52)
    const columnAlpha = Math.min(0.16 + influence.column * 0.08, 0.56)
    const rowAlpha = Math.min(0.16 + influence.row * 0.08, 0.56)
    const adjacentAlpha = Math.min(0.18 + influence.adjacent * 0.1, 0.62)
    const borderAlpha = Math.min(0.16 + totalIntensity * 0.045, 0.46)
    let zIndex = influence.origin > 0 ? 3 : 2
    let filter = `brightness(${Math.max(0.72, 0.98 - totalIntensity * 0.028)}) saturate(${Math.max(0.78, 0.98 - totalIntensity * 0.02)})`

    if (influence.region) shadows.push(`inset 0 0 0 2px rgba(130, 92, 195, ${regionAlpha})`)
    if (influence.column) shadows.push(`inset 0 0 0 2px rgba(37, 137, 103, ${columnAlpha})`)
    if (influence.row) shadows.push(`inset 0 0 0 2px rgba(34, 92, 170, ${rowAlpha})`)
    if (influence.adjacent) shadows.push(`inset 0 0 0 2px rgba(216, 64, 50, ${adjacentAlpha})`)

    shadows.push(
      `inset 0 ${Math.round(sinkDepth * 0.92)}px ${Math.round(sinkDepth * 1.3)}px rgba(11, 31, 39, ${Math.min(0.1 + totalIntensity * 0.03, 0.32)})`,
      `inset 0 -${Math.max(1, Math.round(totalIntensity * 0.4))}px ${Math.round(sinkDepth * 0.9)}px rgba(255, 255, 255, ${Math.min(0.08 + totalIntensity * 0.018, 0.22)})`,
      `inset 0 0 0 ${borderWidth}px rgba(18, 50, 60, ${borderAlpha})`,
    )

    if (influence.origin) {
      shadows.push(
        'inset 0 0 0 4px rgba(255, 255, 255, 0.82)',
        '0 0 0 2px rgba(18, 50, 60, 0.22)',
      )
      filter = `brightness(${Math.min(1.06, 0.9 + influence.origin * 0.04)}) saturate(${Math.min(1.08, 0.94 + influence.origin * 0.04)})`
    }

    return {
      boxShadow: shadows.length ? shadows.join(', ') : undefined,
      filter,
      transform: `translateY(${Math.min(6, totalIntensity * 0.45)}px)`,
      zIndex,
    }
  }

  return (
    <div className={styles.wrap}>
      <Link to="/play" className={styles.back}>← 返回玩游戏列表</Link>

      <div className={styles.tabs}>
        {[['rules', '玩法说明'], ['start', '开始游戏']].map(([key, label]) => (
          <button
            key={key}
            className={`${styles.tab} ${tab === key ? styles.tabActive : ''}`}
            onClick={() => setSearchParams({ tab: key })}
          >
            {label}
          </button>
        ))}
      </div>

      <div className={styles.content}>
        {tab === 'rules' && (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{docs.rules}</ReactMarkdown>
        )}

        {tab === 'start' && (
          <div className={gameStyles.gameShell}>
            <section className={gameStyles.stage}>
              <div className={gameStyles.toolbar}>
                <div className={gameStyles.sizeGroup} aria-label="棋盘尺寸">
                  {SIZES.map(size => (
                    <button
                      key={size}
                      type="button"
                      className={`${gameStyles.sizeButton} ${size === level.size ? gameStyles.sizeButtonActive : ''}`}
                      onClick={() => switchSize(size)}
                    >
                      {size}x{size}
                    </button>
                  ))}
                </div>
                <div className={gameStyles.actions}>
                  <button type="button" className="btn-ghost" onClick={restart}>重开</button>
                  <button type="button" className="btn-primary" onClick={showSolution}>演示解</button>
                </div>
              </div>

              <div
                className={`${gameStyles.board} ${result.solved ? gameStyles.solved : ''}`}
                style={{ '--size': level.size }}
                aria-label={`${level.name} 奶牛摆放棋盘`}
              >
                {level.grid.map((row, rowIndex) =>
                  row.map((region, colIndex) => {
                    const selected = marks[rowIndex][colIndex]
                    const key = `${rowIndex}:${colIndex}`
                    const conflict = result.conflicts.has(key)
                    return (
                      <button
                        key={key}
                        type="button"
                        className={`${gameStyles.cell} ${conflict ? gameStyles.conflict : ''}`}
                        style={{
                          backgroundColor: REGION_COLORS[region % REGION_COLORS.length],
                          ...effectStyle(result.influence[rowIndex][colIndex])
                        }}
                        onClick={() => onCellClick(rowIndex, colIndex)}
                        aria-pressed={selected}
                        aria-label={`第 ${rowIndex + 1} 行第 ${colIndex + 1} 列，区域 ${region + 1}`}
                      >
                        <span className={gameStyles.regionLabel}>{region + 1}</span>
                        {selected && <span className={gameStyles.mark} aria-hidden="true" />}
                      </button>
                    )
                  }),
                )}
              </div>

              {result.solved && (
                <div className={gameStyles.celebrationPanel} role="status" aria-live="polite">
                  <div className={gameStyles.celebrationEmoji} aria-hidden="true">🎉</div>
                  <h3 className={gameStyles.celebrationTitle}>恭喜过关！</h3>
                  <p className={gameStyles.celebrationText}>
                    这一局已经满足同行、同列、同色与相邻约束。
                  </p>
                </div>
              )}
            </section>

            <aside className={gameStyles.sidePanel}>
              <h2 className={gameStyles.statusTitle}>{level.name} 局面</h2>
              <div className={gameStyles.statusGrid}>
                <div className={gameStyles.metric}>
                  <span className={gameStyles.metricValue}>{result.selected}</span>
                  <span className={gameStyles.metricLabel}>已放置</span>
                </div>
                <div className={gameStyles.metric}>
                  <span className={gameStyles.metricValue}>{result.remaining}</span>
                  <span className={gameStyles.metricLabel}>剩余</span>
                </div>
              </div>

              {result.solved && (
                <div className={gameStyles.successBox}>已满足区域、行列与相邻约束，当前局面完成。</div>
              )}
              {!result.solved && result.conflicts.size === 0 && (
                <p className={gameStyles.message}>当前没有冲突，继续补齐剩余奶牛。</p>
              )}

              <div className={gameStyles.ruleList}>
                {RULES.map(([rule, label]) => {
                  const violations = result.violations.filter(item => item.rule === rule)
                  return (
                    <section
                      key={rule}
                      className={`${gameStyles.ruleItem} ${violations.length ? gameStyles.ruleItemBad : ''}`}
                    >
                      <h3>{label}</h3>
                      {violations.length > 0 && (
                        <ul>
                          {violations.map((violation, index) => (
                            <li key={`${rule}-${index}`}>{violation.message}</li>
                          ))}
                        </ul>
                      )}
                    </section>
                  )
                })}
              </div>

              <div className={gameStyles.legend} aria-label="区域色块">
                {Array.from({ length: level.size }, (_, index) => (
                  <span
                    key={index}
                    className={gameStyles.swatch}
                    style={{ backgroundColor: REGION_COLORS[index % REGION_COLORS.length] }}
                    title={`区域 ${index + 1}`}
                  />
                ))}
              </div>
            </aside>
          </div>
        )}
      </div>
    </div>
  )
}
