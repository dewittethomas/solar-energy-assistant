import { useEffect, useMemo, useState } from 'react'
import {
  BatteryCharging,
  Check,
  CirclePlus,
  Clock3,
  Flame,
  Lightbulb,
  Laptop,
  Pencil,
  Shirt,
  Utensils,
  WashingMachine,
  WandSparkles,
  Zap,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client.js'
import { NoProductionDataState } from '../components/ui/NoProductionDataState.jsx'
import { PageHeading } from '../components/ui/PageHeading.jsx'
import { TrainingStateNotice } from '../components/ui/TrainingStateNotice.jsx'
import { buildPlannerWindows, formatTimeInZone, getDateKey, getRelativeDayName, resolveTimeContext } from '../utils/solarTime.js'

const activityIcons = {
  boiler: Flame,
  dishwasher: Utensils,
  dryer: Shirt,
  ev_charging: BatteryCharging,
  laptop_charging: Laptop,
  oven: Flame,
  washing_machine: WashingMachine,
}

const planningPreferences = ['auto', 'today', 'tomorrow', 'dayAfterTomorrow']

export function AssistantPage({ consumingActivities = [], datasetState, modelState, onNavigate, trainingRunId, user }) {
  const { i18n, t } = useTranslation()
  const hasProductionData = Boolean(datasetState?.hasProductionData)
  const isLoading = Boolean(datasetState?.isLoading)
  const [devices, setDevices] = useState([])
  const [selectedDevices, setSelectedDevices] = useState([])
  const [editingDeviceId, setEditingDeviceId] = useState(null)
  const [modalDevice, setModalDevice] = useState(null)
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false)
  const [planningPreference, setPlanningPreference] = useState('auto')
  const [recommendation, setRecommendation] = useState(null)
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState(false)
  const [hasCreatedPlanning, setHasCreatedPlanning] = useState(false)
  const [forecastData, setForecastData] = useState({
    forecast: [],
    server_time: new Date().toISOString(),
    timezone: 'Europe/Brussels',
  })

  useEffect(() => {
    setDevices((currentDevices) => mergeDevices(consumingActivities, currentDevices))
  }, [consumingActivities])

  useEffect(() => {
    if (!user?.installationId || !hasProductionData) {
      return
    }

    const today = new Date()

    api
      .getThreeDayPredictions(user.installationId, today)
      .then(setForecastData)
      .catch(() =>
        setForecastData({
          forecast: [],
          server_time: new Date().toISOString(),
          timezone: 'Europe/Brussels',
        }),
      )
  }, [hasProductionData, user?.installationId])

  useEffect(() => {
    setSelectedDevices((currentDevices) => currentDevices.filter((deviceId) => devices.some((device) => getActivityKey(device) === deviceId)))
  }, [devices])

  const locale = i18n.language === 'fr' ? 'fr-BE' : i18n.language === 'en' ? 'en-GB' : 'nl-BE'
  const timeContext = resolveTimeContext(recommendation || forecastData)
  const plannerLabels = {
    today: t('common.today'),
    tomorrow: t('common.tomorrow'),
    dayAfterTomorrow: t('common.dayAfterTomorrow'),
  }
  const plannerWindows = buildPlannerWindows(forecastData.forecast || [], timeContext, { locale })
  const selectedDeviceObjects = useMemo(
    () => selectedDevices.map((deviceId) => devices.find((device) => getActivityKey(device) === deviceId)).filter(Boolean),
    [devices, selectedDevices],
  )
  const planningResult = useMemo(
    () =>
      buildPlanningResult({
        recommendation,
        plannerWindows,
        plannerLabels,
        planningPreference,
        selectedDevices: selectedDeviceObjects,
        timeContext,
        locale,
        hasCreatedPlanning,
        t,
      }),
    [recommendation, plannerWindows, plannerLabels, planningPreference, selectedDeviceObjects, timeContext, locale, hasCreatedPlanning, t],
  )
  const todayWindowPassed = plannerWindows[0]?.isPast
  const isTrainingGuarded = ['training', 'failed'].includes(modelState)

  function toggleDevice(deviceId) {
    setSelectedDevices((currentDevices) =>
      currentDevices.includes(deviceId)
        ? currentDevices.filter((currentDeviceId) => currentDeviceId !== deviceId)
        : [...currentDevices, deviceId],
    )
  }

  function updateDevice(deviceId, updates) {
    setDevices((currentDevices) =>
      currentDevices.map((device) => (getActivityKey(device) === deviceId ? { ...device, ...updates } : device)),
    )
  }

  function saveModalDevice(event) {
    event.preventDefault()

    if (!modalDevice) {
      return
    }

    if (modalDevice.isNew) {
      const device = {
        id: null,
        name: modalDevice.name.trim(),
        consumption_kwh: Number(modalDevice.consumption_kwh) || 1,
        duration_minutes: Number(modalDevice.duration_minutes) || 60,
        category: 'custom',
        is_custom: true,
      }

      setDevices((currentDevices) => [...currentDevices, device])
      setSelectedDevices((currentDevices) => [...currentDevices, getActivityKey(device)])
      setIsCustomModalOpen(false)
    } else {
      updateDevice(getActivityKey(modalDevice), {
        name: modalDevice.name,
        consumption_kwh: Number(modalDevice.consumption_kwh) || 1,
        duration_minutes: Number(modalDevice.duration_minutes) || 60,
      })
      setEditingDeviceId(null)
    }

    setModalDevice(null)
  }

  async function createPlanning() {
    if (!user?.installationId || selectedDeviceObjects.length === 0) {
      return
    }

    setIsLoadingRecommendation(true)
    setHasCreatedPlanning(true)

    try {
      const requestPayload = buildRecommendationPayload({
        installationId: user.installationId,
        planningPreference,
        serverTime: timeContext.serverTime,
        selected_devices: selectedDeviceObjects.map((device) => ({
          name: device.name,
          consumption_kwh: Number(device.consumption_kwh) || 1,
          duration_minutes: Number(device.duration_minutes) || 60,
        })),
      })
      const result = await api.recommendUsageWindow(requestPayload)
      setRecommendation(result)
    } catch {
      setRecommendation(null)
    } finally {
      setIsLoadingRecommendation(false)
    }
  }

  return (
    <>
      <PageHeading eyebrow={t('pages.assistant.eyebrow')} title={t('pages.assistant.title')} />

      {isTrainingGuarded && (
        <TrainingStateNotice modelState={modelState} onNavigate={onNavigate} trainingRunId={trainingRunId} />
      )}

      {!isTrainingGuarded && !isLoading && !hasProductionData && (
        <NoProductionDataState messageKey="pages.assistant.empty.text" onUpload={() => onNavigate('dataManagement')} />
      )}

      {!isTrainingGuarded && hasProductionData && (
      <section className="assistant-panel planner-panel" aria-label={t('pages.assistant.title')}>
        <div className="assistant-intro">
          <div className="settings-icon solar-icon" aria-hidden="true">
            <WandSparkles size={22} strokeWidth={2.2} />
          </div>
          <div>
            <h2>{t('pages.assistant.heading')}</h2>
            <p>{t('pages.assistant.text')}</p>
          </div>
        </div>

        <section className="planner-step-card">
          <div>
            <p className="eyebrow">{t('pages.assistant.devices.eyebrow')}</p>
            <h2>{t('pages.assistant.devices.title')}</h2>
          </div>

          <div className="planner-appliance-grid">
            {devices.map((device) => {
              const id = getActivityKey(device)
              const Icon = activityIcons[device.id] || Zap
              const isSelected = selectedDevices.includes(id)
                return (
                <article className={isSelected ? 'planner-appliance-card active' : 'planner-appliance-card'} key={id}>
                  <label className="planner-appliance-select">
                    <input checked={isSelected} onChange={() => toggleDevice(id)} type="checkbox" />
                    <span className="device-checkmark" aria-hidden="true">
                      {isSelected && <Check size={14} strokeWidth={3} />}
                    </span>
                    <Icon size={20} strokeWidth={2.2} />
                    <span>
                      <strong>{device.name}</strong>
                      <small>{formatApplianceMeta(device)}</small>
                    </span>
                  </label>

                  <button
                    className="planner-edit-button"
                    onClick={() => {
                      setEditingDeviceId(id)
                      setModalDevice({ ...device })
                    }}
                    type="button"
                  >
                    <Pencil size={15} strokeWidth={2.2} />
                    {t('pages.assistant.devices.edit')}
                  </button>
                </article>
              )
            })}
          </div>

          <button
            className="secondary-action-button add-appliance-button"
            onClick={() => {
              setIsCustomModalOpen(true)
              setModalDevice({ name: '', consumption_kwh: 1, duration_minutes: 60, isNew: true })
            }}
            type="button"
          >
              <CirclePlus size={17} strokeWidth={2.2} />
              {t('pages.assistant.devices.addCustom')}
          </button>

          {selectedDeviceObjects.length > 0 && (
            <div className="planner-selection-summary">
              <strong>{t('pages.assistant.summary.selected', { count: selectedDeviceObjects.length })}</strong>
              <span>{t('pages.assistant.summary.usage', { value: totalUsage(selectedDeviceObjects) })}</span>
              <span>{t('pages.assistant.summary.duration', { value: totalDuration(selectedDeviceObjects) })}</span>
            </div>
          )}
        </section>

        <section className="planner-step-card planner-preference-card">
          <div>
            <p className="eyebrow">{t('pages.assistant.form.title')}</p>
            <h2>{t('pages.assistant.form.timeWindow')}</h2>
          </div>

          <div className="planner-preference-options" role="radiogroup" aria-label={t('pages.assistant.form.title')}>
            {planningPreferences.map((preference) => (
              <button
                aria-checked={planningPreference === preference}
                className={planningPreference === preference ? 'planner-preference active' : 'planner-preference'}
                key={preference}
                onClick={() => setPlanningPreference(preference)}
                role="radio"
                type="button"
              >
                <span />
                {t(`pages.assistant.form.timeOptions.${preference}`)}
              </button>
            ))}
          </div>

          <button
            className="page-primary-cta inline-cta"
            disabled={selectedDevices.length === 0 || isLoadingRecommendation}
            onClick={createPlanning}
            type="button"
          >
            {isLoadingRecommendation ? t('pages.assistant.loadingRecommendation') : t('pages.assistant.getRecommendation')}
          </button>
          {todayWindowPassed && planningPreference === 'auto' && (
            <p className="planner-time-note">{t('pages.assistant.timeAwareness.todayPassed')}</p>
          )}
        </section>

        <section className="schedule-card planner-calendar-card" aria-label={t('pages.assistant.schedule.title')}>
          <div>
            <p className="eyebrow">{t('pages.assistant.schedule.eyebrow')}</p>
            <h2>{resolvePlanningSectionTitle(planningPreference, t)}</h2>
          </div>

          {!planningResult.selectedPlan && (
            <p className="schedule-empty">{resolvePlanningEmptyState(planningPreference, t)}</p>
          )}

          {planningResult.selectedPlan && (
            <div className="planner-recommendation-layout planner-recommendation-layout-agenda">
              <article className="planner-selected-plan-card">
                <div className="planner-result-heading">
                  <div>
                    <p className="eyebrow">{resolvePlanningSectionTitle(planningPreference, t)}</p>
                    <h3>{planningResult.selectedPlan.deviceLabel}</h3>
                  </div>
                  <span className="planner-result-icon">
                    <Lightbulb size={18} strokeWidth={2.2} />
                  </span>
                </div>

                <div className="planner-day-meta">
                  <div>
                    <span>{planningResult.selectedPlan.dayLabel}</span>
                    <strong>{planningResult.selectedPlan.timeLabel}</strong>
                  </div>
                  <div>
                    <span>{t('pages.assistant.schedule.durationLabel', { defaultValue: 'Duur' })}</span>
                    <strong>{planningResult.selectedPlan.durationLabel}</strong>
                  </div>
                </div>

                <div className="planner-day-window">
                  <span>{t('pages.assistant.schedule.expectedProductionWindow', { defaultValue: 'Verwachte productie tijdens dit venster' })}</span>
                  <strong>{planningResult.selectedPlan.expectedProduction}</strong>
                </div>

                <div className="run-schedule-list">
                  {planningResult.selectedPlan.items.map((item) => (
                    <article className="planner-calendar-item selected planner-device-schedule-card" key={`selected-${item.name}-${item.time}`}>
                      <span className="planner-device-name">{item.name}</span>
                      <div className="planner-device-schedule-meta">
                        <div>
                          <small>{t('pages.assistant.schedule.startLabel', { defaultValue: 'Start' })}</small>
                          <strong>{item.startLabel}</strong>
                        </div>
                        <div>
                          <small>{t('pages.assistant.schedule.endLabel', { defaultValue: 'Einde' })}</small>
                          <strong>{item.endLabel}</strong>
                        </div>
                        <div>
                          <small>{t('pages.assistant.schedule.durationLabel', { defaultValue: 'Duur' })}</small>
                          <strong>{item.durationLabel}</strong>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </article>

              <article className="planner-alternatives-card">
                <div>
                  <p className="eyebrow">{t('pages.assistant.schedule.alternativesLabel', { defaultValue: 'Agenda-overzicht' })}</p>
                  <h3>{t('pages.assistant.schedule.alternativesTitle', { defaultValue: 'Andere geschikte momenten' })}</h3>
                </div>

                <div className="planner-calendar-grid">
                  {planningResult.dayCards.map((dayCard) => (
                    <article
                      className={dayCard.isSelected ? 'planner-day-card selected' : 'planner-day-card'}
                      key={dayCard.dateKey}
                    >
                      <div className="planner-day-heading">
                        <strong>{dayCard.title}</strong>
                        {dayCard.isSelected ? <span>{t('pages.assistant.schedule.selectedBadge', { defaultValue: 'Gekozen' })}</span> : null}
                      </div>

                      {dayCard.empty ? (
                        <p className="planner-day-empty">{dayCard.emptyText}</p>
                      ) : (
                        <>
                          <div className="planner-day-window">
                            <span>{dayCard.deviceLabel}</span>
                            <strong>{dayCard.timeLabel}</strong>
                          </div>
                          <div className="planner-day-meta">
                            <div>
                              <span>{t('pages.assistant.schedule.durationLabel', { defaultValue: 'Duur' })}</span>
                              <strong>{dayCard.durationLabel}</strong>
                            </div>
                            <div>
                              <span>{t('pages.assistant.schedule.averageProductionLabel', { defaultValue: 'Gemiddelde productie' })}</span>
                              <strong>{dayCard.expectedProduction}</strong>
                            </div>
                          </div>
                        </>
                      )}
                    </article>
                  ))}
                </div>
              </article>
            </div>
          )}
        </section>
      </section>
      )}

      {(modalDevice || isCustomModalOpen) && (
        <div className="modal-backdrop" role="presentation">
          <form className="planner-modal" onSubmit={saveModalDevice}>
            <div>
              <p className="eyebrow">{modalDevice?.isNew ? t('pages.assistant.devices.addCustom') : t('pages.assistant.devices.edit')}</p>
              <h2>{modalDevice?.isNew ? t('pages.assistant.devices.customName') : modalDevice?.name}</h2>
            </div>
            <label className="configuration-field">
              <span>{t('pages.assistant.modal.name')}</span>
              <input
                onChange={(event) => setModalDevice((current) => ({ ...current, name: event.target.value }))}
                required
                type="text"
                value={modalDevice?.name || ''}
              />
            </label>
            <label className="configuration-field">
              <span>{t('pages.assistant.modal.usage')}</span>
              <input
                min="0"
                onChange={(event) => setModalDevice((current) => ({ ...current, consumption_kwh: event.target.value }))}
                step="0.1"
                type="number"
                value={modalDevice?.consumption_kwh ?? ''}
              />
            </label>
            <label className="configuration-field">
              <span>{t('pages.assistant.modal.duration')}</span>
              <input
                min="1"
                onChange={(event) => setModalDevice((current) => ({ ...current, duration_minutes: event.target.value }))}
                type="number"
                value={modalDevice?.duration_minutes ?? ''}
              />
            </label>
            <div className="modal-action-row">
              <button
                className="secondary-action-button"
                onClick={() => {
                  setModalDevice(null)
                  setIsCustomModalOpen(false)
                  setEditingDeviceId(null)
                }}
                type="button"
              >
                {t('common.cancel')}
              </button>
              <button className="page-primary-cta inline-cta" type="submit">
                {modalDevice?.isNew ? t('pages.assistant.modal.add') : t('pages.assistant.modal.save')}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  )
}

function mergeDevices(sourceDevices, currentDevices) {
  const currentByKey = new Map(currentDevices.map((device) => [getActivityKey(device), device]))

  return sourceDevices.map((device) => ({
    ...device,
    duration_minutes: Number(device.duration_minutes) || 60,
    ...currentByKey.get(getActivityKey(device)),
  }))
}

function buildPlanningResult({
  recommendation,
  plannerWindows,
  plannerLabels,
  planningPreference,
  selectedDevices,
  timeContext,
  locale,
  hasCreatedPlanning,
  t,
}) {
  if (!hasCreatedPlanning || !recommendation || selectedDevices.length === 0) {
    return {
      selectedPlan: null,
      dayCards: buildEmptyDayCards(timeContext, plannerLabels, planningPreference, t),
    }
  }

  const selectedPlan = buildSelectedPlan({
    recommendation,
    selectedDevices,
    plannerLabels,
    timeContext,
    locale,
    t,
  })

  return {
    selectedPlan,
    dayCards: buildDayCards({
      plannerWindows,
      plannerLabels,
      planningPreference,
      selectedPlan,
      selectedDevices,
      timeContext,
      locale,
      t,
    }),
  }
}

function buildSelectedPlan({ recommendation, selectedDevices, plannerLabels, timeContext, locale, t }) {
  const start = recommendation.recommended_start || recommendation.requested_start
  const end = recommendation.recommended_end || recommendation.requested_end

  if (!start || !end) {
    return null
  }

  const scheduleItems = Array.isArray(recommendation.device_schedule) && recommendation.device_schedule.length > 0
    ? recommendation.device_schedule.map((item) => ({
        name: item.device,
        start: item.start,
        end: item.end,
        time: buildTimeLabel(item.start, item.end, timeContext.timezone, locale),
        startLabel: formatTimeInZone(item.start, timeContext.timezone, locale),
        endLabel: formatTimeInZone(item.end, timeContext.timezone, locale),
        durationLabel: formatMinutes(durationBetween(item.start, item.end)),
      }))
    : buildSequentialScheduleItems(selectedDevices, start, timeContext.timezone, locale)

  const scheduleStart = scheduleItems[0]?.start || start
  const scheduleEnd = scheduleItems[scheduleItems.length - 1]?.end || end

  return {
    deviceLabel:
      selectedDevices.length === 1
        ? selectedDevices[0].name
        : t('pages.assistant.schedule.bestPlanTitle', { defaultValue: 'Beste planning' }),
    dateKey: getDateKey(start, timeContext.timezone),
    dayLabel: getRelativeDayName(start, timeContext, plannerLabels),
    timeLabel: buildTimeLabel(scheduleStart, scheduleEnd, timeContext.timezone, locale),
    expectedProduction: `${Number(recommendation.expected_average_power_kw || 0).toFixed(1)} kW`,
    durationLabel: formatDurationFromItems(scheduleItems),
    items: scheduleItems,
  }
}

function buildDayCards({
  plannerWindows,
  plannerLabels,
  planningPreference,
  selectedPlan,
  selectedDevices,
  timeContext,
  locale,
  t,
}) {
  const days = [
    { key: getDateKey(timeContext.serverTime, timeContext.timezone), title: plannerLabels.today },
    { key: getDateKey(addDays(timeContext.serverTime, 1), timeContext.timezone), title: plannerLabels.tomorrow },
    { key: getDateKey(addDays(timeContext.serverTime, 2), timeContext.timezone), title: plannerLabels.dayAfterTomorrow },
  ]
  const preferredDateKey =
    planningPreference === 'today'
      ? days[0].key
      : planningPreference === 'tomorrow'
        ? days[1].key
        : planningPreference === 'dayAfterTomorrow'
          ? days[2].key
          : null

  const visibleDays = preferredDateKey
    ? days.filter((day) => day.key === preferredDateKey)
    : days

  return visibleDays.map((day) => {
    if (selectedPlan?.dateKey === day.key) {
      return {
        ...day,
        deviceLabel: selectedPlan.deviceLabel,
        timeLabel: selectedPlan.timeLabel,
        durationLabel: selectedPlan.durationLabel,
        expectedProduction: selectedPlan.expectedProduction,
        isSelected: true,
      }
    }

    const window = plannerWindows.find((candidate) => candidate.dateKey === day.key)

    if (!window) {
      return {
        ...day,
        empty: true,
        emptyText: t('pages.assistant.schedule.noSuitableMoment', { defaultValue: 'Geen geschikt moment meer' }),
        isSelected: false,
      }
    }

    const items = buildSequentialScheduleItems(selectedDevices, window.start, timeContext.timezone, locale)
    const scheduleStart = items[0]?.start || window.start
    const scheduleEnd = items[items.length - 1]?.end || window.end

    return {
      ...day,
      deviceLabel:
        selectedDevices.length === 1
          ? selectedDevices[0].name
          : t('pages.assistant.schedule.bestPlanTitle', { defaultValue: 'Beste planning' }),
      timeLabel: buildTimeLabel(scheduleStart, scheduleEnd, timeContext.timezone, locale),
      durationLabel: formatDurationFromItems(items),
      expectedProduction: `${(Math.max(Number(window.predictedW || 0), 0) / 1000).toFixed(1)} kW`,
      isSelected: false,
    }
  })
}

function buildEmptyDayCards(timeContext, plannerLabels, planningPreference, t) {
  return buildDayCards({
    plannerWindows: [],
    plannerLabels,
    planningPreference,
    selectedPlan: null,
    selectedDevices: [],
    timeContext,
    locale: 'nl-BE',
    t,
  })
}

function totalUsage(devices) {
  return devices.reduce((sum, device) => sum + Number(device.consumption_kwh || 0), 0).toFixed(1)
}

function totalDuration(devices) {
  const minutes = devices.reduce((sum, device) => sum + Number(device.duration_minutes || 0), 0)

  if (minutes < 60) {
    return `${minutes} min`
  }

  const hours = Math.floor(minutes / 60)
  const remainder = minutes % 60
  return remainder ? `${hours}u ${remainder} min` : `${hours}u`
}

function formatApplianceMeta(device) {
  return `${Number(device.consumption_kwh || 0).toFixed(1)} kWh · ${Number(device.duration_minutes || 60)} min`
}

function buildSequentialScheduleItems(devices, startTimestamp, timezone, locale) {
  let currentStart = startTimestamp

  return devices.map((device) => {
    const durationMinutes = Number(device.duration_minutes || 60)
    const nextEnd = addMinutesToTimestamp(currentStart, durationMinutes)
    const item = {
      name: device.name,
      start: currentStart,
      end: nextEnd,
      time: buildTimeLabel(currentStart, nextEnd, timezone, locale),
      startLabel: formatTimeInZone(currentStart, timezone, locale),
      endLabel: formatTimeInZone(nextEnd, timezone, locale),
      durationLabel: formatMinutes(durationMinutes),
    }

    currentStart = nextEnd
    return item
  })
}

function buildTimeLabel(start, end, timezone, locale) {
  return `${formatTimeInZone(start, timezone, locale)} - ${formatTimeInZone(end, timezone, locale)}`
}

function addMinutesToTimestamp(timestamp, durationMinutes) {
  const date = new Date(timestamp)
  date.setMinutes(date.getMinutes() + Number(durationMinutes || 0))
  return date.toISOString()
}

function formatDurationFromItems(items) {
  const totalMinutes = items.reduce((sum, item) => sum + durationBetween(item.start, item.end), 0)

  return formatMinutes(totalMinutes)
}

function formatMinutes(totalMinutes) {
  if (totalMinutes < 60) {
    return `${totalMinutes} min`
  }

  const hours = Math.floor(totalMinutes / 60)
  const remainder = totalMinutes % 60
  return remainder ? `${hours} uur ${remainder} min` : `${hours} uur`
}

function durationBetween(start, end) {
  const startDate = new Date(start)
  const endDate = new Date(end)
  return Math.max(Math.round((endDate.getTime() - startDate.getTime()) / 60000), 0)
}

function addDays(timestamp, days) {
  const date = new Date(timestamp)
  date.setDate(date.getDate() + days)
  return date.toISOString()
}

function toDateInputValue(date) {
  return date.toISOString().slice(0, 10)
}

function resolvePreferredDate(preference, serverTime) {
  const baseDate = new Date(serverTime)
  const offset = preference === 'tomorrow' ? 1 : preference === 'dayAfterTomorrow' ? 2 : 0
  baseDate.setDate(baseDate.getDate() + offset)
  return toDateInputValue(baseDate)
}

function buildRecommendationPayload({ installationId, planningPreference, serverTime, selected_devices }) {
  const baseDate = new Date(serverTime)
  const payload = {
    installation_id: installationId,
    selected_devices,
  }

  if (planningPreference === 'auto') {
    const start = new Date(serverTime)
    const end = new Date(baseDate)
    end.setDate(baseDate.getDate() + 2)
    end.setHours(23, 59, 59, 999)

    return {
      ...payload,
      start: start.toISOString(),
      end: end.toISOString(),
    }
  }

  return {
    ...payload,
    date: resolvePreferredDate(planningPreference, serverTime),
  }
}

function getActivityKey(activity) {
  return activity.id || activity.name
}

function resolvePlanningSectionTitle(preference, t) {
  if (preference === 'today') {
    return t('pages.assistant.schedule.titleToday', { defaultValue: 'Planning voor vandaag' })
  }

  if (preference === 'tomorrow') {
    return t('pages.assistant.schedule.titleTomorrow', { defaultValue: 'Planning voor morgen' })
  }

  if (preference === 'dayAfterTomorrow') {
    return t('pages.assistant.schedule.titleDayAfterTomorrow', { defaultValue: 'Planning voor overmorgen' })
  }

  return t('pages.assistant.schedule.recommendedTitle', { defaultValue: 'Aanbevolen planning' })
}

function resolvePlanningEmptyState(preference, t) {
  if (preference === 'today') {
    return t('pages.assistant.schedule.emptyToday', { defaultValue: 'Selecteer toestellen en maak een planning voor vandaag.' })
  }

  if (preference === 'tomorrow') {
    return t('pages.assistant.schedule.emptyTomorrow', { defaultValue: 'Selecteer toestellen en maak een planning voor morgen.' })
  }

  if (preference === 'dayAfterTomorrow') {
    return t('pages.assistant.schedule.emptyDayAfterTomorrow', { defaultValue: 'Selecteer toestellen en maak een planning voor overmorgen.' })
  }

  return t('pages.assistant.schedule.emptyAuto', {
    defaultValue: 'SolarWise kiest automatisch het beste moment zodra je op Planning maken klikt.',
  })
}
