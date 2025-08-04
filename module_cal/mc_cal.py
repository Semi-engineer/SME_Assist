# File: mc_cal.py (Fully Refactored for i18n)
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
import database
import math
from language_manager import lang

class OperationManagerWindow(tb.Toplevel):
    def __init__(self, parent, target_entry, lang_manager):
        super().__init__(parent)
        self.lang = lang_manager
        self.title(self.lang.get("op_manager_title"))
        self.geometry("800x800")

        self.target_entry = target_entry
        self.operations = [] 
        self.op_counter = 0

        input_frame = tb.Labelframe(self, text=self.lang.get("op_manager_form_title"), padding=15)
        input_frame.pack(padx=10, pady=10, fill=X)
        
        self.create_detailed_drill_form(input_frame)
        
        add_op_button = tb.Button(input_frame, text=self.lang.get("op_manager_add_button"), command=self.add_operation, bootstyle="primary")
        add_op_button.grid(row=10, column=0, columnspan=2, pady=15, sticky=tk.EW)

        table_frame = tb.Labelframe(self, text=self.lang.get("op_manager_table_title"), padding=15)
        table_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)

        columns = {
            "col_id": (self.lang.get("col_id"), 50), 
            "col_op": (self.lang.get("col_op"), 450), 
            "col_time": (self.lang.get("col_time"), 100)
        }
        self.tree = tb.Treeview(table_frame, columns=[val[0] for val in columns.values()], show='headings', bootstyle="primary")
        
        for key, val in columns.items():
            self.tree.heading(val[0], text=val[0])
            self.tree.column(val[0], width=val[1], anchor=tk.CENTER)
            
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        
        scrollbar = tb.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=tk.Y)

        control_frame = tb.Frame(self)
        control_frame.pack(padx=10, pady=10, fill=X)
        
        delete_button = tb.Button(control_frame, text=self.lang.get("op_manager_delete_button"), command=self.delete_operation, bootstyle="danger")
        delete_button.pack(side=LEFT, padx=5)
        
        self.total_time_label = tb.Label(control_frame, text=self.lang.get("op_manager_total_time", hours=0), font=("Helvetica", 12, "bold"))
        self.total_time_label.pack(side=RIGHT, padx=5)
        
        apply_button = tb.Button(self, text=self.lang.get("apply_value_button"), command=self.apply_value, bootstyle="success")
        apply_button.pack(padx=10, pady=(0,10), fill=X, ipady=10)

    def create_detailed_drill_form(self, parent_frame):
        self.drill_gcode_combo = self.create_input_row(parent_frame, self.lang.get("gcode_select"), "", 0, is_combo=True)
        self.drill_gcode_combo['values'] = ['G81', 'G82', 'G83']
        self.drill_gcode_combo.current(0)
        self.drill_gcode_combo.bind("<<ComboboxSelected>>", self.on_gcode_selected)
        self.drill_depth = self.create_input_row(parent_frame, self.lang.get("depth_input"), "10", 1)
        self.drill_rpm = self.create_input_row(parent_frame, self.lang.get("rpm_input"), "1500", 2)
        self.drill_feed_rate_per_min = self.create_input_row(parent_frame, self.lang.get("feedg01_input"), "150", 3)
        self.drill_rapid_feed = self.create_input_row(parent_frame, self.lang.get("feedg00_input"), "5000", 4)
        self.drill_hole_count = self.create_input_row(parent_frame, self.lang.get("hole_count_input"), "1", 5)
        self.dwell_row, self.drill_dwell = self.create_input_row(parent_frame, self.lang.get("dwell_input"), "500", 6, return_full_row=True)
        self.peck_row, self.drill_peck = self.create_input_row(parent_frame, self.lang.get("peck_input"), "3", 7, return_full_row=True)
        self.on_gcode_selected()

    def on_gcode_selected(self, event=None):
        selected_gcode = self.drill_gcode_combo.get()
        if selected_gcode == 'G81': self.dwell_row.grid_remove(); self.peck_row.grid_remove()
        elif selected_gcode == 'G82': self.dwell_row.grid(); self.peck_row.grid_remove()
        elif selected_gcode == 'G83': self.dwell_row.grid_remove(); self.peck_row.grid()

    def create_input_row(self, parent, label_text, default_value, row_num, is_combo=False, return_full_row=False):
        label = tb.Label(parent, text=label_text)
        label.grid(row=row_num, column=0, padx=5, pady=5, sticky=tk.W)
        if is_combo: widget = tb.Combobox(parent, bootstyle="info", width=30)
        else:
            widget = tb.Entry(parent, bootstyle="info", width=30)
            widget.insert(0, default_value)
        widget.grid(row=row_num, column=1, padx=5, pady=5, sticky=tk.W)
        if return_full_row: return parent.grid_slaves(row=row_num)[1].master, widget
        return widget

    def add_operation(self):
        try:
            gcode = self.drill_gcode_combo.get()
            depth = float(self.drill_depth.get())
            feed_per_min = float(self.drill_feed_rate_per_min.get())
            rapid_feed_rate = float(self.drill_rapid_feed.get())
            count = int(self.drill_hole_count.get())
            if feed_per_min == 0 or rapid_feed_rate == 0: raise ZeroDivisionError("Feed rate cannot be zero")
            
            feed_time_per_hole_min = depth / feed_per_min
            total_time_min = 0; description = ""

            if gcode == 'G81':
                total_time_min = feed_time_per_hole_min * count
                description = self.lang.get("desc_g81", count=count, depth=depth, feed=feed_per_min)
            elif gcode == 'G82':
                dwell_ms = float(self.drill_dwell.get())
                dwell_time_min = dwell_ms / (1000 * 60)
                total_time_min = (feed_time_per_hole_min + dwell_time_min) * count
                description = self.lang.get("desc_g82", count=count, depth=depth, dwell=dwell_ms)
            elif gcode == 'G83':
                peck_depth_q = float(self.drill_peck.get())
                if peck_depth_q <= 0: raise ValueError("Peck Depth must be > 0")
                total_rapid_dist, current_drilled_depth, depth_remaining = 0, 0, depth
                while depth_remaining > 1e-4:
                    peck = min(peck_depth_q, depth_remaining)
                    depth_after_peck = current_drilled_depth + peck
                    depth_remaining -= peck
                    if depth_remaining > 1e-4:
                        total_rapid_dist += depth_after_peck + current_drilled_depth
                    current_drilled_depth = depth_after_peck
                rapid_time_min = total_rapid_dist / rapid_feed_rate
                total_time_min = (feed_time_per_hole_min + rapid_time_min) * count
                description = self.lang.get("desc_g83", count=count, depth=depth, peck=peck_depth_q)
            
            self.op_counter += 1
            self.operations.append({"id": self.op_counter, "desc": description, "time": total_time_min})
            self.refresh_table()
        except (ValueError, ZeroDivisionError) as e:
            messagebox.showerror(self.lang.get("error_title"), self.lang.get("error_numeric_only") + f"\n({e})")
            
    def delete_operation(self):
        if not self.tree.selection(): return
        ids_to_delete = {int(self.tree.item(item, 'values')[0]) for item in self.tree.selection()}
        self.operations = [op for op in self.operations if op["id"] not in ids_to_delete]
        self.refresh_table()

    def refresh_table(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for op in self.operations:
            self.tree.insert('', tk.END, values=(op['id'], op['desc'], f"{op['time']:.3f}"))
        self.update_total_time()
        
    def update_total_time(self):
        total_minutes = sum(op['time'] for op in self.operations)
        total_hours = total_minutes / 60.0
        self.total_time_label.config(text=self.lang.get("op_manager_total_time", hours=total_hours))

    def apply_value(self):
        total_minutes = sum(op['time'] for op in self.operations)
        total_hours = total_minutes / 60.0
        self.target_entry.delete(0, END)
        self.target_entry.insert(0, f"{total_hours:.4f}")
        self.destroy()

class WireEdmCalculatorDialog(tb.Toplevel):
    def __init__(self, parent, target_entry, lang_manager):
        super().__init__(parent)
        self.lang = lang_manager
        self.title(self.lang.get("wire_edm_calc_title"))
        self.geometry("500x450")
        
        self.target_entry = target_entry
        all_settings = database.get_settings()
        self.hourly_rate = all_settings.get('Wire EDM', 950)
        self.sqmm_rate = all_settings.get('Wire EDM_sqmm', 0.15)
        
        self.widgets = {}
        self.create_widgets()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        tb.Label(main_frame, text=self.lang.get("calc_method"), font="-size 12").pack(anchor=W)
        self.calc_method_var = tk.StringVar(value=self.lang.get("method_hours"))
        
        method_values = [self.lang.get("method_hours"), self.lang.get("method_sqmm")]
        method_combo = tb.Combobox(main_frame, textvariable=self.calc_method_var, values=method_values, bootstyle="info")
        method_combo.pack(fill=X, pady=(5, 15))
        method_combo.bind("<<ComboboxSelected>>", self.toggle_forms)

        self.hour_form = tb.Frame(main_frame)
        self.area_form = tb.Frame(main_frame)
        
        tb.Label(self.hour_form, text=self.lang.get("hours_input")).pack(anchor=W, pady=2)
        self.widgets['hours'] = tb.Entry(self.hour_form, bootstyle="info")
        self.widgets['hours'].pack(fill=X)
        
        tb.Label(self.area_form, text=self.lang.get("length_input")).pack(anchor=W, pady=2)
        self.widgets['length'] = tb.Entry(self.area_form, bootstyle="info")
        self.widgets['length'].pack(fill=X)
        
        tb.Label(self.area_form, text=self.lang.get("thickness_input")).pack(anchor=W, pady=5)
        self.widgets['thickness'] = tb.Entry(self.area_form, bootstyle="info")
        self.widgets['thickness'].pack(fill=X)

        tb.Label(self.area_form, text=self.lang.get("price_per_sqmm", rate=self.sqmm_rate), bootstyle="secondary").pack(anchor=W, pady=5)

        calc_button = tb.Button(main_frame, text=self.lang.get("calculate_and_apply"), bootstyle="success", command=self.calculate_and_apply)
        calc_button.pack(pady=20, fill=X, ipady=10)
        self.toggle_forms()

    def toggle_forms(self, event=None):
        if self.calc_method_var.get() == self.lang.get("method_hours"):
            self.area_form.pack_forget()
            self.hour_form.pack(fill=X, expand=True)
        else:
            self.hour_form.pack_forget()
            self.area_form.pack(fill=X, expand=True)

    def calculate_and_apply(self):
        try:
            final_hours = 0.0
            if self.calc_method_var.get() == self.lang.get("method_hours"):
                final_hours = float(self.widgets['hours'].get())
            else:
                length = float(self.widgets['length'].get())
                thickness = float(self.widgets['thickness'].get())
                total_cost = length * thickness * self.sqmm_rate
                if self.hourly_rate > 0:
                    final_hours = total_cost / self.hourly_rate
                else: raise ValueError("Hourly rate for Wire EDM is zero.")

            self.target_entry.delete(0, END)
            self.target_entry.insert(0, f"{final_hours:.4f}")
            self.destroy()
        except (ValueError, TypeError, ZeroDivisionError) as e:
            messagebox.showerror(self.lang.get("error_title"), self.lang.get("error_numeric_only") + f"\n({e})")