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

        raw_predictions = np.asarray(raw_predictions).reshape(-1)

        shortwave_radiation = input_tensor[:, 1]
        scale = 1 / (1 + np.exp(-0.1 * (shortwave_radiation - 30)))

        scaled_predictions = raw_predictions * scale

        results = []

        for i, pred in enumerate(scaled_predictions):
            results.append(
                PredictionOutput(
                    timestamp=datetime.fromisoformat(time_data[i]),
                    value=float(pred)
                )
            )

        return results