import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import styles from './Library.module.css'
import { fallbackGames, fetchJson } from '../lib/api'

export default function PlayList() {
  const [games, setGames] = useState(fallbackGames)

  useEffect(() => {
    let mounted = true
    fetchJson('/api/games')
      .then(d => {
        if (mounted && Array.isArray(d?.games) && d.games.length > 0) {
          setGames(d.games)
        }
      })
      .catch(() => {})
    return () => { mounted = false }
  }, [])

  return (
    <div>
      <h1 className={styles.title}>玩游戏</h1>
      <div className={styles.grid}>
        {games.map(g => {
          const pending = g.status === 'review_pending' || g.status === 'needs_edit'
          return (
            <div key={g.id} className={`${styles.card} ${pending ? styles.cardPending : ''}`}>
              <div className={styles.cardTop}>
                <span className={`${styles.badge} ${pending ? styles.badgePending : ''}`}>
                  {pending ? '待评审' : '已支持'}
                </span>
              </div>
              <h2 className={styles.cardTitle}>{g.name}</h2>
              <p className={styles.cardDesc}>{g.description}</p>
              <div className={styles.cardActions}>
                {pending ? (
                  <>
                    <span className={styles.disabledBtn}>等待 review</span>
                    <a href={g.github_url || 'https://github.com/ChatArch/ChatGame'} target="_blank" rel="noreferrer" className={styles.linkBtn}>GitHub 进展</a>
                  </>
                ) : (
                  <>
                    <Link to={`/play/${g.id}?tab=start`} className={styles.linkBtn}>开始游戏</Link>
                    <Link to={`/play/${g.id}?tab=rules`} className={styles.linkBtn}>玩法说明</Link>
                  </>
                )}
              </div>
            </div>
          )
        })}
        {[1, 2].map(i => (
          <div key={i} className={`${styles.card} ${styles.cardPlaceholder}`}>
            <span className={styles.badge} style={{ background: '#f0f0f0', color: '#999' }}>即将上线</span>
            <h2 className={styles.cardTitle} style={{ color: '#bbb' }}>更多游戏</h2>
            <p className={styles.cardDesc} style={{ color: '#ccc' }}>敬请期待</p>
          </div>
        ))}
      </div>
    </div>
  )
}
