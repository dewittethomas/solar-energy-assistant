import { useState } from 'react'
import { Bot, Check, Flame, Shirt, Utensils, WashingMachine } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { PageHeading } from '../components/ui/PageHeading.jsx'

const devices = [
  { id: 'washingMachine', Icon: WashingMachine },
  { id: 'dishwasher', Icon: Utensils },
  { id: 'dryer', Icon: Shirt },
  { id: 'boiler', Icon: Flame },
]

const scheduleItems = {
  washingMachine: {
    timeKey: 'pages.assistant.schedule.washingMachine.time',
    noteKey: 'pages.assistant.schedule.washingMachine.note',
  },
  dishwasher: {
    timeKey: 'pages.assistant.schedule.dishwasher.time',
    noteKey: 'pages.assistant.schedule.dishwasher.note',
  },
  dryer: {
    timeKey: 'pages.assistant.schedule.dryer.time',
    noteKey: 'pages.assistant.schedule.dryer.note',
  },
  boiler: {
    timeKey: 'pages.assistant.schedule.boiler.time',
    noteKey: 'pages.assistant.schedule.boiler.note',
  },
}

export function AssistantPage() {
  const { t } = useTranslation()
  const [selectedDevices, setSelectedDevices] = useState(['washingMachine', 'dishwasher'])

  function toggleDevice(deviceId) {
    setSelectedDevices((currentDevices) =>
      currentDevices.includes(deviceId)
        ? currentDevices.filter((currentDeviceId) => currentDeviceId !== deviceId)
        : [...currentDevices, deviceId],
    )
  }

  return (
    <>
      <PageHeading eyebrow={t('pages.assistant.eyebrow')} title={t('pages.assistant.title')} />

      <section className="assistant-panel" aria-label={t('pages.assistant.title')}>
        <div className="assistant-intro">
          <div className="settings-icon" aria-hidden="true">
            <Bot size={22} strokeWidth={2.2} />
          </div>
          <div>
            <h2>{t('pages.assistant.heading')}</h2>
            <p>{t('pages.assistant.text')}</p>
          </div>
        </div>

        <section className="assistant-workflow single-workflow">
          <article className="action-form-card">
            <div>
              <p className="eyebrow">{t('pages.assistant.devices.eyebrow')}</p>
              <h2>{t('pages.assistant.devices.title')}</h2>
            </div>

            <div className="device-checkbox-grid">
              {devices.map(({ id, Icon }) => {
                const isSelected = selectedDevices.includes(id)

                return (
                  <label className={isSelected ? 'device-option active' : 'device-option'} key={id}>
                    <input checked={isSelected} onChange={() => toggleDevice(id)} type="checkbox" />
                    <span className="device-checkmark" aria-hidden="true">
                      {isSelected && <Check size={14} strokeWidth={3} />}
                    </span>
                    <Icon size={20} strokeWidth={2.2} />
                    <strong>{t(`pages.assistant.appliances.${id}`)}</strong>
                  </label>
                )
              })}
            </div>

            <div className="assistant-form-grid">
              <label className="configuration-field">
                <span>{t('pages.assistant.form.preferredDate')}</span>
                <input type="date" />
              </label>

              <label className="configuration-field">
                <span>{t('pages.assistant.form.timeWindow')}</span>
                <select defaultValue="daytime">
                  <option value="morning">{t('pages.assistant.form.timeOptions.morning')}</option>
                  <option value="daytime">{t('pages.assistant.form.timeOptions.daytime')}</option>
                  <option value="afternoon">{t('pages.assistant.form.timeOptions.afternoon')}</option>
                  <option value="evening">{t('pages.assistant.form.timeOptions.evening')}</option>
                </select>
              </label>
            </div>
          </article>

          <article className="recommendation-card">
            <div>
              <p className="eyebrow">{t('pages.assistant.result.eyebrow')}</p>
              <h2>{t('pages.assistant.result.title')}</h2>
            </div>

            <div className="recommendation-grid">
              <div>
                <span>{t('pages.assistant.result.timeWindow')}</span>
                <strong>{t('pages.assistant.devices.result.timeWindow')}</strong>
              </div>
              <div>
                <span>{t('pages.assistant.result.expectedProduction')}</span>
                <strong>{t('pages.assistant.devices.result.production')}</strong>
              </div>
              <div>
                <span>{t('pages.assistant.result.confidence')}</span>
                <strong>{t('pages.assistant.devices.result.confidence')}</strong>
              </div>
            </div>

            <p>
              {selectedDevices.length > 0
                ? t('pages.assistant.devices.result.reason')
                : t('pages.assistant.devices.result.empty')}
            </p>
          </article>
        </section>

        <section className="schedule-card" aria-label={t('pages.assistant.schedule.title')}>
          <div>
            <p className="eyebrow">{t('pages.assistant.schedule.eyebrow')}</p>
            <h2>{t('pages.assistant.schedule.title')}</h2>
          </div>

          <div className="run-schedule-list">
            {selectedDevices.length === 0 && (
              <p className="schedule-empty">{t('pages.assistant.schedule.empty')}</p>
            )}

            {selectedDevices.map((deviceId) => {
              const DeviceIcon = devices.find((device) => device.id === deviceId)?.Icon
              const scheduleItem = scheduleItems[deviceId]

              return (
                <article className="run-schedule-item" key={deviceId}>
                  <div className="run-schedule-device">
                    {DeviceIcon && <DeviceIcon size={19} strokeWidth={2.2} />}
                    <strong>{t(`pages.assistant.appliances.${deviceId}`)}</strong>
                  </div>
                  <span>{t(scheduleItem.timeKey)}</span>
                  <p>{t(scheduleItem.noteKey)}</p>
                </article>
              )
            })}
          </div>
        </section>
      </section>
    </>
  )
}
