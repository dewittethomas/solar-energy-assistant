import { useEffect, useMemo, useState } from 'react'
import { CalendarDays, Clock3, Sparkles, SunMedium, TrendingUp } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client.js'
import { ProductionMiniChart } from '../components/dashboard/ProductionMiniChart.jsx'
import { NoProductionDataState } from '../components/ui/NoProductionDataState.jsx'
import { PageHeading } from '../components/ui/PageHeading.jsx'
import { TrainingStateNotice } from '../components/ui/TrainingStateNotice.jsx'
import { translateSeason } from '../utils/presentation.js'

const HISTORY_CHART_HEIGHT = 320

export function AnalysisPage({ datasetState, modelState, onNavigate, trainingRunId }) {
  const { i18n, t } = useTranslation()
  const [analytics, setAnalytics] = useState(null)
  const [isAnalyticsLoading, setIsAnalyticsLoading] = useState(false)
  const hasProductionData = datasetState?.datasets?.length > 0
  const locale = i18n.language === 'fr' ? 'fr-BE' : i18n.language === 'en' ? 'en-GB' : 'nl-BE'

  useEffect(() => {
    const primaryDatasetId = datasetState?.datasets?.[0]?.id

    if (!primaryDatasetId || !hasProductionData) {
      setAnalytics(null)
      return
    }

    let isMounted = true
    setIsAnalyticsLoading(true)

    api
      .getDatasetAnalytics(primaryDatasetId)
      .then((result) => {
        if (isMounted) {
          setAnalytics(result)
        }
      })
      .catch(() => {
        if (isMounted) {
          setAnalytics(null)
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsAnalyticsLoading(false)
        }
      })

    return () => {
      isMounted = false
    }
  }, [datasetState?.datasets, hasProductionData])

  const monthlyData = useMemo(() => {
    return (analytics?.monthly_series || []).map((entry) => ({
      ...entry,
      label: formatMonthLabel(entry.label, locale),
    }))
  }, [analytics?.monthly_series, locale])

  const seasonalData = useMemo(
    () =>
      (analytics?.seasonal_series || []).map((entry) => ({
        ...entry,
        label: translateSeason(entry.label, t),
      })),
    [analytics?.seasonal_series, t],
  )

  const chartUnit = analytics?.production_unit || datasetState?.datasets?.[0]?.production_unit || 'kW'
  const isTrainingGuarded = ['training', 'failed'].includes(modelState)

  return (
    <>
      <PageHeading eyebrow={t('pages.analysis.eyebrow')} title={t('pages.analysis.title')} />

      <section className="homeowner-panel">
        <div className="list-panel-header">
          <div>
            <h2>{t('pages.analysis.heading')}</h2>
            <p>{t('pages.analysis.text')}</p>
          </div>
          <Sparkles size={24} strokeWidth={2.2} />
        </div>

        {isTrainingGuarded && (
          <TrainingStateNotice modelState={modelState} onNavigate={onNavigate} trainingRunId={trainingRunId} />
        )}

        {!isTrainingGuarded && isAnalyticsLoading && <p className="muted-message">{t('pages.analysis.loading')}</p>}

        {!isTrainingGuarded && !isAnalyticsLoading && !hasProductionData && (
          <NoProductionDataState messageKey="pages.analysis.empty.text" onUpload={() => onNavigate('dataManagement')} />
        )}

        {!isTrainingGuarded && !isAnalyticsLoading && hasProductionData && analytics && (
          <>
            <div className="analysis-history-layout">
              <article className="analysis-chart-card">
                <div className="analysis-chart-header">
                  <div>
                    <h2>{t('pages.analysis.monthlyChart')}</h2>
                    <p>{t('pages.analysis.monthlyChartSubtitle')}</p>
                  </div>
                </div>
                <ProductionMiniChart
                  data={monthlyData}
                  height={HISTORY_CHART_HEIGHT}
                  unit={chartUnit}
                  xAxisLabel={t('pages.analysis.monthAxis')}
                  yAxisLabel={t('pages.analysis.averageProductionAxis', { unit: chartUnit })}
                />
              </article>
              <article className="analysis-chart-card">
                <div className="analysis-chart-header">
                  <div>
                    <h2>{t('pages.analysis.seasonalChart')}</h2>
                    <p>{t('pages.analysis.seasonalChartSubtitle')}</p>
                  </div>
                </div>
                <ProductionMiniChart
                  data={seasonalData}
                  height={HISTORY_CHART_HEIGHT}
                  unit={chartUnit}
                  xAxisLabel={t('pages.analysis.seasonAxis')}
                  yAxisLabel={t('pages.analysis.averageProductionAxis', { unit: chartUnit })}
                />
              </article>
            </div>

            <section className="ai-insights-card" aria-label={t('pages.analysis.aiInsights')}>
              <div className="settings-card-header">
                <div className="settings-icon solar-icon" aria-hidden="true">
                  <Sparkles size={22} strokeWidth={2.2} />
                </div>
                <div>
                  <h2>{t('pages.analysis.aiInsights')}</h2>
                  <p>{t('pages.analysis.aiText')}</p>
                </div>
              </div>

              <div className="history-insight-grid">
                <article className="insight-card solar-card">
                  <CalendarDays size={24} strokeWidth={2.2} />
                  <span>{t('pages.analysis.bestProductionMonth')}</span>
                  <strong>{formatMonthLabel(analytics.best_month, locale)}</strong>
                </article>
                <article className="insight-card solar-card">
                  <SunMedium size={24} strokeWidth={2.2} />
                  <span>{t('pages.analysis.strongestSeason')}</span>
                  <strong>{translateSeason(analytics.strongest_season, t)}</strong>
                </article>
                <article className="insight-card solar-card">
                  <Clock3 size={24} strokeWidth={2.2} />
                  <span>{t('pages.analysis.bestProductionWindow')}</span>
                  <strong>{analytics.best_window_start} - {analytics.best_window_end}</strong>
                </article>
                <article className="insight-card solar-card">
                  <Clock3 size={24} strokeWidth={2.2} />
                  <span>{t('pages.analysis.peakProductionHour')}</span>
                  <strong>{analytics.peak_hour}</strong>
                </article>
                <article className="insight-card solar-card">
                  <TrendingUp size={24} strokeWidth={2.2} />
                  <span>{t('pages.analysis.summerWinterDifference')}</span>
                  <strong>{analytics.summer_winter_difference_pct > 0 ? '+' : ''}{analytics.summer_winter_difference_pct}%</strong>
                </article>
              </div>
            </section>
          </>
        )}

        {!isTrainingGuarded && !isAnalyticsLoading && hasProductionData && !analytics && (
          <p className="muted-message">{t('pages.analysis.empty.text')}</p>
        )}
      </section>
    </>
  )
}

function formatMonthLabel(label, locale) {
  const months = {
    january: 0,
    february: 1,
    march: 2,
    april: 3,
    may: 4,
    june: 5,
    july: 6,
    august: 7,
    september: 8,
    october: 9,
    november: 10,
    december: 11,
  }
  const monthIndex = months[String(label || '').trim().toLowerCase()]

  if (monthIndex === undefined) {
    const fallback = String(label || '')
    return fallback ? fallback.charAt(0).toUpperCase() + fallback.slice(1).toLowerCase() : fallback
  }

  const formatted = new Intl.DateTimeFormat(locale, { month: 'long' }).format(new Date(Date.UTC(2026, monthIndex, 1)))
  return formatted.charAt(0).toUpperCase() + formatted.slice(1)
}
