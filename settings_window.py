# File: settings_window.py (Fully Refactored)
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
import database
from language_manager import lang

class SettingsWindow(tb.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(lang.get("settings_window_title"))
        self.geometry("600x600")
        
        self.settings_widgets = {}
        self.material_widgets = {}

        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=10, fill="both", expand=True)

        general_frame = tb.Frame(notebook, padding=15)
        rates_frame = tb.Frame(notebook, padding=15)
        materials_frame = tb.Frame(notebook, padding=15)

        notebook.add(general_frame, text=lang.get("tab_general"))
        notebook.add(rates_frame, text=lang.get("tab_rates"))
        notebook.add(materials_frame, text=lang.get("tab_materials"))

        self.create_general_tab(general_frame)
        self.create_rates_tab(rates_frame)
        self.create_materials_tab(materials_frame)

        save_button = tb.Button(self, text=lang.get("save_all_settings"), bootstyle="success", command=self.save_all_settings)
        save_button.pack(pady=10, padx=10, fill=X, ipady=10)
        
        self.load_current_values()

    def create_general_tab(self, parent_frame):
        tb.Label(parent_frame, text=lang.get("general_margin"), font=("Helvetica", 12)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        entry = tb.Entry(parent_frame, bootstyle="info")
        entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        tb.Label(parent_frame, text=lang.get("general_margin_note"), bootstyle="secondary").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.settings_widgets['profit_margin'] = entry

    def create_rates_tab(self, parent_frame):
        tb.Label(parent_frame, text=lang.get("rates_header"), font=("Helvetica", 12, "bold")).pack(pady=(0, 15), anchor=tk.W)
        settings = database.get_settings()
        rate_keys = [k for k in settings.keys() if k not in ['profit_margin', 'Wire EDM_sqmm']]

        for name in sorted(rate_keys):
            self.create_setting_row(parent_frame, name, f"{name}:")
            
        tb.Separator(parent_frame, orient=HORIZONTAL).pack(fill=X, pady=15)
        tb.Label(parent_frame, text=lang.get("rates_special_header"), font=("Helvetica", 12, "bold")).pack(pady=(0, 15), anchor=tk.W)
        self.create_setting_row(parent_frame, 'Wire EDM_sqmm', lang.get("rate_sqmm"))

    def create_materials_tab(self, parent_frame):
        tb.Label(parent_frame, text=lang.get("materials_header"), font=("Helvetica", 12, "bold")).pack(pady=(0, 15), anchor=tk.W)
        materials = database.get_all_materials()
        for name in sorted(materials.keys()):
            row_frame = tb.Frame(parent_frame)
            row_frame.pack(fill=X, pady=4)
            label = tb.Label(row_frame, text=f"{name}:", width=30)
            label.pack(side=LEFT)
            entry = tb.Entry(row_frame, bootstyle="info")
            entry.pack(side=LEFT, fill=X, expand=True)
            self.material_widgets[name] = entry
            
    def create_setting_row(self, parent, key_name, label_text):
        row_frame = tb.Frame(parent)
        row_frame.pack(fill=X, pady=4)
        label = tb.Label(row_frame, text=label_text, width=25)
        label.pack(side=LEFT)
        entry = tb.Entry(row_frame, bootstyle="info")
        entry.pack(side=LEFT, fill=X, expand=True)
        self.settings_widgets[key_name] = entry

    def load_current_values(self):
        settings = database.get_settings()
        for key, widget in self.settings_widgets.items():
            widget.insert(0, str(settings.get(key, "")))
        materials = database.get_all_materials()
        for name, widget in self.material_widgets.items():
            widget.insert(0, str(materials.get(name, "")))

    def save_all_settings(self):
        try:
            new_settings = {key: float(widget.get()) for key, widget in self.settings_widgets.items()}
            database.update_settings(new_settings)
            new_materials = {name: float(widget.get()) for name, widget in self.material_widgets.items()}
            database.update_materials(new_materials)
            messagebox.showinfo(lang.get("success_title"), lang.get("settings_saved"))
            self.destroy()
        except ValueError:
            messagebox.showerror(lang.get("error_title"), lang.get("error_numeric_only"))