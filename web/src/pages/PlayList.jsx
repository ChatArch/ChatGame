import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import styles from './Library.module.css'

export default function PlayList() {
  const [games, setGames] = useState([])

  useEffect(() => {
    fetch('/api/games')
      .then(r => r.json())
      .then(d => setGames(d.games))
      .catch(() => setGames([{ id: 'cow-puzzle', name: '奶牛摆放谜题', description: '色块区域约束 · 行列唯一 · 无相邻' }]))
  }, [])

  return (
    <div>
      <h1 className={styles.title}>玩游戏</h1>
      <div className={styles.grid}>
        {games.map(g => (
          <div key={g.id} className={styles.card}>
            <div className={styles.cardTop}>
              <span className={styles.badge}>已支持</span>
            </div>
            <h2 className={styles.cardTitle}>{g.name}</h2>
            <p className={styles.cardDesc}>{g.description}</p>
            <div className={styles.cardActions}>
              <Link to={`/play/${g.id}?tab=rules`} className={styles.linkBtn}>玩法说明</Link>
              <Link to={`/play/${g.id}?tab=start`} className={styles.linkBtn}>开始游戏</Link>
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
