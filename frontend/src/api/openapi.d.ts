export interface OwnerPayload {
  first_name: string
  last_name?: string | null
}

export interface OwnerResult {
  id: string
  first_name: string
  last_name?: string | null
  display_name: string
  created_at: string
  updated_at: string
}

export interface InstallationCreate {
  name: string
  city: string
  country: string
  panel_count?: number | null
  capacity_kwp?: number | null
}

export interface ConsumingActivity {
  id?: string | null
  name: string
  consumption_kwh: number
  category?: string | null
  is_custom?: boolean
  duration_minutes?: number
}

export interface SelectedDevice {
  name: string
  consumption_kwh: number
  duration_minutes?: number
}

export interface InstallationConfigurationResult {
  id: string
  owner_id: string
  installation_id: string
  is_active?: boolean | null
  name?: string | null
  city?: string | null
  country?: string | null
  latitude?: number | null
  longitude?: number | null
  panel_count?: number | null
  capacity_kwp?: number | null
  available_consuming_activities: ConsumingActivity[]
  consuming_activities: ConsumingActivity[]
  appliances: Record<string, number>
}

export type ActiveInstallationResult = InstallationConfigurationResult

export interface PredictionNotReadyResult {
  status: string
  detail?: string
}

export interface DataUploadResult {
  dataset_id: string
  dataset_hash: string
  dataset_already_exists: boolean
  installation_id: string
  source_name?: string | null
  production_unit: string
  rows: number
  columns: string[]
  original_columns?: string[]
  internal_columns?: string[]
  value_column: string
  date_column?: string | null
  time_column?: string | null
  measurement_column?: string | null
  time_resolution: {
    kind: string
    interval_minutes: number | null
  }
  parquet_path: string
}

export interface DatasetResult {
  id: string
  installation_id: string
  dataset_hash: string
  path: string
  row_count: number
  granularity: string
  value_column: string
  production_unit?: string | null
  created_at: string
  period_start?: string | null
  period_end?: string | null
  source_name?: string | null
  original_columns?: string[]
  internal_columns?: string[]
  date_column?: string | null
  time_column?: string | null
  measurement_column?: string | null
}

export interface DatasetAnalyticsPoint {
  label: string
  value: number
}

export interface DatasetAnalyticsResult {
  dataset_id: string
  period_start: string
  period_end: string
  production_unit?: string | null
  monthly_series: DatasetAnalyticsPoint[]
  seasonal_series: DatasetAnalyticsPoint[]
  best_month: string
  strongest_season: string
  best_window_start: string
  best_window_end: string
  peak_hour: string
  summer_winter_difference_pct: number
}
