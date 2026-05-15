import { useEffect, useState, useRef } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import styles from './LibraryDetail.module.css'
import solverStyles from './Solver.module.css'

export default function SolveDetail() {
  const { id } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'strategy'
  const [docs, setDocs] = useState(null)
  const [loadingDocs, setLoadingDocs] = useState(true)

  // Solver states
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [solving, setSolving] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const inputRef = useRef()

  useEffect(() => {
    setLoadingDocs(true)
    fetch(`/api/games/${id}/docs`)
      .then(r => r.json())
      .then(d => { setDocs(d); setLoadingDocs(false) })
      .catch(() => setLoadingDocs(false))
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
      const res = await fetch('/api/solve', { method: 'POST', body: fd })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '求解失败')
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
              {loadingDocs ? <p className={styles.muted}>加载中…</p> :
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{docs?.rules || '暂无玩法说明'}</ReactMarkdown>}
            </div>
            {loadingDocs ? <p className={styles.muted}>加载中…</p> :
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{docs?.strategy || '暂无游戏攻略'}</ReactMarkdown>}
          </div>
        )}

        {tab === 'solver' && (
          <div className={solverStyles.solverWorkspace}>
            <section className={solverStyles.controlPanel}>
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
            </section>

            <section className={solverStyles.resultPanel}>
              <h3 className={solverStyles.sectionTitle} style={{ fontSize: '14px' }}>
                答案 {result && <span className={solverStyles.badge}>{result.elapsed_ms} ms</span>}
              </h3>

              {result ? (
                <div className={solverStyles.resultArea}>
                  <div className={solverStyles.annotatedWrap}>
                    <img
                      src={`data:image/png;base64,${result.annotated_image}`}
                      alt="标注结果"
                      className={solverStyles.annotatedImg}
                    />
                  </div>
                </div>
              ) : (
                <div className={solverStyles.resultPlaceholder}>上传截图后，答案会展示在这里</div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  )
}
