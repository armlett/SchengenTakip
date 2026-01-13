# background.py
import asyncio
import flet as ft
from datetime import datetime
import database as db
from constants import SCHENGEN_COUNTRIES
from location_manager import get_current_location

async def location_check_loop(page, update_ui_callback, restart_event):
    """
    Arka plan konum kontrol döngüsü.
    :param page: Flet sayfa nesnesi (SnackBar göstermek için)
    :param update_ui_callback: UI'ı güncellemek için çağrılacak fonksiyon
    :param restart_event: Döngüyü anında uyandırmak için event tetikleyici
    """
    while True:
        # 1. Süreyi Çek
        interval_str = db.get_setting('interval')
        interval_min = int(interval_str) if interval_str else 60

        # 2. İşlemleri Yap
        if db.get_setting('auto_location') == '1':
            try:
                current_country = await asyncio.to_thread(get_current_location)
                now_dt = datetime.now()
                now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
                
                if current_country:
                    time_info = now_dt.strftime("%d.%m %H:%M")
                    db.update_setting('last_known_country', f"{current_country} ({time_info})")
                    db.update_setting('last_location_time', time_info)

                    active_travel = await asyncio.to_thread(db.get_active_travel)
                    if active_travel:
                        t_id, t_full_name, t_entry_str = active_travel
                        t_country = t_full_name.split(" - ")[0] if " - " in t_full_name else t_full_name 
                        
                        if current_country != t_country:
                            t_entry_dt = datetime.strptime(t_entry_str, "%Y-%m-%d %H:%M:%S")
                            if (now_dt - t_entry_dt).total_seconds() <= 86400:
                                await asyncio.to_thread(db.close_travel, t_id, now_str)
                                if current_country in SCHENGEN_COUNTRIES:
                                    display_name = f"{current_country} - {now_str}"
                                    await asyncio.to_thread(db.add_travel, display_name, now_str)
                            else:
                                page.snack_bar = ft.SnackBar(ft.Text(f"Ülke değişti: {current_country}."), open=True)
                                page.update()
                    elif current_country in SCHENGEN_COUNTRIES:
                        display_name = f"{current_country} - {now_str}"
                        await asyncio.to_thread(db.add_travel, display_name, now_str)
                
                # UI Güncellemesini Tetikle
                await update_ui_callback()
                
            except Exception as e:
                print(f"Loop Error: {e}")

        # 3. Bekleme Mantığı
        sleep_seconds = interval_min * 60
        try:
            # Alarm çalana kadar veya süre bitene kadar bekle
            await asyncio.wait_for(restart_event.wait(), timeout=sleep_seconds)
            restart_event.clear()
            print("Döngü tetiklendi, yeniden başlıyor...")
        except asyncio.TimeoutError:
            pass