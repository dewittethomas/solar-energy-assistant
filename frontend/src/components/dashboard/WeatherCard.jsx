import { Cloud, CloudSun, SunMedium } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { IconBadge } from '../ui/IconBadge.jsx'

export function WeatherCard({ weather }) {
  const { t } = useTranslation()

  return (
    <article className="summary-card weather-card">
      <div className="card-title-row">
        <div>
          <p className="eyebrow">{t('dashboard.weather.title')}</p>
        </div>
        <IconBadge>
          <CloudSun size={22} strokeWidth={2.2} />
        </IconBadge>
      </div>

      <div className="weather-overview">
        <div className="weather-current">
          <div>
            <strong>{t(weather.currentTemperatureKey)}</strong>
            <span>{t(weather.cloudStatusKey)}</span>
          </div>
          <div className="weather-icon-cluster" aria-hidden="true">
            <SunMedium className="weather-sun" size={32} strokeWidth={2} />
            <Cloud className="weather-cloud" size={38} strokeWidth={2} />
          </div>
        </div>

        <div className="weather-tomorrow">
          <div className="tomorrow-summary">
            <span>{t('dashboard.weather.tomorrow')}</span>
          </div>
          <strong className="tomorrow-range">
            {t(weather.tomorrowMinKey)} - {t(weather.tomorrowMaxKey)}
          </strong>
          <div className="tomorrow-condition">
            <Cloud className="tomorrow-cloud-icon" size={19} strokeWidth={2} />
            <span>{t('dashboard.weather.tomorrowCloudStatus')}</span>
          </div>
        </div>
      </div>
    </article>
  )
}
