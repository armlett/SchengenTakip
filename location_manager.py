# location_manager.py
import os
import requests
from plyer import gps

def get_ip_location():
    """Windows/PC için IP tabanlı konum tespiti"""
    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        data = response.json()
        if data['status'] == 'success':
            return data['country']
    except:
        return None
    return None

def get_android_gps_location():
    """Android için GPS sensör tabanlı konum tespiti"""
    try:
        # Android'de GPS'i yapılandır ve tek seferlik konum almayı dene
        # Not: Android izinleri APK derlenirken build.yml'de belirtilmelidir.
        lat, lon = None, None
        
        def on_location(**kwargs):
            nonlocal lat, lon
            lat = kwargs.get('lat')
            lon = kwargs.get('lon')

        gps.configure(on_location=on_location)
        gps.start(1, 1) # 1 saniye aralıkla güncelleme iste
        
        # Konumun gelmesi için kısa bir süre bekle (GPS soğuk başlama yapabilir)
        import time
        for _ in range(10):
            if lat is not None:
                break
            time.sleep(1)
        
        gps.stop()

        if lat and lon:
            # Koordinatı ülke ismine çevir (Reverse Geocoding)
            res = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}", 
                               headers={'User-Agent': 'SchengenTrackerApp'})
            return res.json().get('address', {}).get('country')
    except Exception as e:
        print(f"GPS Hatası: {e}")
    return None

def get_current_location():
    """OS kontrolü yaparak doğru metodu seçer"""
    # Android ortamı tespiti (Flet/Pydroid vb.)
    is_android = "ANDROID_ARGUMENT" in os.environ or "PYTHON_SERVICE_ARGUMENT" in os.environ

    if is_android:
        # Önce GPS dene
        loc = get_android_gps_location()
        # GPS başarısız olursa (Örn: Bina içi) IP'ye dön
        if not loc:
            loc = get_ip_location()
        return loc
    else:
        # Windows/PC ise doğrudan IP kullan
        return get_ip_location()