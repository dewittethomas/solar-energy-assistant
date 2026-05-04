class Settings:
    def __init__(self):
        self.api_base_url = "https://api.open-meteo.com/v1/forecast"

def get_settings() -> Settings:
    return Settings()