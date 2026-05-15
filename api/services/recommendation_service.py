from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from models.recommendation import UsageWindowRecommendationRequest
from responses.prediction_result import PredictionResult
from responses.recommendation_result import UsageWindowRecommendationResult
from services.prediction_service import PredictionService

@dataclass(frozen=True)
class PredictionSlot:
    start: datetime
    end: datetime
    power_kw: float
    energy_kwh: float

@dataclass(frozen=True)
class UsageWindowCandidate:
    start: datetime
    end: datetime
    duration_hours: float
    solar_energy_kwh: float
    average_power_kw: float

class RecommendationService:
    def __init__(
        self,
        prediction_service: PredictionService
    ) -> None:
        self.prediction_service = prediction_service

    def recommend_usage_window(
        self,
        request: UsageWindowRecommendationRequest
    ) -> UsageWindowRecommendationResult:
        start = self._to_local_naive(request.start)
        end = self._to_local_naive(request.end)
        self._validate_request_window(start, end)
        predictions = self.prediction_service.predict_solar_yield(
            installation_id=request.installation_id,
            start_date=start.date().isoformat(),
            end_date=end.date().isoformat()
        )
        slots = self._build_slots(predictions, start, end)
        candidates = self._build_candidates(slots)
        candidate = self._select_candidate(
            candidates
        )

        return self._build_result(
            request,
            start,
            end,
            candidate
        )

    def _validate_request_window(
        self,
        start: datetime,
        end: datetime
    ) -> None:
        if end <= start:
            raise ValueError('end must be after start')

    def _build_slots(
        self,
        predictions: PredictionResult,
        start: datetime,
        end: datetime
    ) -> list[PredictionSlot]:
        slots = []

        for day in predictions.predictions:
            for prediction in day.predictions:
                slot_start = datetime.combine(day.day, prediction.hour)
                slot_end = slot_start + timedelta(hours=1)
                clipped_start = max(slot_start, start)
                clipped_end = min(slot_end, end)

                if clipped_end <= clipped_start:
                    continue

                duration_hours = (
                    clipped_end - clipped_start
                ).total_seconds() / 3600
                power_kw = prediction.value / 1000
                slots.append(
                    PredictionSlot(
                        start=clipped_start,
                        end=clipped_end,
                        power_kw=power_kw,
                        energy_kwh=power_kw * duration_hours
                    )
                )

        if not slots:
            raise ValueError('No forecast data found inside the requested window')

        return slots

    def _build_candidates(
        self,
        slots: list[PredictionSlot]
    ) -> list[UsageWindowCandidate]:
        candidates = []

        for start_index in range(len(slots)):
            solar_energy_kwh = 0.0
            duration_hours = 0.0

            for end_index in range(start_index, len(slots)):
                slot = slots[end_index]
                solar_energy_kwh += slot.energy_kwh
                duration_hours += (
                    slot.end - slot.start
                ).total_seconds() / 3600
                candidates.append(
                    UsageWindowCandidate(
                        start=slots[start_index].start,
                        end=slot.end,
                        duration_hours=duration_hours,
                        solar_energy_kwh=solar_energy_kwh,
                        average_power_kw=solar_energy_kwh / duration_hours
                    )
                )

        return candidates

    def _select_candidate(
        self,
        candidates: list[UsageWindowCandidate]
    ) -> UsageWindowCandidate:
        return max(
            candidates,
            key=lambda candidate: (
                candidate.average_power_kw,
                -candidate.duration_hours,
                -candidate.start.timestamp()
            )
        )

    def _build_result(
        self,
        request: UsageWindowRecommendationRequest,
        start: datetime,
        end: datetime,
        candidate: UsageWindowCandidate
    ) -> UsageWindowRecommendationResult:
        energy_shortfall_kwh = self._energy_shortfall(
            candidate,
            request.energy_requirement_kwh
        )
        surplus_kwh = max(
            candidate.solar_energy_kwh - request.energy_requirement_kwh,
            0.0
        )

        return UsageWindowRecommendationResult(
            installation_id=request.installation_id,
            preferred_strategy=request.preferred_strategy,
            requested_start=start,
            requested_end=end,
            recommended_start=candidate.start,
            recommended_end=candidate.end,
            duration_hours=round(candidate.duration_hours, 2),
            energy_requirement_kwh=round(request.energy_requirement_kwh, 3),
            expected_solar_energy_kwh=round(candidate.solar_energy_kwh, 3),
            expected_energy_shortfall_kwh=round(energy_shortfall_kwh, 3),
            expected_surplus_kwh=round(surplus_kwh, 3),
            expected_average_power_kw=round(candidate.average_power_kw, 3),
            coverage_ratio=round(
                candidate.solar_energy_kwh / request.energy_requirement_kwh,
                3
            ),
            message=self._build_message(energy_shortfall_kwh)
        )

    def _energy_shortfall(
        self,
        candidate: UsageWindowCandidate,
        energy_requirement_kwh: float
    ) -> float:
        return max(energy_requirement_kwh - candidate.solar_energy_kwh, 0.0)

    def _build_message(self, energy_shortfall_kwh: float) -> str:
        if energy_shortfall_kwh == 0:
            return (
                'The recommended window is expected to produce enough solar '
                'energy for the requested task.'
            )

        return (
            'The recommended window has the strongest expected solar production, '
            'but it does not fully cover the requested task energy.'
        )

    def _to_local_naive(self, value: datetime) -> datetime:
        timezone = ZoneInfo(self.prediction_service.settings.timezone)

        if value.tzinfo:
            return value.astimezone(timezone).replace(tzinfo=None)

        return value
