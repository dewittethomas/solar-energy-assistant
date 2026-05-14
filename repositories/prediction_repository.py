from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import onnxruntime as ort

from models.prediction import Prediction
from responses.prediction_result import (
    DailyPredictionResult,
    HourlyPredictionResult,
    PredictionResult,
)

class PredictionRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, tuple[ort.InferenceSession, str]] = {}

    def predict_solar_yield(
        self,
        model_path: Path,
        prediction_inputs: list[Prediction],
        time_data: list[str]
    ) -> PredictionResult:
        session, input_name = self._get_session(model_path)
        input_tensor = self._build_input_tensor(prediction_inputs)
        raw_predictions = session.run(
            None,
            {input_name: input_tensor}
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

    def _get_session(self, model_path: Path) -> tuple[ort.InferenceSession, str]:
        resolved_path = self._resolve_model_path(model_path)
        cache_key = resolved_path.as_posix()

        cached_session = self._sessions.get(cache_key)

        if cached_session:
            return cached_session

        session_options = ort.SessionOptions()
        session_options.intra_op_num_threads = 2
        session_options.inter_op_num_threads = 1
        session = ort.InferenceSession(
            resolved_path.as_posix(),
            sess_options=session_options,
            providers=['CPUExecutionProvider']
        )
        input_name = session.get_inputs()[0].name
        self._sessions[cache_key] = (session, input_name)

        return self._sessions[cache_key]

    def _resolve_model_path(self, model_path: Path) -> Path:
        resolved_path = (
            model_path
            if model_path.is_absolute()
            else Path.cwd() / model_path
        )

        if not resolved_path.exists():
            raise ValueError(f'Model file does not exist: {model_path}')

        return resolved_path

    def _build_input_tensor(
        self,
        prediction_inputs: list[Prediction]
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
        time_data: list[str]
    ) -> PredictionResult:
        grouped_days = defaultdict(list)

        for prediction, time_value in zip(predictions, time_data):
            timestamp = datetime.fromisoformat(time_value)
            grouped_days[timestamp.date()].append(
                HourlyPredictionResult(
                    hour=timestamp.time(),
                    value=float(prediction)
                )
            )

        daily_results = []

        for day, hourly_predictions in sorted(grouped_days.items()):
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
