import { useEffect, useState } from 'react'
import { Activity, BarChart3, Brain, Database } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client.js'
import { NoProductionDataState } from '../components/ui/NoProductionDataState.jsx'
import { PageHeading } from '../components/ui/PageHeading.jsx'
import { TrainingStateNotice } from '../components/ui/TrainingStateNotice.jsx'
import { models } from '../data/fallbackManagementData.js'
import { formatAccuracyPercent, formatDatasetDisplayName, formatModelDisplayName } from '../utils/presentation.js'

export function ModelsPage({ datasetState, modelState, onNavigate, trainingRunId, user }) {
  const { t } = useTranslation()
  const hasProductionData = Boolean(datasetState?.hasProductionData)
  const isLoading = Boolean(datasetState?.isLoading)
  const [availableModels, setAvailableModels] = useState(models)
  const [activeModelId, setActiveModelId] = useState(models[0]?.id)
  const activeModel = availableModels.find((model) => model.id === activeModelId) || availableModels[0]
  const isTrainingGuarded = ['training', 'failed'].includes(modelState)

  useEffect(() => {
    if (!user?.installationId || !hasProductionData) {
      return
    }

    api
      .listModels(user.installationId)
      .then((result) => {
        const mappedModels = result.map((model) => mapModel(model, t))
        setAvailableModels(mappedModels.length ? mappedModels : models)
        setActiveModelId(mappedModels.find((model) => model.isActive)?.id || mappedModels[0]?.id || models[0]?.id)
      })
      .catch(() => setAvailableModels(models))
  }, [hasProductionData, t, user?.installationId])

  async function activateModel(modelId) {
    setActiveModelId(modelId)

    try {
      const activatedModel = await api.activateModel(modelId)
      setAvailableModels((currentModels) =>
        currentModels.map((model) => ({
          ...model,
          isActive: model.id === activatedModel.id,
        })),
      )
    } catch {
      setAvailableModels((currentModels) =>
        currentModels.map((model) => ({
          ...model,
          isActive: model.id === modelId,
        })),
      )
    }
  }

  return (
    <>
      <PageHeading eyebrow={t('pages.models.eyebrow')} title={t('pages.models.title')} />

      {isTrainingGuarded && (
        <TrainingStateNotice modelState={modelState} onNavigate={onNavigate} trainingRunId={trainingRunId} />
      )}

      {!isTrainingGuarded && !isLoading && !hasProductionData && (
        <NoProductionDataState
          messageKey="pages.models.empty.text"
          onUpload={() => onNavigate('dataManagement')}
          titleKey="pages.models.empty.title"
          titleDefault="Nog geen model beschikbaar"
        />
      )}

      {!isTrainingGuarded && hasProductionData && (
        <section className="model-overview-panel" aria-label={t('pages.models.listLabel')}>
          <article className="active-model-summary">
            <div className="active-model-heading">
              <span className="settings-icon weather-icon" aria-hidden="true">
                <Brain size={24} strokeWidth={2.2} />
              </span>
              <div>
                <p className="eyebrow">{t('pages.models.activeTitle')}</p>
                <h2>{activeModel?.name}</h2>
                <p>{t('pages.models.text')}</p>
              </div>
              <span className="status-badge ready">{t('pages.models.enabled')}</span>
            </div>

            <dl className="model-summary-metrics">
              {activeModel?.accuracyValue ? (
                <div>
                  <dt>
                    <BarChart3 size={16} strokeWidth={2.2} />
                    {t(activeModel.accuracyLabelKey)}
                  </dt>
                  <dd>{activeModel.accuracyValue}</dd>
                </div>
              ) : null}
              <div>
                <dt>
                  <Activity size={16} strokeWidth={2.2} />
                  {t('pages.models.mse')}
                </dt>
                <dd>
                  {activeModel?.mse || t('pages.models.notAvailable', { defaultValue: 'Nog niet beschikbaar' })}
                  <small>{t('pages.models.errorHelp')}</small>
                </dd>
              </div>
              {activeModel?.datasetLabel ? (
                <div>
                  <dt>
                    <Database size={16} strokeWidth={2.2} />
                    {t('pages.models.dataset')}
                  </dt>
                  <dd>{activeModel.datasetLabel}</dd>
                </div>
              ) : null}
            </dl>

            <div className="model-action-row stacked-model-actions">
              <details className="advanced-details">
                <summary>{t('pages.models.advanced.title')}</summary>
                <dl>
                  <div>
                    <dt>{t('pages.models.advanced.trainingDate')}</dt>
                    <dd>{activeModel?.trainedOn}</dd>
                  </div>
                  <div>
                    <dt>{t('pages.models.advanced.metadata')}</dt>
                    <dd>{activeModel?.metadata}</dd>
                  </div>
                  <div>
                    <dt>{t('pages.models.advanced.version')}</dt>
                    <dd>{activeModel?.version}</dd>
                  </div>
                  <div>
                    <dt>{t('pages.models.accuracyHelpTitle')}</dt>
                    <dd>{t('pages.models.accuracyHelp')}</dd>
                  </div>
                  <div>
                    <dt>{t('pages.models.errorHelpTitle')}</dt>
                    <dd>{t('pages.models.errorHelp')}</dd>
                  </div>
                </dl>
              </details>
            </div>
          </article>

          <div className="model-comparison-section">
            <div>
              <h2>{t('pages.models.comparisonTitle')}</h2>
              <p>{t('pages.models.comparisonText')}</p>
            </div>

            <div className="dataset-table-wrap">
              <table className="dataset-table model-comparison-table">
                <thead>
                  <tr>
                    <th>{t('pages.models.table.model')}</th>
                    <th>{t('pages.models.accuracyColumn', { defaultValue: 'Nauwkeurigheid' })}</th>
                    <th>{t('pages.models.mse')}</th>
                    <th>{t('pages.models.dataset')}</th>
                    <th>{t('pages.models.table.status')}</th>
                  </tr>
                </thead>
                <tbody>
                  {availableModels.map((model) => {
                    const isActive = activeModelId === model.id

                    return (
                      <tr key={model.id}>
                        <td className="model-name-cell">
                          <strong>{model.name}</strong>
                        </td>
                        <td>{model.accuracyValue || t('pages.models.notAvailable', { defaultValue: 'Nog niet beschikbaar' })}</td>
                        <td>{model.mse || t('pages.models.notAvailable', { defaultValue: 'Nog niet beschikbaar' })}</td>
                        <td>{model.datasetLabel || t('pages.models.hiddenDataset', { defaultValue: 'Geavanceerde details' })}</td>
                        <td className="model-status-cell">
                          {isActive ? (
                            <span className="status-badge ready model-status">{t('pages.models.enabled')}</span>
                          ) : (
                            <button
                              aria-label={t('pages.models.activateModel', { model: model.name })}
                              className="secondary-action-button model-action-button"
                              onClick={() => activateModel(model.id)}
                              type="button"
                            >
                              {t('pages.models.disabled')}
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}
    </>
  )
}

function mapModel(model, t) {
  const accuracyMetric =
    Number.isFinite(Number(model.r2)) && Number(model.r2) >= 0
      ? { labelKey: 'pages.models.r2', value: formatAccuracyPercent(model.r2, t) }
      : Number.isFinite(Number(model.accuracy)) && Number(model.accuracy) >= 0
        ? { labelKey: 'pages.models.r2', value: formatAccuracyPercent(model.accuracy, t) }
        : null

  return {
    id: model.id,
    name: formatModelDisplayName(model, t),
    dataset: model.dataset_id,
    datasetLabel: formatDatasetDisplayName(model, t),
    trainedOn: model.created_at,
    metadata: model.metadata || model.model_type || t('pages.models.advanced.defaultMetadata', { defaultValue: 'Configured forecasting model' }),
    version: model.version || 'v1.0',
    accuracyLabelKey: accuracyMetric?.labelKey,
    accuracyValue: accuracyMetric?.value || null,
    mse:
      Number.isFinite(Number(model.offset_kw)) && Number(model.offset_kw) > 0
        ? `${Number(model.offset_kw).toFixed(2)} kW`
        : Number.isFinite(Number(model.mae)) && Number(model.mae) > 0
          ? `${Number(model.mae).toFixed(2)} kW`
          : Number.isFinite(Number(model.rmse)) && Number(model.rmse) > 0
            ? `${Number(model.rmse).toFixed(2)} kW`
            : null,
    isActive: model.is_active,
  }
}
