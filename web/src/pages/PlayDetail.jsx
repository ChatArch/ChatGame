import { useEffect, useState } from 'react'
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
  levels,
  marksFromSolution,
  toggleMark,
} from '../games/cowPuzzle'

const RULES = [
  ['region', '每个颜色区域恰好 1 头'],
  ['row-column', '每行每列恰好 1 头'],
  ['adjacent', '任意两头不能相邻'],
]

export default function PlayDetail() {
  const { id } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'rules'
  const [docs, setDocs] = useState(null)
  const [loadingDocs, setLoadingDocs] = useState(true)
  const [level, setLevel] = useState(() => getLevelBySize(8))
  const [marks, setMarks] = useState(() => createEmptyMarks(8))

  useEffect(() => {
    fetch(`/api/games/${id}/docs`)
      .then(r => r.json())
      .then(d => { setDocs(d); setLoadingDocs(false) })
      .catch(() => setLoadingDocs(false))
  }, [id])

  const result = evaluateBoard(level, marks)

  function switchSize(size) {
    const nextLevel = getRandomLevelBySize(size)
    setLevel(nextLevel)
    setMarks(createEmptyMarks(nextLevel.size))
  }

  function restart() {
    const nextLevel = getRandomLevelBySize(level.size, level.id)
    setLevel(nextLevel)
    setMarks(createEmptyMarks(nextLevel.size))
  }

  function showSolution() {
    setMarks(marksFromSolution(level.size, level.solution))
  }

  function onCellClick(row, col) {
    setMarks(current => toggleMark(current, row, col))
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
          loadingDocs
            ? <p className={styles.muted}>加载中…</p>
            : <ReactMarkdown remarkPlugins={[remarkGfm]}>{docs?.rules || '暂无玩法说明'}</ReactMarkdown>
        )}

        {tab === 'start' && (
          <div className={gameStyles.gameShell}>
            <section className={gameStyles.stage}>
              <div className={gameStyles.toolbar}>
                <div className={gameStyles.sizeGroup} aria-label="棋盘尺寸">
                  {levels.map(item => (
                    <button
                      key={item.id}
                      type="button"
                      className={`${gameStyles.sizeButton} ${item.id === level.id ? gameStyles.sizeButtonActive : ''}`}
                      onClick={() => switchSize(item.size)}
                    >
                      {item.size}x{item.size}
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
                        style={{ backgroundColor: REGION_COLORS[region % REGION_COLORS.length] }}
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
