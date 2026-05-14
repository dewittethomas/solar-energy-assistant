from repositories.prediction_repository import PredictionRepository
from repositories.geocoding_repository import GeocodingRepository
from repositories.weather_repository import WeatherRepository
from repositories.cache_repository import CacheRepository
from repositories.parquet_repository import ParquetRepository
from repositories.model_training_repository import ModelTrainingRepository
from services.weather_service import WeatherService
from services.geocoding_service import GeocodingService
from services.cache_service import CacheService
from services.prediction_service import PredictionService
from services.data_upload_service import DataUploadService
from services.csv_preprocessing_service import CsvPreprocessingService
from services.parquet_service import ParquetService
from services.model_training_service import ModelTrainingService
from pipeline import CsvPreprocessingPipeline, ModelTrainingPipeline

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

def get_weather_repository():
    return WeatherRepository()

def get_weather_service():
    repo = get_weather_repository()
    return WeatherService(repo)

# Geocoding
def get_geocoding_repository():
    return GeocodingRepository()

def get_geocoding_service():
    repo = get_geocoding_repository()
    return GeocodingService(repo)

# Data uploads
def get_parquet_repository():
    return ParquetRepository()

def get_parquet_service():
    repo = get_parquet_repository()
    return ParquetService(repo)

def get_csv_preprocessing_service():
    parquet_service = get_parquet_service()
    return CsvPreprocessingService(parquet_service=parquet_service)

def get_csv_preprocessing_pipeline():
    preprocessing_service = get_csv_preprocessing_service()
    return CsvPreprocessingPipeline(preprocessing_service)

def get_data_upload_service():
    pipeline = get_csv_preprocessing_pipeline()
    return DataUploadService(pipeline)

# Model training
def get_model_training_repository():
    return ModelTrainingRepository()

def get_model_training_service():
    repo = get_model_training_repository()
    weather_service = get_weather_service()
    geocoding_service = get_geocoding_service()
    return ModelTrainingService(weather_service, geocoding_service, repo)

def get_model_training_pipeline():
    training_service = get_model_training_service()
    return ModelTrainingPipeline(training_service)
