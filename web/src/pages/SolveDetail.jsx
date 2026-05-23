import { useEffect, useState, useRef } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import styles from './LibraryDetail.module.css'
import solverStyles from './Solver.module.css'
import { cowPuzzleSamples } from '../games/cowPuzzleSamples'
import { fallbackDocs, fetchJson } from '../lib/api'

export default function SolveDetail() {
  const { id } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'strategy'
  const [docs, setDocs] = useState(fallbackDocs)

  // Solver states
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [solving, setSolving] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [sampleSize, setSampleSize] = useState(null)
  const inputRef = useRef()

  useEffect(() => {
    let mounted = true
    fetchJson(`/api/games/${id}/docs`)
      .then(d => { if (mounted) setDocs({ ...fallbackDocs, ...d }) })
      .catch(() => {})
    return () => { mounted = false }
  }, [id])

  // --- Solver Handlers ---
  function handleFile(f) {
    if (!f) return
    if (!f.type.startsWith('image/')) {
      setError('请上传有效的图片文件')
      return
    }
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
    setError(null)
    setSampleSize(null)
  }

  async function handleSample(sample) {
    setSolving(false)
    setResult(null)
    setError(null)
    try {
      const response = await fetch(sample.url)
      if (!response.ok) throw new Error('示例图加载失败')
      const blob = await response.blob()
      const sampleFile = new File([blob], `${sample.id}.png`, { type: blob.type || 'image/png' })
      setFile(sampleFile)
      setPreview(sample.url)
      setSampleSize(sample.size)
    } catch (err) {
      setError(err.message)
    }
  }

  function onDrop(e) {
    e.preventDefault()
    handleFile(e.dataTransfer.files[0])
  }

  async function onSolve() {
    if (!file) return
    setSolving(true)
    setError(null)
    setResult(null)

    const fd = new FormData()
    fd.append('image', file)
    fd.append('game', id) // current game id
    if (sampleSize) fd.append('n', String(sampleSize))

    try {
      const data = await fetchJson('/api/solve', { method: 'POST', body: fd }, 60000)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setSolving(false)
    }
  }
  // -----------------------

  return (
    <div className={styles.wrap}>
      <Link to="/solve" className={styles.back}>← 返回解游戏列表</Link>

      <div className={styles.tabs}>
        {[['strategy', '游戏攻略'], ['solver', '自动求解']].map(([key, label]) => (
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
        {tab === 'strategy' && (
          <div>
            <h2 className={solverStyles.sectionTitle}>玩法与攻略</h2>
            <div style={{ marginBottom: '24px' }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{docs.rules}</ReactMarkdown>
            </div>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{docs.strategy}</ReactMarkdown>
          </div>
        )}

        {tab === 'solver' && (
          <div className={solverStyles.solverWorkspace}>
            <section className={solverStyles.controlPanel}>
              <h2 className={solverStyles.sectionTitle}>自动求解</h2>
              <p className={solverStyles.helperText}>上传当前关卡截图，系统会自动识别棋盘并生成标注结果。</p>
              <div className={solverStyles.sampleGrid} aria-label="示例图">
                {cowPuzzleSamples.map(sample => (
                  <button
                    key={sample.id}
                    type="button"
                    className={`${solverStyles.sampleCard} ${sampleSize === sample.size ? solverStyles.sampleCardActive : ''}`}
                    onClick={() => handleSample(sample)}
                  >
                    <img src={sample.url} alt={sample.title} className={solverStyles.sampleImg} />
                    <span>{sample.title}</span>
                  </button>
                ))}
              </div>
              <div
                className={`${solverStyles.dropzone} ${file ? solverStyles.hasFile : ''}`}
                onClick={() => inputRef.current.click()}
                onDragOver={e => e.preventDefault()}
                onDrop={onDrop}
              >
                {preview
                  ? <img src={preview} alt="预览" className={solverStyles.previewImg} />
                  : <span className={solverStyles.dropHint}>拖拽或点击上传游戏截图</span>
                }
                <input ref={inputRef} type="file" accept="image/*" hidden
                  onChange={e => handleFile(e.target.files[0])} />
              </div>

              <button className="btn-primary" onClick={onSolve} disabled={!file || solving}
                style={{ width: '100%', marginTop: 8 }}>
                {solving ? '求解中…' : '求解'}
              </button>

              {error && <div className={solverStyles.error}>{error}</div>}
            </section>

            <section className={solverStyles.resultPanel}>
              <h3 className={solverStyles.sectionTitle} style={{ fontSize: '14px' }}>
                答案 {result && <span className={solverStyles.badge}>{result.elapsed_ms} ms</span>}
              </h3>

              {result ? (
                <div className={solverStyles.resultStage}>
                  <div className={solverStyles.annotatedWrap}>
                    <div
                      className={`${solverStyles.resultNotice} ${
                        result.solution_status === 'multiple'
                          ? solverStyles.resultWarning
                          : solverStyles.resultOk
                      }`}
                    >
                      <strong>
                        {result.solution_status === 'multiple' ? '多解提示' : '唯一解'}
                      </strong>
                      <span>{result.message || '已找到可用解。'}</span>
                    </div>
                    <img
                      src={`data:image/png;base64,${result.annotated_image}`}
                      alt="标注结果"
                      className={solverStyles.annotatedImg}
                    />
                  </div>
                </div>
              ) : (
                <div className={solverStyles.resultStage}>
                  <div className={solverStyles.resultPlaceholder}>上传截图后，这里会显示求解结果</div>
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  )
}
