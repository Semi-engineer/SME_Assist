# File: language_manager.py
import json
import os

class LanguageManager:
    def __init__(self, lang_code='th'):
        self.lang_code = lang_code
        self.data = {}
        self.load_language(lang_code)

    def load_language(self, lang_code):
        filepath = os.path.join('lang', f'{lang_code}.json')
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.lang_code = lang_code
        except FileNotFoundError:
            print(f"Language file not found: {filepath}")
            self.data = {}

    def get(self, key, **kwargs):
        template = self.data.get(key, f'<{key}>')
        if kwargs:
            return template.format(**kwargs)
        return template

# สร้าง instance กลาง
lang = LanguageManager()