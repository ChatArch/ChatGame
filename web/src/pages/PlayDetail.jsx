import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import styles from './LibraryDetail.module.css'

export default function PlayDetail() {
  const { id } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'rules'
  const [docs, setDocs] = useState(null)
  const [loadingDocs, setLoadingDocs] = useState(true)

  useEffect(() => {
    setLoadingDocs(true)
    fetch(`/api/games/${id}/docs`)
      .then(r => r.json())
      .then(d => { setDocs(d); setLoadingDocs(false) })
      .catch(() => setLoadingDocs(false))
  }, [id])

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
          <div>
            <div className={styles.playHeader}>
              <button className="btn-primary" disabled style={{ marginBottom: '16px' }}>开始游戏 (敬请期待)</button>
            </div>
            <p className={styles.muted}>在线游玩入口预留中，当前先保留按钮位置。</p>
          </div>
        )}
      </div>
    </div>
  )
}
