import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle2, FileSpreadsheet, RefreshCw, UploadCloud } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client.js'
import { UploadDatasetButton } from '../components/ui/UploadDatasetButton.jsx'
import { PageHeading } from '../components/ui/PageHeading.jsx'
import { formatDatasetDisplayName, formatUiDate, formatUiDateRange } from '../utils/presentation.js'

const unitOptions = ['W', 'kW', 'Wh', 'kWh']

export function DataManagementPage({ onInspectDataset, onNavigate, onStartTraining, onUploadDataset, user }) {
  const { i18n, t } = useTranslation()
  const locale = i18n.language === 'fr' ? 'fr-BE' : i18n.language === 'en' ? 'en-GB' : 'nl-BE'
  const [apiDatasets, setApiDatasets] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [inspection, setInspection] = useState(null)
  const [mapping, setMapping] = useState(createEmptyMapping())
  const [uploadStatus, setUploadStatus] = useState('empty')
  const [uploadMessage, setUploadMessage] = useState('')
  const [retrainingDatasetId, setRetrainingDatasetId] = useState(null)

  useEffect(() => {
    if (!user?.installationId) {
      return
    }

    setIsLoading(true)
    api
      .listDatasets(user.installationId)
      .then((result) => setApiDatasets(result.map((dataset) => mapDataset(dataset, t, locale))))
      .catch(() => setApiDatasets([]))
      .finally(() => setIsLoading(false))
  }, [locale, t, user?.installationId])

  const previewRows = useMemo(() => buildPreviewRows(inspection?.preview_rows || [], mapping), [inspection?.preview_rows, mapping])
  const canUpload = Boolean(selectedFile && mapping.date_column && mapping.measurement_column && mapping.unit)
  const currentStateLabel = resolveStateLabel(uploadStatus, t)

  async function handleFile(file) {
    if (!file) {
      return
    }

    setSelectedFile(file)
    setInspection(null)
    setMapping(createEmptyMapping())
    setUploadMessage('')
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadStatus('error')
      setUploadMessage(t('pages.dataManagement.upload.invalidType'))
      return
    }

    setUploadStatus('validating')
    setUploadMessage(t('pages.dataManagement.upload.inspecting', { defaultValue: 'Kolommen lezen...' }))

    try {
      const result = await onInspectDataset(file)
      const suggestedMapping = inferMapping(result.columns || [])
      setInspection(result)
      setMapping(suggestedMapping)

      if (suggestedMapping.date_column && suggestedMapping.measurement_column && suggestedMapping.unit) {
        setUploadStatus('ready')
        setUploadMessage(
          t('pages.dataManagement.upload.ready', {
            defaultValue: 'Dataset is klaar om toegevoegd te worden.',
          }),
        )
        return
      }

      setUploadStatus('mapping')
      setUploadMessage(
        suggestedMapping.date_column
          ? t('pages.dataManagement.upload.productionRecognitionFailed', {
              defaultValue:
                'SolarWise kon de productiekolom niet automatisch herkennen. Controleer de geselecteerde kolommen.',
            })
          : t('pages.dataManagement.upload.dateRecognitionFailed', {
              defaultValue:
                'SolarWise kon de datumkolom niet automatisch herkennen. Kies hieronder welke kolom de datum en tijd bevat.',
            }),
      )
    } catch (error) {
      setUploadStatus('error')
      setUploadMessage(mapFriendlyError(error.message, t))
    }
  }

  async function uploadDataset() {
    if (!canUpload) {
      return
    }

    setUploadStatus('uploading')
    setUploadMessage(t('pages.dataManagement.upload.uploading'))

    try {
      const uploadedDataset = await onUploadDataset({
        file: selectedFile,
        installationId: user.installationId,
        mapping,
      })

      setApiDatasets((currentDatasets) => upsertDataset(currentDatasets, mapDataset(uploadedDataset, t, locale)))
      setUploadStatus(uploadedDataset?.dataset_already_exists ? 'warning' : 'success')
      setUploadMessage(
        uploadedDataset?.dataset_already_exists
          ? t('pages.dataManagement.upload.alreadyUploaded', {
              defaultValue: 'This dataset was already uploaded.',
            })
          : t('pages.dataManagement.upload.uploadedSuccessfully', {
              defaultValue: 'Dataset uploaded successfully.',
            }),
      )
      setSelectedFile(null)
      setInspection(null)
      setMapping(createEmptyMapping())
      await wait(900)
      await onStartTraining?.(uploadedDataset)
    } catch (error) {
      setUploadStatus('error')
      setUploadMessage(mapFriendlyError(error.message, t))
    }
  }

  async function retrainDataset(dataset) {
    setRetrainingDatasetId(dataset.id)

    try {
      const trainingRun = await api.trainModelFromParquet(dataset.path)

      if (trainingRun?.training_run_id) {
        onNavigate('training', { trainingRunId: trainingRun.training_run_id })
      }
    } catch (error) {
      setUploadStatus('error')
      setUploadMessage(error.message || t('pages.dataManagement.retrainFailed'))
    } finally {
      setRetrainingDatasetId(null)
    }
  }

  function updateMapping(key, value) {
    const nextValue = value === '__none__' ? null : value
    const nextMapping = { ...mapping, [key]: nextValue }
    setMapping(nextMapping)

    if (nextMapping.date_column && nextMapping.measurement_column && nextMapping.unit) {
      setUploadStatus('ready')
      setUploadMessage(
        t('pages.dataManagement.upload.ready', {
          defaultValue: 'Dataset is klaar om toegevoegd te worden.',
        }),
      )
      return
    }

    if (inspection) {
      setUploadStatus('mapping')
      setUploadMessage(
        t('pages.dataManagement.upload.mappingIncomplete', {
          defaultValue: 'Controleer de geselecteerde kolommen.',
        }),
      )
    }
  }

  return (
    <>
      <PageHeading eyebrow={t('pages.dataManagement.eyebrow')} title={t('pages.dataManagement.title')} />

      <section className="dataset-page-panel" aria-label={t('pages.dataManagement.listLabel')}>
        {(apiDatasets.length > 0 || isLoading) && (
          <div className="dataset-toolbar">
            <div>
              <h2>{t('pages.dataManagement.listTitle')}</h2>
              <p>{t('pages.dataManagement.text')}</p>
            </div>
            {apiDatasets.length > 0 && <UploadDatasetButton onClick={() => setShowUpload((value) => !value)} />}
          </div>
        )}

        {!isLoading && apiDatasets.length > 0 && (
          <article className="active-model-summary dataset-summary-card">
            <div className="active-model-heading">
              <span className="settings-icon solar-icon" aria-hidden="true">
                <FileSpreadsheet size={24} strokeWidth={2.2} />
              </span>
              <div>
                <p className="eyebrow">{t('pages.dataManagement.summary.eyebrow', { defaultValue: 'Actieve dataset' })}</p>
                <h2>{apiDatasets[0].name}</h2>
                <p>{formatUiDateRange(apiDatasets[0].periodStart, apiDatasets[0].periodEnd, locale)}</p>
              </div>
              <span className={`status-badge ${apiDatasets[0].status}`}>{t(apiDatasets[0].statusKey)}</span>
            </div>

            <dl className="model-summary-metrics">
              <div>
                <dt>{t('pages.dataManagement.rows')}</dt>
                <dd>{apiDatasets[0].rows}</dd>
              </div>
              <div>
                <dt>{t('pages.dataManagement.summary.unit', { defaultValue: 'Eenheid' })}</dt>
                <dd>{apiDatasets[0].unit || '-'}</dd>
              </div>
              <div>
                <dt>{t('pages.dataManagement.summary.uploadedAt', { defaultValue: 'Geüpload op' })}</dt>
                <dd>{formatUiDate(apiDatasets[0].createdAt, locale)}</dd>
              </div>
            </dl>
          </article>
        )}

        {showUpload && (
          <section className="upload-card guided-upload-card" aria-label={t('pages.dataManagement.upload.title')}>
            <div className="upload-step-header">
              <span className="upload-step-index">1</span>
              <div>
                <strong>{t('pages.dataManagement.upload.title')}</strong>
                <p>{currentStateLabel}</p>
              </div>
            </div>

            <label className={uploadStatus === 'error' ? 'upload-dropzone error' : 'upload-dropzone'}>
              <input
                accept=".csv,text/csv"
                onChange={(event) => handleFile(event.target.files?.[0])}
                type="file"
              />
              <UploadCloud size={30} strokeWidth={2.1} />
              <strong>{t('pages.dataManagement.upload.dropTitle')}</strong>
              <span>{t('pages.dataManagement.upload.browse')}</span>
              <small>{t('pages.dataManagement.upload.format')}</small>
            </label>

            {selectedFile && (
              <div className="file-preview">
                <FileSpreadsheet size={22} strokeWidth={2.2} />
                <div>
                  <strong>{selectedFile.name}</strong>
                  <span>{formatFileSize(selectedFile.size)}</span>
                </div>
              </div>
            )}

            {inspection && (
              <div className="column-preview upload-preview-card">
                <span>{t('pages.dataManagement.upload.previewFile', { defaultValue: 'Bestand' })}: {inspection.filename}</span>
                <strong>{t('pages.dataManagement.upload.previewRows', { count: previewRows.length || 5, defaultValue: '{{count}} voorbeeldrijen geladen' })}</strong>
              </div>
            )}

            {uploadMessage && (
              <div className={`validation-message ${uploadStatus}`}>
                {['error', 'warning'].includes(uploadStatus) ? (
                  <AlertTriangle size={17} strokeWidth={2.2} />
                ) : (
                  <CheckCircle2 size={17} strokeWidth={2.2} />
                )}
                <span>{uploadMessage}</span>
              </div>
            )}

            {inspection?.columns?.length > 0 && (
              <>
                <div className="upload-step-header">
                  <span className="upload-step-index">2</span>
                  <div>
                    <strong>{t('pages.dataManagement.upload.mappingTitle', { defaultValue: 'Kolommen koppelen' })}</strong>
                    <p>
                      {t('pages.dataManagement.upload.mappingText', {
                        defaultValue: 'Kies welke kolommen de datum, tijd en productie bevatten.',
                      })}
                    </p>
                  </div>
                </div>

                <div className="column-preview">
                  <span>{t('pages.dataManagement.upload.columns')}</span>
                  <div>
                    {inspection.columns.map((column) => (
                      <strong key={column}>{column}</strong>
                    ))}
                  </div>
                </div>

                <div className="mapping-grid">
                  <label className="configuration-field">
                    <span>{t('pages.dataManagement.upload.dateColumn', { defaultValue: 'Datum-kolom *' })}</span>
                    <select onChange={(event) => updateMapping('date_column', event.target.value)} value={mapping.date_column ?? ''}>
                      <option value="">{t('pages.dataManagement.upload.selectColumn', { defaultValue: 'Kies een kolom' })}</option>
                      {inspection.columns.map((column) => (
                        <option key={column} value={column}>
                          {column}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="configuration-field">
                    <span>{t('pages.dataManagement.upload.timeColumn', { defaultValue: 'Tijd-kolom' })}</span>
                    <select onChange={(event) => updateMapping('time_column', event.target.value)} value={mapping.time_column ?? '__none__'}>
                      <option value="__none__">
                        {t('pages.dataManagement.upload.noSeparateTimeColumn', { defaultValue: 'Geen aparte tijdkolom' })}
                      </option>
                      {inspection.columns.map((column) => (
                        <option key={column} value={column}>
                          {column}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="configuration-field">
                    <span>{t('pages.dataManagement.upload.productionColumn', { defaultValue: 'Productie-kolom *' })}</span>
                    <select
                      onChange={(event) => updateMapping('measurement_column', event.target.value)}
                      value={mapping.measurement_column ?? ''}
                    >
                      <option value="">{t('pages.dataManagement.upload.selectColumn', { defaultValue: 'Kies een kolom' })}</option>
                      {inspection.columns.map((column) => (
                        <option key={column} value={column}>
                          {column}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="configuration-field">
                    <span>{t('pages.dataManagement.upload.productionUnit', { defaultValue: 'Productie-eenheid *' })}</span>
                    <small className="field-helper-text">
                      {t('pages.dataManagement.upload.productionUnitHelp', {
                        defaultValue: 'Is je productie gemeten in W, kW, Wh of kWh?',
                      })}
                    </small>
                    <select onChange={(event) => updateMapping('unit', event.target.value)} value={mapping.unit ?? ''}>
                      <option value="">{t('pages.dataManagement.upload.selectUnit', { defaultValue: 'Kies een eenheid' })}</option>
                      {unitOptions.map((unit) => (
                        <option key={unit} value={unit}>
                          {unit}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <div className="validation-message ready">
                  <CheckCircle2 size={17} strokeWidth={2.2} />
                  <span>
                    {mapping.date_column
                      ? t('pages.dataManagement.upload.dateDetected', { defaultValue: 'Datum kolom gevonden' })
                      : t('pages.dataManagement.upload.mappingMissing', { defaultValue: 'Controleer de geselecteerde kolommen.' })}
                    {' · '}
                    {mapping.measurement_column
                      ? t('pages.dataManagement.upload.productionDetected', { defaultValue: 'Productie kolom gevonden' })
                      : t('pages.dataManagement.upload.mappingMissing', { defaultValue: 'Controleer de geselecteerde kolommen.' })}
                  </span>
                </div>
              </>
            )}

            {previewRows.length > 0 && (
              <>
                <div className="upload-step-header">
                  <span className="upload-step-index">3</span>
                  <div>
                    <strong>{t('pages.dataManagement.upload.previewTitle', { defaultValue: 'Preview' })}</strong>
                    <p>
                      {t('pages.dataManagement.upload.previewText', {
                        defaultValue: 'Controleer de eerste rijen voordat je het dataset toevoegt.',
                      })}
                    </p>
                  </div>
                </div>

                <div className="preview-table-wrap">
                  <table className="preview-table">
                    <thead>
                      <tr>
                        <th>{t('pages.dataManagement.upload.previewDatetime', { defaultValue: 'Datum/tijd' })}</th>
                        <th>{t('pages.dataManagement.upload.previewProduction', { defaultValue: 'Productie' })}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewRows.map((row, index) => (
                        <tr key={`${row.datetime}-${index}`}>
                          <td>{row.datetime || '-'}</td>
                          <td>{row.production || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}

            <button
              className="primary-action-button upload-button"
              disabled={!canUpload || uploadStatus === 'uploading'}
              onClick={uploadDataset}
              type="button"
            >
              {uploadStatus === 'uploading' ? (
                <RefreshCw className="spin-icon" size={17} strokeWidth={2.2} />
              ) : (
                <UploadCloud size={18} strokeWidth={2.4} />
              )}
              {uploadStatus === 'uploading'
                ? t('pages.dataManagement.upload.uploadingShort')
                : t('pages.dataManagement.upload.confirm')}
            </button>
          </section>
        )}

        {isLoading && <p className="muted-message">{t('pages.dataManagement.loading')}</p>}

        {!isLoading && apiDatasets.length === 0 && !showUpload && (
          <section className="empty-state">
            <div className="dataset-empty-illustration" aria-hidden="true">
              <FileSpreadsheet size={38} strokeWidth={1.9} />
              <UploadCloud size={26} strokeWidth={2.2} />
            </div>
            <h2>{t('pages.dataManagement.empty.title')}</h2>
            <p>{t('pages.dataManagement.empty.text')}</p>
            <div className="empty-benefits">
              <span>
                <CheckCircle2 size={15} strokeWidth={2.4} />
                {t('pages.dataManagement.empty.benefits.forecasts')}
              </span>
              <span>
                <CheckCircle2 size={15} strokeWidth={2.4} />
                {t('pages.dataManagement.empty.benefits.recommendations')}
              </span>
              <span>
                <CheckCircle2 size={15} strokeWidth={2.4} />
                {t('pages.dataManagement.empty.benefits.analysis')}
              </span>
            </div>
            <UploadDatasetButton onClick={() => setShowUpload(true)} />
          </section>
        )}

        {!isLoading && apiDatasets.length > 0 && (
          <div className="dataset-table-wrap">
            <table className="dataset-table">
              <thead>
                <tr>
                  <th>{t('pages.dataManagement.table.dataset')}</th>
                  <th>{t('pages.dataManagement.rows')}</th>
                  <th>{t('pages.dataManagement.summary.unit', { defaultValue: 'Eenheid' })}</th>
                  <th>{t('pages.dataManagement.dateRange')}</th>
                  <th>{t('pages.dataManagement.table.status')}</th>
                  <th>{t('pages.dataManagement.table.action')}</th>
                </tr>
              </thead>
              <tbody>
                {apiDatasets.map((dataset) => (
                  <tr key={dataset.rawId}>
                    <td>
                      <strong>{dataset.name}</strong>
                      <details className="advanced-details">
                        <summary>{t('pages.dataManagement.advanced.title')}</summary>
                        <dl>
                          <div>
                            <dt>{t('pages.dataManagement.advanced.originalFile', { defaultValue: 'Originele bestandsnaam' })}</dt>
                            <dd>{dataset.sourceName || '-'}</dd>
                          </div>
                          <div>
                            <dt>{t('pages.dataManagement.advanced.originalColumns', { defaultValue: 'Originele kolommen' })}</dt>
                            <dd>{dataset.originalColumns.length ? dataset.originalColumns.join(', ') : '-'}</dd>
                          </div>
                          <div>
                            <dt>{t('pages.dataManagement.advanced.dateColumn', { defaultValue: 'Datumkolom' })}</dt>
                            <dd>{dataset.dateColumn || '-'}</dd>
                          </div>
                          <div>
                            <dt>{t('pages.dataManagement.advanced.measurementColumn', { defaultValue: 'Productiekolom' })}</dt>
                            <dd>{dataset.measurementColumn || '-'}</dd>
                          </div>
                          <div>
                            <dt>{t('pages.dataManagement.advanced.unit', { defaultValue: 'Productie-eenheid' })}</dt>
                            <dd>{dataset.unit || '-'}</dd>
                          </div>
                          <div>
                            <dt>{t('pages.dataManagement.advanced.hash')}</dt>
                            <dd>{dataset.hash}</dd>
                          </div>
                        </dl>
                      </details>
                    </td>
                    <td>{dataset.rows}</td>
                    <td>{dataset.unit || '-'}</td>
                    <td>{dataset.dateRange}</td>
                    <td>
                      <span className={`status-badge ${dataset.status}`}>{t(dataset.statusKey)}</span>
                    </td>
                    <td>
                      <button
                        className="secondary-action-button"
                        disabled={!dataset.path || retrainingDatasetId === dataset.id}
                        onClick={() => retrainDataset(dataset)}
                        type="button"
                      >
                        {retrainingDatasetId === dataset.id
                          ? t('pages.dataManagement.retraining')
                          : t('pages.dataManagement.retrain')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}

function createEmptyMapping() {
  return {
    date_column: null,
    time_column: null,
    measurement_column: null,
    unit: null,
  }
}

function mapDataset(dataset, t, locale) {
  const status = normalizeStatus(dataset.status || (dataset.used_for_recommendations ? 'used' : 'ready'))
  const rawId = dataset.id || dataset.dataset_id || 'dataset'
  const originalColumns = Array.isArray(dataset.original_columns) ? dataset.original_columns : []
  const internalColumns = Array.isArray(dataset.internal_columns) ? dataset.internal_columns : []

  return {
    id: rawId,
    name: formatDatasetDisplayName(dataset, t),
    rawId,
    path: dataset.path || dataset.parquet_path || null,
    rows: Number(dataset.rows || dataset.row_count || 0).toLocaleString(locale),
    periodStart: dataset.period_start || dataset.created_at || null,
    periodEnd: dataset.period_end || dataset.created_at || null,
    createdAt: dataset.created_at || null,
    dateRange:
      dataset.period_start && dataset.period_end
        ? formatUiDateRange(dataset.period_start, dataset.period_end, locale)
        : dataset.created_at
          ? formatUiDate(dataset.created_at, locale)
          : '-',
    status,
    statusKey: `datasetMeta.status.${status}`,
    hash: dataset.hash || dataset.dataset_hash || `sha256:${String(rawId).slice(-6)}...`,
    sourceName: dataset.source_name || formatDatasetDisplayName(dataset, t),
    originalColumns,
    internalColumns,
    dateColumn: dataset.date_column || null,
    timeColumn: dataset.time_column || null,
    measurementColumn: dataset.measurement_column || null,
    columns: originalColumns.join(', ') || dataset.columns?.join(', ') || '-',
    unit: dataset.production_unit || null,
  }
}

function upsertDataset(currentDatasets, nextDataset) {
  const existingIndex = currentDatasets.findIndex((dataset) => dataset.rawId === nextDataset.rawId)

  if (existingIndex === -1) {
    return [nextDataset, ...currentDatasets]
  }

  const updated = [...currentDatasets]
  updated[existingIndex] = nextDataset
  return updated
}

function inferMapping(columns) {
  const normalizedColumns = columns.map((column) => ({
    original: column,
    normalized: String(column).trim().toLowerCase(),
  }))

  const dateColumn =
    findColumn(normalizedColumns, ['datetime', 'timestamp']) ||
    findColumn(normalizedColumns, ['date', 'datum', 'day'])

  const timeColumn = dateColumn && /(datetime|timestamp)/i.test(dateColumn) ? null : findColumn(normalizedColumns, ['time', 'tijd', 'uur', 'hour'])

  return {
    date_column: dateColumn,
    time_column: timeColumn,
    measurement_column:
      findColumn(normalizedColumns, ['power_w', 'power_kw', 'power', 'production', 'opbrengst', 'vermogen']) ||
      null,
    unit: findUnit(normalizedColumns),
  }
}

function findColumn(columns, patterns) {
  const match = columns.find((column) => patterns.some((pattern) => column.normalized.includes(pattern)))
  return match?.original || null
}

function findUnit(columns) {
  const combined = columns.map((column) => column.normalized).join(' ')

  if (combined.includes('kw')) {
    return 'kW'
  }

  if (combined.includes('power_w') || combined.includes(' watt') || combined.endsWith('w')) {
    return 'W'
  }

  return 'kW'
}

function buildPreviewRows(rows, mapping) {
  if (!mapping.date_column || !mapping.measurement_column) {
    return []
  }

  return rows.slice(0, 5).map((row) => {
    const values = row.values || {}
    const dateValue = values[mapping.date_column] || ''
    const timeValue = mapping.time_column ? values[mapping.time_column] || '' : ''
    const datetime = [dateValue, timeValue].filter(Boolean).join(' ')
    const measurement = values[mapping.measurement_column] || ''

    return {
      datetime,
      production: measurement ? `${measurement} ${mapping.unit || ''}`.trim() : '',
    }
  })
}

function mapFriendlyError(message, t) {
  const normalized = String(message || '').toLowerCase()

  if (normalized.includes("'date'") || normalized.includes('date_column')) {
    return t('pages.dataManagement.upload.dateRecognitionFailed', {
      defaultValue:
        'SolarWise kon de datumkolom niet automatisch herkennen. Kies hieronder welke kolom de datum en tijd bevat.',
    })
  }

  if (normalized.includes('measurement_column') || normalized.includes('power datasets')) {
    return t('pages.dataManagement.upload.productionRecognitionFailed', {
      defaultValue: 'SolarWise kon de productiekolom niet automatisch herkennen. Controleer de geselecteerde kolommen.',
    })
  }

  if (normalized.includes('mapping must') || normalized.includes('missing mapping field')) {
    return t('pages.dataManagement.upload.mappingMissing', {
      defaultValue: 'Controleer de geselecteerde kolommen.',
    })
  }

  return t('pages.dataManagement.upload.invalid')
}

function resolveStateLabel(status, t) {
  if (status === 'uploading') {
    return t('pages.dataManagement.upload.stateUploading', { defaultValue: 'Dataset wordt verwerkt' })
  }

  if (status === 'ready') {
    return t('pages.dataManagement.upload.stateReady', { defaultValue: 'Dataset is klaar om toegevoegd te worden.' })
  }

  if (status === 'mapping') {
    return t('pages.dataManagement.upload.stateMapping', { defaultValue: 'Kolommen koppelen' })
  }

  if (status === 'error') {
    return t('pages.dataManagement.upload.stateFailed', { defaultValue: 'Controleer de geselecteerde kolommen.' })
  }

  if (status === 'warning') {
    return t('pages.dataManagement.upload.stateWarning', { defaultValue: 'Dataset bestaat al' })
  }

  if (status === 'validating') {
    return t('pages.dataManagement.upload.stateValidating', { defaultValue: 'CSV wordt gecontroleerd' })
  }

  if (status === 'success') {
    return t('pages.dataManagement.upload.stateSuccess', { defaultValue: 'SolarWise analyseert je productiegegevens.' })
  }

  return t('pages.dataManagement.upload.stateEmpty', {
    defaultValue: 'Sleep je CSV hierheen of klik om te bladeren.',
  })
}

function normalizeStatus(status) {
  const normalized = String(status).toLowerCase()

  if (normalized.includes('process')) {
    return 'processing'
  }

  if (normalized.includes('error') || normalized.includes('fail')) {
    return 'error'
  }

  if (normalized.includes('used') || normalized.includes('recommend')) {
    return 'used'
  }

  return 'ready'
}

function formatFileSize(size) {
  if (size < 1024 * 1024) {
    return `${Math.max(1, Math.round(size / 1024))} KB`
  }

  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
