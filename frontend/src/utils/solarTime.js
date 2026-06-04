const DEFAULT_TIMEZONE = 'Europe/Brussels'
const DEFAULT_MINIMUM_WINDOW_KW = 0.5
const DEFAULT_MINIMUM_PEAK_RATIO = 0.35

export function resolveTimeContext(payload = {}) {
  return {
    serverTime: payload.server_time || payload.serverTime || new Date().toISOString(),
    timezone: payload.timezone || DEFAULT_TIMEZONE,
  }
}

export function getDateKey(timestamp, timezone = DEFAULT_TIMEZONE) {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(timestamp))
}

export function formatTimeInZone(timestamp, timezone = DEFAULT_TIMEZONE, locale = 'nl-BE') {
  return new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: timezone,
  }).format(new Date(timestamp))
}

export function getRelativeDayName(timestamp, { serverTime, timezone }, labels) {
  const base = new Date(serverTime)
  const targetKey = getDateKey(timestamp, timezone)
  const todayKey = getDateKey(base, timezone)

  if (targetKey === todayKey) {
    return labels.today
  }

  const tomorrow = new Date(base)
  tomorrow.setDate(base.getDate() + 1)
  const dayAfterTomorrow = new Date(base)
  dayAfterTomorrow.setDate(base.getDate() + 2)

  if (targetKey === getDateKey(tomorrow, timezone)) {
    return labels.tomorrow
  }

  if (targetKey === getDateKey(dayAfterTomorrow, timezone)) {
    return labels.dayAfterTomorrow
  }

  return new Intl.DateTimeFormat('nl-BE', {
    day: '2-digit',
    month: '2-digit',
    timeZone: timezone,
  }).format(new Date(timestamp))
}

export function isPastTimestamp(timestamp, serverTime) {
  return new Date(timestamp).getTime() < new Date(serverTime).getTime()
}

export function buildWindowLabel(start, end, timezone = DEFAULT_TIMEZONE, locale = 'nl-BE') {
  return `${formatTimeInZone(start, timezone, locale)} - ${formatTimeInZone(end, timezone, locale)}`
}

export function buildPlannerWindows(forecast, timeContext, options = {}) {
  const { serverTime, timezone } = timeContext
  const intervalHours = options.intervalHours || 3
  const locale = options.locale || 'nl-BE'
  const mode = options.mode || 'per_day'
  const filterPast = options.filterPast !== false
  const thresholdKw = options.minimumWindowKw ?? DEFAULT_MINIMUM_WINDOW_KW
  const thresholdRatio = options.minimumPeakRatio ?? DEFAULT_MINIMUM_PEAK_RATIO
  const targetDateKey = options.targetDateKey || null
  const byDay = new Map()
  const allCandidates = []

  forecast.forEach((entry, index) => {
    if (!entry?.timestamp) {
      return
    }

    const dayKey = getDateKey(entry.timestamp, timezone)
    const nextEntry = forecast[index + 1]
    const start = entry.timestamp
    const end =
      nextEntry && getDateKey(nextEntry.timestamp, timezone) === dayKey
        ? nextEntry.timestamp
        : new Date(new Date(start).getTime() + intervalHours * 60 * 60 * 1000).toISOString()

    const candidate = {
      dateKey: dayKey,
      start,
      end,
      predictedW: Number(entry.predicted_w ?? entry.predictedW ?? entry.value_w ?? entry.value ?? 0),
      predictedKw: Number(entry.predicted_w ?? entry.predictedW ?? entry.value_w ?? entry.value ?? 0) / 1000,
      isPast: isPastTimestamp(end, serverTime),
      label: buildWindowLabel(start, end, timezone, locale),
    }

    if (targetDateKey && dayKey !== targetDateKey) {
      return
    }

    allCandidates.push(candidate)

    const current = byDay.get(dayKey)
    const betterCandidate =
      (!filterPast || !candidate.isPast) &&
      (!current || current.isPast || candidate.predictedW > current.predictedW)

    if (!current || betterCandidate || (!current.isPast && candidate.predictedW > current.predictedW)) {
      byDay.set(dayKey, candidate)
    }
  })

  const peakByDay = new Map()
  allCandidates.forEach((candidate) => {
    const currentPeak = peakByDay.get(candidate.dateKey) ?? 0
    if (candidate.predictedKw > currentPeak) {
      peakByDay.set(candidate.dateKey, candidate.predictedKw)
    }
  })

  const filtered = Array.from(byDay.values()).filter((candidate) => {
    if (filterPast && candidate.isPast) {
      return false
    }

    const dayPeak = peakByDay.get(candidate.dateKey) ?? 0

    if (candidate.predictedKw < thresholdKw) {
      return false
    }

    if (dayPeak > 0 && candidate.predictedKw < dayPeak * thresholdRatio) {
      return false
    }

    return true
  })

  if (mode === 'best_overall') {
    return filtered.sort((left, right) => right.predictedW - left.predictedW).slice(0, 1)
  }

  return filtered.slice(0, 3)
}
