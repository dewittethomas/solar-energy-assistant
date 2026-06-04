export function getForecastValidity({ dashboardOutputKw, forecast = [], installationKwp }) {
  const numericCapacity = Number(installationKwp)

  if (!Number.isFinite(numericCapacity) || numericCapacity <= 0) {
    return {
      invalid: false,
      maxObservedKw: null,
      capacityKw: null,
      thresholdKw: null,
    }
  }

  const forecastKilowatts = forecast
    .map((entry) => Number(entry?.predicted_w ?? entry?.value_w ?? 0) / 1000)
    .filter((value) => Number.isFinite(value) && value >= 0)

  const values = [...forecastKilowatts]
  const numericDashboardOutput = Number(dashboardOutputKw)

  if (Number.isFinite(numericDashboardOutput) && numericDashboardOutput >= 0) {
    values.push(numericDashboardOutput)
  }

  const maxObservedKw = values.length ? Math.max(...values) : null
  const thresholdKw = numericCapacity * 1.2

  return {
    invalid: Number.isFinite(maxObservedKw) && maxObservedKw > thresholdKw,
    maxObservedKw,
    capacityKw: numericCapacity,
    thresholdKw,
  }
}
