from pydantic import BaseModel


class TrainingRunQueuedResult(BaseModel):
    training_run_id: str
    status: str


class TrainingRunSummaryResult(BaseModel):
    records: int
    period_start: str
    period_end: str
    best_window_start: str
    best_window_end: str
    average_daily_production_kwh: float


class TrainingRunStatusResult(BaseModel):
    training_run_id: str
    status: str
    phase: str
    progress: int
    current_trial: int | None = None
    total_trials: int | None = None
    best_rmse: float | None = None
    error_code: str | None = None
    summary: TrainingRunSummaryResult | None = None
