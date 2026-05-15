import { useState } from 'react'
import { Activity, BarChart3, CalendarDays, Database, SlidersHorizontal } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { PageHeading } from '../components/ui/PageHeading.jsx'
import { models } from '../data/demoManagementData.js'

export function ModelsPage() {
  const { t } = useTranslation()
  const [activeModelId, setActiveModelId] = useState(models[0]?.id)

  return (
    <>
      <PageHeading eyebrow={t('pages.models.eyebrow')} title={t('pages.models.title')} />

      <section className="list-panel" aria-label={t('pages.models.listLabel')}>
        <div className="list-panel-header">
          <div>
            <h2>{t('pages.models.listTitle')}</h2>
            <p>{t('pages.models.text')}</p>
          </div>
          <SlidersHorizontal size={24} strokeWidth={2.2} />
        </div>

        <div className="vertical-list">
          {models.map((model) => (
            <article className="list-row" key={model.id}>
              <div className="list-row-main">
                <div className="model-row-top">
                  <span className="status-badge">
                    {activeModelId === model.id ? t('pages.models.enabled') : t('pages.models.disabled')}
                  </span>
                  <button
                    aria-label={t('pages.models.activateModel', { model: model.name })}
                    aria-pressed={activeModelId === model.id}
                    className={activeModelId === model.id ? 'model-toggle active' : 'model-toggle'}
                    onClick={() => setActiveModelId(model.id)}
                    type="button"
                  >
                    <span />
                  </button>
                </div>
                <h3>{model.name}</h3>
              </div>

              <dl className="detail-grid model-detail-grid">
                <div>
                  <dt>
                    <BarChart3 size={16} strokeWidth={2.2} />
                    {t('pages.models.r2')}
                  </dt>
                  <dd>{model.r2}</dd>
                </div>
                <div>
                  <dt>
                    <Activity size={16} strokeWidth={2.2} />
                    {t('pages.models.mse')}
                  </dt>
                  <dd>{model.mse}</dd>
                </div>
                <div>
                  <dt>
                    <Database size={16} strokeWidth={2.2} />
                    {t('pages.models.dataset')}
                  </dt>
                  <dd>{model.dataset}</dd>
                </div>
                <div>
                  <dt>
                    <CalendarDays size={16} strokeWidth={2.2} />
                    {t('pages.models.trainedOn')}
                  </dt>
                  <dd>{model.trainedOn}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>
    </>
  )
}
