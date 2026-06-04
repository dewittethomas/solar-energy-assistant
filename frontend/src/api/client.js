const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const predictionCache = new Map()
const dashboardCache = new Map()
const PREDICTION_CACHE_TTL_MS = 60_000
const DASHBOARD_CACHE_TTL_MS = 15 * 60_000

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)
    const error = new Error(errorBody?.detail || `Request failed: ${response.status}`)
    error.status = response.status
    throw error
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

function appendDefined(formData, key, value) {
  if (value !== undefined && value !== null && value !== '') {
    formData.append(key, value)
  }
}

function normalizeTimeEnvelope(payload = {}) {
  return {
    ...payload,
    server_time: payload.server_time || new Date().toISOString(),
    timezone: payload.timezone || 'Europe/Brussels',
  }
}

function normalizePredictionResponse(payload = {}) {
  if (payload?.status === 'not_ready') {
    return normalizeTimeEnvelope(payload)
  }

  if (Array.isArray(payload)) {
    return normalizeTimeEnvelope({
      forecast: payload.map((entry) => normalizePredictionPoint(entry, payload.unit)),
    })
  }

  if (Array.isArray(payload.forecast)) {
    return normalizeTimeEnvelope({
      ...payload,
      forecast: payload.forecast.map((entry) => normalizePredictionPoint(entry, payload.unit)),
    })
  }

  const flattenedForecast = Array.isArray(payload.predictions)
    ? payload.predictions.flatMap((dayBlock) => {
        if (Array.isArray(dayBlock.predictions)) {
          return dayBlock.predictions.map((entry) => ({
            timestamp: `${dayBlock.day}T${String(entry.hour).slice(0, 5)}:00`,
            predicted_w: normalizePredictedWatts(entry, payload.unit),
          }))
        }

        return {
          timestamp: dayBlock.timestamp,
          predicted_w: normalizePredictedWatts(dayBlock, payload.unit),
        }
      })
    : []

  return normalizeTimeEnvelope({
    ...payload,
    unit: payload.unit || 'W',
    forecast: flattenedForecast.filter(Boolean),
  })
}

function normalizePredictionPoint(entry = {}, fallbackUnit) {
  return {
    timestamp: entry.timestamp || entry.datetime || entry.time || entry.date_time,
    predicted_w: normalizePredictedWatts(entry, fallbackUnit),
  }
}

function normalizePredictedWatts(entry = {}, fallbackUnit) {
  const unit = String(entry.unit || fallbackUnit || '').toLowerCase()
  const kwValue = entry.predicted_kw ?? entry.predictedKw ?? entry.value_kw ?? entry.kw
  const wValue = entry.predicted_w ?? entry.predictedW ?? entry.prediction_w ?? entry.value_w
  const genericValue = entry.value

  let numeric = Number(kwValue ?? wValue ?? genericValue ?? 0)

  if (!Number.isFinite(numeric)) {
    return 0
  }

  if (kwValue !== undefined || unit === 'kw') {
    numeric *= 1000
  }

  return sanitizePredictedWatts(numeric)
}

function sanitizePredictedWatts(value) {
  if (!Number.isFinite(value) || value < 0) {
    return 0
  }

  if (value > 50000) {
    return 0
  }

  return value
}

function normalizeRecommendationResponse(payload = {}) {
  const normalized = normalizeTimeEnvelope(payload)
  const bestWindowStart = normalized.best_window_start || null
  const bestWindowEnd = normalized.best_window_end || null

  return {
    ...normalized,
    expected_production_kwh: normalized.expected_production_kwh ?? normalized.expected_kwh ?? null,
    recommended_time_window:
      normalized.recommended_time_window ||
      (bestWindowStart && bestWindowEnd ? `${bestWindowStart}|${bestWindowEnd}` : null),
  }
}

function buildPredictionCacheKey(installationId, startDate, endDate) {
  return `${installationId}:${startDate}:${endDate}`
}

function buildDashboardCacheKey(installationId) {
  return `dashboard:${installationId}`
}

function readCache(cache, key, ttlMs) {
  const entry = cache.get(key)

  if (!entry) {
    return null
  }

  if (Date.now() - entry.createdAt > ttlMs) {
    cache.delete(key)
    return null
  }

  return entry.promise
}

function writeCache(cache, key, promise) {
  cache.set(key, {
    createdAt: Date.now(),
    promise,
  })

  return promise
}

function toDateInputValue(date) {
  return date.toISOString().slice(0, 10)
}

