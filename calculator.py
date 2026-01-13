# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime, timedelta
from constants import SCHENGEN_COUNTRIES

def get_total_days_in_last_180():
    try:
        conn = sqlite3.connect('schengen_tracker.db')
        conn.text_factory = str
        cursor = conn.cursor()
        
        today = datetime.now().date()
        window_start = today - timedelta(days=179) # 180 günlük pencere (bugün dahil)
        
        cursor.execute("SELECT country_name, entry_date, exit_date FROM travels")
        travels = cursor.fetchall()
        
        # HARCANAN TÜM ÖZGÜN TARİHLERİ BURADA TOPLAYACAĞIZ
        spent_dates = set()
        
        for country_full_name, entry_str, exit_str in travels:
            # Ülke ismini temizle
            country_pure_name = country_full_name.split(" - ")[0] if " - " in country_full_name else country_full_name
            
            # Ülke Schengen listesinde değilse bu kaydı atla
            if country_pure_name not in SCHENGEN_COUNTRIES:
                continue

            # Tarihleri parse et
            entry_dt = datetime.strptime(entry_str, '%Y-%m-%d %H:%M:%S').date()
            if exit_str:
                exit_dt = datetime.strptime(exit_str, '%Y-%m-%d %H:%M:%S').date()
            else:
                exit_dt = today # Seyahat devam ediyorsa bugünü bitiş say

            # Seyahatin pencereye giren kısmını bul
            calc_start = max(entry_dt, window_start)
            calc_end = min(exit_dt, today)

            # EĞER GEÇERLİ BİR ARALIKSA, HER GÜNÜ TEK TEK SEPETE EKLE
            if calc_end >= calc_start:
                current_day = calc_start
                while current_day <= calc_end:
                    spent_dates.add(current_day) # Aynı gün tekrar gelirse 'set' onu tek sayar
                    current_day += timedelta(days=1)

        # Sepette kaç tane özgün gün birikti?
        total_used_days = len(spent_dates)
        remaining_days = 90 - total_used_days
        
        return total_used_days, max(0, remaining_days)
    
    except Exception as e:
        print(f"Hesaplama hatası: {e}")
        return 0, 90
    finally:
        conn.close()