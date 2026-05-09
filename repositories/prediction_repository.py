import onnxruntime as ort
import numpy as np

from collections import defaultdict
from datetime import datetime
from typing import List

from core.settings import get_settings
from models.prediction import Prediction
from responses.prediction_result import (
    PredictionResult,
    DailyPredictionResult,
    HourlyPredictionResult,
)

class PredictionRepository:
    def __init__(self):
        settings = get_settings()

        session_options = ort.SessionOptions()
        session_options.intra_op_num_threads = 2
        session_options.inter_op_num_threads = 1

        self.session = ort.InferenceSession(
            settings.model_file,
            sess_options=session_options,
            providers=['CPUExecutionProvider']
        )
        self.input_name = self.session.get_inputs()[0].name

    def predict_solar_yield(
        self,
        prediction_inputs: List[Prediction],
        time_data: List[str]
    ) -> PredictionResult:
        input_tensor = self._build_input_tensor(prediction_inputs)

        raw_predictions = self.session.run(
            None,
            {self.input_name: input_tensor}
        )[0]

        raw_predictions = np.asarray(raw_predictions).reshape(-1)

        final_predictions = self._post_process_predictions(
            raw_predictions,
            input_tensor
        )

        return self._build_response(
            final_predictions,
            time_data
        )

    def _build_input_tensor(
        self,
        prediction_inputs: List[Prediction]
    ) -> np.ndarray:
        return np.array(
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

    def _post_process_predictions(
        self,
        raw_predictions: np.ndarray,
        input_tensor: np.ndarray
    ) -> np.ndarray:
        shortwave_radiation = input_tensor[:, 1]

        scale = 1 / (
            1 + np.exp(-0.1 * (shortwave_radiation - 30))
        )

        scaled_predictions = raw_predictions * scale

        return np.maximum(
            scaled_predictions,
            0.0
        )

    def _build_response(
        self,
        predictions: np.ndarray,
        time_data: List[str]
    ) -> PredictionResult:
        grouped_days = defaultdict(list)

        for i, prediction in enumerate(predictions):
            timestamp = datetime.fromisoformat(
                time_data[i]
            )

            grouped_days[timestamp.date()].append(
                HourlyPredictionResult(
                    hour=timestamp.time(),
                    value=float(prediction)
                )
            )

        daily_results = []

        for day, hourly_predictions in grouped_days.items():
            daily_average = np.mean(
                [p.value for p in hourly_predictions]
            )

            daily_results.append(
                DailyPredictionResult(
                    day=day,
                    average=float(daily_average),
                    predictions=hourly_predictions
                )
            )

        total_average = np.mean(predictions)

        return PredictionResult(
            total_average=float(total_average),
            predictions=daily_results
        )