export const api = {
  getOwner() {
    return request('/owner')
  },

  createOwner(payload) {
    return request('/owner', {
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
    })
  },

  updateOwner(payload) {
    return request('/owner', {
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
      method: 'PUT',
    })
  },

  createInstallation(payload) {
    return request('/installations', {
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
    })
  },

  getActiveInstallation() {
    return request('/installations/active')
  },

  resetLocalState() {
    return request('/developer/reset-local-state', {
      method: 'POST',
    })
  },

  deleteOwner() {
    return request('/developer/owner', {
      method: 'DELETE',
    })
  },

  listDatasets(installationId) {
    const query = installationId ? `?installation_id=${encodeURIComponent(installationId)}` : ''
    return request(`/datasets${query}`)
  },

  getDataset(datasetId) {
    return request(`/datasets/${encodeURIComponent(datasetId)}`)
  },

  getDatasetAnalytics(datasetId) {
    return request(`/datasets/${encodeURIComponent(datasetId)}/analytics`)
  },

  uploadDataset({ file, installationId, mapping }) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('installation_id', installationId)
    appendDefined(formData, 'mapping', mapping ? JSON.stringify(mapping) : null)

    return request('/datasets', {
      body: formData,
      method: 'POST',
    })
  },

  getTrainingRun(trainingRunId) {
    return request(`/models/training-runs/${encodeURIComponent(trainingRunId)}`)
  },

  trainModelFromParquet(parquetPath) {
    const formData = new FormData()
    formData.append('parquet_path', parquetPath)
    formData.append('activate_model', 'true')

    return request('/models/train', {
      body: formData,
      method: 'POST',
    })
  },

  inspectDataset(file) {
    const formData = new FormData()
    formData.append('file', file)

    return request('/datasets/inspect', {
      body: formData,
      method: 'POST',
    })
  },

  getDashboard(installationId) {
    const cacheKey = buildDashboardCacheKey(installationId)
    const cached = readCache(dashboardCache, cacheKey, DASHBOARD_CACHE_TTL_MS)

    if (cached) {
      return cached
    }

    const requestPromise = request(`/installations/${encodeURIComponent(installationId)}/dashboard`)
      .then(normalizeTimeEnvelope)
      .catch((error) => {
        dashboardCache.delete(cacheKey)
        throw error
      })

    return writeCache(dashboardCache, cacheKey, requestPromise)
  },

  getPredictions(installationId, startDate, endDate) {
    const cacheKey = buildPredictionCacheKey(installationId, startDate, endDate)
    const cached = readCache(predictionCache, cacheKey, PREDICTION_CACHE_TTL_MS)

    if (cached) {
      return cached
    }

    const searchParams = new URLSearchParams({ start_date: startDate, end_date: endDate })
    searchParams.set('installation_id', installationId)

    const requestPromise = request(`/predictions?${searchParams}`)
      .catch(() => {
        searchParams.delete('installation_id')
        return request(`/installations/${encodeURIComponent(installationId)}/predictions?${searchParams}`)
      })
      .then(normalizePredictionResponse)
      .catch((error) => {
        predictionCache.delete(cacheKey)
        throw error
      })

    return writeCache(predictionCache, cacheKey, requestPromise)
  },

  getThreeDayPredictions(installationId, referenceDate = new Date()) {
    const startDate = new Date(referenceDate)
    const endDate = new Date(referenceDate)
    endDate.setDate(startDate.getDate() + 2)

    return this.getPredictions(
      installationId,
      toDateInputValue(startDate),
      toDateInputValue(endDate),
    )
  },

  getConfiguration(installationId) {
    return request(`/installations/${encodeURIComponent(installationId)}/configuration`)
  },

  saveConfiguration(installationId, configuration) {
    return request(`/installations/${encodeURIComponent(installationId)}/configuration`, {
      body: JSON.stringify(configuration),
      headers: { 'Content-Type': 'application/json' },
      method: 'PUT',
    })
  },

  listModels(installationId) {
    const query = installationId ? `?installation_id=${encodeURIComponent(installationId)}` : ''
    return request(`/models${query}`)
  },

  activateModel(modelId) {
    return request(`/models/${encodeURIComponent(modelId)}/activate`, {
      method: 'PATCH',
    })
  },

  recommendUsageWindow(payload) {
    return request('/recommendations/usage-window', {
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
    }).then(normalizeRecommendationResponse)
  },
}
