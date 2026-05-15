import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import styles from './LibraryDetail.module.css'

// 简单 Markdown → HTML（只处理标题和段落，足够展示文档）
function renderMd(md) {
  return md
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2>$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g,      '<code>$1</code>')
    .replace(/^---$/gm,       '<hr/>')
    .replace(/^> (.+)$/gm,    '<blockquote>$1</blockquote>')
    .replace(/\n\n/g,         '</p><p>')
    .replace(/^/,             '<p>')
    .replace(/$/,             '</p>')
}

export default function LibraryDetail() {
  const { id } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'rules'
  const [docs, setDocs] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    fetch(`/api/games/${id}/docs`)
      .then(r => r.json())
      .then(d => { setDocs(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [id])

  const content = docs ? (tab === 'rules' ? docs.rules : docs.strategy) : ''

  return (
    <div className={styles.wrap}>
      <Link to="/library" className={styles.back}>← 返回游戏库</Link>

      <div className={styles.tabs}>
        {[['rules', '玩法说明'], ['strategy', '游戏攻略']].map(([t, label]) => (
          <button key={t}
            className={`${styles.tab} ${tab === t ? styles.tabActive : ''}`}
            onClick={() => setSearchParams({ tab: t })}
          >{label}</button>
        ))}
      </div>

      <div className={styles.content}>
        {loading
          ? <p className={styles.muted}>加载中…</p>
          : <div dangerouslySetInnerHTML={{ __html: renderMd(content || '暂无内容') }} />
        }
      </div>
    </div>
  )
}
