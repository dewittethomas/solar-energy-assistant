import {
  BarChart3,
  CalendarDays,
  Database,
  LayoutDashboard,
  Settings,
  SlidersHorizontal,
  WandSparkles,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'

const primaryItems = [
  { id: 'dashboard', labelKey: 'navigation.dashboard', Icon: LayoutDashboard },
  { id: 'forecasts', labelKey: 'navigation.forecasts', Icon: CalendarDays },
  { id: 'assistant', labelKey: 'navigation.assistant', Icon: WandSparkles },
  { id: 'analysis', labelKey: 'navigation.analysis', Icon: BarChart3 },
]

const secondaryItems = [
  { id: 'dataManagement', labelKey: 'navigation.datasets', Icon: Database },
  { id: 'models', labelKey: 'navigation.predictionModel', Icon: SlidersHorizontal },
  { id: 'configuration', labelKey: 'navigation.settings', Icon: Settings },
]

export function Sidebar({ activePage, onNavigate }) {
  const { t } = useTranslation()

  return (
    <aside className="sidebar" aria-label="Main navigation">
      <nav className="nav-list">
        {primaryItems.map(({ id, labelKey, Icon }) => (
          <button
            className={activePage === id ? 'nav-link active' : 'nav-link'}
            key={id}
            onClick={() => onNavigate(id)}
            type="button"
          >
            <Icon size={18} strokeWidth={2.35} />
            {t(labelKey)}
          </button>
        ))}
      </nav>
      <nav className="nav-list secondary-nav" aria-label={t('navigation.advanced')}>
        <span className="nav-section-label">{t('navigation.advanced')}</span>
        {secondaryItems.map(({ id, labelKey, Icon }) => (
          <button
            className={activePage === id ? 'nav-link secondary active' : 'nav-link secondary'}
            key={id}
            onClick={() => onNavigate(id)}
            type="button"
          >
            <Icon size={18} strokeWidth={2.25} />
            <span>{t(labelKey)}</span>
          </button>
        ))}
      </nav>
    </aside>
  )
}
