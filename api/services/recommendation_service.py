from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from models.recommendation import UsageWindowRecommendationRequest
from responses.prediction_result import PredictionResult
from responses.recommendation_result import (
    DeviceScheduleResult,
    UsageWindowRecommendationResult,
)
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
        start, end = self._resolve_request_window(request)
        self._validate_request_window(start, end)
        predictions = self.prediction_service.predict_solar_yield(
            installation_id=request.installation_id,
            start_date=start.date().isoformat(),
            end_date=end.date().isoformat()
        )
        slots = self._build_slots(predictions, start, end)
        candidates = self._build_candidates(slots)
        candidate = self._select_candidate(
            candidates,
            request,
        )

        return self._build_result(
            request,
            start,
            end,
            candidate
        )

    def _resolve_request_window(
        self,
        request: UsageWindowRecommendationRequest
    ) -> tuple[datetime, datetime]:
        start = request.start or request.preferred_start
        end = request.end or request.preferred_end

        if start and end:
            return self._to_local_naive(start), self._to_local_naive(end)

        if request.date:
            return (
                datetime.combine(request.date, datetime.min.time()),
                datetime.combine(request.date, datetime.max.time())
            )

        raise ValueError(
            'Provide start/end, preferred_start/preferred_end, or date'
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

        for prediction in predictions.predictions:
            slot_start = prediction.timestamp
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
        candidates: list[UsageWindowCandidate],
        request: UsageWindowRecommendationRequest,
    ) -> UsageWindowCandidate:
        required_duration_hours = self._required_duration_hours(request)

        if required_duration_hours > 0:
            eligible = [
                candidate
                for candidate in candidates
                if candidate.duration_hours >= required_duration_hours
            ]

            if eligible:
                candidates = eligible

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
            self._energy_requirement_kwh(request)
        )
        surplus_kwh = max(
            candidate.solar_energy_kwh - self._energy_requirement_kwh(request),
            0.0
        )
        energy_requirement_kwh = self._energy_requirement_kwh(request)
        confidence = min(
            candidate.solar_energy_kwh / energy_requirement_kwh,
            1.0
        )
        short_reason = self._build_short_reason(energy_shortfall_kwh)

        return UsageWindowRecommendationResult(
            installation_id=request.installation_id,
            preferred_strategy=request.preferred_strategy,
            requested_start=start,
            requested_end=end,
            recommended_start=candidate.start,
            recommended_end=candidate.end,
            duration_hours=round(candidate.duration_hours, 2),
            energy_requirement_kwh=round(energy_requirement_kwh, 3),
            expected_solar_energy_kwh=round(candidate.solar_energy_kwh, 3),
            expected_energy_shortfall_kwh=round(energy_shortfall_kwh, 3),
            expected_surplus_kwh=round(surplus_kwh, 3),
            expected_average_power_kw=round(candidate.average_power_kw, 3),
            coverage_ratio=round(
                candidate.solar_energy_kwh / energy_requirement_kwh,
                3
            ),
            confidence=round(confidence, 3),
            short_reason=short_reason,
            recommended_time_window=(
                f'{candidate.start.isoformat()} / {candidate.end.isoformat()}'
            ),
            expected_production_kwh=round(candidate.solar_energy_kwh, 3),
            device_schedule=self._build_device_schedule(request, candidate),
            message=self._build_message(energy_shortfall_kwh)
        )

    def _energy_requirement_kwh(
        self,
        request: UsageWindowRecommendationRequest
    ) -> float:
        if request.selected_devices:
            return sum(
                device.consumption_kwh
                for device in request.selected_devices
            )

        if request.energy_requirement_kwh is None:
            raise ValueError(
                'energy_requirement_kwh or selected_devices is required'
            )

        return request.energy_requirement_kwh

    def _build_device_schedule(
        self,
        request: UsageWindowRecommendationRequest,
        candidate: UsageWindowCandidate
    ) -> list[DeviceScheduleResult]:
        devices = request.selected_devices

        if not devices:
            return []

        schedule = []
        current_start = candidate.start

        for device in devices:
            duration_minutes = max(int(device.duration_minutes or 60), 1)
            start = current_start
            end = start + timedelta(minutes=duration_minutes)
            schedule.append(
                DeviceScheduleResult(
                    device=device.name,
                    consumption_kwh=round(device.consumption_kwh, 3),
                    start=start,
                    end=end,
                    reason=(
                        'Scheduled inside the strongest expected solar '
                        'production window.'
                    )
                )
            )
            current_start = end

        return schedule

    def _required_duration_hours(
        self,
        request: UsageWindowRecommendationRequest
    ) -> float:
        if not request.selected_devices:
            return 0.0

        total_minutes = sum(
            max(int(device.duration_minutes or 60), 1)
            for device in request.selected_devices
        )
        return total_minutes / 60

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

    def _build_short_reason(self, energy_shortfall_kwh: float) -> str:
        if energy_shortfall_kwh == 0:
            return 'Expected production covers the selected usage.'

        return 'Best solar window, but some grid energy may still be needed.'

    def _to_local_naive(self, value: datetime) -> datetime:
        timezone = ZoneInfo(self.prediction_service.settings.timezone)

        if value.tzinfo:
            return value.astimezone(timezone).replace(tzinfo=None)

        return value
