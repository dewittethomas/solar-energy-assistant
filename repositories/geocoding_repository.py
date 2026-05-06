import requests
from typing import Dict, Any, Optional

class GeocodingRepository:
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
    
    def geocode_location(self, location: str) -> Optional[Dict[str, Any]]:
        params = {
            'q': location,
            'format': 'json',
            'limit': 1
        }
        
        headers = {'User-Agent': 'Solar Energy Assistant/0.1.0'}
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                return {
                    'latitude': float(data[0]['lat']),
                    'longitude': float(data[0]['lon'])
                }
            
            return None
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to geocode location '{location}': {str(e)}")
        except (KeyError, IndexError, ValueError) as e:
            raise RuntimeError(f"Failed to parse geocoding response for location '{location}': {str(e)}")