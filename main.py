# -*- coding: utf-8 -*-
import flet as ft
import asyncio
from datetime import datetime

# Modüller
import database as db
from constants import SCHENGEN_COUNTRIES
from calculator import get_total_days_in_last_180
from location_manager import get_current_location

async def main(page: ft.Page):
    db.init_db()
    page.title = "Schengen Takipçisi v2.7 (Anlık Tepki)"
    page.window_width = 450
    page.window_height = 850
    page.bgcolor = ft.Colors.GREY_50
    page.scroll = ft.ScrollMode.AUTO

    # --- KRİTİK DEĞİŞKENLER ---
    selected_travel_id = None
    delete_target_id = None
    
    # YENİ: Döngüyü uyandırmak için tetikleyici (Alarm)
    restart_loop_event = asyncio.Event() 

    # --- BİLEŞENLER ---
    used_text = ft.Text("0", size=40, weight="bold", color="white")
    rem_text = ft.Text("90", size=40, weight="bold", color="white")
    progress_bar = ft.ProgressBar(value=0, color="amber", bgcolor="white24", height=8)
    
    location_status = ft.Text("Takip Kapalı", size=12, italic=True)
    current_interval_lbl = ft.Text("Sıklık: --", size=11, color="grey")
    
    history_list = ft.ListView(expand=True, spacing=10, padding=10)
    
    country_dropdown = ft.Dropdown(
        label="Ülke Seçin",
        options=[ft.dropdown.Option(c) for c in SCHENGEN_COUNTRIES],
        enable_filter=True,
    )
    entry_input = ft.TextField(label="Giriş Tarihi")
    exit_input = ft.TextField(label="Çıkış Tarihi")

    # --- YARDIMCI FONKSİYONLAR ---
    async def update_interval_label():
        try:
            val_str = db.get_setting('interval')
            val = int(val_str) if val_str else 60
            if val >= 60 and val % 60 == 0:
                hours = val // 60
                current_interval_lbl.value = f"Sıklık: {hours} Saat"
            else:
                current_interval_lbl.value = f"Sıklık: {val} Dakika"
            current_interval_lbl.update()
        except:
            current_interval_lbl.value = "Sıklık: 60 dk"
            current_interval_lbl.update()

    async def load_history():
        history_list.controls.clear()
        rows = await asyncio.to_thread(db.fetch_all_travels)
        for row in rows:
            t_id, country, entry, exit_val, is_active = row
            buttons = ft.Row(tight=True)
            if is_active:
                buttons.controls.append(ft.IconButton(ft.Icons.LOGOUT, icon_color="orange", on_click=lambda e, i=t_id: asyncio.create_task(open_exit_confirmation(i))))
            buttons.controls.append(ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red700", on_click=lambda e, i=t_id: asyncio.create_task(open_delete_dialog(i))))

            history_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FLIGHT_LAND, "blue"),
                    title=ft.Text(country, weight="bold"),
                    subtitle=ft.Text(f"Giriş: {entry}\nÇıkış: {exit_val if exit_val else 'Devam Ediyor...'}"),
                    trailing=buttons
                )
            )
        page.update()

    async def update_ui(e=None):
        is_auto = db.get_setting('auto_location') == '1'
        last_country = db.get_setting('last_known_country')
        last_time = db.get_setting('last_location_time')

        location_switch.value = is_auto
        if is_auto:
            time_info = f" ({last_time})" if last_time else ""
            location_status.value = f"Konum: {last_country}{time_info}"
            location_status.color = ft.Colors.GREEN
        else:
            location_status.value = "Takip Kapalı"
            location_status.color = ft.Colors.RED

        used, rem = get_total_days_in_last_180()
        used_text.value, rem_text.value = str(used), str(rem)
        ratio = used / 90
        progress_bar.value = ratio if ratio <= 1 else 1
        rem_text.color = "red" if rem <= 10 else "white"
        
        await update_interval_label()
        await load_history()

    # --- POPUP MENÜ ---
    radio_minutes = ft.RadioGroup(content=ft.Row([
        ft.Radio(value="1", label="1 dk"),
        ft.Radio(value="5", label="5 dk"),
        ft.Radio(value="10", label="10 dk"),
        ft.Radio(value="20", label="20 dk"),
        ft.Radio(value="30", label="30 dk"),
    ], wrap=True))

    radio_hours = ft.RadioGroup(content=ft.Row([
        ft.Radio(value="1", label="1 sa"),
        ft.Radio(value="2", label="2 sa"),
        ft.Radio(value="4", label="4 sa"),
        ft.Radio(value="6", label="6 sa"),
        ft.Radio(value="8", label="8 sa"),
    ], wrap=True))

    container_minutes = ft.Container(content=radio_minutes, visible=True)
    container_hours = ft.Container(content=radio_hours, visible=False)

    def on_mode_change(e):
        idx = int(e.control.selected_index or 0)
        if idx == 0: 
            container_minutes.visible = True
            container_hours.visible = False
            if not radio_minutes.value: radio_minutes.value = "30"
        else: 
            container_minutes.visible = False
            container_hours.visible = True
            if not radio_hours.value: radio_hours.value = "1"
        page.update()

    mode_selector = ft.CupertinoSlidingSegmentedButton(
        selected_index=0,
        thumb_color=ft.Colors.BLUE_200,
        on_change=on_mode_change,
        controls=[ft.Text("Dakika"), ft.Text("Saat")],
    )

    # --- DEĞİŞİKLİK 1: KAYDET FONKSİYONU ---
    async def save_interval_setting(e):
        final_minutes = 60
        if container_minutes.visible:
            val = radio_minutes.value
            final_minutes = int(val) if val else 30
        else:
            val = radio_hours.value
            hours = int(val) if val else 1
            final_minutes = hours * 60
            
        db.update_setting('interval', str(final_minutes))
        
        # YENİ: Döngüyü uyandır!
        restart_loop_event.set()
        
        interval_dialog.open = False
        page.snack_bar = ft.SnackBar(ft.Text(f"Sıklık güncellendi: {final_minutes} dk. Takip yeniden başlıyor..."), open=True)
        page.update()
        await update_interval_label()

    interval_dialog = ft.AlertDialog(
        title=ft.Text("Sorgu Sıklığı"),
        content=ft.Column([
            ft.Container(height=10),
            mode_selector,
            ft.Divider(),
            ft.Text("Bir seçenek belirleyin:", size=12, color="grey"),
            container_minutes,
            container_hours
        ], tight=True, width=300),
        actions=[
            ft.TextButton("Vazgeç", on_click=lambda _: setattr(interval_dialog, "open", False) or page.update()),
            ft.FilledButton("Kaydet", on_click=save_interval_setting)
        ]
    )

    async def open_interval_settings(e):
        val_str = db.get_setting('interval')
        val = int(val_str) if val_str else 60
        if val >= 60 and val % 60 == 0:
            mode_selector.selected_index = 1
            container_minutes.visible = False
            container_hours.visible = True
            radio_hours.value = str(val // 60)
        else:
            mode_selector.selected_index = 0
            container_minutes.visible = True
            container_hours.visible = False
            radio_minutes.value = str(val)
        interval_dialog.open = True
        page.update()

    # --- EVENT HANDLERS ---
    async def toggle_location_switch(e):
        current_db_status = db.get_setting('auto_location') == '1'
        location_switch.value = current_db_status
        location_confirm_dialog.open = True
        page.update()

    async def close_location_dialog(confirmed):
        location_confirm_dialog.open = False
        if confirmed:
            curr = db.get_setting('auto_location') == '1'
            new_s = '0' if curr else '1'
            db.update_setting('auto_location', new_s)
            if new_s == '0':
                db.update_setting('last_known_country', 'Bilinmiyor')
            
            # Switch açıldığında/kapandığında da döngüyü uyandır ki hemen tepki versin
            restart_loop_event.set()
            
            await update_ui()
        else:
            page.update()

    async def save_new_travel(e):
        try:
            datetime.strptime(entry_input.value, "%Y-%m-%d %H:%M:%S")
            name = f"{country_dropdown.value} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            await asyncio.to_thread(db.add_travel, name, entry_input.value)
            add_dialog.open = False
            await update_ui()
        except: 
            entry_input.error_text = "Hatalı format!" 
            page.update()

    async def handle_exit_confirmed(e):
        await asyncio.to_thread(db.close_travel, selected_travel_id, exit_input.value)
        confirm_exit_dialog.open = False
        await update_ui()

    async def handle_delete_confirmed(e):
        nonlocal delete_target_id
        if delete_target_id:
            await asyncio.to_thread(db.delete_travel, delete_target_id)
            delete_dialog.open = False
            delete_target_id = None
            await update_ui()

    # --- DIALOGS ---
    confirm_exit_dialog = ft.AlertDialog(title=ft.Text("Kapat"), content=exit_input,
        actions=[ft.TextButton("Vazgeç", on_click=lambda _: setattr(confirm_exit_dialog, "open", False) or page.update()), ft.TextButton("Kaydet", on_click=handle_exit_confirmed)])
    add_dialog = ft.AlertDialog(title=ft.Text("Yeni Kayıt"), content=ft.Column([country_dropdown, entry_input], tight=True),
        actions=[ft.TextButton("İptal", on_click=lambda _: setattr(add_dialog, "open", False) or page.update()), ft.TextButton("Kaydet", on_click=save_new_travel)])
    delete_dialog = ft.AlertDialog(title=ft.Text("Kaydı Sil"), content=ft.Text("Emin misiniz?"),
        actions=[ft.TextButton("Vazgeç", on_click=lambda _: setattr(delete_dialog, "open", False) or page.update()), ft.TextButton("Evet, Sil", on_click=handle_delete_confirmed, icon=ft.Icons.DELETE_FOREVER, icon_color="red")])
    location_confirm_dialog = ft.AlertDialog(title=ft.Text("Emin misiniz?"), content=ft.Text("Değişikliği onaylıyor musunuz?"),
        actions=[ft.TextButton("Hayır", on_click=lambda _: asyncio.create_task(close_location_dialog(False))), ft.TextButton("Evet", on_click=lambda _: asyncio.create_task(close_location_dialog(True)))])

    page.overlay.extend([confirm_exit_dialog, add_dialog, delete_dialog, location_confirm_dialog, interval_dialog])

    async def open_exit_confirmation(t_id):
        nonlocal selected_travel_id
        selected_travel_id = t_id
        exit_input.value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        confirm_exit_dialog.open = True
        page.update()
    async def open_add_dialog(e):
        entry_input.value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        add_dialog.open = True
        page.update()
    async def open_delete_dialog(travel_id):
        nonlocal delete_target_id
        delete_target_id = travel_id
        delete_dialog.open = True
        page.update()

    location_switch = ft.Switch(value=False, on_change=toggle_location_switch)

    # --- LAYOUT ---
    dashboard = ft.Container(
        content=ft.Column([
            ft.Text("90 GÜN DURUMU", size=12, weight="bold", color="white70"),
            ft.Row([
                ft.Column([used_text, ft.Text("KULLANILAN", size=10, color="white70")], horizontal_alignment="center"),
                ft.Container(width=1, height=40, bgcolor="white24"), 
                ft.Column([rem_text, ft.Text("KALAN HAK", size=10, color="white70")], horizontal_alignment="center"),
            ], alignment="spaceEvenly"),
            progress_bar
        ]),
        padding=20, bgcolor=ft.Colors.BLUE_900, border_radius=20, shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK26)
    )

    settings_card = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LOCATION_ON, color="red400"),
                    ft.Text("Otomatik Takip", weight="bold", size=16),
                ]),
                location_status,
                current_interval_lbl 
            ], spacing=2),
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.SETTINGS, icon_color="grey", tooltip="Sıklık Ayarı",
                    on_click=lambda e: asyncio.create_task(open_interval_settings(e))
                ),
                location_switch
            ])
        ], alignment="spaceBetween"),
        padding=15, bgcolor="white", border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12)
    )

    page.add(ft.Column([
        ft.Text("SCHENGEN TAKİBİ", size=24, weight="bold", color=ft.Colors.BLUE_900),
        dashboard,
        ft.Container(height=10),
        settings_card,
        ft.Container(height=10),
        ft.Row([ft.Text("GEÇMİŞ", size=20, weight="bold"), ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=open_add_dialog)], "spaceBetween"),
        ft.Container(history_list, height=350),
        ft.FilledButton("Yenile", icon=ft.Icons.REFRESH, on_click=lambda e: asyncio.create_task(update_ui()), width=400)
    ], horizontal_alignment="center"))

    # --- DEĞİŞİKLİK 2: AKILLI DÖNGÜ ---
    async def location_check_loop():
        while True:
            # Döngü başında veritabanından güncel süreyi çek
            interval_str = db.get_setting('interval')
            interval_min = int(interval_str) if interval_str else 60

            # İşlemleri yap
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
                    await update_ui()
                except Exception as e:
                    print(f"Loop Error: {e}")

            # --- BEKLEME MANTIĞI ---
            # Bekleme süresini saniyeye çevir
            sleep_seconds = interval_min * 60
            
            try:
                # Ya süre bitene kadar bekle, ya da 'restart_loop_event' tetiklenirse hemen uyan
                await asyncio.wait_for(restart_loop_event.wait(), timeout=sleep_seconds)
                
                # Eğer buraya geldiysek event tetiklenmiş demektir (Kaydet tuşuna basıldı)
                restart_loop_event.clear() # Alarmı sustur, bir sonraki sefere hazırla
                print("Ayarlar değişti, döngü yeniden başlatılıyor...")
                # while True başa döner, yeni intervali okur ve hemen işlem yapar.
                
            except asyncio.TimeoutError:
                # Süre doldu, normal döngüye devam et
                pass

    asyncio.create_task(location_check_loop())
    await update_ui()

if __name__ == "__main__":
    ft.app(target=main)