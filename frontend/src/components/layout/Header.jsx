import { UserRound } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export function Header() {
  const { t } = useTranslation()

  return (
    <header className="top-header">
      <h1>{t('app.title')}</h1>
      <div className="profile">
        <div className="profile-icon" aria-hidden="true">
          <UserRound size={20} strokeWidth={2.4} />
        </div>
        <strong>{t('profile.name')}</strong>
      </div>
    </header>
  )
}
