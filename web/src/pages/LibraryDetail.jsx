import { useEffect, useState, useRef } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import styles from './LibraryDetail.module.css'
import solverStyles from './Solver.module.css'
import { fallbackDocs, fetchJson } from '../lib/api'

export default function LibraryDetail() {
  const { id } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  // tabs: 'play' | 'solve'
  const tab = searchParams.get('tab') || 'play'
  const [docs, setDocs] = useState(fallbackDocs)

  // Solver states
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [solving, setSolving] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
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
      <Link to="/library" className={styles.back}>← 返回游戏库</Link>

      <div className={styles.tabs}>
        {[['play', '玩游戏'], ['solve', '解游戏']].map(([t, label]) => (
          <button key={t}
            className={`${styles.tab} ${tab === t ? styles.tabActive : ''}`}
            onClick={() => setSearchParams({ tab: t })}
          >{label}</button>
        ))}
      </div>

      <div className={styles.content}>
        {tab === 'play' && (
          <div>
            <div className={styles.playHeader}>
              <button className="btn-primary" disabled style={{ marginBottom: '16px' }}>开始玩 (敬请期待)</button>
            </div>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{docs.rules}</ReactMarkdown>
          </div>
        )}

        {tab === 'solve' && (
          <div className={solverStyles.solveLayout}>
            {/* 左侧：攻略 */}
            <div className={solverStyles.strategyCol}>
              <h2 className={solverStyles.sectionTitle}>游戏攻略</h2>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{docs.strategy}</ReactMarkdown>
            </div>

            {/* 右侧：求解器 */}
            <div className={solverStyles.solverCol}>
              <h2 className={solverStyles.sectionTitle}>自动求解</h2>
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

              {result && (
                <div className={solverStyles.resultArea} style={{ marginTop: '16px' }}>
                  <h3 className={solverStyles.sectionTitle} style={{ fontSize: '14px' }}>
                    答案 <span className={solverStyles.badge}>{result.elapsed_ms} ms</span>
                  </h3>
                  <div className={solverStyles.annotatedWrap}>
                    <img
                      src={`data:image/png;base64,${result.annotated_image}`}
                      alt="标注结果"
                      className={solverStyles.annotatedImg}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
