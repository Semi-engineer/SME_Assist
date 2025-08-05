# File: quote_app.py (Refactored Version)
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import font_manager
from tkinter import messagebox
import pdf_generator
import database
from settings_window import SettingsWindow
from language_manager import lang
from app_config import ICON_PATH

# ===================================================================
# ===== PAGE CLASSES (แต่ละหน้าเป็นคลาสของตัวเอง) =======================
# ===================================================================

class PlaceholderPage(tb.Frame):
    """A simple placeholder page for features not yet implemented."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.label = tb.Label(self, text=lang.get('coming_soon'), font=("Helvetica", 24, "bold"), bootstyle="secondary")
        self.label.pack(expand=True)

    def update_language(self):
        """Updates the language for this page's widgets."""
        self.label.config(text=lang.get('coming_soon'))

class QuotingPage(tb.Frame):
    """A frame that contains all widgets and logic for the quoting page."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app # Reference to the main app instance
        self.widgets = {}
        self.quote_operations = []
        self.op_counter = 0

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        left_panel = tb.Frame(self, padding=(0, 10, 10, 10))
        left_panel.grid(row=0, column=0, sticky="nsew")
        right_panel = tb.Frame(self, padding=(10, 10, 0, 10))
        right_panel.grid(row=0, column=1, sticky="nsew")

        self.build_left_panel(left_panel)
        self.build_right_panel(right_panel)
        self.clear_form(clear_job_info=False)

    def build_left_panel(self, parent):
        header_frame = tb.Frame(parent)
        header_frame.pack(fill=X, pady=(0, 15), expand=False)
        
        self.widgets['quote_info_frame'] = tb.Labelframe(header_frame, text=f" {lang.get('quote_info')} ", padding=15)
        self.widgets['quote_info_frame'].pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        self.widgets['quote_info_frame'].grid_columnconfigure(1, weight=1)
        self.widgets['job_name_label'] = tb.Label(self.widgets['quote_info_frame'], text=lang.get("job_name"))
        self.widgets['job_name_label'].grid(row=0, column=0, sticky=W, pady=2)
        self.widgets['job_name_entry'] = tb.Entry(self.widgets['quote_info_frame'])
        self.widgets['job_name_entry'].grid(row=0, column=1, sticky=EW, pady=2)
        self.widgets['customer_name_label'] = tb.Label(self.widgets['quote_info_frame'], text=lang.get("customer_name"))
        self.widgets['customer_name_label'].grid(row=1, column=0, sticky=W, pady=2)
        self.widgets['customer_name_entry'] = tb.Entry(self.widgets['quote_info_frame'])
        self.widgets['customer_name_entry'].grid(row=1, column=1, sticky=EW, pady=2)
        
        self.widgets['part_details_frame'] = tb.Labelframe(header_frame, text=f" {lang.get('part_details')} ", padding=15)
        self.widgets['part_details_frame'].pack(side=RIGHT, fill=X, expand=True, padx=(5, 0))
        self.widgets['part_details_frame'].grid_columnconfigure(1, weight=1)
        self.widgets['material_label'] = tb.Label(self.widgets['part_details_frame'], text=lang.get("material"))
        self.widgets['material_label'].grid(row=0, column=0, sticky=W, pady=2)
        self.widgets['material_combo'] = tb.Combobox(self.widgets['part_details_frame'], state="readonly", values=list(self.app.MATERIAL_COSTS.keys()))
        self.widgets['material_combo'].grid(row=0, column=1, sticky=EW, pady=2)
        if list(self.app.MATERIAL_COSTS.keys()): self.widgets['material_combo'].current(0)
        self.widgets['quantity_label'] = tb.Label(self.widgets['part_details_frame'], text=lang.get("quantity"))
        self.widgets['quantity_label'].grid(row=1, column=0, sticky=W, pady=2)
        self.widgets['quantity_entry'] = tb.Entry(self.widgets['part_details_frame'])
        self.widgets['quantity_entry'].grid(row=1, column=1, sticky=EW, pady=2)
        
        self.widgets['notebook'] = ttk.Notebook(parent)
        self.widgets['notebook'].pack(fill=BOTH, expand=True)
        ops_tab_frame = tb.Frame(self.widgets['notebook'], padding=15)
        cost_summary_tab_frame = tb.Frame(self.widgets['notebook'], padding=15)
        notes_tab_frame = tb.Frame(self.widgets['notebook'], padding=15)
        self.widgets['notebook'].add(ops_tab_frame, text=lang.get("tab_operations"))
        self.widgets['notebook'].add(cost_summary_tab_frame, text=lang.get("tab_cost_summary"))
        self.widgets['notebook'].add(notes_tab_frame, text=lang.get("tab_notes"))
        
        self.populate_ops_tab(ops_tab_frame)
        self.populate_cost_tab(cost_summary_tab_frame)
        self.populate_notes_tab(notes_tab_frame)
        
    def build_right_panel(self, parent):
        self.widgets['price_card'] = tb.Labelframe(parent, text=lang.get("price_summary"), padding=20, bootstyle="success")
        self.widgets['price_card'].pack(fill=X, pady=(0, 15), expand=False)
        self.widgets['price_card'].grid_columnconfigure(0, weight=1)
        self.widgets['final_price_label'] = tb.Label(self.widgets['price_card'], text="0.00", style='CardValue.TLabel', anchor=CENTER)
        self.widgets['final_price_label'].grid(row=0, column=0, sticky=EW)
        self.widgets['unit_thb_label'] = tb.Label(self.widgets['price_card'], text=lang.get("unit_thb"), style='CardUnit.TLabel', anchor=E)
        self.widgets['unit_thb_label'].grid(row=0, column=1, sticky=SE, padx=10)
        self.widgets['price_per_unit_label'] = tb.Label(self.widgets['price_card'], text=lang.get("price_per_unit", price=0), bootstyle="inverse-success")
        self.widgets['price_per_unit_label'].grid(row=1, column=0, columnspan=2, sticky=EW, pady=(5,0))
        
        self.widgets['chart_frame'] = tb.Labelframe(parent, text=lang.get('chart_title'), padding=15)
        self.widgets['chart_frame'].pack(fill=BOTH, expand=True, pady=15)
        fig = plt.Figure(figsize=(5, 4), dpi=100)
        self.widgets['chart_axes'] = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=self.widgets['chart_frame'])
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
        self.widgets['chart_canvas'] = canvas
        
        self.widgets['save_pdf_btn'] = tb.Button(parent, text=f"💾 {lang.get('save_pdf', default='Save PDF')}", command=self.save_pdf, bootstyle="info")
        self.widgets['save_pdf_btn'].pack(fill=X, pady=(15,0), ipady=10)

    def populate_ops_tab(self, parent):
        self.widgets['add_op_subframe'] = tb.Labelframe(parent, text=lang.get("op_add_new"), padding=10)
        self.widgets['add_op_subframe'].pack(fill=X, pady=(0, 15))
        self.widgets['add_op_subframe'].grid_columnconfigure(1, weight=1)
        self.widgets['op_desc_label'] = tb.Label(self.widgets['add_op_subframe'], text=lang.get("op_desc"))
        self.widgets['op_desc_label'].grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.widgets['op_desc_entry'] = tb.Entry(self.widgets['add_op_subframe'])
        self.widgets['op_desc_entry'].grid(row=0, column=1, columnspan=3, sticky=EW, padx=5, pady=2)
        self.widgets['op_method_label'] = tb.Label(self.widgets['add_op_subframe'], text=lang.get("op_pricing_method"))
        self.widgets['op_method_label'].grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.widgets['op_method_var'] = tk.StringVar(value=lang.get("op_method_time"))
        self.widgets['method_combo'] = tb.Combobox(self.widgets['add_op_subframe'], state="readonly", textvariable=self.widgets['op_method_var'], values=[lang.get("op_method_time"), lang.get("op_method_fixed")])
        self.widgets['method_combo'].grid(row=1, column=1, columnspan=3, sticky=EW, padx=5, pady=2)
        self.widgets['method_combo'].bind("<<ComboboxSelected>>", self.toggle_op_inputs)
        
        self.widgets['op_time_frame'] = tb.Frame(self.widgets['add_op_subframe'])
        self.widgets['op_time_frame'].grid(row=2, column=0, columnspan=4, sticky=EW)
        self.widgets['op_hours_label'] = tb.Label(self.widgets['op_time_frame'], text=lang.get("op_hours"))
        self.widgets['op_hours_label'].grid(row=0, column=0, padx=5)
        self.widgets['op_hours_entry'] = tb.Entry(self.widgets['op_time_frame'], width=8)
        self.widgets['op_hours_entry'].grid(row=0, column=1, padx=5)
        self.widgets['op_rate_label'] = tb.Label(self.widgets['op_time_frame'], text=lang.get("op_machine_rate"))
        self.widgets['op_rate_label'].grid(row=0, column=2, padx=5)
        self.widgets['op_rate_combo'] = tb.Combobox(self.widgets['op_time_frame'], state="readonly", values=list(self.app.HOURLY_RATES.keys()))
        self.widgets['op_rate_combo'].grid(row=0, column=3, padx=5, sticky=EW)
        if list(self.app.HOURLY_RATES.keys()): self.widgets['op_rate_combo'].current(0)
        self.widgets['op_time_frame'].grid_columnconfigure(3, weight=1)

        self.widgets['op_fixed_frame'] = tb.Frame(self.widgets['add_op_subframe'])
        self.widgets['op_fixed_frame'].grid(row=2, column=0, columnspan=4, sticky=EW)
        self.widgets['op_cost_label'] = tb.Label(self.widgets['op_fixed_frame'], text=lang.get("op_fixed_cost"))
        self.widgets['op_cost_label'].grid(row=0, column=0, padx=5)
        self.widgets['op_cost_entry'] = tb.Entry(self.widgets['op_fixed_frame'])
        self.widgets['op_cost_entry'].grid(row=0, column=1, padx=5, sticky=EW)
        self.widgets['op_fixed_frame'].grid_columnconfigure(1, weight=1)
        
        self.widgets['add_op_button'] = tb.Button(self.widgets['add_op_subframe'], text=lang.get("op_add_btn"), bootstyle="primary", command=self.add_operation)
        self.widgets['add_op_button'].grid(row=3, column=0, columnspan=4, sticky=EW, pady=(10,0), padx=5)
        
        op_list_frame = tb.Frame(parent)
        op_list_frame.pack(fill=BOTH, expand=True)
        columns = {"col_id": (lang.get("col_id"), 50), "col_desc": (lang.get("col_desc"), 300), "col_details": (lang.get("col_details"), 150), "col_cost": (lang.get("col_cost"), 100)}
        self.widgets['ops_tree'] = tb.Treeview(op_list_frame, columns=[val[0] for val in columns.values()], show='headings', bootstyle="primary")
        for val in columns.values(): self.widgets['ops_tree'].heading(val[0], text=val[0]); self.widgets['ops_tree'].column(val[0], width=val[1], anchor=W)
        self.widgets['ops_tree'].pack(fill=BOTH, expand=True, side=LEFT)
        scrollbar = tb.Scrollbar(op_list_frame, orient=VERTICAL, command=self.widgets['ops_tree'].yview)
        self.widgets['ops_tree'].configure(yscroll=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.widgets['delete_op_button'] = tb.Button(parent, text=lang.get("op_delete_btn"), bootstyle="danger-outline", command=self.delete_operation)
        self.widgets['delete_op_button'].pack(fill=X, pady=(10,0))
        self.toggle_op_inputs()
        
    def populate_cost_tab(self, parent):
        parent.grid_columnconfigure(1, weight=1)
        def create_cost_row(label_key, row):
            label = tb.Label(parent, text=lang.get(label_key))
            label.grid(row=row, column=0, sticky=W, padx=5, pady=3)
            value_label = tb.Label(parent, text="0.00", anchor=E)
            value_label.grid(row=row, column=1, sticky=EW, padx=5, pady=3)
            return label, value_label
        self.widgets['cost_material_label_tab'], self.widgets['cost_material_value'] = create_cost_row("cost_material", 0)
        self.widgets['cost_labor_label_tab'], self.widgets['cost_labor_value'] = create_cost_row("cost_labor", 1)
        self.widgets['cost_subtotal_label_tab'], self.widgets['cost_subtotal_value'] = create_cost_row("cost_total", 2)
        self.widgets['cost_profit_label_tab'], self.widgets['cost_profit_value'] = create_cost_row("profit", 3)

    def populate_notes_tab(self, parent):
        self.widgets['notes_text'] = ScrolledText(parent, wrap=WORD, autohide=True, padding=10)
        self.widgets['notes_text'].pack(fill=BOTH, expand=True)

    def update_language(self):
        self.widgets['quote_info_frame'].config(text=f" {lang.get('quote_info')} ")
        self.widgets['job_name_label'].config(text=lang.get("job_name"))
        self.widgets['customer_name_label'].config(text=lang.get("customer_name"))
        self.widgets['part_details_frame'].config(text=f" {lang.get('part_details')} ")
        self.widgets['material_label'].config(text=lang.get("material"))
        self.widgets['quantity_label'].config(text=lang.get("quantity"))
        self.widgets['notebook'].tab(0, text=lang.get("tab_operations"))
        self.widgets['notebook'].tab(1, text=lang.get("tab_cost_summary"))
        self.widgets['notebook'].tab(2, text=lang.get("tab_notes"))
        self.widgets['add_op_subframe'].config(text=lang.get("op_add_new"))
        self.widgets['op_desc_label'].config(text=lang.get("op_desc"))
        self.widgets['op_method_label'].config(text=lang.get("op_pricing_method"))
        self.widgets['method_combo']['values'] = [lang.get("op_method_time"), lang.get("op_method_fixed")]
        self.widgets['op_hours_label'].config(text=lang.get("op_hours"))
        self.widgets['op_rate_label'].config(text=lang.get("op_machine_rate"))
        self.widgets['op_cost_label'].config(text=lang.get("op_fixed_cost"))
        self.widgets['add_op_button'].config(text=lang.get("op_add_btn"))
        self.widgets['delete_op_button'].config(text=lang.get("op_delete_btn"))
        tree_columns = {"col_id": (lang.get("col_id"), 50), "col_desc": (lang.get("col_desc"), 300), "col_details": (lang.get("col_details"), 150), "col_cost": (lang.get("col_cost"), 100)}
        for i, val in enumerate(tree_columns.values()): self.widgets['ops_tree'].heading(i, text=val[0])
        self.widgets['price_card'].config(text=lang.get("price_summary"))
        self.widgets['chart_frame'].config(text=lang.get('chart_title'))
        self.widgets['save_pdf_btn'].config(text=f"💾 {lang.get('save_pdf', default='Save PDF')}")
        self.widgets['cost_material_label_tab'].config(text=lang.get("cost_material"))
        self.widgets['cost_labor_label_tab'].config(text=lang.get("cost_labor"))
        self.widgets['cost_subtotal_label_tab'].config(text=lang.get("cost_total"))
        self.refresh_operations_table()
        self.calculate_price()

    def refresh_data(self):
        self.widgets['material_combo']['values'] = list(self.app.MATERIAL_COSTS.keys())
        self.widgets['op_rate_combo']['values'] = list(self.app.HOURLY_RATES.keys())

    def toggle_op_inputs(self, event=None):
        if self.widgets['op_method_var'].get() == lang.get("op_method_time"):
            self.widgets['op_time_frame'].grid()
            self.widgets['op_fixed_frame'].grid_remove()
        else:
            self.widgets['op_time_frame'].grid_remove()
            self.widgets['op_fixed_frame'].grid()

    def add_operation(self):
        desc = self.widgets['op_desc_entry'].get()
        method = self.widgets['op_method_var'].get()
        if not desc: return
        try:
            op_data = {"desc": desc}
            if method == lang.get("op_method_time"):
                hours = float(self.widgets['op_hours_entry'].get() or 0)
                rate_key = self.widgets['op_rate_combo'].get()
                rate_value = self.app.HOURLY_RATES.get(rate_key, 0)
                cost = hours * rate_value
                op_data.update({"method": "time", "hours": hours, "rate": rate_value, "cost": cost})
            else:
                cost = float(self.widgets['op_cost_entry'].get() or 0)
                op_data.update({"method": "fixed", "hours": "-", "rate": "-", "cost": cost})
            self.op_counter += 1
            op_data["id"] = self.op_counter
            self.quote_operations.append(op_data)
            self.refresh_operations_table()
            self.calculate_price()
            self.widgets['op_desc_entry'].delete(0, END)
            self.widgets['op_hours_entry'].delete(0, END)
            self.widgets['op_cost_entry'].delete(0, END)
        except (ValueError, tk.TclError) as e:
            messagebox.showerror(lang.get("error_title"), lang.get("error_numeric_only") + f"\n({e})")

    def delete_operation(self):
        if not self.widgets['ops_tree'].selection(): return
        selected_item = self.widgets['ops_tree'].selection()[0]
        values = self.widgets['ops_tree'].item(selected_item, "values")
        if not values: return
        op_id_to_delete = int(values[0])
        self.quote_operations = [op for op in self.quote_operations if op['id'] != op_id_to_delete]
        self.refresh_operations_table()
        self.calculate_price()

    def refresh_operations_table(self):
        tree = self.widgets['ops_tree']
        for item in tree.get_children(): tree.delete(item)
        for op in self.quote_operations:
            details = lang.get("op_details_fixed")
            if op['method'] == 'time':
                details = lang.get("op_details_time", hours=op['hours'], rate=op['rate'])
            cost_str = f"{op['cost']:,.2f}"
            tree.insert('', END, values=(op['id'], op['desc'], details, cost_str))

    def draw_initial_chart(self):
        ax = self.widgets['chart_axes']
        ax.clear()
        ax.text(0.5, 0.5, lang.get('chart_placeholder'), fontproperties=self.app.thai_font, ha='center', va='center', fontsize=14, color='grey')
        self.widgets['chart_canvas'].draw()

    def update_pie_chart(self, data):
        ax = self.widgets['chart_axes']
        ax.clear()
        chart_labels = { 'total_material_cost': lang.get('chart_label_material'), 'total_labor_cost': lang.get('chart_label_labor'), 'profit': lang.get('chart_label_profit') }
        labels = [chart_labels.get(key, key) for key in data.keys()]
        values = list(data.values())
        filtered_labels = [label for i, label in enumerate(labels) if values[i] > 0]
        filtered_values = [value for value in values if value > 0]
        if not filtered_values:
            self.draw_initial_chart()
            return
        colors = ['#17A2B8', '#FFC107', '#28A745']
        wedges, _, autotexts = ax.pie(filtered_values, autopct='%1.1f%%', startangle=90, colors=colors, wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}, pctdistance=0.85)
        legend = ax.legend(wedges, filtered_labels, title=lang.get("chart_legend_title"), loc="center left", bbox_to_anchor=(0.95, 0, 0.5, 1))
        plt.setp(legend.get_texts(), fontproperties=self.app.thai_font)
        plt.setp(legend.get_title(), fontproperties=self.app.thai_font)
        plt.setp(autotexts, size=10, weight="bold", color="white")
        ax.axis('equal')
        self.widgets['chart_canvas'].draw()

    def calculate_price(self, return_data=False):
        try:
            quantity = int(self.widgets['quantity_entry'].get() or 1)
            if quantity <= 0: raise ValueError("Quantity must be > 0")
            material_cost_per_unit = self.app.MATERIAL_COSTS.get(self.widgets['material_combo'].get(), 0)
            total_material_cost = material_cost_per_unit * quantity
            total_labor_cost_per_unit = sum(op['cost'] for op in self.quote_operations)
            total_labor_cost = total_labor_cost_per_unit * quantity
            sub_total = total_material_cost + total_labor_cost
            profit = sub_total * self.app.PROFIT_MARGIN
            final_price = sub_total + profit
            
            unit_str = lang.get("unit_thb")
            self.widgets['final_price_label'].config(text=f"{final_price:,.2f}")
            self.widgets['price_per_unit_label'].config(text=lang.get("price_per_unit", price=final_price / quantity if quantity > 0 else 0))
            self.widgets['cost_material_value'].config(text=f"{total_material_cost:,.2f} {unit_str}")
            self.widgets['cost_labor_value'].config(text=f"{total_labor_cost:,.2f} {unit_str}")
            self.widgets['cost_subtotal_value'].config(text=f"{sub_total:,.2f} {unit_str}")
            self.widgets['cost_profit_value'].config(text=f"{profit:,.2f} {unit_str}")
            self.widgets['cost_profit_label_tab'].config(text=lang.get("profit", percent=self.app.PROFIT_MARGIN*100))
            
            chart_data = {'total_material_cost': total_material_cost, 'total_labor_cost': total_labor_cost, 'profit': profit}
            self.update_pie_chart(chart_data)

            if return_data:
                return {
                    "quantity": quantity, "material_cost_per_unit": material_cost_per_unit,
                    "total_labor_cost_per_unit": total_labor_cost_per_unit, "sub_total": sub_total,
                    "profit": profit, "final_price": final_price
                }
        except (ValueError, ZeroDivisionError) as e:
            messagebox.showerror(lang.get("error_title"), lang.get('error_numeric_only') + f"\n\n({e})")
            self.clear_results()
            if return_data: return None

    def clear_results(self):
        unit_str = lang.get("unit_thb")
        self.widgets['final_price_label'].config(text="0.00")
        self.widgets['price_per_unit_label'].config(text=lang.get("price_per_unit", price=0))
        self.widgets['cost_material_value'].config(text=f"0.00 {unit_str}")
        self.widgets['cost_labor_value'].config(text=f"0.00 {unit_str}")
        self.widgets['cost_subtotal_value'].config(text=f"0.00 {unit_str}")
        self.widgets['cost_profit_value'].config(text=f"0.00 {unit_str}")
        self.draw_initial_chart()

    def clear_form(self, clear_job_info=True):
        if clear_job_info:
            self.widgets['job_name_entry'].delete(0, END)
            self.widgets['customer_name_entry'].delete(0, END)
        if list(self.app.MATERIAL_COSTS.keys()): self.widgets['material_combo'].current(0)
        self.widgets['quantity_entry'].delete(0, END)
        self.widgets['quantity_entry'].insert(0, "1")
        self.quote_operations = []
        if 'ops_tree' in self.widgets: self.refresh_operations_table()
        self.clear_results()

    def save_pdf(self):
        price_data = self.calculate_price(return_data=True)
        if not price_data:
            messagebox.showwarning(lang.get("cannot_save_title", default="Cannot Save"), lang.get("calculate_first_warning", default="Please calculate a price before saving."))
            return

        default_filename = f"{lang.get('quote_filename', default='Quote')}_{self.widgets['job_name_entry'].get() or 'untitled'}.pdf"
        filepath = filedialog.asksaveasfilename(title=lang.get("save_pdf_title", default="Save Quote as PDF"), initialfile=default_filename, defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")])
        
        if not filepath: return
        
        operations_for_pdf = []
        for op in self.quote_operations:
            details = lang.get("op_details_fixed")
            if op['method'] == 'time':
                details = lang.get("op_details_time", hours=op['hours'], rate=op['rate'])
            operations_for_pdf.append({"desc": op['desc'], "details": details, "cost": op['cost'] * price_data['quantity']})

        quote_data_for_pdf = {
            "job_name": self.widgets['job_name_entry'].get(),
            "customer_name": self.widgets['customer_name_entry'].get(),
            "operations": operations_for_pdf,
            "notes": self.widgets['notes_text'].get("1.0", "end-1c"),
            "quantity": price_data['quantity'],
            "material_cost_per_unit": price_data['material_cost_per_unit'],
            "total_labor_cost_per_unit": price_data['total_labor_cost_per_unit'],
            "sub_total": price_data['sub_total'],
            "profit_margin_percent": self.app.PROFIT_MARGIN * 100,
            "profit": price_data['profit'],
            "final_price": price_data['final_price']
        }
        
        try:
            pdf_generator.create_quote_pdf(quote_data_for_pdf, filepath)
            messagebox.showinfo(lang.get("success_title"), f"{lang.get('pdf_saved_success', default='PDF saved successfully at:')}\n{filepath}")
        except Exception as e:
            messagebox.showerror(lang.get("error_title"), f"{lang.get('pdf_saved_error', default='Failed to create PDF:')}\n{e}")

# ===================================================================
# ===== MAIN APP CLASS ==============================================
# ===================================================================
class MainApp(tb.Window):
    def __init__(self):
        super().__init__(themename="litera")
        self.title(lang.get("app_title"))
        self.geometry("1600x900")

        try:
            self.iconbitmap(ICON_PATH)
        except tk.TclError:
            print(f"Could not find icon file at: {ICON_PATH}")


        database.initialize_db()
        self.refresh_data_from_db()
        
        try:
            font_path = 'C:/Windows/Fonts/tahoma.ttf'
            self.thai_font = font_manager.FontProperties(fname=font_path)
        except FileNotFoundError:
            self.thai_font = font_manager.FontProperties()

        self.configure_styles()
        
        self.pages = {}
        self.create_main_layout()
        self.show_page("quoting")

    def configure_styles(self):
        style = tb.Style.get_instance()
        style.configure('Nav.TButton', font=('Helvetica', 11), anchor='w', padding=(20, 15))
        style.configure('CardValue.TLabel', font=('Helvetica', 42, 'bold'))
        style.configure('CardUnit.TLabel', font=('Helvetica', 14))

    def create_main_layout(self):
        container = tb.Frame(self)
        container.pack(fill=BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        nav_frame = tb.Frame(container, bootstyle="light", width=250)
        nav_frame.grid(row=0, column=0, sticky="nsew")
        nav_frame.pack_propagate(False)
        self.nav_title = tb.Label(nav_frame, text="SME Quoting", font=("Helvetica", 22, "bold"), bootstyle="inverse-light")
        self.nav_title.pack(pady=20, padx=10)
        
        self.nav_buttons = {}
        nav_buttons_info = {"quoting": ("📝", "nav_quoting"), "history": ("🗄️", "nav_history"), "customers": ("👥", "nav_customers")}
        for name, (icon, key) in nav_buttons_info.items():
            btn = tb.Button(nav_frame, text=f" {icon} {lang.get(key)}", style='Nav.TButton', bootstyle="light", command=lambda n=name: self.show_page(n))
            btn.pack(fill=X, pady=1, padx=10)
            self.nav_buttons[name] = btn

        self.settings_btn = tb.Button(nav_frame, text=f"⚙️ {lang.get('settings')}", style='Nav.TButton', bootstyle="light", command=self.open_settings_window)
        self.settings_btn.pack(fill=X, pady=1, padx=10, side=BOTTOM)

        self.content_frame = tb.Frame(container, bootstyle="secondary")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        self.pages["quoting"] = QuotingPage(self.content_frame, self)
        self.pages["history"] = PlaceholderPage(self.content_frame, self)
        self.pages["customers"] = PlaceholderPage(self.content_frame, self)

        for page in self.pages.values():
            page.place(x=0, y=0, relwidth=1, relheight=1)

    def show_page(self, page_name):
        page = self.pages.get(page_name)
        if page: page.tkraise()

    def refresh_data_from_db(self):
        all_settings = database.get_settings()
        non_hourly_keys = ['profit_margin', 'Wire EDM_sqmm']
        self.PROFIT_MARGIN = all_settings.get('profit_margin', 0.25)
        self.HOURLY_RATES = { k: v for k, v in all_settings.items() if k not in non_hourly_keys }
        self.MATERIAL_COSTS = database.get_all_materials()

    def open_settings_window(self):
        dialog = SettingsWindow(parent=self)
        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)
        
        self.refresh_data_from_db()
        self.update_ui_language()

    def update_ui_language(self):
        self.title(lang.get("app_title"))
        self.nav_buttons["quoting"].config(text=f"📝 {lang.get('nav_quoting')}")
        self.nav_buttons["history"].config(text=f"🗄️ {lang.get('nav_history')}")
        self.nav_buttons["customers"].config(text=f"👥 {lang.get('nav_customers')}")
        self.settings_btn.config(text=f"⚙️ {lang.get('settings')}")
        
        for page in self.pages.values():
            if hasattr(page, 'update_language'): page.update_language()
            if hasattr(page, 'refresh_data'): page.refresh_data()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()