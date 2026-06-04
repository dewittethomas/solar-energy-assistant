import { useEffect, useMemo, useState } from 'react'
import { CalendarClock, Clock3, CloudSun } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client.js'
import { PredictionChart } from '../components/dashboard/PredictionChart.jsx'
import { NoProductionDataState } from '../components/ui/NoProductionDataState.jsx'
import { PageHeading } from '../components/ui/PageHeading.jsx'
import { TrainingStateNotice } from '../components/ui/TrainingStateNotice.jsx'
import { getForecastValidity } from '../utils/forecastValidation.js'
import { convertWattsToUnit, formatTemperature, mapWeatherLabel } from '../utils/presentation.js'
import { buildPlannerWindows, formatTimeInZone, getRelativeDayName, resolveTimeContext } from '../utils/solarTime.js'

export function ForecastsPage({ datasetState, installation, modelState, onNavigate, trainingRunId, user }) {
  const { i18n, t } = useTranslation()
  const hasProductionData = Boolean(datasetState?.hasProductionData)
  const isLoading = Boolean(datasetState?.isLoading)
  const [forecastData, setForecastData] = useState({
    forecast: [],
    server_time: new Date().toISOString(),
    timezone: 'Europe/Brussels',
  })
  const [dashboard, setDashboard] = useState(null)

  useEffect(() => {
    if (!user?.installationId || !hasProductionData) {
      return
    }

    async function loadForecasts() {
      try {
        const dashboardResult = await api.getDashboard(user.installationId)
        const timezone = dashboardResult?.timezone || 'Europe/Brussels'
        const predictionResult = await api.getThreeDayPredictions(user.installationId, new Date(), timezone)

        setDashboard(dashboardResult)
        setForecastData(predictionResult)
      } catch {
        setDashboard(null)
      }
    }

    loadForecasts()
  }, [hasProductionData, user?.installationId])

  const locale = i18n.language === 'fr' ? 'fr-BE' : i18n.language === 'en' ? 'en-GB' : 'nl-BE'
  const timeContext = resolveTimeContext(forecastData)
  const labels = useMemo(
    () => ({
      today: t('common.today'),
      tomorrow: t('common.tomorrow'),
      dayAfterTomorrow: t('common.dayAfterTomorrow'),
    }),
    [t],
  )
  const plannerWindows = buildPlannerWindows(forecastData.forecast || [], timeContext, { locale, mode: 'best_overall' })
  const bestWindow = plannerWindows[0]
  const tomorrowWeather = formatTomorrowWeather(dashboard, t)
  const isTrainingGuarded = ['training', 'failed'].includes(modelState)
  const forecastUnit = forecastData.unit || 'kW'
  const installationKwp = installation?.installationKwp ?? user?.installationKwp ?? null
  const forecastValidity = getForecastValidity({
    dashboardOutputKw: dashboard?.current_output_kw,
    forecast: forecastData.forecast || [],
    installationKwp,
  })
  const hasInvalidForecast = forecastValidity.invalid
  const chartData = mapForecastForChart(forecastData.forecast || [], timeContext, locale, labels, forecastUnit)

  return (
    <>
      <PageHeading eyebrow={t('pages.forecasts.eyebrow')} title={t('pages.forecasts.title')} />

      {isTrainingGuarded && (
        <TrainingStateNotice modelState={modelState} onNavigate={onNavigate} trainingRunId={trainingRunId} />
      )}

      {!isTrainingGuarded && !isLoading && !hasProductionData && (
        <NoProductionDataState messageKey="pages.forecasts.empty.text" onUpload={() => onNavigate('dataManagement')} />
      )}

      {!isTrainingGuarded && hasProductionData && !hasInvalidForecast && (
        <section className="homeowner-grid">
          <article className="insight-card solar-card">
            <Clock3 size={24} strokeWidth={2.2} />
            <span>{t('pages.forecasts.bestWindow', { defaultValue: 'Beste moment komende 3 dagen' })}</span>
            <strong>
              {bestWindow
                ? `${getRelativeDayName(bestWindow.start, timeContext, labels)} ${bestWindow.label}`
                : t('common.windowPassed')}
            </strong>
          </article>
          <article className="insight-card weather-impact-card">
            <CloudSun size={24} strokeWidth={2.2} />
            <span>{t('pages.forecasts.weather')}</span>
            <strong>{mapWeatherLabel(dashboard?.current_weather?.status, t)}</strong>
            <small>{formatTemperature(dashboard?.current_weather?.temperature_c) || '-'}</small>
          </article>
          <article className="insight-card">
            <CalendarClock size={24} strokeWidth={2.2} />
            <span>{t('pages.forecasts.tomorrow')}</span>
            <strong>{tomorrowWeather}</strong>
          </article>
        </section>
      )}

      {!isTrainingGuarded && hasProductionData && !hasInvalidForecast && <PredictionChart data={chartData} unit={forecastUnit} />}

      {!isTrainingGuarded && hasProductionData && hasInvalidForecast && (
        <section className="forecast-warning-panel" aria-live="polite">
          <div className="forecast-warning-card">
            <strong>{t('dashboard.invalidForecast.title', { defaultValue: 'Deze voorspelling lijkt niet geldig.' })}</strong>
            <p>{t('dashboard.invalidForecast.text', { defaultValue: 'Controleer de productie-eenheid van je dataset of train het model opnieuw.' })}</p>
            <button className="secondary-action-button" onClick={() => onNavigate('dataManagement')} type="button">
              {t('dashboard.invalidForecast.cta', { defaultValue: 'Dataset controleren' })}
            </button>
          </div>
        </section>
      )}
    </>
  )
}

function formatTomorrowWeather(dashboard, t) {
  const min = formatTemperature(dashboard?.tomorrow_weather?.min_temperature_c)?.replace(' °C', '')
  const max = formatTemperature(dashboard?.tomorrow_weather?.max_temperature_c)?.replace(' °C', '')

  if (min && max) {
    return `${min} - ${max} °C`
  }

  return mapWeatherLabel(dashboard?.tomorrow_weather?.status, t)
}

function mapForecastForChart(forecast, timeContext, locale, labels, unit) {
  return forecast
    .map((entry) => ({
      label: `${getRelativeDayName(entry.timestamp, timeContext, labels)} ${formatTimeInZone(entry.timestamp, timeContext.timezone, locale)}`,
      value: convertWattsToUnit(entry?.predicted_w ?? entry?.value_w ?? 0, unit),
    }))
    .filter((entry) => Number.isFinite(entry.value) && entry.value >= 0)
}

