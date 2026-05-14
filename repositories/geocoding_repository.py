import requests

class GeocodingRepository:
    def __init__(self) -> None:
        self.base_url = 'https://nominatim.openstreetmap.org/search'

    def geocode_location(self, location: str) -> dict[str, float] | None:
        params = {
            'q': location,
            'format': 'json',
            'limit': 1
        }
        headers = {'User-Agent': 'Solar Energy Assistant/0.1.0'}

        try:
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data:
                return {
                    'latitude': float(data[0]['lat']),
                    'longitude': float(data[0]['lon'])
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
