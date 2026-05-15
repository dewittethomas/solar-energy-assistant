import { useState } from 'react'
import {
  BatteryCharging,
  Check,
  Flame,
  Hash,
  Languages,
  Moon,
  PanelsTopLeft,
  Shirt,
  SunMedium,
  Utensils,
  WashingMachine,
  Zap,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { PageHeading } from '../components/ui/PageHeading.jsx'

const languages = [
  { id: 'nl', labelKey: 'settings.language.nl.label', descriptionKey: 'settings.language.nl.description' },
  { id: 'fr', labelKey: 'settings.language.fr.label', descriptionKey: 'settings.language.fr.description' },
  { id: 'en', labelKey: 'settings.language.en.label', descriptionKey: 'settings.language.en.description' },
]

const tabs = [
  { id: 'installation', labelKey: 'settings.tabs.installation' },
  { id: 'consumption', labelKey: 'settings.tabs.consumption' },
  { id: 'preferences', labelKey: 'settings.tabs.preferences' },
]

const consumptionItems = [
  { id: 'car', icon: BatteryCharging, labelKey: 'settings.consumption.car.title', textKey: 'settings.consumption.car.text' },
  {
    id: 'washingMachine',
    icon: WashingMachine,
    labelKey: 'settings.consumption.washingMachine.title',
    textKey: 'settings.consumption.washingMachine.text',
  },
  {
    id: 'dishwasher',
    icon: Utensils,
    labelKey: 'settings.consumption.dishwasher.title',
    textKey: 'settings.consumption.dishwasher.text',
  },
  { id: 'dryer', icon: Shirt, labelKey: 'settings.consumption.dryer.title', textKey: 'settings.consumption.dryer.text' },
  { id: 'boiler', icon: Flame, labelKey: 'settings.consumption.boiler.title', textKey: 'settings.consumption.boiler.text' },
]

export function ConfigurationPage({
  assistantConsumption,
  installation,
  onAssistantConsumptionChange,
  onInstallationChange,
  preferences,
  onPreferencesChange,
}) {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState('installation')

  function updatePreference(key, value) {
    onPreferencesChange((currentPreferences) => ({
      ...currentPreferences,
      [key]: value,
    }))
  }

  function updateInstallation(key, value) {
    onInstallationChange((currentInstallation) => ({
      ...currentInstallation,
      [key]: value,
    }))
  }

  function updateConsumption(key, value) {
    onAssistantConsumptionChange((currentConsumption) => ({
      ...currentConsumption,
      [key]: value,
    }))
  }

  return (
    <>
      <PageHeading eyebrow={t('settings.eyebrow')} title={t('settings.title')} />

      <section className="configuration-shell" aria-label={t('settings.title')}>
        <div className="configuration-tabs" role="tablist" aria-label={t('settings.tabs.label')}>
          {tabs.map((tab) => (
            <button
              aria-selected={activeTab === tab.id}
              className={activeTab === tab.id ? 'configuration-tab active' : 'configuration-tab'}
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              role="tab"
              type="button"
            >
              {t(tab.labelKey)}
            </button>
          ))}
        </div>

        {activeTab === 'installation' && (
          <section className="settings-panel" aria-label={t('settings.installation.title')}>
            <article className="settings-card">
              <div className="settings-card-header">
                <div className="settings-icon" aria-hidden="true">
                  <PanelsTopLeft size={22} strokeWidth={2.2} />
                </div>
                <div>
                  <h2>{t('settings.installation.title')}</h2>
                  <p>{t('settings.installation.text')}</p>
                </div>
              </div>

              <div className="installation-form">
                <label className="configuration-field">
                  <span>
                    <Hash size={18} strokeWidth={2.2} />
                    {t('settings.installation.panelCount')}
                  </span>
                  <input
                    min="0"
                    onChange={(event) => updateInstallation('panelCount', Number(event.target.value))}
                    type="number"
                    value={installation.panelCount}
                  />
                </label>
              </div>
            </article>

            <article className="settings-card">
              <div className="settings-card-header">
                <div className="settings-icon" aria-hidden="true">
                  <Zap size={22} strokeWidth={2.2} />
                </div>
                <div>
                  <h2>{t('settings.installation.powerTitle')}</h2>
                  <p>{t('settings.installation.powerText')}</p>
                </div>
              </div>

              <div className="installation-form">
                <label className="configuration-field">
                  <span>
                    <Zap size={18} strokeWidth={2.2} />
                    {t('settings.installation.installationKwp')}
                  </span>
                  <input
                    min="0"
                    onChange={(event) => updateInstallation('installationKwp', Number(event.target.value))}
                    step="0.1"
                    type="number"
                    value={installation.installationKwp}
                  />
                </label>
              </div>
            </article>
          </section>
        )}

        {activeTab === 'consumption' && (
          <section className="settings-panel" aria-label={t('settings.consumption.title')}>
            {consumptionItems.map(({ id, icon: ConsumptionIcon, labelKey, textKey }) => (
              <article className="settings-card" key={id}>
                <div className="settings-card-header">
                  <div className="settings-icon" aria-hidden="true">
                    <ConsumptionIcon size={22} strokeWidth={2.2} />
                  </div>
                  <div>
                    <h2>{t(labelKey)}</h2>
                    <p>{t(textKey)}</p>
                  </div>
                </div>

                <div className="installation-form">
                  <label className="configuration-field">
                    <span>
                      <Zap size={18} strokeWidth={2.2} />
                      {t('settings.consumption.kwh')}
                    </span>
                    <input
                      min="0"
                      onChange={(event) => updateConsumption(id, Number(event.target.value))}
                      step="0.1"
                      type="number"
                      value={assistantConsumption[id]}
                    />
                  </label>
                </div>
              </article>
            ))}
          </section>
        )}

        {activeTab === 'preferences' && (
          <section className="settings-panel" aria-label={t('settings.preferencesLabel')}>
            <article className="settings-card">
              <div className="settings-card-header">
                <div className="settings-icon" aria-hidden="true">
                  {preferences.darkMode ? (
                    <Moon size={22} strokeWidth={2.2} />
                  ) : (
                    <SunMedium size={22} strokeWidth={2.2} />
                  )}
                </div>
                <div>
                  <h2>{t('settings.appearance.title')}</h2>
                  <p>{t('settings.appearance.text')}</p>
                </div>
              </div>

              <button
                aria-pressed={preferences.darkMode}
                className={preferences.darkMode ? 'toggle-switch active' : 'toggle-switch'}
                onClick={() => updatePreference('darkMode', !preferences.darkMode)}
                type="button"
              >
                <span className="toggle-track" aria-hidden="true">
                  <SunMedium className="toggle-icon sun" size={16} strokeWidth={2.4} />
                  <Moon className="toggle-icon moon" size={16} strokeWidth={2.4} />
                  <span className="toggle-thumb" />
                </span>
                {preferences.darkMode ? t('settings.appearance.dark') : t('settings.appearance.light')}
              </button>
            </article>

            <article className="settings-card">
              <div className="settings-card-header">
                <div className="settings-icon" aria-hidden="true">
                  <Languages size={22} strokeWidth={2.2} />
                </div>
                <div>
                  <h2>{t('settings.language.title')}</h2>
                  <p>{t('settings.language.text')}</p>
                </div>
              </div>

              <div className="language-options" role="radiogroup" aria-label={t('settings.language.label')}>
                {languages.map((language) => {
                  const isSelected = preferences.language === language.id

                  return (
                    <button
                      aria-checked={isSelected}
                      className={isSelected ? 'language-option active' : 'language-option'}
                      key={language.id}
                      onClick={() => updatePreference('language', language.id)}
                      role="radio"
                      type="button"
                    >
                      <span>
                        <strong>{t(language.labelKey)}</strong>
                        <small>{t(language.descriptionKey)}</small>
                      </span>
                      {isSelected && <Check size={18} strokeWidth={2.4} />}
                    </button>
                  )
                })}
              </div>
            </article>
          </section>
        )}
      </section>
    </>
  )
}
