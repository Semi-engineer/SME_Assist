# File: database.py
import sqlite3

DATABASE_FILE = 'SME_Assist.db'

# --- เพิ่ม Rate ใหม่สำหรับ Wire EDM ---
DEFAULT_SETTINGS = {
    # Hourly Rates
    'Lathe': 550, 'Milling': 650, 'CNC': 600, 'Wire EDM': 800,
    'EDM Sinker': 1000, 'Grinding': 680, 'Basic Machine': 300,
    
    # Special Rates
    'Wire EDM_sqmm': 0.15, # << ย้ายมาเป็น key พิเศษ ไม่ใช่ชื่อเครื่องจักร
    
    # General Settings
    'profit_margin': 0.25
}

DEFAULT_MATERIALS = {
    'เหล็ก (Steel S45C)': 80, 'อลูมิเนียม (Aluminum 6061)': 180,
    'สแตนเลส (Stainless Steel 304)': 250, 'ทองเหลือง (Brass)': 300
}

def connect_db():
    return sqlite3.connect(DATABASE_FILE)

def initialize_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value REAL NOT NULL
        )''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            name TEXT PRIMARY KEY, cost REAL NOT NULL
        )''')
    cursor.execute("SELECT key FROM settings")
    existing_keys = {row[0] for row in cursor.fetchall()}
    for key, value in DEFAULT_SETTINGS.items():
        if key not in existing_keys:
            print(f"Adding new setting: {key}")
            cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
    cursor.execute("SELECT name FROM materials")
    existing_materials = {row[0] for row in cursor.fetchall()}
    for name, cost in DEFAULT_MATERIALS.items():
        if name not in existing_materials:
            print(f"Adding new material: {name}")
            cursor.execute("INSERT INTO materials (name, cost) VALUES (?, ?)", (name, cost))
    conn.commit()
    conn.close()

def get_settings():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return settings

def update_settings(new_settings_dict):
    conn = connect_db()
    cursor = conn.cursor()
    for key, value in new_settings_dict.items():
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, float(value)))
    conn.commit()
    conn.close()
    print("Settings updated successfully.")

def get_all_materials():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, cost FROM materials")
    materials = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return materials

def update_materials(new_materials_dict):
    conn = connect_db()
    cursor = conn.cursor()
    for name, cost in new_materials_dict.items():
        cursor.execute("INSERT OR REPLACE INTO materials (name, cost) VALUES (?, ?)", (name, float(cost)))
    conn.commit()
    conn.close()
    print("Materials updated successfully.")