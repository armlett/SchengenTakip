# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime, timedelta
from constants import SCHENGEN_COUNTRIES

def get_total_days_in_last_180():
    """
    Son 180 günlük hareketli pencere içinde, sadece Schengen ülkelerinde 
    geçen günleri (giriş ve çıkış dahil) hesaplar.
    """
    try:
        conn = sqlite3.connect('schengen_tracker.db')
        conn.text_factory = str
        cursor = conn.cursor()
        
        today = datetime.now().date()
        window_start = today - timedelta(days=180)
        
        # Ülke ismini de çekiyoruz ki Schengen kontrolü yapabilelim
        cursor.execute("SELECT country_name, entry_date, exit_date FROM travels")
        travels = cursor.fetchall()
        
        total_used_days = 0
        
        for country_full_name, entry_str, exit_str in travels:
            # İsimdeki tarih ekini temizle (Örn: "Almanya - 2026..." -> "Almanya")
            country_pure_name = country_full_name.split(" - ")[0] if " - " in country_full_name else country_full_name
            
            # Ülke Schengen listesinde değilse hesaplamaya katma
            if country_pure_name not in SCHENGEN_COUNTRIES:
                continue

            entry_date = datetime.strptime(entry_str, '%Y-%m-%d %H:%M:%S').date()
            
            if exit_str:
                exit_date = datetime.strptime(exit_str, '%Y-%m-%d %H:%M:%S').date()
            else:
                # Aktif seyahat ise bugünü çıkış kabul et
                exit_date = today

            # 180 günlük pencereye giren tarihleri belirle
            actual_start = max(entry_date, window_start)
            actual_end = exit_date
            
            if actual_end >= actual_start:
                # KURAL: (Fark + 1) Giriş ve çıkış günleri dahil edilir.
                delta = (actual_end - actual_start).days + 1
                total_used_days += delta

        remaining_days = 90 - total_used_days
        return total_used_days, max(0, remaining_days)
    
    except Exception as e:
        print(f"Hesaplama hatası: {e}")
        return 0, 90
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    used, remaining = get_total_days_in_last_180()
    print(f"Son 180 günde kullanılan: {used} gün")
    print(f"Kalan hak: {remaining} gün")