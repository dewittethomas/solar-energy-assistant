import { BarChart3, Gauge, SunMedium, Zap } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { IconBadge } from '../ui/IconBadge.jsx'

const infoIcons = {
  peak: SunMedium,
  yield: BarChart3,
  output: Zap,
}

export function InfoCard({ items }) {
  const { t } = useTranslation()

  return (
    <article className="summary-card info-card">
      <div className="card-title-row">
        <div>
          <p className="eyebrow">{t('dashboard.info.title')}</p>
          <h2>{t('dashboard.info.today')}</h2>
        </div>
        <IconBadge>
          <Gauge size={22} strokeWidth={2.2} />
        </IconBadge>
      </div>

      <div className="info-grid">
        {items.map((item) => {
          const ItemIcon = infoIcons[item.type]

          return (
            <div key={item.labelKey}>
              <ItemIcon size={20} strokeWidth={2.2} />
              <span>{t(item.labelKey)}</span>
              <strong>{t(item.valueKey)}</strong>
            </div>
          )
        })}
      </div>
    </article>
  )
}
