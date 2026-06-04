import numpy as np
import pandas as pd
from pvlib import solarposition

WEATHER_COLUMNS = [
    'direct_normal_irradiance',
    'diffuse_radiation',
    'shortwave_radiation',
    'cloud_cover',
    'temperature_2m',
    'relative_humidity_2m',
    'wind_speed_10m',
    'surface_pressure',
]
SOLAR_POSITION_COLUMNS = [
    'solar_elevation_deg',
    'solar_azimuth_deg',
]
CYCLICAL_FEATURE_COLUMNS = [
    'hour_sin',
    'hour_cos',
    'day_of_year_sin',
    'day_of_year_cos',
]
FEATURE_COLUMNS = [
    *WEATHER_COLUMNS,
    *SOLAR_POSITION_COLUMNS,
    *CYCLICAL_FEATURE_COLUMNS,
]

def generate_solar_position_data(
    start_date: str | pd.Timestamp,
    end_date: str | pd.Timestamp,
    latitude: float,
    longitude: float,
    timezone: str = 'Europe/Brussels',
    frequency: str = 'h',
    include_night: bool = True,
) -> pd.DataFrame:
    times = pd.date_range(
        start=start_date,
        end=end_date,
        freq=frequency,
        tz=timezone,
        inclusive='left',
    )

    solpos = solarposition.get_solarposition(
        time=times,
        latitude=latitude,
        longitude=longitude,
    )

    result = pd.DataFrame({
        'datetime': solpos.index.tz_localize(None),
        'solar_elevation_deg': solpos['apparent_elevation'].values,
        'solar_azimuth_deg': solpos['azimuth'].values,
    })

    if not include_night:
        result = result[result['solar_elevation_deg'] > 0]

    return result.reset_index(drop=True)

def add_cyclical_time_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result['hour'] = result['timestamp'].dt.hour
    result['day_of_year'] = result['timestamp'].dt.dayofyear

    hour_angle = 2 * np.pi * result['hour'] / 24
    day_angle = 2 * np.pi * result['day_of_year'] / 365
    result['hour_sin'] = np.sin(hour_angle)
    result['hour_cos'] = np.cos(hour_angle)
    result['day_of_year_sin'] = np.sin(day_angle)
    result['day_of_year_cos'] = np.cos(day_angle)

    return result.drop(columns=['hour', 'day_of_year'])