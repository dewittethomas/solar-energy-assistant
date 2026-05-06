from core.settings import get_settings

from repositories.prediction_repository import PredictionRepository
from repositories.geocoding_repository import GeocodingRepository
from repositories.weather_repository import WeatherRepository
from repositories.cache_repository import CacheRepository
from services.weather_service import WeatherService
from services.geocoding_service import GeocodingService
from services.cache_service import CacheService
from services.prediction_service import PredictionService

_cache_repository = CacheRepository()

def get_cache_repository():
    return _cache_repository

def get_cache_service():
    repo = get_cache_repository()
    return CacheService(repo)

# Predictions
def get_prediction_service():
    repo = get_prediction_repository()
    weather_service = get_weather_service()
    geocoding_service = get_geocoding_service()
    cache_service = get_cache_service()
    return PredictionService(weather_service, geocoding_service, repo, cache_service)

def get_prediction_repository():
    return PredictionRepository()

# Weather
def get_weather_repository():
    return WeatherRepository()

def get_weather_service():
    return WeatherService()

# Geocoding
def get_geocoding_repository():
    return GeocodingRepository()

def get_geocoding_service():
    repo = get_geocoding_repository()
    return GeocodingService(repo)

# Weather
def get_weather_repository():
    return WeatherRepository()

def get_weather_service():
    return WeatherService()

# Geocoding
def get_geocoding_repository():
    return GeocodingRepository()

def get_geocoding_service():
    repo = get_geocoding_repository()
    return GeocodingService(repo)