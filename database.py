# database.py - Android Uyumlu Tam Sürüm
import sqlite3
import os

def get_db_path():
    """Android ve Windows için doğru yolu bulur"""
    db_name = 'schengen_tracker.db'
    try:
        # Android ortamı kontrolü
        from jnius import autoclass
        Context = autoclass('android.content.Context')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        files_dir = activity.getFilesDir().getAbsolutePath()
        return os.path.join(files_dir, db_name)
    except:
        # Windows/PC ortamı
        return os.path.join(os.getcwd(), db_name)

def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.text_factory = str 
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS travels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_name TEXT NOT NULL,
            entry_date TIMESTAMP NOT NULL,
            exit_date TIMESTAMP,
            is_active INTEGER DEFAULT 1)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT)''')
    
    # Varsayılanlar
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_location', '0')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('interval', '60')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('last_known_country', 'Bilinmiyor')")
    
    conn.commit()
    conn.close()

# --- CRUD İŞLEMLERİ (Aynen kalacak) ---
def get_setting(key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def update_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def fetch_all_travels():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, country_name, entry_date, exit_date, is_active FROM travels ORDER BY entry_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_travel(country_name, entry_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO travels (country_name, entry_date, is_active) VALUES (?, ?, ?)", (country_name, entry_date, 1))
    conn.commit()
    conn.close()

def close_travel(travel_id, exit_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE travels SET exit_date = ?, is_active = 0 WHERE id = ?", (exit_date, travel_id))
    conn.commit()
    conn.close()

def delete_travel(travel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM travels WHERE id = ?", (travel_id,))
    conn.commit()
    conn.close()

def get_active_travel():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, country_name, entry_date FROM travels WHERE is_active = 1 LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row