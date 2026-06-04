import requests

class GeocodingRepository:
    def __init__(self) -> None:
        self.base_url = 'https://geocoding-api.open-meteo.com/v1/search'

    def geocode_location(self, location: str) -> dict[str, float] | None:
        params = {
            'name': location,
            'count': 10,
            'language': 'en',
            'format': 'json',
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])

            if results:
                return {
                    'latitude': float(results[0]['latitude']),
                    'longitude': float(results[0]['longitude'])
                }

            return None
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Failed to geocode location '{location}': {str(exc)}"
            ) from exc
        except (KeyError, IndexError, ValueError) as exc:
            raise RuntimeError(
                f"Failed to parse geocoding response for location "
                f"'{location}': {str(exc)}"
            ) from exc
