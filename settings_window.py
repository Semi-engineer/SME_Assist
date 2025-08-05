# File: settings_window.py (Corrected)
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
import database
from language_manager import lang
from ttkbootstrap.dialogs import Querybox

class SettingsWindow(tb.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(lang.get("settings_window_title"))
        self.geometry("700x700")
        
        self.settings_widgets = {}
        self.material_widgets = {} # << บรรทัดที่แก้ไข
        
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

        # เปลี่ยนปุ่ม Save ให้เรียกใช้ฟังก์ชันใหม่ที่ถูกต้อง
        save_button = tb.Button(self, text=lang.get("save_all_settings"), bootstyle="success", command=self.save_all_changes)
        save_button.pack(pady=10, padx=10, fill=X, ipady=10)
        
        self.load_current_values()

    def create_general_tab(self, parent_frame):
        parent_frame.grid_columnconfigure(1, weight=1)
        tb.Label(parent_frame, text=lang.get("general_margin"), font=("Helvetica", 12)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)
        entry = tb.Entry(parent_frame, bootstyle="info")
        entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=10)
        tb.Label(parent_frame, text=lang.get("general_margin_note"), bootstyle="secondary").grid(row=0, column=2, sticky=tk.W, padx=5, pady=10)
        self.settings_widgets['profit_margin'] = entry

        tb.Label(parent_frame, text=lang.get("language_select_label", default="Language:"), font=("Helvetica", 12)).grid(row=1, column=0, sticky=tk.W, padx=5, pady=10)
        self.lang_var = tk.StringVar(value=lang.lang_code)
        lang_combo = tb.Combobox(parent_frame, textvariable=self.lang_var, values=['th', 'en'])
        lang_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=10)

    def create_rates_tab(self, parent_frame):
        tb.Label(parent_frame, text=lang.get("rates_header"), font=("Helvetica", 12, "bold")).pack(pady=(0, 15), anchor=tk.W)
        settings = database.get_settings()
        rate_keys = [k for k in settings.keys() if k not in ['profit_margin', 'Wire EDM_sqmm']]
        for name in sorted(rate_keys):
            self.create_setting_row(parent_frame, name, f"{name}:")
            
        tb.Separator(parent_frame, orient=HORIZONTAL).pack(fill=X, pady=15)
        tb.Label(parent_frame, text=lang.get("rates_special_header"), font=("Helvetica", 12, "bold")).pack(pady=(0, 15), anchor=tk.W)
        self.create_setting_row(parent_frame, 'Wire EDM_sqmm', lang.get("rate_sqmm"))
        
    def create_setting_row(self, parent, key_name, label_text):
        row_frame = tb.Frame(parent)
        row_frame.pack(fill=X, pady=4)
        label = tb.Label(row_frame, text=label_text, width=25)
        label.pack(side=LEFT)
        entry = tb.Entry(row_frame, bootstyle="info")
        entry.pack(side=LEFT, fill=X, expand=True)
        self.settings_widgets[key_name] = entry

    def create_materials_tab(self, parent):
        table_frame = tb.Frame(parent)
        table_frame.pack(fill=BOTH, expand=True)
        columns = {"name": (lang.get("material"), 400), "cost": (lang.get("op_fixed_cost"), 100)}
        self.material_tree = tb.Treeview(table_frame, columns=[val[0] for val in columns.values()], show='headings', bootstyle="primary")
        for val in columns.values():
            self.material_tree.heading(val[0], text=val[0])
            self.material_tree.column(val[0], width=val[1])
        self.material_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = tb.Scrollbar(table_frame, orient=VERTICAL, command=self.material_tree.yview)
        self.material_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.material_tree.bind("<Double-1>", self.edit_material_cost)

        action_frame = tb.Labelframe(parent, text=lang.get("op_add_new"), padding=10)
        action_frame.pack(fill=X, pady=(15, 0))
        action_frame.grid_columnconfigure(1, weight=1)
        tb.Label(action_frame, text=f"{lang.get('material')}:").grid(row=0, column=0, padx=5, pady=5)
        self.new_mat_name_entry = tb.Entry(action_frame)
        self.new_mat_name_entry.grid(row=0, column=1, sticky=EW, padx=5, pady=5)
        tb.Label(action_frame, text=f"{lang.get('op_fixed_cost')}:").grid(row=0, column=2, padx=5, pady=5)
        self.new_mat_cost_entry = tb.Entry(action_frame, width=10)
        self.new_mat_cost_entry.grid(row=0, column=3, padx=5, pady=5)
        add_btn = tb.Button(action_frame, text=lang.get("op_add_btn"), bootstyle="success", command=self.add_new_material)
        add_btn.grid(row=0, column=4, padx=10, pady=5)

        delete_btn = tb.Button(parent, text=lang.get("op_delete_btn"), bootstyle="danger-outline", command=self.delete_selected_material)
        delete_btn.pack(fill=X, pady=(10,0))
    
    def refresh_material_tree(self):
        for item in self.material_tree.get_children():
            self.material_tree.delete(item)
        materials = database.get_all_materials()
        for name, cost in materials.items():
            self.material_tree.insert("", END, values=(name, f"{cost:,.2f}"))

    def add_new_material(self):
        name = self.new_mat_name_entry.get().strip()
        cost_str = self.new_mat_cost_entry.get()
        try:
            cost = float(cost_str)
            if not name:
                messagebox.showwarning("ข้อมูลไม่ครบถ้วน", "กรุณาใส่ชื่อวัสดุ")
                return
            if database.add_material(name, cost):
                self.refresh_material_tree()
                self.new_mat_name_entry.delete(0, END)
                self.new_mat_cost_entry.delete(0, END)
            else:
                messagebox.showerror("ผิดพลาด", f"วัสดุชื่อ '{name}' มีอยู่แล้วในระบบ")
        except ValueError:
            messagebox.showerror(lang.get("error_title"), lang.get("error_numeric_only"))

    def delete_selected_material(self):
        selected_item = self.material_tree.selection()
        if not selected_item:
            messagebox.showwarning("ไม่ได้เลือกรายการ", "กรุณาเลือกวัสดุที่ต้องการลบ")
            return
        item_values = self.material_tree.item(selected_item, "values")
        material_name = item_values[0]
        if messagebox.askyesno("ยืนยันการลบ", f"คุณต้องการลบ '{material_name}' ใช่หรือไม่?"):
            database.delete_material(material_name)
            self.refresh_material_tree()

    def edit_material_cost(self, event):
        selected_item = self.material_tree.selection()
        if not selected_item: return
        item_values = self.material_tree.item(selected_item, "values")
        name, old_cost = item_values[0], item_values[1]
        new_cost = Querybox.get_string(prompt=f"แก้ไขราคาสำหรับ:\n{name}", title="แก้ไขราคาวัสดุ", initialvalue=old_cost.replace(',', ''))
        if new_cost:
            try:
                database.update_materials({name: float(new_cost)})
                self.refresh_material_tree()
            except ValueError:
                messagebox.showerror(lang.get("error_title"), lang.get("error_numeric_only"))

    def load_current_values(self):
        settings = database.get_settings()
        for key, widget in self.settings_widgets.items():
            widget.insert(0, str(settings.get(key, "")))
        self.refresh_material_tree()

    def save_all_changes(self):
        """บันทึกเฉพาะแท็บ General และ Rates"""
        try:
            selected_lang = self.lang_var.get()
            lang.save_language_setting(selected_lang)
            lang.load_language_data(selected_lang)
            new_settings = {key: float(widget.get()) for key, widget in self.settings_widgets.items()}
            database.update_settings(new_settings)
            messagebox.showinfo(lang.get("success_title"), lang.get("settings_saved"))
            self.destroy()
        except ValueError:
            messagebox.showerror(lang.get("error_title"), lang.get("error_numeric_only"))