# File: quote_app.py (Improved)
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import font_manager
from tkinter import messagebox # << เพิ่ม import

import database
from settings_window import SettingsWindow
from language_manager import lang
from module_cal.mc_cal import OperationManagerWindow, WireEdmCalculatorDialog 

class MachineQuotingApp(tb.Window):
    def __init__(self):
        super().__init__(themename="litera")
        self.widgets = {}
        database.initialize_db()
        self.refresh_data_from_db()
        
        try:
            font_path = 'C:/Windows/Fonts/tahoma.ttf'
            self.thai_font = font_manager.FontProperties(fname=font_path)
        except FileNotFoundError:
            self.thai_font = font_manager.FontProperties()
        
        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=True)
        self.rebuild_ui()

    def switch_language(self, lang_code):
        lang.load_language(lang_code)
        self.rebuild_ui()
        self.calculate_price()

    def rebuild_ui(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        self.title(lang.get("app_title"))
        self.geometry("1400x850")

        top_bar = tb.Frame(self.main_frame)
        top_bar.pack(fill=X, pady=(0, 5), padx=10)
        
        lang_th_btn = tb.Button(top_bar, text=lang.get("lang_th"), bootstyle="secondary", command=lambda: self.switch_language('th'))
        lang_th_btn.pack(side=RIGHT, padx=(0,5), pady=5)
        lang_en_btn = tb.Button(top_bar, text=lang.get("lang_en"), bootstyle="secondary", command=lambda: self.switch_language('en'))
        lang_en_btn.pack(side=RIGHT, padx=5, pady=5)

        settings_button = tb.Button(top_bar, text=f"⚙️ {lang.get('settings')}", bootstyle="primary", command=self.open_settings_window)
        settings_button.pack(side=LEFT, padx=0, pady=5)
        
        paned_window = ttk.PanedWindow(self.main_frame, orient=HORIZONTAL)
        paned_window.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        left_frame = tb.Frame(paned_window, padding=10)
        paned_window.add(left_frame, weight=1)
        right_frame = tb.Frame(paned_window, padding=10)
        paned_window.add(right_frame, weight=2)
        
        self.create_left_panel(left_frame)
        self.create_right_panel(right_frame)

        self.update_rate_labels()
        self.draw_initial_chart()
        self.clear_form(clear_job_info=False)
        
    def create_left_panel(self, parent):
        quote_info_frame = tb.Labelframe(parent, text=f" {lang.get('quote_info')} ", padding=15, bootstyle="info")
        quote_info_frame.pack(fill=X, pady=(0, 10))
        quote_info_frame.grid_columnconfigure(1, weight=1)
        tb.Label(quote_info_frame, text=lang.get("job_name")).grid(row=0, column=0, sticky=W, pady=2)
        self.widgets['job_name'] = tb.Entry(quote_info_frame)
        self.widgets['job_name'].grid(row=0, column=1, sticky=EW, pady=2)
        tb.Label(quote_info_frame, text=lang.get("customer_name")).grid(row=1, column=0, sticky=W, pady=2)
        self.widgets['customer_name'] = tb.Entry(quote_info_frame)
        self.widgets['customer_name'].grid(row=1, column=1, sticky=EW, pady=2)
        
        part_details_frame = tb.Labelframe(parent, text=f" {lang.get('part_details')} ", padding=15, bootstyle="info")
        part_details_frame.pack(fill=X, pady=10)
        part_details_frame.grid_columnconfigure(1, weight=1)
        tb.Label(part_details_frame, text=lang.get("material")).grid(row=0, column=0, sticky=W, pady=2)
        self.widgets['material_combo'] = tb.Combobox(part_details_frame, values=list(self.MATERIAL_COSTS.keys()))
        self.widgets['material_combo'].grid(row=0, column=1, sticky=EW, pady=2)
        if list(self.MATERIAL_COSTS.keys()): self.widgets['material_combo'].current(0)
        tb.Label(part_details_frame, text=lang.get("quantity")).grid(row=1, column=0, sticky=W, pady=2)
        self.widgets['quantity_entry'] = tb.Entry(part_details_frame)
        self.widgets['quantity_entry'].grid(row=1, column=1, sticky=EW, pady=2)
        
        ops_frame = tb.Labelframe(parent, text=f" {lang.get('operations')} ", padding=15, bootstyle="info")
        ops_frame.pack(fill=X, pady=10, expand=True)
        ops_frame.grid_columnconfigure(1, weight=1)
        self.widgets['time_entries'] = {}
        self.widgets['rate_labels'] = {}
        row_counter = 0
        for machine_name in sorted(self.HOURLY_RATES.keys()):
            self.widgets['rate_labels'][machine_name] = tb.Label(ops_frame)
            self.widgets['rate_labels'][machine_name].grid(row=row_counter, column=0, sticky=W, pady=5)
            entry = tb.Entry(ops_frame, bootstyle="default")
            entry.grid(row=row_counter, column=1, sticky=EW, pady=5, padx=(10,5))
            self.widgets['time_entries'][machine_name] = entry
            if machine_name in ['Milling', 'CNC', 'Wire EDM']:
                 calc_btn = tb.Button(ops_frame, text=lang.get("calculate_hours"), bootstyle="info-outline", command=lambda m=machine_name: self.open_calculation_dialog(m))
                 calc_btn.grid(row=row_counter, column=2, padx=5)
            row_counter += 1

        main_control_frame = tb.Frame(parent)
        main_control_frame.pack(fill=X, pady=20, side=BOTTOM)
        main_control_frame.grid_columnconfigure((0,1), weight=1)
        calc_price_btn = tb.Button(main_control_frame, text=f"💲 {lang.get('calculate_price')}", command=self.calculate_price, bootstyle="success", padding=15)
        calc_price_btn.grid(row=0, column=0, sticky=EW, padx=5)
        clear_btn = tb.Button(main_control_frame, text=f"🗑️ {lang.get('clear_form')}", command=self.clear_form, bootstyle="danger-outline", padding=15)
        clear_btn.grid(row=0, column=1, sticky=EW, padx=5)
        
    def create_right_panel(self, parent):
        price_summary_frame = tb.Labelframe(parent, text=f" {lang.get('price_summary')} ", padding=20, bootstyle="success")
        price_summary_frame.pack(fill=X, pady=(0, 10))
        price_summary_frame.grid_columnconfigure(0, weight=1)
        self.widgets['final_price_label'] = tb.Label(price_summary_frame, text="0.00", font=("Helvetica", 48, "bold"), anchor=CENTER)
        self.widgets['final_price_label'].grid(row=0, column=0, sticky=EW)
        tb.Label(price_summary_frame, text=lang.get("unit_thb"), font=("Helvetica", 16), anchor=E).grid(row=0, column=1, sticky=SE, padx=10)
        self.widgets['price_per_unit_label'] = tb.Label(price_summary_frame, text=lang.get("price_per_unit", price=0), font=("Helvetica", 12), bootstyle="secondary")
        self.widgets['price_per_unit_label'].grid(row=1, column=0, columnspan=2, sticky=EW, pady=(5,0))
        
        cost_breakdown_frame = tb.Labelframe(parent, text=f" {lang.get('cost_breakdown')} ", padding=15, bootstyle="info")
        cost_breakdown_frame.pack(fill=X, pady=10)
        cost_breakdown_frame.grid_columnconfigure(1, weight=1)
        def create_cost_row(label_key, row):
            label = tb.Label(cost_breakdown_frame, text=lang.get(label_key))
            label.grid(row=row, column=0, sticky=W, padx=5, pady=3)
            value_label = tb.Label(cost_breakdown_frame, text="0.00", anchor=E, bootstyle="dark")
            value_label.grid(row=row, column=1, sticky=EW, padx=5, pady=3)
            return label, value_label
        
        _, self.widgets['cost_material'] = create_cost_row("cost_material", 0)
        _, self.widgets['cost_labor'] = create_cost_row("cost_labor", 1)
        _, self.widgets['cost_subtotal'] = create_cost_row("cost_total", 2)
        self.widgets['cost_profit_label'], self.widgets['cost_profit'] = create_cost_row("profit", 3)

        chart_frame = tb.Labelframe(parent, text=f" {lang.get('chart_title')} ", padding=15, bootstyle="info")
        chart_frame.pack(fill=BOTH, expand=True, pady=10)
        fig = plt.Figure(figsize=(5, 4), dpi=100)
        self.widgets['chart_axes'] = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
        self.widgets['chart_canvas'] = canvas

    def refresh_data_from_db(self):
        all_settings = database.get_settings()
        non_hourly_keys = ['profit_margin', 'Wire EDM_sqmm']
        self.PROFIT_MARGIN = all_settings.get('profit_margin', 0.25)
        self.HOURLY_RATES = { k: v for k, v in all_settings.items() if k not in non_hourly_keys }
        self.MATERIAL_COSTS = database.get_all_materials()

    def open_settings_window(self):
        dialog = SettingsWindow(parent=self)
        self.wait_window(dialog)
        self.refresh_data_from_db()
        self.rebuild_ui()

    def update_rate_labels(self):
        for name, label in self.widgets['rate_labels'].items():
            rate = self.HOURLY_RATES.get(name, 0.0)
            label.config(text=f"{name} ({rate:,.0f} {lang.get('hourly_rate_unit')}):")

    def draw_initial_chart(self):
        ax = self.widgets['chart_axes']
        ax.clear()
        ax.text(0.5, 0.5, lang.get('chart_placeholder'), fontproperties=self.thai_font, horizontalalignment='center', verticalalignment='center', fontsize=14, color='grey')
        self.widgets['chart_canvas'].draw()

    def update_pie_chart(self, data):
        ax = self.widgets['chart_axes']
        ax.clear()
        chart_labels = {
            'total_material_cost': lang.get('chart_label_material'),
            'total_labor_cost': lang.get('chart_label_labor'),
            'profit': lang.get('chart_label_profit')
        }
        labels = [chart_labels.get(key, key) for key in data.keys()]
        values = list(data.values())
        filtered_labels = [label for i, label in enumerate(labels) if values[i] > 0]
        filtered_values = [value for value in values if value > 0]
        if not filtered_values:
            self.draw_initial_chart()
            return
        colors = ['#4A90E2', '#F5A623', '#50E3C2']
        wedges, _, autotexts = ax.pie(filtered_values, autopct='%1.1f%%', startangle=90, colors=colors, wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}, pctdistance=0.85)
        legend = ax.legend(wedges, filtered_labels, title=lang.get("chart_legend_title"), loc="center left", bbox_to_anchor=(0.95, 0, 0.5, 1))
        plt.setp(legend.get_texts(), fontproperties=self.thai_font)
        plt.setp(legend.get_title(), fontproperties=self.thai_font)
        plt.setp(autotexts, size=10, weight="bold", color="white")
        ax.axis('equal')
        self.widgets['chart_canvas'].draw()

    def open_calculation_dialog(self, machine_type):
        """เปิดหน้าต่างคำนวณที่เหมาะสม (เปิดใช้งาน Milling, CNC)"""
        target_entry = self.widgets['time_entries'][machine_type]
        dialog = None
        if machine_type in ['Milling', 'CNC']:
            dialog = OperationManagerWindow(parent=self, target_entry=target_entry, lang_manager=lang)
        elif machine_type == 'Wire EDM':
            dialog = WireEdmCalculatorDialog(parent=self, target_entry=target_entry, lang_manager=lang)
        if dialog:
            dialog.grab_set()

    def calculate_price(self):
        """คำนวณราคา (ปรับปรุง Error Handling)"""
        try:
            quantity = int(self.widgets['quantity_entry'].get() or 1)
            if quantity <= 0: raise ValueError("Quantity must be > 0")
            
            material_cost_per_unit = self.MATERIAL_COSTS.get(self.widgets['material_combo'].get(), 0)
            total_material_cost = material_cost_per_unit * quantity

            labor_cost_per_unit = 0
            for name, entry in self.widgets['time_entries'].items():
                hours = float(entry.get() or "0")
                labor_cost_per_unit += hours * self.HOURLY_RATES.get(name, 0)
            total_labor_cost = labor_cost_per_unit * quantity

            sub_total = total_material_cost + total_labor_cost
            profit = sub_total * self.PROFIT_MARGIN
            final_price = sub_total + profit

            unit_str = lang.get("unit_thb")
            self.widgets['cost_material'].config(text=f"{total_material_cost:,.2f} {unit_str}")
            self.widgets['cost_labor'].config(text=f"{total_labor_cost:,.2f} {unit_str}")
            self.widgets['cost_subtotal'].config(text=f"{sub_total:,.2f} {unit_str}")
            self.widgets['cost_profit'].config(text=f"{profit:,.2f} {unit_str}")
            self.widgets['final_price_label'].config(text=f"{final_price:,.2f}")
            self.widgets['price_per_unit_label'].config(text=lang.get("price_per_unit", price=final_price / quantity))
            self.widgets['cost_profit_label'].config(text=lang.get("profit", percent=self.PROFIT_MARGIN*100))

            chart_data = {
                'total_material_cost': total_material_cost,
                'total_labor_cost': total_labor_cost,
                'profit': profit
            }
            self.update_pie_chart(chart_data)
        except (ValueError, ZeroDivisionError) as e:
            # --- แสดง Error เป็น Popup ---
            messagebox.showerror(lang.get("error_title"), f"{lang.get('error_numeric_only')}\n\n({e})")
            self.clear_results()

    def clear_results(self):
        unit_str = lang.get("unit_thb")
        self.widgets['cost_material'].config(text=f"0.00 {unit_str}")
        self.widgets['cost_labor'].config(text=f"0.00 {unit_str}")
        self.widgets['cost_subtotal'].config(text=f"0.00 {unit_str}")
        self.widgets['cost_profit'].config(text=f"0.00 {unit_str}")
        self.widgets['final_price_label'].config(text="0.00")
        self.widgets['price_per_unit_label'].config(text=lang.get("price_per_unit", price=0))
        self.draw_initial_chart()

    def clear_form(self, clear_job_info=True):
        if clear_job_info:
            self.widgets['job_name'].delete(0, END)
            self.widgets['customer_name'].delete(0, END)
        if list(self.MATERIAL_COSTS.keys()): self.widgets['material_combo'].current(0)
        self.widgets['quantity_entry'].delete(0, END)
        self.widgets['quantity_entry'].insert(0, "1")
        for entry in self.widgets['time_entries'].values():
            entry.delete(0, END)
            entry.insert(0, "0.0")
        self.clear_results()

if __name__ == "__main__":
    app = MachineQuotingApp()
    app.mainloop()