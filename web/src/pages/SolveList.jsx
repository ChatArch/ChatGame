import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import styles from './Library.module.css'
import { fallbackGames, fetchJson } from '../lib/api'

function GameCard({ game }) {
  const pending = game.status === 'pending_review'
  return (
    <div className={`${styles.card} ${pending ? styles.cardPending : ''}`}>
      <div className={styles.cardTop}>
        <span className={`${styles.badge} ${pending ? styles.badgePending : ''}`}>
          {game.badge || (pending ? '待评审' : '已支持')}
        </span>
      </div>
      <h2 className={styles.cardTitle}>{game.name}</h2>
      <p className={styles.cardDesc}>{game.description}</p>
      {pending ? (
        <div className={styles.cardActions}>
          <a href={game.progress_url || 'https://github.com/ChatArch/ChatGame'}
            className={styles.linkBtn} target="_blank" rel="noreferrer">
            GitHub 进展
          </a>
          <span className={styles.disabledBtn}>等待 review</span>
        </div>
      ) : (
        <div className={styles.cardActions}>
          <Link to={`/solve/${game.id}?tab=strategy`} className={styles.linkBtn}>游戏攻略</Link>
          <Link to={`/solve/${game.id}?tab=solver`} className={styles.linkBtn}>自动求解</Link>
        </div>
      )}
    </div>
  )
}

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
        {games.map(g => <GameCard key={g.id} game={g} />)}
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
