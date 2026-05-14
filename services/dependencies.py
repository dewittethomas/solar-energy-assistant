from repositories.prediction_repository import PredictionRepository
from repositories.geocoding_repository import GeocodingRepository
from repositories.weather_repository import WeatherRepository
from repositories.cache_repository import CacheRepository
from repositories.parquet_repository import ParquetRepository
from repositories.model_training_repository import ModelTrainingRepository
from repositories.metadata_repository import MetadataRepository
from repositories.dataset_repository import DatasetRepository
from repositories.model_repository import ModelRepository
from repositories.user_repository import UserRepository
from services.weather_service import WeatherService
from services.geocoding_service import GeocodingService
from services.cache_service import CacheService
from services.prediction_service import PredictionService
from services.data_upload_service import DataUploadService
from services.preprocessing_service import PreprocessingService
from services.parquet_service import ParquetService
from services.training_service import TrainingService
from services.evaluation_service import EvaluationService
from services.metadata_service import MetadataService
from services.dataset_service import DatasetService
from services.model_service import ModelService
from services.recommendation_service import RecommendationService
from services.user_service import UserService
from pipeline import CsvPreprocessingPipeline, ModelTrainingPipeline

_cache_repository = CacheRepository()

def get_cache_repository():
    return _cache_repository

def get_cache_service():
    repo = get_cache_repository()
    return CacheService(repo)

def get_metadata_repository():
    return MetadataRepository()

def get_metadata_service():
    repo = get_metadata_repository()
    return MetadataService(repo)

def get_dataset_repository():
    return DatasetRepository(get_metadata_repository())

def get_dataset_service():
    repo = get_dataset_repository()
    return DatasetService(repo)

def get_model_repository():
    return ModelRepository(get_metadata_repository())

def get_model_service():
    repo = get_model_repository()
    return ModelService(repo)

def get_user_repository():
    return UserRepository(get_metadata_repository())

def get_user_service():
    repo = get_user_repository()
    return UserService(repo)

# Predictions
def get_prediction_service():
    repo = get_prediction_repository()
    weather_service = get_weather_service()
    geocoding_service = get_geocoding_service()
    model_service = get_model_service()
    cache_service = get_cache_service()
    return PredictionService(
        weather_service,
        geocoding_service,
        repo,
        model_service,
        cache_service
    )

def get_prediction_repository():
    return PredictionRepository()

def get_recommendation_service():
    prediction_service = get_prediction_service()
    return RecommendationService(prediction_service)

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

def get_preprocessing_service():
    parquet_service = get_parquet_service()
    return PreprocessingService(parquet_service=parquet_service)

def get_csv_preprocessing_pipeline():
    preprocessing_service = get_preprocessing_service()
    return CsvPreprocessingPipeline(preprocessing_service)

def get_data_upload_service():
    pipeline = get_csv_preprocessing_pipeline()
    metadata_service = get_metadata_service()
    return DataUploadService(pipeline, metadata_service)

# Model training
def get_model_training_repository():
    return ModelTrainingRepository()

def get_evaluation_service():
    return EvaluationService()

def get_training_service():
    repo = get_model_training_repository()
    weather_service = get_weather_service()
    geocoding_service = get_geocoding_service()
    metadata_service = get_metadata_service()
    evaluation_service = get_evaluation_service()
    return TrainingService(
        weather_service,
        geocoding_service,
        repo,
        metadata_service,
        evaluation_service
    )

def get_model_training_pipeline():
    training_service = get_training_service()
    return ModelTrainingPipeline(training_service)
