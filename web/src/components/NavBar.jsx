import { NavLink } from 'react-router-dom'
import styles from './NavBar.module.css'

export default function NavBar() {
  return (
    <header className={styles.nav}>
      <span className={styles.logo}>🎮 chatgame</span>
      <nav className={styles.links}>
        <NavLink to="/play"       className={({ isActive }) => isActive ? styles.active : ''}>玩游戏</NavLink>
        <NavLink to="/solve"      className={({ isActive }) => isActive ? styles.active : ''}>解游戏</NavLink>
        <NavLink to="/contribute" className={({ isActive }) => isActive ? styles.active : ''}>接入游戏</NavLink>
      </nav>
    </header>
  )
}
