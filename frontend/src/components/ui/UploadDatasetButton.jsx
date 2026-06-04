import { UploadCloud } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export function UploadDatasetButton({ className = '', onClick, type = 'button' }) {
  const { t } = useTranslation()
  const resolvedClassName = className ? `primary-action-button upload-button ${className}` : 'primary-action-button upload-button'

  return (
    <button className={resolvedClassName} onClick={onClick} type={type}>
      <UploadCloud size={18} strokeWidth={2.4} />
      <span>{t('pages.dataManagement.upload.button')}</span>
    </button>
  )
}
