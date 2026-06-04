from pydantic import BaseModel

class Prediction(BaseModel):
    direct_normal_irradiance: float
    diffuse_radiation: float
    shortwave_radiation: float
    cloud_cover: float
    temperature_2m: float
    relative_humidity_2m: float
    wind_speed_10m: float
    surface_pressure: float
    solar_elevation_deg: float
    solar_azimuth_deg: float
    hour_sin: float
    hour_cos: float
    day_of_year_sin: float
    day_of_year_cos: float
