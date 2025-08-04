# -*- coding: utf-8 -*-
# sales_order_app.py

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.widgets import DateEntry
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import sqlite3
from datetime import date

class DatabaseManager:
    def __init__(self, db_file="sme_erp.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row

    def execute_query(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.lastrowid

    def fetch_all(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
        
    def __del__(self):
        if self.conn:
            self.conn.close()

class SalesOrderApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="cosmo")
        self.title("สร้างคำสั่งขาย (Sales Order)")
        self.geometry("950x700")

        self.db = DatabaseManager()
        self.default_font = ("Sarabun", 12)
        self.style.configure('.', font=self.default_font)

        # ตัวแปรสำหรับเก็บข้อมูล
        self.customers_map = {}
        self.products_map = {}
        self.current_order_items = [] # เก็บรายการสินค้าในออเดอร์ปัจจุบัน (ในหน่วยความจำ)
        self.total_amount_var = tk.DoubleVar(value=0.0)

        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
        # --- Frame หลัก ---
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # --- ส่วน Header ---
        header_frame = ttk.Labelframe(main_frame, text="ข้อมูลคำสั่งขาย", padding=10)
        header_frame.pack(fill=X, pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        header_frame.columnconfigure(3, weight=1)

        ttk.Label(header_frame, text="ลูกค้า:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.customer_combo = ttk.Combobox(header_frame, state="readonly")
        self.customer_combo.grid(row=0, column=1, padx=5, pady=5, sticky=EW)

        ttk.Label(header_frame, text="วันที่:").grid(row=0, column=2, padx=5, pady=5, sticky=W)
        self.order_date_entry = DateEntry(header_frame, dateformat='%Y-%m-%d')
        self.order_date_entry.grid(row=0, column=3, padx=5, pady=5, sticky=W)

        # --- ส่วนเพิ่มรายการ ---
        line_item_frame = ttk.Labelframe(main_frame, text="เพิ่มรายการสินค้า", padding=10)
        line_item_frame.pack(fill=X, pady=(0, 10))
        line_item_frame.columnconfigure(1, weight=1)

        ttk.Label(line_item_frame, text="สินค้า:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.product_combo = ttk.Combobox(line_item_frame, state="readonly")
        self.product_combo.grid(row=0, column=1, sticky=EW, padx=5, pady=5)

        ttk.Label(line_item_frame, text="จำนวน:").grid(row=0, column=2, sticky=W, padx=5, pady=5)
        self.quantity_entry = ttk.Entry(line_item_frame, width=10)
        self.quantity_entry.grid(row=0, column=3, sticky=W, padx=5, pady=5)

        ttk.Button(line_item_frame, text="เพิ่มลงในรายการ", command=self.add_item_to_order, bootstyle=INFO).grid(row=0, column=4, padx=10, pady=5)

        # --- ส่วนสรุปรายการ (ตาราง) ---
        summary_frame = ttk.Labelframe(main_frame, text="สรุปรายการ", padding=10)
        summary_frame.pack(fill=BOTH, expand=YES)

        coldata = [
            {"text": "รหัสสินค้า", "stretch": False, "width": 80},
            {"text": "ชื่อสินค้า", "stretch": True},
            {"text": "จำนวน", "stretch": False, "width": 80},
            {"text": "ราคา/หน่วย", "stretch": False, "width": 120},
            {"text": "ราคารวม", "stretch": False, "width": 120},
        ]
        self.table = Tableview(summary_frame, coldata=coldata, bootstyle=PRIMARY, stripecolor=(self.style.colors.light, None))
        self.table.pack(fill=BOTH, expand=YES)

        # --- ส่วนท้าย ---
        footer_frame = ttk.Frame(main_frame, padding=(0, 10))
        footer_frame.pack(fill=X)
        footer_frame.columnconfigure(1, weight=1)

        ttk.Label(footer_frame, text="ยอดรวมสุทธิ:", font=(self.default_font[0], 14, 'bold')).grid(row=0, column=0, sticky=E, padx=5)
        ttk.Label(footer_frame, textvariable=self.total_amount_var, font=(self.default_font[0], 14, 'bold'), bootstyle="success").grid(row=0, column=1, sticky=W, padx=5)
        
        ttk.Button(footer_frame, text="บันทึกคำสั่งขาย", command=self.save_order, bootstyle=SUCCESS, width=20).grid(row=0, column=2, sticky=E, padx=10)


    def load_initial_data(self):
        # โหลดข้อมูลลูกค้า
        customers = self.db.fetch_all("SELECT customer_id, customer_name FROM Customers ORDER BY customer_name")
        customer_names = []
        for c in customers:
            display_name = f"{c['customer_name']} (ID: {c['customer_id']})"
            customer_names.append(display_name)
            self.customers_map[display_name] = c['customer_id']
        self.customer_combo['values'] = customer_names

        # โหลดข้อมูลสินค้า
        products = self.db.fetch_all("SELECT product_id, product_name, unit_price FROM Products ORDER BY product_name")
        product_names = []
        for p in products:
            display_name = f"{p['product_name']}"
            product_names.append(display_name)
            self.products_map[display_name] = {'id': p['product_id'], 'price': p['unit_price']}
        self.product_combo['values'] = product_names
        
    def add_item_to_order(self):
        product_name = self.product_combo.get()
        quantity_str = self.quantity_entry.get()

        if not product_name or not quantity_str:
            Messagebox.show_warning("ข้อมูลไม่ครบ", "กรุณาเลือกสินค้าและใส่จำนวน")
            return
        
        try:
            quantity = int(quantity_str)
            if quantity <= 0: raise ValueError
        except ValueError:
            Messagebox.show_error("ข้อมูลผิดพลาด", "จำนวนต้องเป็นตัวเลขที่มากกว่า 0")
            return

        product_data = self.products_map[product_name]
        item = {
            'product_id': product_data['id'],
            'product_name': product_name,
            'quantity': quantity,
            'unit_price': product_data['price'],
            'subtotal': quantity * product_data['price']
        }
        self.current_order_items.append(item)
        self.refresh_order_table()
        self.quantity_entry.delete(0, END)

    def refresh_order_table(self):
        self.table.delete_rows()
        total = 0.0
        for item in self.current_order_items:
            row = [item['product_id'], item['product_name'], item['quantity'], f"{item['unit_price']:.2f}", f"{item['subtotal']:.2f}"]
            self.table.insert_row('end', row)
            total += item['subtotal']
        self.table.load_table_data()
        self.total_amount_var.set(f"{total:.2f}")

    def save_order(self):
        customer_display_name = self.customer_combo.get()
        order_date = self.order_date_entry.entry.get()

        if not customer_display_name:
            Messagebox.show_warning("ข้อมูลไม่ครบ", "กรุณาเลือกลูกค้า")
            return
        
        if not self.current_order_items:
            Messagebox.show_warning("ไม่มีรายการ", "กรุณาเพิ่มรายการสินค้าอย่างน้อย 1 รายการ")
            return

        # บันทึก SalesOrder เพื่อเอา order_id
        customer_id = self.customers_map[customer_display_name]
        total_amount = self.total_amount_var.get()
        
        so_sql = "INSERT INTO SalesOrders (order_date, customer_id, total_amount, status) VALUES (?, ?, ?, ?)"
        so_params = (order_date, customer_id, total_amount, 'Confirmed')
        order_id = self.db.execute_query(so_sql, so_params)

        if order_id:
            # บันทึก OrderItems
            oi_sql = "INSERT INTO OrderItems (order_id, product_id, quantity, price_per_unit) VALUES (?, ?, ?, ?)"
            for item in self.current_order_items:
                oi_params = (order_id, item['product_id'], item['quantity'], item['unit_price'])
                self.db.execute_query(oi_sql, oi_params)
            
            Messagebox.show_info("สำเร็จ", f"บันทึกคำสั่งขาย ID: {order_id} เรียบร้อยแล้ว")
            self.clear_form()
        else:
            Messagebox.show_error("ผิดพลาด", "ไม่สามารถบันทึกคำสั่งขายได้")
            
    def clear_form(self):
        self.customer_combo.set('')
        self.product_combo.set('')
        self.quantity_entry.delete(0, END)
        self.current_order_items = []
        self.refresh_order_table()


if __name__ == "__main__":
    app = SalesOrderApp()
    app.mainloop()