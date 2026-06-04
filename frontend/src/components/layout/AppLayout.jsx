import { Header } from './Header.jsx'
import { Sidebar } from './Sidebar.jsx'

export function AppLayout({ activePage, children, darkMode, onNavigate, user }) {
  return (
    <div className="app-shell" data-theme={darkMode ? 'dark' : 'light'}>
      <Header user={user} />
      <div className="body-layout">
        <Sidebar activePage={activePage} onNavigate={onNavigate} />
        <main className="content">{children}</main>
      </div>
    </div>
  )
}
