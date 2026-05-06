import onnxruntime as ort
import numpy as np
from typing import List

from models.prediction_input import PredictionInput
from models.prediction_output import PredictionOutput
from core.settings import get_settings
from datetime import datetime


class PredictionRepository:
    def __init__(self):
        settings = get_settings()

        self.session = ort.InferenceSession(settings.model_file)
        self.input_name = self.session.get_inputs()[0].name
    def predict_solar_yield(
        self,
        prediction_inputs: List[PredictionInput],
        time_data: List[str]
    ) -> List[PredictionOutput]:
        input_tensor = np.array(
            [
                [
                    inp.temperature_2m,
                    inp.wind_direction_10m,
                    inp.wind_speed_10m,
                    inp.cloud_cover,
                    inp.shortwave_radiation,
                    inp.diffuse_radiation,
                    inp.direct_normal_irradiance,
                    inp.terrestrial_radiation,
                    inp.hour_sin,
                    inp.hour_cos,
                    inp.day_of_year_sin,
                    inp.day_of_year_cos
                ]
                for inp in prediction_inputs
            ],
            dtype=np.float32
        )

        raw_predictions = self.session.run(
            None,
            {self.input_name: input_tensor}
        )[0]

        predictions = np.maximum(0.0, raw_predictions)

        results = []

        for i, pred in enumerate(predictions):
            timestamp = datetime.fromisoformat(time_data[i])

            value = float(pred[0]) if hasattr(pred, "__len__") else float(pred)

            results.append(
                PredictionOutput(
                    timestamp=timestamp,
                    value=value
                )
            )

        return results