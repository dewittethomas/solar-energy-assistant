import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, CloudSun, Gauge, Lightbulb, PanelsTopLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client.js'
import { PredictionChart } from '../components/dashboard/PredictionChart.jsx'
import { NoProductionDataState } from '../components/ui/NoProductionDataState.jsx'
import { PageHeading } from '../components/ui/PageHeading.jsx'
import { TrainingStateNotice } from '../components/ui/TrainingStateNotice.jsx'
import { weather } from '../data/fallbackDashboardData.js'
import { getForecastValidity } from '../utils/forecastValidation.js'
import {
  convertWattsToUnit,
  formatCountryLabel,
  formatPowerFromKilowatts,
  formatPowerFromWatts,
  formatTemperature,
  mapWeatherLabel,
} from '../utils/presentation.js'
import { buildPlannerWindows, formatTimeInZone, getDateKey, getRelativeDayName, resolveTimeContext } from '../utils/solarTime.js'

export function DashboardPage({ datasetState, installation, modelState, onNavigate, trainingRunId, user }) {
  const { i18n, t } = useTranslation()
  const hasProductionData = Boolean(datasetState?.hasProductionData)
  const isLoading = Boolean(datasetState?.isLoading)
  const [dashboard, setDashboard] = useState(null)
  const [forecastData, setForecastData] = useState({
    forecast: [],
    server_time: new Date().toISOString(),
    timezone: 'Europe/Brussels',
  })

  useEffect(() => {
    if (!user?.installationId || !hasProductionData) {
      return
    }

    async function loadDashboard() {
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

    loadDashboard()
  }, [hasProductionData, user?.installationId])

  const locale = i18n.language === 'fr' ? 'fr-BE' : i18n.language === 'en' ? 'en-GB' : 'nl-BE'
  const timeContext = resolveTimeContext({
    server_time: dashboard?.server_time || forecastData.server_time,
    timezone: dashboard?.timezone || forecastData.timezone,
  })
  const displayedWeather = dashboard ? mapWeather(dashboard, t) : weather
  const installationInfo = mapInstallationInfo(user, installation, t)
  const plannerLabels = useMemo(
    () => ({
      today: t('common.today'),
      tomorrow: t('common.tomorrow'),
      dayAfterTomorrow: t('common.dayAfterTomorrow'),
    }),
    [t],
  )
  const todayWindows = buildPlannerWindows(forecastData.forecast || [], timeContext, {
    locale,
    targetDateKey: getDateKey(timeContext.serverTime, timeContext.timezone),
  })
  const allWindows = buildPlannerWindows(forecastData.forecast || [], timeContext, { locale })
  const nextWindow = chooseNextBestWindow(todayWindows, allWindows)
  const hasStrongWindow = Boolean(nextWindow)
  const predictedOutputNow = Number.isFinite(Number(dashboard?.current_output_kw))
    ? Number(dashboard.current_output_kw)
    : null
  const forecastUnit = forecastData.unit || 'kW'
  const installationKwp = installation?.installationKwp ?? user?.installationKwp ?? null
  const forecastValidity = getForecastValidity({
    dashboardOutputKw: predictedOutputNow,
    forecast: forecastData.forecast || [],
    installationKwp,
  })
  const hasInvalidForecast = forecastValidity.invalid
  const peakTodayWatts = getPeakTodayWatts(forecastData.forecast || [], timeContext.serverTime, timeContext.timezone)
  const outputNow = hasInvalidForecast
    ? '-'
    : predictedOutputNow !== undefined && predictedOutputNow !== null
      ? formatPowerFromKilowatts(predictedOutputNow, forecastUnit, locale)
      : peakTodayWatts !== null
        ? formatPowerFromWatts(peakTodayWatts, forecastUnit, locale)
        : t('dashboard.info.outputValue')
  const peakToday = peakTodayWatts !== null ? formatPowerFromWatts(peakTodayWatts, forecastUnit, locale) : null
  const chartData = mapForecastForChart(forecastData.forecast || [], timeContext, locale, plannerLabels, forecastUnit)
  const isTrainingGuarded = ['training', 'failed'].includes(modelState)

  return (
    <>
      <PageHeading eyebrow={t('dashboard.eyebrow')} title={t('dashboard.title')} />

      {isTrainingGuarded && (
        <TrainingStateNotice modelState={modelState} onNavigate={onNavigate} trainingRunId={trainingRunId} />
      )}

      {!isTrainingGuarded && !isLoading && !hasProductionData && (
        <NoProductionDataState messageKey="dashboard.empty.text" onUpload={() => onNavigate('dataManagement')} />
      )}

      {!isTrainingGuarded && hasProductionData && (
        <section className="monitoring-widget-grid" aria-label={t('dashboard.title')}>
          <article className="monitoring-widget production-widget">
            <div className="widget-heading">
              <p className="widget-label">{t('dashboard.installation.title')}</p>
              <PanelsTopLeft size={18} strokeWidth={2.2} />
            </div>
            <strong>{installationInfo.panelSummary}</strong>
            <p>{installationInfo.location}</p>
            <div className="widget-meta-row">
              {installationInfo.panelCount && <span>{installationInfo.panelCount}</span>}
              {installationInfo.power && <span>{installationInfo.power}</span>}
            </div>
          </article>

          <article className="monitoring-widget production-widget">
            <div className="widget-heading">
              <p className="widget-label">{t('dashboard.forecastStatus.title')}</p>
              <Gauge size={18} strokeWidth={2.2} />
            </div>
            {hasInvalidForecast ? (
              <>
                <strong>{t('dashboard.invalidForecast.title', { defaultValue: 'Deze voorspelling lijkt niet geldig.' })}</strong>
                <p>{t('dashboard.invalidForecast.text', { defaultValue: 'Controleer de productie-eenheid van je dataset of train het model opnieuw.' })}</p>
                <div className="widget-meta-row">
                  <span>
                    {t('dashboard.invalidForecast.capacityLabel', { defaultValue: 'Installatievermogen' })}: {installationKwp} kWp
                  </span>
                </div>
              </>
            ) : (
              <>
                <strong>{outputNow}</strong>
                <p>{t('dashboard.info.output')}</p>
                <div className="widget-meta-row">
                  {peakToday ? <span>{t('dashboard.info.peak')}: {peakToday}</span> : null}
                </div>
              </>
            )}
          </article>

          <article className="monitoring-widget weather-widget">
            <div className="widget-heading">
              <p className="widget-label">{t('dashboard.weather.title')}</p>
              <CloudSun size={18} strokeWidth={2.2} />
            </div>
            <strong>{displayedWeather.currentTemperature || '-'}</strong>
            <p>{displayedWeather.cloudStatus || '-'}</p>
            <div className="widget-meta-row">
              <span>{t('dashboard.weather.tomorrow')}</span>
              <span>
                {displayedWeather.tomorrowMin || '-'} - {displayedWeather.tomorrowMax || '-'}
              </span>
            </div>
          </article>

          <article className="monitoring-widget recommendation-widget" aria-label={t('dashboard.action.title', { defaultValue: 'Volgende goede periode' })}>
            <div className="widget-heading">
              <p className="widget-label">{t('dashboard.action.eyebrow')}</p>
              <Lightbulb size={18} strokeWidth={2.2} />
            </div>
            <strong>
              {hasInvalidForecast
                ? t('dashboard.invalidForecast.ctaTitle', { defaultValue: 'Controleer je dataset' })
                : t('dashboard.action.title', { defaultValue: 'Volgende beste productievenster' })}
            </strong>
            <p>
              {hasInvalidForecast
                ? t('dashboard.invalidForecast.text', { defaultValue: 'Controleer de productie-eenheid van je dataset of train het model opnieuw.' })
                : hasStrongWindow
                  ? `${getRelativeDayName(nextWindow.start, timeContext, plannerLabels)} ${nextWindow.label}`
                  : t('dashboard.action.noStrongWindowToday', { defaultValue: 'Vandaag geen sterk productievenster meer' })}
            </p>
            <button
              className="page-primary-cta inline-cta"
              onClick={() => onNavigate(hasInvalidForecast ? 'dataManagement' : 'assistant')}
              type="button"
            >
              {hasInvalidForecast
                ? t('dashboard.invalidForecast.cta', { defaultValue: 'Dataset controleren' })
                : t(hasStrongWindow ? 'dashboard.action.openPlanner' : 'dashboard.action.planTomorrow', {
                    defaultValue: hasStrongWindow ? 'Open planner' : 'Plan voor morgen',
                  })}
              <ArrowRight size={17} strokeWidth={2.2} />
            </button>
          </article>
        </section>
      )}

      {!isTrainingGuarded && hasProductionData && !hasInvalidForecast && (
        <PredictionChart className="monitoring-chart-panel" data={chartData} unit={forecastUnit} />
      )}

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

function mapWeather(dashboard, t) {
  const tomorrowMin = formatTemperature(dashboard?.tomorrow_weather?.min_temperature_c)
  const tomorrowMax = formatTemperature(dashboard?.tomorrow_weather?.max_temperature_c)

  return {
    ...weather,
    currentTemperature: formatTemperature(dashboard?.current_weather?.temperature_c),
    cloudStatus: mapWeatherLabel(dashboard?.current_weather?.status, t),
    tomorrowMin: tomorrowMin?.replace(' °C', '') || null,
    tomorrowMax: tomorrowMax?.replace(' °C', '') || null,
  }
}

function mapInstallationInfo(user, installation, t) {
  const panelCount = installation?.panelCount || user?.panelCount
  const installationKwp = installation?.installationKwp || user?.installationKwp

  return {
    panelSummary: installation?.name || t('dashboard.installation.profileFallback'),
    location: [installation?.city, formatCountryLabel(installation?.country, t)].filter(Boolean).join(', ') || user?.location || '-',
    panelCount: panelCount ? `${panelCount} ${t('dashboard.installation.panelsUnit')}` : null,
    power: installationKwp ? `${installationKwp} kWp` : null,
  }
}

function mapForecastForChart(forecast, timeContext, locale, labels, unit) {
  return forecast
    .map((entry) => ({
      label: `${getRelativeDayName(entry.timestamp, timeContext, labels)} ${formatTimeInZone(entry.timestamp, timeContext.timezone, locale)}`,
      value: convertWattsToUnit(entry?.predicted_w ?? entry?.value_w ?? 0, unit),
    }))
    .filter((entry) => Number.isFinite(entry.value) && entry.value >= 0)
}

function getPeakTodayWatts(forecast, serverTime, timezone) {
  const todayKey = getDateKey(serverTime, timezone)
  const todayEntries = forecast.filter((entry) => getDateKey(entry.timestamp, timezone) === todayKey)

  if (!todayEntries.length) {
    return null
  }

  return todayEntries.reduce((peak, entry) => {
    const value = Number(entry?.predicted_w ?? entry?.value_w ?? 0)
    return Number.isFinite(value) && value > peak ? value : peak
  }, 0)
}

function chooseNextBestWindow(todayWindows, allWindows) {
  if (todayWindows.length > 0) {
    return todayWindows[0]
  }

  const tomorrowWindow = allWindows[0] || null
  const dayAfterTomorrowWindow = allWindows[1] || null

  if (!tomorrowWindow) {
    return dayAfterTomorrowWindow
  }

  if (!dayAfterTomorrowWindow) {
    return tomorrowWindow
  }

  return dayAfterTomorrowWindow.predictedW > tomorrowWindow.predictedW * 1.15
    ? dayAfterTomorrowWindow
    : tomorrowWindow
}

