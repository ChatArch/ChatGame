import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import styles from './Library.module.css'
import { fallbackGames, fetchJson } from '../lib/api'

export default function SolveList() {
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
      <h1 className={styles.title}>解游戏</h1>
      <div className={styles.grid}>
        {games.map(g => (
          <div key={g.id} className={styles.card}>
            <div className={styles.cardTop}>
              <span className={styles.badge}>已支持</span>
            </div>
            <h2 className={styles.cardTitle}>{g.name}</h2>
            <p className={styles.cardDesc}>{g.description}</p>
            <div className={styles.cardActions}>
              <Link to={`/solve/${g.id}?tab=strategy`} className={styles.linkBtn}>游戏攻略</Link>
              <Link to={`/solve/${g.id}?tab=solver`} className={styles.linkBtn}>自动求解</Link>
            </div>
          </div>
        ))}
        {/* 占位卡片 */}
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
