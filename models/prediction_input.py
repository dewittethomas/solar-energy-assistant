from pydantic import BaseModel

class PredictionInput(BaseModel):
    cloud_cover: float
    shortwave_radiation: float
    diffuse_radiation: float
    direct_normal_irradiance: float
    terrestrial_radiation: float
    hour_sin: float
    hour_cos: float
    day_of_year_sin: float
    day_of_year_cos: float