# -*- coding: utf-8 -*-
import flet as ft
import asyncio
from datetime import datetime

# Modüller
import database as db
import ui  # Yeni oluşturduğumuz UI dosyası
import background # Yeni oluşturduğumuz arka plan dosyası
from constants import SCHENGEN_COUNTRIES
from calculator import get_total_days_in_last_180

async def main(page: ft.Page):
    db.init_db()
    page.title = "Schengen Takipçisi v2.8 (Refactored)"
    page.window_width = 450
    page.window_height = 850
    page.bgcolor = ft.Colors.GREY_50
    page.scroll = ft.ScrollMode.AUTO

    # --- DEĞİŞKENLER ---
    selected_travel_id = None
    delete_target_id = None
    restart_loop_event = asyncio.Event() 

    # --- UI BİLEŞENLERİ (Referansları tutuyoruz) ---
    used_text = ft.Text("0", size=40, weight="bold", color="white")
    rem_text = ft.Text("90", size=40, weight="bold", color="white")
    progress_bar = ft.ProgressBar(value=0, color="amber", bgcolor="white24", height=8)
    
    location_status = ft.Text("Takip Kapalı", size=12, italic=True)
    current_interval_lbl = ft.Text("Sıklık: --", size=11, color="grey")
    
    history_list = ft.ListView(expand=True, spacing=10, padding=10)
    
    country_dropdown = ft.Dropdown(label="Ülke Seçin", options=[ft.dropdown.Option(c) for c in SCHENGEN_COUNTRIES], enable_filter=True)
    entry_input = ft.TextField(label="Giriş Tarihi")
    exit_input = ft.TextField(label="Çıkış Tarihi")

    # --- GÜNCELLEME FONKSİYONLARI ---
    async def update_ui(e=None):
        """Tüm arayüzü yenileyen merkezi fonksiyon"""
        is_auto = db.get_setting('auto_location') == '1'
        last_country = db.get_setting('last_known_country')
        
        # Switch ve Durum
        location_switch.value = is_auto
        if is_auto:
            location_status.value = f"Konum: {last_country}"
            location_status.color = ft.Colors.GREEN
        else:
            location_status.value = "Takip Kapalı"
            location_status.color = ft.Colors.RED

        # Hesaplamalar
        used, rem = get_total_days_in_last_180()
        used_text.value, rem_text.value = str(used), str(rem)
        ratio = used / 90
        progress_bar.value = ratio if ratio <= 1 else 1
        rem_text.color = "red" if rem <= 10 else "white"
        
        # Sıklık Etiketi
        try:
            val = int(db.get_setting('interval') or 60)
            if val >= 60 and val % 60 == 0:
                current_interval_lbl.value = f"Sıklık: {val // 60} Saat"
            else:
                current_interval_lbl.value = f"Sıklık: {val} Dakika"
            current_interval_lbl.update()
        except: pass
        
        await load_history()

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
                    subtitle=ft.Text(f"Giriş: {entry}\nÇıkış: {exit_val if exit_val else 'Devam...'}"),
                    trailing=buttons
                )
            )
        page.update()

    # --- POPUP VE AYARLAR ---
    radio_minutes = ft.RadioGroup(content=ft.Column([ft.Radio(value=str(x), label=f"{x} dk") for x in [1, 5, 10, 20, 30]]))
    radio_hours = ft.RadioGroup(content=ft.Column([ft.Radio(value=str(x), label=f"{x} sa") for x in [1, 2, 4, 6, 8]]))
    
    container_minutes = ft.Container(content=radio_minutes, visible=True)
    container_hours = ft.Container(content=radio_hours, visible=False)

    def on_mode_change(e):
        idx = int(e.control.selected_index or 0)
        container_minutes.visible = (idx == 0)
        container_hours.visible = (idx == 1)
        if idx == 0 and not radio_minutes.value: radio_minutes.value = "30"
        if idx == 1 and not radio_hours.value: radio_hours.value = "1"
        page.update()

    mode_selector = ft.CupertinoSlidingSegmentedButton(selected_index=0, thumb_color=ft.Colors.BLUE_200, on_change=on_mode_change, controls=[ft.Text("Dakika"), ft.Text("Saat")])

    async def save_interval_setting(e):
        final = 60
        if container_minutes.visible:
            final = int(radio_minutes.value or 30)
        else:
            final = int(radio_hours.value or 1) * 60
        db.update_setting('interval', str(final))
        restart_loop_event.set() # Döngüyü uyandır
        interval_dialog.open = False
        page.snack_bar = ft.SnackBar(ft.Text("Sıklık güncellendi"), open=True)
        page.update()
        await update_ui()

    async def open_interval_settings(e):
        val = int(db.get_setting('interval') or 60)
        if val >= 60 and val % 60 == 0:
            mode_selector.selected_index = 1
            container_minutes.visible, container_hours.visible = False, True
            radio_hours.value = str(val // 60)
        else:
            mode_selector.selected_index = 0
            container_minutes.visible, container_hours.visible = True, False
            radio_minutes.value = str(val)
        interval_dialog.open = True
        page.update()

    # --- HANDLERS (Olaylar) ---
    async def toggle_location_switch(e):
        location_switch.value = (db.get_setting('auto_location') == '1') # Görseli geri al (onay bekliyoruz)
        location_confirm_dialog.open = True
        page.update()

    async def close_location_dialog(confirmed):
        location_confirm_dialog.open = False
        if confirmed:
            curr = db.get_setting('auto_location') == '1'
            new_s = '0' if curr else '1'
            db.update_setting('auto_location', new_s)
            if new_s == '0': db.update_setting('last_known_country', 'Bilinmiyor')
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
        except: entry_input.error_text = "Hatalı format!"; page.update()

    async def handle_exit_confirmed(e):
        await asyncio.to_thread(db.close_travel, selected_travel_id, exit_input.value)
        confirm_exit_dialog.open = False
        await update_ui()

    async def handle_delete_confirmed(e):
        if delete_target_id: await asyncio.to_thread(db.delete_travel, delete_target_id)
        delete_dialog.open = False
        await update_ui()

    # --- DIALOGS (Tanımlamalar) ---
    interval_dialog = ft.AlertDialog(title=ft.Text("Sorgu Sıklığı"), content=ui.create_interval_dialog_content(mode_selector, container_minutes, container_hours),
        actions=[ft.TextButton("İptal", on_click=lambda _: setattr(interval_dialog, "open", False) or page.update()), ft.FilledButton("Kaydet", on_click=save_interval_setting)])
    
    confirm_exit_dialog = ft.AlertDialog(title=ft.Text("Kapat"), content=exit_input, actions=[ft.TextButton("İptal", on_click=lambda _: setattr(confirm_exit_dialog, "open", False) or page.update()), ft.TextButton("Kaydet", on_click=handle_exit_confirmed)])
    add_dialog = ft.AlertDialog(title=ft.Text("Yeni Kayıt"), content=ft.Column([country_dropdown, entry_input], tight=True), actions=[ft.TextButton("İptal", on_click=lambda _: setattr(add_dialog, "open", False) or page.update()), ft.TextButton("Kaydet", on_click=save_new_travel)])
    delete_dialog = ft.AlertDialog(title=ft.Text("Sil"), content=ft.Text("Emin misiniz?"), actions=[ft.TextButton("Hayır", on_click=lambda _: setattr(delete_dialog, "open", False) or page.update()), ft.TextButton("Evet", on_click=handle_delete_confirmed)])
    location_confirm_dialog = ft.AlertDialog(title=ft.Text("Onay"), content=ft.Text("Değişikliği onaylıyor musunuz?"), actions=[ft.TextButton("Hayır", on_click=lambda _: asyncio.create_task(close_location_dialog(False))), ft.TextButton("Evet", on_click=lambda _: asyncio.create_task(close_location_dialog(True)))])
    
    page.overlay.extend([confirm_exit_dialog, add_dialog, delete_dialog, location_confirm_dialog, interval_dialog])

    # Dialog Açıcılar
    async def open_exit_confirmation(t_id): nonlocal selected_travel_id; selected_travel_id = t_id; exit_input.value = datetime.now().strftime('%Y-%m-%d %H:%M:%S'); confirm_exit_dialog.open = True; page.update()
    async def open_add_dialog(e): entry_input.value = datetime.now().strftime('%Y-%m-%d %H:%M:%S'); add_dialog.open = True; page.update()
    async def open_delete_dialog(t_id): nonlocal delete_target_id; delete_target_id = t_id; delete_dialog.open = True; page.update()

    location_switch = ft.Switch(on_change=toggle_location_switch)

    # --- SAYFA YERLEŞİMİ (Layout) ---
    # ui.py'den gelen fonksiyonları kullanıyoruz
    page.add(ft.Column([
        ft.Text("SCHENGEN TAKİBİ", size=24, weight="bold", color=ft.Colors.BLUE_900),
        ui.create_dashboard(used_text, rem_text, progress_bar),
        ft.Container(height=10),
        ui.create_settings_card(location_status, current_interval_lbl, location_switch, lambda e: asyncio.create_task(open_interval_settings(e))),
        ft.Container(height=10),
        ft.Row([ft.Text("GEÇMİŞ", size=20, weight="bold"), ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=open_add_dialog)], "spaceBetween"),
        ft.Container(history_list, height=350),
        ft.FilledButton("Yenile", icon=ft.Icons.REFRESH, on_click=lambda e: asyncio.create_task(update_ui()), width=400)
    ], horizontal_alignment="center"))

    # Arka plan görevini başlat (background.py'den)
    asyncio.create_task(background.location_check_loop(page, update_ui, restart_loop_event))
    await update_ui()

if __name__ == "__main__":
    ft.app(main)