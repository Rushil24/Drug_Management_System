import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from PIL import Image, ImageTk

# ---------- DB CONFIG ----------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "muskan",
    "database": "drug_inventory",
    "port": 3306
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ---------- UI ----------
class StockInwardApp:
    def __init__(self, root):
        self.root = root
        root.title("Stock Inward / Goods Receipt")
        root.geometry("1100x700")
        root.minsize(900, 550)

        # configure root grid so everything expands
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # ===== Background placeholder =====
        try:
            self.bg_img = ImageTk.PhotoImage(file="C:\\Users\\muska\\Downloads\\background.png")  # replace with your file
        except:
            self.bg_img = ImageTk.PhotoImage(Image.new("RGB", (1100, 700), "#eaf0f7"))
        bg_label = tk.Label(root, image=self.bg_img)
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ===== Main container frame =====
        container = tk.Frame(root, bg="#ffffff")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(3, weight=1)  # table expands
        container.grid_columnconfigure(0, weight=1)

        # ===== Header with logo =====
        header_frame = tk.Frame(container, bg="#2c3e50", height=70)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        try:
            self.logo_img = ImageTk.PhotoImage(file="C:\\Users\\muska\\Downloads\\logo.png")  # replace with your file
        except:
            self.logo_img = ImageTk.PhotoImage(Image.new("RGB", (60, 60), "#4a90e2"))

        logo_label = tk.Label(header_frame, image=self.logo_img, bg="#2c3e50")
        logo_label.grid(row=0, column=0, padx=15, pady=5)

        title_label = tk.Label(header_frame, text="Stock Inward / Goods Receipt",
                               font=("Segoe UI", 18, "bold"), bg="#2c3e50", fg="white")
        title_label.grid(row=0, column=1, sticky="w")

        # ===== Input form =====
        form_frame = ttk.Frame(container, padding=12)
        form_frame.grid(row=1, column=0, sticky="ew")
        for i in range(6):
            form_frame.grid_columnconfigure(i, weight=1)

        ttk.Label(form_frame, text="Drug:").grid(row=0, column=0, sticky="w", pady=4)
        self.drug_cb = ttk.Combobox(form_frame, state="readonly")
        self.drug_cb.grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(form_frame, text="Location:").grid(row=0, column=2, sticky="w")
        self.loc_cb = ttk.Combobox(form_frame, state="readonly")
        self.loc_cb.grid(row=0, column=3, sticky="ew", padx=5)

        ttk.Label(form_frame, text="Batch No:").grid(row=1, column=0, sticky="w", pady=4)
        self.batch_entry = ttk.Entry(form_frame)
        self.batch_entry.grid(row=1, column=1, sticky="ew", padx=5)

        ttk.Label(form_frame, text="Mfg Date (YYYY-MM-DD):").grid(row=1, column=2, sticky="w")
        self.mfg_entry = ttk.Entry(form_frame)
        self.mfg_entry.grid(row=1, column=3, sticky="ew", padx=5)

        ttk.Label(form_frame, text="Expiry Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", pady=4)
        self.exp_entry = ttk.Entry(form_frame)
        self.exp_entry.grid(row=2, column=1, sticky="ew", padx=5)

        ttk.Label(form_frame, text="Quantity:").grid(row=2, column=2, sticky="w")
        self.qty_entry = ttk.Entry(form_frame)
        self.qty_entry.grid(row=2, column=3, sticky="ew", padx=5)

        ttk.Label(form_frame, text="Unit Cost:").grid(row=3, column=0, sticky="w", pady=4)
        self.cost_entry = ttk.Entry(form_frame)
        self.cost_entry.grid(row=3, column=1, sticky="ew", padx=5)

        ttk.Label(form_frame, text="Remarks:").grid(row=3, column=2, sticky="w")
        self.remark_entry = ttk.Entry(form_frame)
        self.remark_entry.grid(row=3, column=3, sticky="ew", padx=5)

        # ===== Buttons =====
        btn_frame = tk.Frame(container, bg="#ffffff")
        btn_frame.grid(row=2, column=0, sticky="ew", pady=8)
        btn_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.add_button(btn_frame, "Receive Stock", self.receive_stock, 0)
        self.add_button(btn_frame, "Clear Inputs", self.clear_inputs, 1)
        self.add_button(btn_frame, "Refresh Lists", self.load_lookups, 2)
        self.add_button(btn_frame, "Refresh Table", self.load_batches_table, 3)
        self.add_button(btn_frame, "Exit", root.quit, 4)

        # ===== Table =====
        table_frame = ttk.Frame(container)
        table_frame.grid(row=3, column=0, sticky="nsew", pady=(5, 10), padx=10)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        cols = ("id","drug","batch_no","quantity","manufacture_date","expiry_date","unit_cost","location")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        # ===== Load data =====
        self.load_lookups()
        self.load_batches_table()

    # -------- Button helper --------
    def add_button(self, parent, text, command, col):
        btn = tk.Button(parent, text=text, command=command,
                        bg="#3498db", fg="white", activebackground="#2980b9",
                        font=("Segoe UI", 10, "bold"), relief="flat", height=2)
        btn.grid(row=0, column=col, sticky="ew", padx=6)

    # -------- DB functions --------
    def load_lookups(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM drugs ORDER BY name")
            self.drug_map = {f"{r[0]} - {r[1]}": r[0] for r in cur.fetchall()}
            self.drug_cb["values"] = list(self.drug_map.keys())
            cur.execute("SELECT id, name FROM locations ORDER BY name")
            self.loc_map = {f"{r[0]} - {r[1]}": r[0] for r in cur.fetchall()}
            self.loc_cb["values"] = list(self.loc_map.keys())
        except Error as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            try: cur.close(); conn.close()
            except: pass

    def load_batches_table(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT b.id, d.name, b.batch_no, b.quantity, b.manufacture_date,
                       b.expiry_date, b.unit_cost, l.name
                FROM drug_batch b
                JOIN drugs d ON b.drug_id=d.id
                LEFT JOIN locations l ON b.location_id=l.id
                WHERE b.status='available'
                ORDER BY d.name
            """)
            rows = cur.fetchall()
            for r in self.tree.get_children():
                self.tree.delete(r)
            for r in rows:
                self.tree.insert("", "end", values=r)
        except Error as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            try: cur.close(); conn.close()
            except: pass

    def clear_inputs(self):
        for e in [self.batch_entry, self.mfg_entry, self.exp_entry, self.qty_entry, self.cost_entry, self.remark_entry]:
            e.delete(0, tk.END)
        self.drug_cb.set(""); self.loc_cb.set("")

    def receive_stock(self):
        messagebox.showinfo("Info", "Stock receiving logic here (same as your existing one).")


# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = StockInwardApp(root)
    root.mainloop()
