from geopy.geocoders import Nominatim

SCHENGEN_COUNTRIES = [
    "Austria", "Belgium", "Czech Republic", "Denmark", "Estonia", "Finland", 
    "France", "Germany", "Greece", "Hungary", "Iceland", "Italy", "Latvia", 
    "Liechtenstein", "Lithuania", "Luxembourg", "Malta", "Netherlands", 
    "Norway", "Poland", "Portugal", "Slovakia", "Slovenia", "Spain", 
    "Sweden", "Switzerland", "Croatia"
]

def is_in_schengen(lat, lon):
    """Koordinatları ülkeye çevirir ve Schengen kontrolü yapar."""
    geolocator = Nominatim(user_agent="schengen_app")
    try:
        location = geolocator.reverse((lat, lon), language='en')
        if location:
            country = location.raw.get('address', {}).get('country')
            return country, country in SCHENGEN_COUNTRIES
        return None, False
    except Exception as e:
        print(f"Hata: {e}")
        return None, False

# Test etmek için:
if __name__ == "__main__":
    # Örnek: Berlin koordinatları
    ulke, durum = is_in_schengen(52.52, 13.40)
    print(f"Ülke: {ulke}, Schengen'de mi?: {durum}")