import { ChevronRight, Home, MapPin, UserRound } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { countryCodeToApiValue, countryOptions } from '../../data/countries.js'

export function LoginFlow({ initialStep = 'owner', isBusy, onCreateInstallation, onCreateOwner }) {
  const { t } = useTranslation()
  const [step, setStep] = useState(initialStep)
  const [ownerForm, setOwnerForm] = useState({
    firstName: '',
    lastName: '',
  })
  const [installationForm, setInstallationForm] = useState({
    city: '',
    countryCode: 'BE',
    name: 'Thuisinstallatie',
    panelCount: '',
    capacityKwp: '',
  })
  const [formError, setFormError] = useState('')

  const canContinueOwner = ownerForm.firstName.trim().length > 0
  const canCreateInstallation =
    installationForm.name.trim() &&
    installationForm.city.trim() &&
    installationForm.countryCode.trim()

  async function submitOwner(event) {
    event.preventDefault()

    if (!canContinueOwner) {
      return
    }

    setFormError('')

    try {
      await onCreateOwner({
        first_name: ownerForm.firstName.trim(),
        last_name: ownerForm.lastName.trim() || null,
      })
      setStep('installation')
    } catch (caughtError) {
      setFormError(caughtError.message)
    }
  }

  async function submitInstallation(event) {
    event.preventDefault()

    if (!canCreateInstallation) {
      return
    }

    setFormError('')

    try {
      await onCreateInstallation({
        capacity_kwp: parseOptionalNumber(installationForm.capacityKwp),
        city: installationForm.city.trim(),
        country: countryCodeToApiValue(installationForm.countryCode),
        name: installationForm.name.trim(),
        panel_count: parseOptionalNumber(installationForm.panelCount),
      })
    } catch (caughtError) {
      setFormError(caughtError.message)
    }
  }

  return (
    <main className="login-page onboarding-page">
      <section className="login-panel onboarding-panel">
        <div className="login-header onboarding-header">
          <div>
            <p className="eyebrow">{t(`login.${step}.stepLabel`)}</p>
            <h1>{t('login.title')}</h1>
            <p>{t(`login.${step}.subtitle`)}</p>
          </div>
          <div className="onboarding-progress" aria-hidden="true">
            <span className={step === 'owner' ? 'onboarding-progress-step active' : 'onboarding-progress-step'} />
            <span className={step === 'installation' ? 'onboarding-progress-step active' : 'onboarding-progress-step'} />
          </div>
        </div>

        {step === 'owner' && (
          <form className="create-account-form onboarding-form" onSubmit={submitOwner}>
            <div className="login-section-heading">
              <h2>{t('login.owner.title')}</h2>
              <p>{t('login.owner.text')}</p>
            </div>

            <div className="login-form-grid">
              <label className="configuration-field">
                <span>
                  <UserRound size={18} strokeWidth={2.2} />
                  {t('login.owner.firstName')}
                </span>
                <input
                  onChange={(event) => setOwnerForm((current) => ({ ...current, firstName: event.target.value }))}
                  required
                  type="text"
                  value={ownerForm.firstName}
                />
              </label>

              <label className="configuration-field">
                <span>
                  <UserRound size={18} strokeWidth={2.2} />
                  {t('login.owner.lastName')}
                </span>
                <input
                  onChange={(event) => setOwnerForm((current) => ({ ...current, lastName: event.target.value }))}
                  required
                  type="text"
                  value={ownerForm.lastName}
                />
              </label>
            </div>

            {formError && <p className="form-error">{formError}</p>}

            <button className="create-account-button" disabled={!canContinueOwner || isBusy} type="submit">
              {t('login.owner.submit')}
              <ChevronRight size={18} strokeWidth={2.2} />
            </button>
          </form>
        )}

        {step === 'installation' && (
          <form className="create-account-form onboarding-form" onSubmit={submitInstallation}>
            <div className="login-section-heading">
              <h2>{t('login.installation.title')}</h2>
              <p>{t('login.installation.text')}</p>
              <small className="required-field-legend">{t('login.installation.requiredLegend')}</small>
            </div>

            <div className="login-form-grid">
              <label className="configuration-field wide-field">
                <span>
                  <Home size={18} strokeWidth={2.2} />
                  {t('login.installation.name')}
                </span>
                <input
                  onChange={(event) => setInstallationForm((current) => ({ ...current, name: event.target.value }))}
                  required
                  type="text"
                  value={installationForm.name}
                />
              </label>

              <label className="configuration-field">
                <span>
                  <MapPin size={18} strokeWidth={2.2} />
                  {t('login.installation.city')}
                </span>
                <input
                  onChange={(event) => setInstallationForm((current) => ({ ...current, city: event.target.value }))}
                  placeholder={t('login.installation.cityPlaceholder')}
                  required
                  type="text"
                  value={installationForm.city}
                />
              </label>

              <label className="configuration-field">
                <span>
                  <MapPin size={18} strokeWidth={2.2} />
                  {t('login.installation.country')}
                </span>
                <select
                  onChange={(event) => setInstallationForm((current) => ({ ...current, countryCode: event.target.value }))}
                  value={installationForm.countryCode}
                >
                  {countryOptions.map((country) => (
                    <option key={country.code} value={country.code}>
                      {t(country.labelKey)}
                    </option>
                  ))}
                </select>
              </label>

              <label className="configuration-field">
                <span>{t('login.installation.panelCount')}</span>
                <input
                  min="0"
                  onChange={(event) => setInstallationForm((current) => ({ ...current, panelCount: event.target.value }))}
                  placeholder="18"
                  type="number"
                  value={installationForm.panelCount}
                />
              </label>

              <label className="configuration-field">
                <span>{t('login.installation.capacityKwp')}</span>
                <input
                  min="0"
                  onChange={(event) => setInstallationForm((current) => ({ ...current, capacityKwp: event.target.value }))}
                  placeholder="4.25"
                  step="0.01"
                  type="number"
                  value={installationForm.capacityKwp}
                />
              </label>
            </div>

            <p className="muted-message onboarding-helper">{t('login.installation.optionalHelp')}</p>

            {formError && <p className="form-error">{formError}</p>}

            <button className="create-account-button" disabled={!canCreateInstallation || isBusy} type="submit">
              {t('login.installation.submit')}
            </button>
          </form>
        )}
      </section>
    </main>
  )
}

function parseOptionalNumber(value) {
  return value === '' ? null : Number(value)
}
