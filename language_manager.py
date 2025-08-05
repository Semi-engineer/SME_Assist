# File: language_manager.py (Updated)
import json
import os
from app_config import CONFIG_PATH, LANG_DIR

class LanguageManager:
    def __init__(self):
        self.lang_code = self.load_language_setting()
        self.data = {}
        self.load_language_data(self.lang_code)

    def load_language_data(self, lang_code):
        # ใช้ LANG_DIR ที่ import เข้ามา
        filepath = os.path.join(LANG_DIR, f'{lang_code}.json') 
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.lang_code = lang_code
            print(f"Loaded language data: {lang_code}")
        except FileNotFoundError:
            print(f"Language file not found: {filepath}")
            self.data = {}

    def get(self, key, **kwargs):
        template = self.data.get(key, f'<{key}>')
        if kwargs:
            return template.format(**kwargs)
        return template

    def load_language_setting(self):
        """โหลดค่าภาษาที่บันทึกไว้จาก config.json"""
        try:
            # ใช้ CONFIG_PATH ที่ import เข้ามา
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('language', 'th')
        except (FileNotFoundError, json.JSONDecodeError):
            return 'th'

    def save_language_setting(self, lang_code):
        """บันทึกค่าภาษาลงใน config.json"""
        # ใช้ CONFIG_PATH ที่ import เข้ามา
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f: 
            json.dump({'language': lang_code}, f, indent=4)
        print(f"Language setting saved: {lang_code}")

# สร้าง instance กลาง
lang = LanguageManager()