import time
from SchengenTracker.database import init_db
import sqlite3
from datetime import datetime
from SchengenTracker.tracker import is_in_schengen

def run_tracking_cycle(lat, lon):
    """
    Bu fonksiyon her konum güncellemesinde çağrılacak.
    """
    country, schengen_status = is_in_schengen(lat, lon)
    
    if not country:
        print("Ülke tespiti başarısız, bir sonraki döngü bekleniyor...")
        return

    conn = sqlite3.connect('schengen_tracker.db')
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Aktif bir seyahat var mı?
    cursor.execute("SELECT id, country_name FROM travels WHERE is_active = 1")
    active_travel = cursor.fetchone()

    if active_travel:
        travel_id, last_country = active_travel
        
        if schengen_status:
            if country != last_country:
                # Ülke değişti ama hala Schengen'de
                cursor.execute("UPDATE travels SET exit_date = ?, is_active = 0 WHERE id = ?", (now, travel_id))
                cursor.execute("INSERT INTO travels (country_name, entry_date) VALUES (?, ?)", (country, now))
                print(f"Ülke değişti: {last_country} -> {country}")
        else:
            # Schengen'den çıkış yaptı
            cursor.execute("UPDATE travels SET exit_date = ?, is_active = 0 WHERE id = ?", (now, travel_id))
            print(f"Schengen bölgesinden çıkıldı: {last_country}")
    else:
        # Aktif kayıt yok, yeni giriş var mı?
        if schengen_status:
            cursor.execute("INSERT INTO travels (country_name, entry_date) VALUES (?, ?)", (country, now))
            print(f"Schengen bölgesine yeni giriş: {country}")

    conn.commit()
    conn.close()

# TEST ETMEK İÇİN (Simülasyon):
if __name__ == "__main__":
    init_db()
    print("Takip başlatıldı... (Test verileri gönderiliyor)")
    # Örnek: Önce Fransa (Schengen), sonra İngiltere (Schengen Dışı) simülasyonu
    run_tracking_cycle(48.8566, 2.3522) # Paris
    time.sleep(2)
    run_tracking_cycle(51.5074, -0.1278) # Londra