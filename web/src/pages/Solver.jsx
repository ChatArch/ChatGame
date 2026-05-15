import { useState, useRef } from 'react'
import styles from './Solver.module.css'

const GAMES = [{ id: 'cow-puzzle', name: '牛牛摆放谜题' }]

export default function Solver() {
  const [file, setFile]             = useState(null)
  const [preview, setPreview]       = useState(null)
  const [game, setGame]             = useState('cow-puzzle')
  const [n, setN]                   = useState('')
  const [loading, setLoading]       = useState(false)
  const [result, setResult]         = useState(null)
  const [error, setError]           = useState(null)
  const [hoveredStep, setHoveredStep] = useState(null)
  const inputRef = useRef()

  function handleFile(f) {
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
    setError(null)
  }

  function onDrop(e) {
    e.preventDefault()
    handleFile(e.dataTransfer.files[0])
  }

  async function onSolve() {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)

    const fd = new FormData()
    fd.append('image', file)
    fd.append('game', game)
    if (n) fd.append('n', n)

    try {
      const res = await fetch('/api/solve', { method: 'POST', body: fd })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '求解失败')
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.layout}>
      {/* ── 左栏：输入 ── */}
      <section className={styles.left}>
        <h2 className={styles.sectionTitle}>上传截图</h2>

        <div
          className={`${styles.dropzone} ${file ? styles.hasFile : ''}`}
          onClick={() => inputRef.current.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={onDrop}
        >
          {preview
            ? <img src={preview} alt="预览" className={styles.previewImg} />
            : <span className={styles.dropHint}>拖拽或点击上传游戏截图</span>
          }
          <input ref={inputRef} type="file" accept="image/*" hidden
            onChange={e => handleFile(e.target.files[0])} />
        </div>

        <div className={styles.controls}>
          <label className={styles.label}>游戏类型
            <select value={game} onChange={e => setGame(e.target.value)} className={styles.select}>
              {GAMES.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
            </select>
          </label>
          <label className={styles.label}>棋盘大小 N
            <input type="number" min={4} max={20} placeholder="自动推断"
              value={n} onChange={e => setN(e.target.value)} className={styles.input} />
          </label>
        </div>

        <button className="btn-primary" onClick={onSolve} disabled={!file || loading}
          style={{ width: '100%', marginTop: 8 }}>
          {loading ? '求解中…' : '求解'}
        </button>

        {error && <div className={styles.error}>{error}</div>}
      </section>

      {/* ── 右栏：结果 ── */}
      <section className={styles.right}>
        {result ? (
          <>
            <h2 className={styles.sectionTitle}>
              答案
              <span className={styles.badge}>{result.elapsed_ms} ms</span>
            </h2>

            <div className={styles.resultWrap}>
              {/* 标注图 */}
              <div className={styles.annotatedWrap}>
                <img
                  src={`data:image/png;base64,${result.annotated_image}`}
                  alt="标注结果"
                  className={styles.annotatedImg}
                />
                {/* 高亮覆盖层 */}
                {hoveredStep !== null && (
                  <GridHighlight
                    step={result.steps.find(s => s.step === hoveredStep)}
                    n={result.n}
                  />
                )}
              </div>

              {/* 步骤列表 */}
              <ol className={styles.steps}>
                {result.steps.map(s => (
                  <li key={s.step}
                    className={`${styles.step} ${hoveredStep === s.step ? styles.stepActive : ''}`}
                    onMouseEnter={() => setHoveredStep(s.step)}
                    onMouseLeave={() => setHoveredStep(null)}
                  >
                    <span className={styles.stepNum}>{s.step}</span>
                    <span>行 {s.row} 列 {s.col}</span>
                    <span className={styles.stepColor}>{s.color_name}</span>
                  </li>
                ))}
              </ol>
            </div>
          </>
        ) : (
          <div className={styles.empty}>
            {loading ? '正在求解，请稍候…' : '上传截图后点击「求解」查看答案'}
          </div>
        )}
      </section>
    </div>
  )
}

// 标注图上的高亮覆盖（简单的格子高亮，定位在标注图内）
function GridHighlight({ step, n }) {
  if (!step) return null
  const pct = 100 / n
  return (
    <div className={styles.hlOverlay} style={{
      top:    `${step.row * pct}%`,
      left:   `${step.col * pct}%`,
      width:  `${pct}%`,
      height: `${pct}%`,
    }} />
  )
}
