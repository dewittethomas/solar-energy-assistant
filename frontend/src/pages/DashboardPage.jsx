import { useTranslation } from 'react-i18next'
import { InfoCard } from '../components/dashboard/InfoCard.jsx'
import { PredictionChart } from '../components/dashboard/PredictionChart.jsx'
import { WeatherCard } from '../components/dashboard/WeatherCard.jsx'
import { PageHeading } from '../components/ui/PageHeading.jsx'
import { predictionData, todayInfo, weather } from '../data/demoDashboardData.js'

export function DashboardPage() {
  const { t } = useTranslation()

  return (
    <>
      <PageHeading eyebrow={t('dashboard.eyebrow')} title={t('dashboard.title')} />

      <section className="summary-grid" aria-label="Current solar conditions">
        <WeatherCard weather={weather} />
        <InfoCard items={todayInfo} />
      </section>

      <PredictionChart data={predictionData} />
    </>
  )
}
