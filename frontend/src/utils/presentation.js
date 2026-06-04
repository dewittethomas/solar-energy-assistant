import { countryOptions, countryValueToCode } from '../data/countries.js'

export function convertWattsToUnit(value, unit = 'kW') {
  const numeric = Number(value || 0)

  if (!Number.isFinite(numeric)) {
    return 0
  }

  if (String(unit).toLowerCase() === 'w') {
    return numeric
  }

  return numeric / 1000
}

export function convertKilowattsToUnit(value, unit = 'kW') {
  const numeric = Number(value || 0)

  if (!Number.isFinite(numeric)) {
    return 0
  }

  if (String(unit).toLowerCase() === 'w') {
    return numeric * 1000
  }

  return numeric
}

export function formatPowerFromWatts(value, unit = 'kW', locale = 'nl-BE', digits) {
  return formatProductionValue(convertWattsToUnit(value, unit), unit, locale, digits)
}

export function formatPowerFromKilowatts(value, unit = 'kW', locale = 'nl-BE', digits) {
  return formatProductionValue(convertKilowattsToUnit(value, unit), unit, locale, digits)
}

export function formatProductionValue(value, unit = 'kW', locale = 'nl-BE', digits) {
  const numeric = Number(value)

  if (!Number.isFinite(numeric)) {
    return '-'
  }

  const decimals = digits ?? (unit === 'W' || unit === 'Wh' ? 0 : 1)

  return `${new Intl.NumberFormat(locale, {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  }).format(numeric)} ${unit}`
}

export function formatTemperature(value) {
  if (value === null || value === undefined) {
    return null
  }

  return `${Math.round(Number(value))} °C`
}

export function formatUiDate(value, locale = 'nl-BE') {
  if (!value) {
    return '-'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return '-'
  }

  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}

export function formatUiDateRange(start, end, locale = 'nl-BE') {
  if (!start || !end) {
    return '-'
  }

  return `${formatUiDate(start, locale)} - ${formatUiDate(end, locale)}`
}

export function mapWeatherLabel(status, t) {
  const key = String(status || '').trim().toLowerCase()

  if (!key) {
    return '-'
  }

  const labelKey = {
    clear: 'weather.labels.clear',
    sunny: 'weather.labels.sunny',
    partly_cloudy: 'weather.labels.partlyCloudy',
    cloudy: 'weather.labels.cloudy',
    rain: 'weather.labels.rain',
    light_rain: 'weather.labels.lightRain',
    overcast: 'weather.labels.overcast',
  }[key]

  return labelKey
    ? t(labelKey)
    : key.replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

export function translateSeason(label, t) {
  const key = String(label || '').trim().toLowerCase()
  const labelKey = {
    winter: 'seasons.winter',
    spring: 'seasons.spring',
    summer: 'seasons.summer',
    autumn: 'seasons.autumn',
    fall: 'seasons.autumn',
    lente: 'seasons.spring',
    zomer: 'seasons.summer',
    herfst: 'seasons.autumn',
  }[key]

  return labelKey ? t(labelKey) : label
}

export function formatAccuracyPercent(value, t) {
  const numeric = Number(value)

  if (!Number.isFinite(numeric)) {
    return t('pages.models.notAvailable')
  }

  return `${Math.round(numeric * 100)}%`
}

export function formatModelDisplayName(model, t) {
  const raw = String(model.model_name || model.model_type || model.name || '').trim().toLowerCase()
  const mapped = {
    catboost: t('pages.models.names.catboostDefault', { defaultValue: 'CatBoost voorspellingsmodel' }),
    catboost_default: t('pages.models.names.catboostDefault', { defaultValue: 'CatBoost voorspellingsmodel' }),
    xgboost_default: t('pages.models.names.xgboostDefault', { defaultValue: 'XGBoost voorspellingsmodel' }),
    random_forest: t('pages.models.names.randomForestBaseline', { defaultValue: 'Random Forest voorspellingsmodel' }),
    random_forest_baseline: t('pages.models.names.randomForestBaseline', { defaultValue: 'Random Forest voorspellingsmodel' }),
    linear_regression: t('pages.models.names.linearRegressionBaseline', { defaultValue: 'Linear Regression voorspellingsmodel' }),
    linear_regression_baseline: t('pages.models.names.linearRegressionBaseline', { defaultValue: 'Linear Regression voorspellingsmodel' }),
  }[raw]

  if (mapped) {
    return mapped
  }

  const suffix = String(model.id || model.model_id || '').replace(/^model-/, '').slice(0, 8)
  return `${t('pages.models.names.fallback', { defaultValue: 'Voorspellingsmodel' })} ${suffix || 'standaard'}`
}

export function formatDatasetDisplayName(dataset, t) {
  const explicitName = String(dataset.source_name || dataset.filename || '').trim()
  const normalizedExplicit = explicitName.toLowerCase()

  if (explicitName && !normalizedExplicit.startsWith('standardized')) {
    return explicitName
  }

  const rawPath = String(dataset.dataset_path || dataset.path || '').trim()
  const fileName = rawPath.split('/').pop()?.split('\\').pop()

  if (fileName) {
    const normalizedFileName = fileName.toLowerCase()

    if (!normalizedFileName.endsWith('.parquet') && !normalizedFileName.startsWith('standardized')) {
      return fileName
    }
  }

  const rawId = String(dataset.dataset_id || dataset.id || dataset.dataset_hash || '')
  const suffix = rawId.replace(/^dataset-/, '').slice(0, 8)
  return `${t('pages.models.datasetFriendly', { defaultValue: 'Productiedataset' })} ${suffix}`
}

export function formatCountryLabel(country, t) {
  if (!country) {
    return ''
  }

  const code = /^[A-Z]{2}$/.test(String(country)) ? String(country) : countryValueToCode(String(country))
  const option = countryOptions.find((candidate) => candidate.code === code)
  return option ? t(option.labelKey) : String(country)
}

export function formatLocationLabel(city, country, t) {
  return [city, formatCountryLabel(country, t)].filter(Boolean).join(', ')
}
