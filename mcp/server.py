from mcp.server.fastmcp import FastMCP
from services.dependencies import get_prediction_service
from services.prediction_service import PredictionService

mcp = FastMCP("Solar Panel Yield Data")

service: PredictionService = get_prediction_service()

@mcp.tool()
def get_solar_yield_data_by_period(start_date: str, end_date: str) -> list[dict]:
    """Get solar yield data for a specific period. Dates should be in YYYY-MM-DD format."""
    return service.predict_solar_yield(start_date, end_date)