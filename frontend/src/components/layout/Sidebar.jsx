import { Bot, Database, LayoutDashboard, Settings, SlidersHorizontal } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const navigationItems = [
  { id: 'dashboard', labelKey: 'navigation.dashboard', Icon: LayoutDashboard },
  { id: 'assistant', labelKey: 'navigation.assistant', Icon: Bot },
  { id: 'models', labelKey: 'navigation.models', Icon: SlidersHorizontal },
  { id: 'dataManagement', labelKey: 'navigation.dataManagement', Icon: Database },
  { id: 'configuration', labelKey: 'navigation.settings', Icon: Settings },
]

export function Sidebar({ activePage, onNavigate }) {
  const { t } = useTranslation()

  return (
    <aside className="sidebar" aria-label="Main navigation">
      <nav className="nav-list">
        {navigationItems.map(({ id, labelKey, Icon }) => (
          <button
            className={activePage === id ? 'nav-link active' : 'nav-link'}
            key={id}
            onClick={() => onNavigate(id)}
            type="button"
          >
            <Icon size={18} strokeWidth={2.2} />
            {t(labelKey)}
          </button>
        ))}
      </nav>
    </aside>
  )
}
