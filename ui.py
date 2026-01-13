# ui.py
import flet as ft

# Dashboard (Mavi Üst Panel) Tasarımı
def create_dashboard(used_text, rem_text, progress_bar):
    return ft.Container(
        content=ft.Column([
            ft.Text("90 GÜN DURUMU", size=12, weight="bold", color="white70"),
            ft.Row([
                ft.Column([used_text, ft.Text("KULLANILAN", size=10, color="white70")], horizontal_alignment="center"),
                ft.Container(width=1, height=40, bgcolor="white24"), 
                ft.Column([rem_text, ft.Text("KALAN HAK", size=10, color="white70")], horizontal_alignment="center"),
            ], alignment="spaceEvenly"),
            progress_bar
        ]),
        padding=20,
        bgcolor=ft.Colors.BLUE_900,
        border_radius=20,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK26)
    )

# Ayarlar Kartı Tasarımı
def create_settings_card(location_status, current_interval_lbl, location_switch, open_settings_func):
    return ft.Container(
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
                    on_click=open_settings_func # Fonksiyon main.py'den gelecek
                ),
                location_switch
            ])
        ], alignment="spaceBetween"),
        padding=15,
        bgcolor="white",
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12)
    )

# Popup Menü İçeriği (Tablar ve Radyo Butonları)
def create_interval_dialog_content(mode_selector, container_minutes, container_hours):
    return ft.Column([
        ft.Container(height=10),
        mode_selector,
        ft.Divider(),
        ft.Text("Bir seçenek belirleyin:", size=12, color="grey"),
        container_minutes,
        container_hours
    ], tight=True, width=300)