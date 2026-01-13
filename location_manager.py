# -*- coding: utf-8 -*-
import os
import time
from plyer import gps

def get_android_native_country(lat, lon):
    """
    Android'in kendi sistem kütüphanesini kullanarak 
    koordinatı ülke ismine çevirir (İnternetsiz deneme yapar).
    """
    try:
        from jnius import autoclass
        
        # Android'in temel sınıflarına erişelim
        Context = autoclass('android.content.Context')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Geocoder = autoclass('android.location.Geocoder')
        Locale = autoclass('java.util.Locale')

        activity = PythonActivity.mActivity
        # Geocoder nesnesi oluştur (Türkçe sonuç vermesi için Locale.GERMANY veya Locale.ENGLISH de seçilebilir)
        geocoder = Geocoder(activity, Locale.getDefault())
        
        # Koordinattan adres bilgilerini al (Sadece 1 sonuç iste)
        addresses = geocoder.getFromLocation(lat, lon, 1)
        
        if addresses and addresses.size() > 0:
            address = addresses.get(0)
            country_name = address.getCountryName() # Doğrudan ülke ismini verir
            return country_name
    except Exception as e:
        print(f"Android Native Geocoder Hatası: {e}")
    return None

def get_android_gps_location():
    """GPS Sensöründen ham koordinatları alır"""
    try:
        res_data = {"lat": None, "lon": None}
        
        def on_location(**kwargs):
            res_data["lat"] = kwargs.get('lat')
            res_data["lon"] = kwargs.get('lon')

        gps.configure(on_location=on_location)
        gps.start(1000, 1)
        
        # GPS/Fake GPS uydularını bekle (30 saniye)
        for i in range(30):
            if res_data["lat"] is not None:
                break
            time.sleep(1)
        
        gps.stop()

        if res_data["lat"] and res_data["lon"]:
            # İNTERNETSİZ: Android'in kendi Geocoder'ını kullan
            return get_android_native_country(res_data["lat"], res_data["lon"])
            
    except Exception as e:
        print(f"GPS Kritik Hata: {e}")
    return None

def get_current_location():
    # Android ortamı tespiti
    if os.path.exists('/data/user/0'):
        return get_android_gps_location()
    
    # Windows'ta ise mecbur IP (Internet şart)
    try:
        import requests
        response = requests.get('http://ip-api.com/json/', timeout=5)
        return response.json().get('country')
    except:
        return "Bilinmiyor"