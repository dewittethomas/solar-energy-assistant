import { CalendarDays, Database, MapPin, Rows3, Timer } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { PageHeading } from '../components/ui/PageHeading.jsx'
import { datasets } from '../data/demoManagementData.js'

export function DataManagementPage() {
  const { t } = useTranslation()

  return (
    <>
      <PageHeading eyebrow={t('pages.dataManagement.eyebrow')} title={t('pages.dataManagement.title')} />

      <section className="list-panel" aria-label={t('pages.dataManagement.listLabel')}>
        <div className="list-panel-header">
          <div>
            <h2>{t('pages.dataManagement.listTitle')}</h2>
            <p>{t('pages.dataManagement.text')}</p>
          </div>
          <Database size={24} strokeWidth={2.2} />
        </div>

        <div className="vertical-list">
          {datasets.map((dataset) => (
            <article className="list-row" key={dataset.id}>
              <div className="list-row-main">
                <span className="status-badge">{t(dataset.statusKey)}</span>
                <h3>{dataset.id}</h3>
              </div>

              <dl className="detail-grid">
                <div>
                  <dt>
                    <MapPin size={16} strokeWidth={2.2} />
                    {t('pages.dataManagement.location')}
                  </dt>
                  <dd>{dataset.location}</dd>
                </div>
                <div>
                  <dt>
                    <Timer size={16} strokeWidth={2.2} />
                    {t('pages.dataManagement.resolution')}
                  </dt>
                  <dd>{t(dataset.resolutionKey)}</dd>
                </div>
                <div>
                  <dt>
                    <Rows3 size={16} strokeWidth={2.2} />
                    {t('pages.dataManagement.rows')}
                  </dt>
                  <dd>{dataset.rows}</dd>
                </div>
                <div>
                  <dt>
                    <CalendarDays size={16} strokeWidth={2.2} />
                    {t('pages.dataManagement.dateRange')}
                  </dt>
                  <dd>{dataset.dateRange}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>
    </>
  )
}
