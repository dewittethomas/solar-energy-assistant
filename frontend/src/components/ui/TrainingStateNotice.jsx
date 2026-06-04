import { AlertTriangle, ArrowRight, RefreshCw } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export function TrainingStateNotice({ modelState, onNavigate, trainingRunId }) {
  const { t } = useTranslation()

  if (modelState === 'training') {
    return (
      <section className="training-guard-state" aria-live="polite">
        <span className="training-guard-icon processing" aria-hidden="true">
          <RefreshCw size={24} strokeWidth={2.2} />
        </span>
        <div>
          <h2>{t('training.guard.title')}</h2>
          <p>{t('training.guard.text')}</p>
        </div>
        <button
          className="page-primary-cta inline-cta"
          onClick={() => onNavigate('training', { trainingRunId })}
          type="button"
        >
          {t('training.guard.button')}
          <ArrowRight size={17} strokeWidth={2.2} />
        </button>
      </section>
    )
  }

  if (modelState === 'failed') {
    return (
      <section className="training-guard-state failed" aria-live="polite">
        <span className="training-guard-icon failed" aria-hidden="true">
          <AlertTriangle size={24} strokeWidth={2.2} />
        </span>
        <div>
          <h2>{t('training.failed.title')}</h2>
          <p>{t('training.failed.text')}</p>
        </div>
        <button className="page-primary-cta inline-cta" onClick={() => onNavigate('dataManagement')} type="button">
          {t('training.failed.retry')}
          <ArrowRight size={17} strokeWidth={2.2} />
        </button>
      </section>
    )
  }

  return null
}
