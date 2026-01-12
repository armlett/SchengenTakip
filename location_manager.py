import geocoder
from geopy.geocoders import Nominatim

def get_current_location():
    try:
        # IP tabanlı hızlı konum tespiti
        g = geocoder.ip('me')
        if g.latlng:
            lat, lon = g.latlng
            
            # Koordinatı ülke ismine çevirme
            geolocator = Nominatim(user_agent="schengen_tracker")
            location = geolocator.reverse(f"{lat}, {lon}", language='tr')
            
            address = location.raw.get('address', {})
            country = address.get('country', '')
            return country
    except Exception as e:
        print(f"Konum alınamadı: {e}")
        return None

# Test etmek için:
if __name__ == "__main__":
    current_country = get_current_location()
    print(f"Şu anki konumunuz: {current_country}")