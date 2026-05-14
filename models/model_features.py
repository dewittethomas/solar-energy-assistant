RADIATION_COLUMNS = [
    'shortwave_radiation',
    'diffuse_radiation',
    'direct_normal_irradiance',
    'terrestrial_radiation'
]
WEATHER_COLUMNS = [
    'cloud_cover',
    *RADIATION_COLUMNS
]
FEATURE_COLUMNS = [
    *WEATHER_COLUMNS,
    'hour_sin',
    'hour_cos',
    'day_of_year_sin',
    'day_of_year_cos'
]
MONTHLY_FEATURE_COLUMNS = [
    *WEATHER_COLUMNS,
    'month_sin',
    'month_cos',
    'day_of_year_sin',
    'day_of_year_cos'
]
