import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, ArrowRight, CheckCircle2, Circle, LoaderCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client.js'
import { PageHeading } from '../components/ui/PageHeading.jsx'

const phaseOrder = [
  'queued',
  'validating_dataset',
  'preparing_features',
  'optimizing',
  'training_final_model',
  'evaluating',
  'saving_model',
  'completed',
]

export function TrainingProgressPage({ onNavigate, onTrainingStatusChange, trainingRunId }) {
  const { t } = useTranslation()
  const [trainingRun, setTrainingRun] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (trainingRun?.status !== 'completed') {
      return undefined
    }

    const timeoutId = setTimeout(() => {
      onNavigate('dashboard')
    }, 2000)

    return () => clearTimeout(timeoutId)
  }, [onNavigate, trainingRun?.status])

  useEffect(() => {
    if (!trainingRunId) {
      return undefined
    }

    let isMounted = true
    let intervalId = null

    async function loadTrainingRun() {
      try {
        const result = await api.getTrainingRun(trainingRunId)

        if (!isMounted) {
          return
        }

        setTrainingRun(result)
        setError('')
        onTrainingStatusChange?.(result)

        if (['completed', 'failed'].includes(result.status)) {
          clearInterval(intervalId)
        }
      } catch (caughtError) {
        if (!isMounted) {
          return
        }

        setError(caughtError.message)
      }
    }

    loadTrainingRun()
    intervalId = setInterval(loadTrainingRun, 1500)

    return () => {
      isMounted = false
      clearInterval(intervalId)
    }
  }, [onTrainingStatusChange, trainingRunId])

  const currentPhase = trainingRun?.phase || trainingRun?.status || 'queued'
  const progress = normalizeProgress(trainingRun, currentPhase)
  const isCompleted = trainingRun?.status === 'completed'
  const isFailed = trainingRun?.status === 'failed'
  const phaseIndex = Math.max(phaseOrder.indexOf(currentPhase), 0)
  const technicalDetails = useMemo(() => buildTechnicalDetails(trainingRun, t), [t, trainingRun])

  if (isCompleted) {
    return (
      <section className="training-page">
        <article className="training-status-card success">
          <CheckCircle2 size={42} strokeWidth={2.1} />
          <div>
            <h1>{t('training.completed.title')}</h1>
            <p>{t('training.completed.text', { defaultValue: 'SolarWise heeft je productiegegevens verwerkt en een voorspellingsmodel aangemaakt. Je wordt doorgestuurd naar je overzicht.' })}</p>
          </div>
          <ul className="training-success-list">
            <li><CheckCircle2 size={18} strokeWidth={2.2} />{t('training.completed.checklist.dataset', { defaultValue: 'Productiegegevens verwerkt' })}</li>
            <li><CheckCircle2 size={18} strokeWidth={2.2} />{t('training.completed.checklist.model', { defaultValue: 'Voorspellingsmodel getraind' })}</li>
            <li><CheckCircle2 size={18} strokeWidth={2.2} />{t('training.completed.checklist.forecast', { defaultValue: 'Voorspellingen klaar' })}</li>
          </ul>
          <div className="training-action-row">
            <button className="page-primary-cta inline-cta" onClick={() => onNavigate('dashboard')} type="button">
              {t('training.completed.overview', { defaultValue: 'Open overzicht' })}
              <ArrowRight size={17} strokeWidth={2.2} />
            </button>
            <button className="secondary-action-button" onClick={() => onNavigate('assistant')} type="button">
              {t('training.completed.openPlanner', { defaultValue: 'Open planner' })}
            </button>
          </div>
        </article>
      </section>
    )
  }

  if (isFailed) {
    return (
      <section className="training-page">
        <article className="training-status-card failed">
          <AlertTriangle size={42} strokeWidth={2.1} />
          <div>
            <h1>{t('training.failed.title')}</h1>
            <p>{t('training.failed.text')}</p>
            {trainingRun?.error_code && (
              <p className="training-error-code">
                {t(`training.errorCodes.${trainingRun.error_code}`, { defaultValue: trainingRun.error_code })}
              </p>
            )}
          </div>
          <div className="training-action-row">
            <button className="page-primary-cta inline-cta" onClick={() => onNavigate('dataManagement')} type="button">
              {t('training.failed.retry')}
              <ArrowRight size={17} strokeWidth={2.2} />
            </button>
            <button className="secondary-action-button" onClick={() => onNavigate('dataManagement')} type="button">
              {t('training.failed.backToUploads')}
            </button>
          </div>
        </article>
      </section>
    )
  }

  return (
    <>
      <PageHeading eyebrow={t('training.eyebrow')} title={t('training.title')} />
      <section className="training-page">
        <article className="training-card" aria-live="polite">
          <div className="training-card-header">
            <span className="training-spinner" aria-hidden="true">
              <LoaderCircle size={28} strokeWidth={2.2} />
            </span>
            <div>
              <h2>{t('training.subtitle')}</h2>
              <p>{t('training.currentPhase', { phase: t(`training.phases.${currentPhase}`) })}</p>
            </div>
          </div>

          <div className="training-progress-block">
            <div className="training-progress-meta">
              <span>{t('training.progress')}</span>
              <strong>{progress}%</strong>
            </div>
            <div className="training-progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={progress}>
              <span style={{ width: `${progress}%` }} />
            </div>
          </div>

          <ol className="training-phase-list">
            {phaseOrder.map((phase, index) => {
              const state = index < phaseIndex ? 'done' : index === phaseIndex ? 'active' : 'pending'
              const Icon = state === 'done' ? CheckCircle2 : state === 'active' ? LoaderCircle : Circle

              return (
                <li className={`training-phase-item ${state}`} key={phase}>
                  <Icon size={18} strokeWidth={2.2} />
                  <span>{t(`training.phases.${phase}`)}</span>
                </li>
              )
            })}
          </ol>

          {(technicalDetails.length > 0 || error) && (
            <details className="advanced-details training-technical-details">
              <summary>{t('training.technicalDetails')}</summary>
              <dl>
                {technicalDetails.map((detail) => (
                  <div key={detail.label}>
                    <dt>{detail.label}</dt>
                    <dd>{detail.value}</dd>
                  </div>
                ))}
                {error && (
                  <div>
                    <dt>{t('training.pollingError')}</dt>
                    <dd>{error}</dd>
                  </div>
                )}
              </dl>
            </details>
          )}
        </article>
      </section>
    </>
  )
}

function normalizeProgress(trainingRun, phase) {
  if (Number.isFinite(Number(trainingRun?.progress))) {
    return Math.max(0, Math.min(100, Number(trainingRun.progress)))
  }

  const index = Math.max(phaseOrder.indexOf(phase), 0)
  return Math.round((index / (phaseOrder.length - 1)) * 100)
}

function buildTechnicalDetails(trainingRun, t) {
  const details = []

  if (trainingRun?.current_trial && trainingRun?.total_trials) {
    details.push({
      label: t('training.trialLabel'),
      value: t('training.trialValue', {
        current: trainingRun.current_trial,
        total: trainingRun.total_trials,
      }),
    })
  }

  if (trainingRun?.best_rmse !== undefined && trainingRun?.best_rmse !== null) {
    details.push({
      label: t('training.bestRmse'),
      value: Number(trainingRun.best_rmse).toFixed(3),
    })
  }

  return details
}
