import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { fetchAuthBootstrap, logoutAuth } from '../lib/api'
import styles from './NavBar.module.css'

export default function NavBar() {
  const [session, setSession] = useState(null)
  const location = useLocation()

  useEffect(() => {
    let cancelled = false
    fetchAuthBootstrap()
      .then((data) => {
        if (!cancelled) setSession(data)
      })
      .catch(() => {
        if (!cancelled) {
          setSession({ auth_available: false, identity: 'guest', authenticated: false })
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function handleLogout() {
    const next = await logoutAuth(session)
    setSession({ ...session, ...next, authenticated: false, identity: 'guest', user: null, csrf_token: null })
  }

  function handleLoginNavigation(event) {
    if (
      ['/solve', '/contribute'].some((path) => location.pathname.startsWith(path))
      && !window.confirm('当前页面的未保存内容可能丢失，继续登录？')
    ) {
      event.preventDefault()
    }
  }

  const currentPath = `${location.pathname}${location.search}${location.hash}`
  const loginHref = session?.login_url
    ? `${session.login_url}?next=${encodeURIComponent(currentPath || '/')}`
    : '/login'

  return (
    <header className={styles.nav}>
      <span className={styles.logo}>🎮 chatgame</span>
      <nav className={styles.links}>
        <NavLink to="/play"       className={({ isActive }) => isActive ? styles.active : ''}>玩游戏</NavLink>
        <NavLink to="/solve"      className={({ isActive }) => isActive ? styles.active : ''}>解游戏</NavLink>
        <NavLink to="/contribute" className={({ isActive }) => isActive ? styles.active : ''}>接入游戏</NavLink>
      </nav>
      <div className={styles.session}>
        {session?.auth_available ? (
          session.authenticated ? (
            <>
              <span className={styles.identity}>已登录：{session.user?.display_name || session.user?.user_id}</span>
              <button type="button" onClick={handleLogout}>退出</button>
            </>
          ) : (
            <>
              <span className={styles.identity}>访客</span>
              <a href={loginHref} onClick={handleLoginNavigation}>登录</a>
            </>
          )
        ) : (
          <span className={styles.identity}>访客</span>
        )}
      </div>
    </header>
  )
}
