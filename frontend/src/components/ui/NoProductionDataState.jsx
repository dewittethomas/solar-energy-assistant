import { FileSpreadsheet, UploadCloud } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { UploadDatasetButton } from './UploadDatasetButton.jsx'

export function NoProductionDataState({
  messageKey = 'common.noProductionData.text',
  onUpload,
  titleKey = 'common.noProductionData.title',
  titleDefault = 'Nog geen productiegegevens beschikbaar',
}) {
  const { t } = useTranslation()

  return (
    <section className="empty-state production-empty-state">
      <div className="dataset-empty-illustration" aria-hidden="true">
        <FileSpreadsheet size={38} strokeWidth={1.9} />
        <UploadCloud size={26} strokeWidth={2.2} />
      </div>
      <h2>{t(titleKey, { defaultValue: titleDefault })}</h2>
      <p>{t(messageKey)}</p>
      <UploadDatasetButton onClick={onUpload} />
    </section>
  )
}
