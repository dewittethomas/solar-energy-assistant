export const datasets = [
  {
    id: 'dataset-001',
    location: 'Brussels',
    resolutionKey: 'demo.resolution.hourly',
    rows: '8,760',
    dateRange: 'Jan 2024 - Dec 2024',
    statusKey: 'demo.status.ready',
  },
  {
    id: 'dataset-002',
    location: 'Ghent',
    resolutionKey: 'demo.resolution.fifteenMinutes',
    rows: '35,040',
    dateRange: 'Jan 2025 - Dec 2025',
    statusKey: 'demo.status.ready',
  },
  {
    id: 'dataset-003',
    location: 'Antwerp',
    resolutionKey: 'demo.resolution.hourly',
    rows: '4,320',
    dateRange: 'Jan 2026 - Jun 2026',
    statusKey: 'demo.status.ready',
  },
]

export const models = [
  {
    id: 'model-001',
    name: 'XGBoost Solar Forecast',
    dataset: 'dataset-001',
    trainedOn: 'May 12, 2026',
    r2: '0.91',
    mse: '0.18 kW',
  },
  {
    id: 'model-002',
    name: 'Random Forest Baseline',
    dataset: 'dataset-002',
    trainedOn: 'May 8, 2026',
    r2: '0.86',
    mse: '0.27 kW',
  },
  {
    id: 'model-003',
    name: 'Linear Regression Benchmark',
    dataset: 'dataset-003',
    trainedOn: 'Apr 30, 2026',
    r2: '0.74',
    mse: '0.46 kW',
  },
]
