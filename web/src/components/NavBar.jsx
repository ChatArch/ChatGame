import { NavLink } from 'react-router-dom'
import styles from './NavBar.module.css'

export default function NavBar() {
  return (
    <header className={styles.nav}>
      <span className={styles.logo}>🎮 chatgame</span>
      <nav className={styles.links}>
        <NavLink to="/solver"     className={({ isActive }) => isActive ? styles.active : ''}>求解</NavLink>
        <NavLink to="/library"    className={({ isActive }) => isActive ? styles.active : ''}>游戏库</NavLink>
        <NavLink to="/contribute" className={({ isActive }) => isActive ? styles.active : ''}>贡献游戏</NavLink>
      </nav>
    </header>
  )
}
