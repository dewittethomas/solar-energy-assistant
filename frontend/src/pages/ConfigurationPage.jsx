import { useState } from 'react'
import {
  BatteryCharging,
  Check,
  CirclePlus,
  Edit3,
  Flame,
  Hash,
  Languages,
  MapPin,
  PanelsTopLeft,
  Zap,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { countryCodeToApiValue, countryOptions, countryValueToCode } from '../data/countries.js'
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

const activityIcons = {
  boiler: Flame,
  ev_charging: BatteryCharging,
}

export function ConfigurationPage({
  availableConsumingActivities = [],
  consumingActivities = [],
  installation,
  onDeleteOwner,
  onConsumingActivitiesChange,
  onInstallationChange,
  preferences,
  onPreferencesChange,
  onResetLocalState,
}) {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState('installation')
  const [saveState, setSaveState] = useState('idle')
  const [developerAction, setDeveloperAction] = useState('idle')
  const activityChoices = mergeActivities(availableConsumingActivities, consumingActivities)
  const [editingActivityKey, setEditingActivityKey] = useState(null)
  const [activityDraft, setActivityDraft] = useState(null)

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
    setSaveState('idle')
  }

  function updateActivity(activity, updates = {}) {
    onConsumingActivitiesChange((currentActivities) => {
      const activityId = getActivityKey(activity)
      const existingActivity = currentActivities.find((currentActivity) => getActivityKey(currentActivity) === activityId)
      const nextActivity = normalizeActivity({
        ...activity,
        ...existingActivity,
        ...updates,
      })

      if (existingActivity) {
        return currentActivities.map((currentActivity) =>
          getActivityKey(currentActivity) === activityId ? nextActivity : currentActivity,
        )
      }

      return [...currentActivities, nextActivity]
    })
    setSaveState('idle')
  }

  function removeActivity(activity) {
    onConsumingActivitiesChange((currentActivities) =>
      currentActivities.filter((currentActivity) => getActivityKey(currentActivity) !== getActivityKey(activity)),
    )
    setSaveState('idle')
  }

  function saveSettings() {
    setSaveState('saving')
    window.setTimeout(() => setSaveState('saved'), 450)
  }

  async function runDeveloperAction(action) {
    setDeveloperAction(action)

    try {
      if (action === 'delete-owner') {
        await onDeleteOwner?.()
        return
      }

      if (action === 'reset-local-state') {
        await onResetLocalState?.()
      }
    } finally {
      setDeveloperAction('idle')
    }
  }

  function startEditingActivity(activity) {
    const currentActivity =
      consumingActivities.find((candidate) => getActivityKey(candidate) === getActivityKey(activity)) || normalizeActivity(activity)
    setEditingActivityKey(getActivityKey(activity))
    setActivityDraft({
      ...currentActivity,
      isActive: consumingActivities.some((candidate) => getActivityKey(candidate) === getActivityKey(activity)),
    })
  }

  function closeActivityEditor() {
    setEditingActivityKey(null)
    setActivityDraft(null)
  }

  function saveActivityDraft() {
    if (!activityDraft?.name?.trim()) {
      return
    }

    const normalized = normalizeActivity({
      ...activityDraft,
      name: activityDraft.name.trim(),
      consumption_kwh: Number(activityDraft.consumption_kwh) || 0,
      duration_minutes: Number(activityDraft.duration_minutes) || 60,
    })

    if (activityDraft.isActive) {
      updateActivity(normalized, normalized)
    } else {
      removeActivity(normalized)
    }

    closeActivityEditor()
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
          <section className="settings-panel single-settings-panel" aria-label={t('settings.installation.title')}>
            <article className="settings-card installation-settings-card">
              <div className="settings-card-header">
                <div className="settings-icon" aria-hidden="true">
                  <PanelsTopLeft size={22} strokeWidth={2.2} />
                </div>
                <div>
                  <h2>{t('settings.installation.title')}</h2>
                  <p>{t('settings.installation.text')}</p>
                </div>
              </div>

              <div className="installation-form compact-installation-form">
                <label className="configuration-field wide-field">
                  <span>
                    <PanelsTopLeft size={18} strokeWidth={2.2} />
                    {t('settings.installation.name')}
                  </span>
                  <input
                    onChange={(event) => updateInstallation('name', event.target.value)}
                    placeholder={t('settings.installation.namePlaceholder')}
                    type="text"
                    value={installation.name ?? ''}
                  />
                </label>

                <label className="configuration-field">
                  <span>
                    <MapPin size={18} strokeWidth={2.2} />
                    {t('settings.installation.city')}
                  </span>
                  <input
                    onChange={(event) => updateInstallation('city', event.target.value)}
                    placeholder={t('settings.installation.cityPlaceholder')}
                    type="text"
                    value={installation.city ?? ''}
                  />
                </label>

                <label className="configuration-field">
                  <span>
                    <MapPin size={18} strokeWidth={2.2} />
                    {t('settings.installation.country')}
                  </span>
                  <select
                    onChange={(event) => updateInstallation('country', countryCodeToApiValue(event.target.value))}
                    value={countryValueToCode(installation.country)}
                  >
                    {countryOptions.map((country) => (
                      <option key={country.code} value={country.code}>
                        {t(country.labelKey)}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="settings-subsection wide-field">
                  <strong>{t('settings.installation.optionalTitle', { defaultValue: 'Optionele gegevens' })}</strong>
                  <p>{t('settings.installation.optionalHelp')}</p>
                </div>

                <label className={`configuration-field optional-field ${installation.panelCount === null ? 'is-empty' : ''}`}>
                  <span>
                    <Hash size={18} strokeWidth={2.2} />
                    {t('settings.installation.panelCount')}
                  </span>
                  <input
                    min="0"
                    onChange={(event) => updateInstallation('panelCount', parseOptionalNumber(event.target.value))}
                    placeholder={t('settings.installation.panelPlaceholder', { defaultValue: 'bijv. 12' })}
                    type="number"
                    value={installation.panelCount ?? ''}
                  />
                </label>

                <label className={`configuration-field optional-field ${installation.installationKwp === null ? 'is-empty' : ''}`}>
                  <span>
                    <Zap size={18} strokeWidth={2.2} />
                    {t('settings.installation.installationKwp')}
                  </span>
                  <input
                    min="0"
                    onChange={(event) => {
                      const nextValue = parseOptionalNumber(event.target.value)
                      onInstallationChange((currentInstallation) => ({
                        ...currentInstallation,
                        capacityKwp: nextValue,
                        installationKwp: nextValue,
                      }))
                      setSaveState('idle')
                    }}
                    placeholder={t('settings.installation.powerPlaceholder', { defaultValue: 'bijv. 4.8' })}
                    step="0.1"
                    type="number"
                    value={installation.installationKwp ?? ''}
                  />
                </label>
              </div>

              <div className="settings-card-footer">
                <button className="page-primary-cta" onClick={saveSettings} type="button">
                  {saveState === 'saving' ? t('settings.saving') : t('settings.saveChanges')}
                </button>
              </div>
            </article>
          </section>
        )}

        {activeTab === 'consumption' && (
          <section className="settings-panel" aria-label={t('settings.consumption.title')}>
            <article className="settings-card">
              <div className="settings-card-header">
                <div className="settings-icon" aria-hidden="true">
                  <Zap size={22} strokeWidth={2.2} />
                </div>
                <div>
                  <h2>{t('settings.consumption.tableTitle', { defaultValue: 'Mijn toestellen' })}</h2>
                  <p>{t('settings.consumption.tableText', { defaultValue: 'Beheer je toestellen en pas hun verbruik alleen aan wanneer nodig.' })}</p>
                </div>
              </div>

              <div className="consumption-toolbar">
                <button className="create-account-button" onClick={() => startEditingActivity({
                  id: null,
                  name: '',
                  category: 'custom',
                  consumption_kwh: 1,
                  duration_minutes: 60,
                  is_custom: true,
                })} type="button">
                  <CirclePlus size={18} strokeWidth={2.2} />
                  {t('settings.consumption.addDevice', { defaultValue: 'Toestel toevoegen' })}
                </button>
              </div>

              <div className="dataset-table-wrap">
                <table className="dataset-table consumption-table">
                  <thead>
                    <tr>
                      <th>{t('settings.consumption.columns.device', { defaultValue: 'Toestel' })}</th>
                      <th>{t('settings.consumption.columns.category', { defaultValue: 'Categorie' })}</th>
                      <th>{t('settings.consumption.columns.usage', { defaultValue: 'Verbruik' })}</th>
                      <th>{t('settings.consumption.columns.duration', { defaultValue: 'Duur' })}</th>
                      <th>{t('settings.consumption.columns.status', { defaultValue: 'Status' })}</th>
                      <th>{t('settings.consumption.columns.actions', { defaultValue: 'Acties' })}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activityChoices.map((activity) => {
                      const selectedActivity = consumingActivities.find(
                        (candidate) => getActivityKey(candidate) === getActivityKey(activity),
                      )
                      const resolved = selectedActivity || activity
                      const isActive = Boolean(selectedActivity)

                      return (
                        <tr key={getActivityKey(activity)}>
                          <td>
                            <strong>{resolved.name}</strong>
                          </td>
                          <td>{translateCategory(resolved.category, t)}</td>
                          <td>{Number(resolved.consumption_kwh || 0).toFixed(1)} kWh</td>
                          <td>{Number(resolved.duration_minutes || 60)} min</td>
                          <td>
                            <span className={`status-badge ${isActive ? 'ready' : 'processing'}`}>
                              {isActive ? t('settings.consumption.enabled') : t('settings.consumption.disabled')}
                            </span>
                          </td>
                          <td>
                            <button className="secondary-action-button" onClick={() => startEditingActivity(resolved)} type="button">
                              <Edit3 size={16} strokeWidth={2.1} />
                              {t('settings.consumption.edit', { defaultValue: 'Bewerken' })}
                            </button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {editingActivityKey && activityDraft && (
                <div className="settings-modal-backdrop" role="presentation">
                  <div className="settings-modal" role="dialog" aria-modal="true" aria-labelledby="edit-appliance-title">
                    <div className="settings-card-header">
                      <div className="settings-icon" aria-hidden="true">
                        <Zap size={22} strokeWidth={2.2} />
                      </div>
                      <div>
                        <h2 id="edit-appliance-title">{t('settings.consumption.editTitle', { defaultValue: 'Toestel bewerken' })}</h2>
                        <p>{t('settings.consumption.editText', { defaultValue: 'Pas naam, categorie, verbruik en status aan.' })}</p>
                      </div>
                    </div>

                    <div className="installation-form">
                      <label className="configuration-field">
                        <span>{t('settings.consumption.customName')}</span>
                        <input
                          onChange={(event) => setActivityDraft((current) => ({ ...current, name: event.target.value }))}
                          type="text"
                          value={activityDraft.name}
                        />
                      </label>

                      <label className="configuration-field">
                        <span>{t('settings.consumption.columns.category', { defaultValue: 'Categorie' })}</span>
                        <select
                          onChange={(event) => setActivityDraft((current) => ({ ...current, category: event.target.value }))}
                          value={activityDraft.category || 'custom'}
                        >
                          {['laundry', 'kitchen', 'heating', 'mobility', 'electronics', 'custom'].map((category) => (
                            <option key={category} value={category}>
                              {translateCategory(category, t)}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="configuration-field">
                        <span>{t('settings.consumption.kwh')}</span>
                        <input
                          min="0"
                          onChange={(event) => setActivityDraft((current) => ({ ...current, consumption_kwh: event.target.value }))}
                          step="0.1"
                          type="number"
                          value={activityDraft.consumption_kwh}
                        />
                      </label>

                      <label className="configuration-field">
                        <span>{t('settings.consumption.duration')}</span>
                        <input
                          min="1"
                          onChange={(event) => setActivityDraft((current) => ({ ...current, duration_minutes: event.target.value }))}
                          type="number"
                          value={activityDraft.duration_minutes}
                        />
                      </label>

                      <button
                        aria-pressed={activityDraft.isActive}
                        className={activityDraft.isActive ? 'toggle-switch active' : 'toggle-switch'}
                        onClick={() => setActivityDraft((current) => ({ ...current, isActive: !current.isActive }))}
                        type="button"
                      >
                        <span className="toggle-track" aria-hidden="true">
                          <Check className="toggle-icon sun" size={16} strokeWidth={2.4} />
                          <Zap className="toggle-icon moon" size={16} strokeWidth={2.4} />
                          <span className="toggle-thumb" />
                        </span>
                        {activityDraft.isActive ? t('settings.consumption.enabled') : t('settings.consumption.disabled')}
                      </button>
                    </div>

                    <div className="settings-modal-actions">
                      <button className="secondary-action-button" onClick={closeActivityEditor} type="button">
                        {t('common.cancel', { defaultValue: 'Annuleren' })}
                      </button>
                      <button className="page-primary-cta" onClick={saveActivityDraft} type="button">
                        {t('common.save', { defaultValue: 'Opslaan' })}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </article>
          </section>
        )}

        {activeTab === 'preferences' && (
          <section className="settings-panel" aria-label={t('settings.preferencesLabel')}>
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

            <article className="settings-card">
              <div className="settings-card-header">
                <div className="settings-icon" aria-hidden="true">
                  <Zap size={22} strokeWidth={2.2} />
                </div>
                <div>
                  <h2>{t('settings.developer.title')}</h2>
                  <p>{t('settings.developer.text')}</p>
                </div>
              </div>

              <button
                aria-pressed={preferences.developerMode}
                className={preferences.developerMode ? 'toggle-switch active' : 'toggle-switch'}
                onClick={() => updatePreference('developerMode', !preferences.developerMode)}
                type="button"
              >
                <span className="toggle-track" aria-hidden="true">
                  <Check className="toggle-icon sun" size={16} strokeWidth={2.4} />
                  <Zap className="toggle-icon moon" size={16} strokeWidth={2.4} />
                  <span className="toggle-thumb" />
                </span>
                {preferences.developerMode ? t('settings.developer.enabled') : t('settings.developer.disabled')}
              </button>

              {preferences.developerMode && (
                <div className="developer-panel">
                  <p>{t('settings.developer.warning')}</p>
                  <div className="developer-action-row">
                    <button
                      className="secondary-action-button"
                      disabled={developerAction !== 'idle'}
                      onClick={() => runDeveloperAction('delete-owner')}
                      type="button"
                    >
                      {developerAction === 'delete-owner'
                        ? t('settings.developer.working')
                        : t('settings.developer.deleteOwner')}
                    </button>
                    <button
                      className="secondary-action-button destructive-button"
                      disabled={developerAction !== 'idle'}
                      onClick={() => runDeveloperAction('reset-local-state')}
                      type="button"
                    >
                      {developerAction === 'reset-local-state'
                        ? t('settings.developer.working')
                        : t('settings.developer.resetDatabase')}
                    </button>
                  </div>
                </div>
              )}
            </article>
          </section>
        )}

      </section>
    </>
  )
}

function mergeActivities(availableActivities, selectedActivities) {
  const activities = new Map()

  availableActivities.forEach((activity) => activities.set(getActivityKey(activity), normalizeActivity(activity)))
  selectedActivities.forEach((activity) => activities.set(getActivityKey(activity), normalizeActivity(activity)))

  return Array.from(activities.values())
}

function getActivityKey(activity) {
  return activity.id || activity.name
}

function normalizeActivity(activity) {
  return {
    id: activity.id || null,
    name: activity.name,
    consumption_kwh: Number(activity.consumption_kwh) || 0,
    duration_minutes: Number(activity.duration_minutes) || 60,
    category: activity.category || (activity.is_custom ? 'custom' : null),
    is_custom: Boolean(activity.is_custom),
  }
}

function translateCategory(category, t) {
  const normalized = String(category || 'custom').toLowerCase()
  const keyMap = {
    custom: 'other',
    electronics: 'electronics',
    heating: 'heating',
    kitchen: 'kitchen',
    laundry: 'laundry',
    mobility: 'mobility',
  }

  return t(`settings.consumption.categories.${keyMap[normalized] || 'other'}`)
}

function parseOptionalNumber(value) {
  return value === '' ? null : Number(value)
}
