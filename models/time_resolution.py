from dataclasses import dataclass

@dataclass
class TimeResolution:
    kind: str
    interval_minutes: float | None
