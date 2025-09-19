import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
from datetime import datetime
import base64
import io
import csv
import os

# Optional: try to use Pillow for better image support; if not available we fall back to PhotoImage
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# ----------- Database connection -----------
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        database='drug_inventory',
        user='root',
        password='muskan'
    )


# ----------- Main App -----------
class DrugInventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drug Inventory Management System")
        self.root.geometry("1100x700")
        # icon and image refs to avoid GC
        self._images = {}

        # ---------- Styling ----------
        style = ttk.Style(self.root)
        # Use a theme that is styleable
        try:
            style.theme_use('clam')
        except Exception:
            pass
        base_font = ("Segoe UI", 10)
        style.configure('.', font=base_font)
        style.configure('Header.TLabel', font=("Segoe UI", 16, "bold"))
        style.configure('Accent.TButton', foreground='white', background='#0078D7', font=("Segoe UI", 10, "bold"), padding=8)
        style.map('Accent.TButton', background=[('active', '#005A9E')])
        style.configure('TButton', padding=6)
        style.configure('TEntry', padding=6)
        style.configure('Treeview', rowheight=26, font=("Segoe UI", 10))
        style.configure('Treeview.Heading', font=("Segoe UI", 10, "bold"))

        style.configure('TNotebook.Tab', font=("Segoe UI", 10, "bold"), padding=[12, 8])

        # ---------- Top header ----------
        header = ttk.Frame(root)
        header.pack(side='top', fill='x')

        logo = self._load_image_if_exists("C:\\Users\\muska\\Downloads\\logo.png", (42, 42))
        if logo:
            logo_lbl = ttk.Label(header, image=logo)
            logo_lbl.image = logo
            logo_lbl.pack(side='left', padx=12, pady=8)
            self._images['logo'] = logo

        title_lbl = ttk.Label(header, text="Drug Inventory Management System", style='Header.TLabel')
        title_lbl.pack(side='left', padx=8)

        # status label on header right
        self.status_var = tk.StringVar(value="Ready")
        status_lbl = ttk.Label(header, textvariable=self.status_var)
        status_lbl.pack(side='right', padx=12)

        # ---------- Notebook ----------
        self.tab_control = ttk.Notebook(root)
        self.tab_control.pack(expand=1, fill='both', padx=12, pady=(6,12))

        # Create tabs
        self.roles_tab = ttk.Frame(self.tab_control)
        self.users_tab = ttk.Frame(self.tab_control)
        self.drugs_tab = ttk.Frame(self.tab_control)
        self.vendors_tab = ttk.Frame(self.tab_control)
        self.locations_tab = ttk.Frame(self.tab_control)
        self.purchase_orders_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.roles_tab, text='Roles')
        self.tab_control.add(self.users_tab, text='Users')
        self.tab_control.add(self.drugs_tab, text='Drugs')
        self.tab_control.add(self.vendors_tab, text='Vendors')
        self.tab_control.add(self.locations_tab, text='Locations')
        self.tab_control.add(self.purchase_orders_tab, text='Purchase Orders')

        # per-tab background image (optional)
        self._maybe_set_tab_background(self.roles_tab, "C:\\Users\\muska\\Downloads\\background.png")
        self._maybe_set_tab_background(self.users_tab, "C:\\Users\\muska\\Downloads\\background.png")
        self._maybe_set_tab_background(self.drugs_tab, "C:\\Users\\muska\\Downloads\\background.png")
        self._maybe_set_tab_background(self.vendors_tab, "C:\\Users\\muska\\Downloads\\background.png")
        self._maybe_set_tab_background(self.locations_tab, "C:\\Users\\muska\\Downloads\\background.png")
        self._maybe_set_tab_background(self.purchase_orders_tab, "C:\\Users\\muska\\Downloads\\background.png")

        # Initialize tabs (keeps all original functionality)
        self.init_roles_tab()
        self.init_users_tab()
        self.init_drugs_tab()
        self.init_vendors_tab()
        self.init_locations_tab()
        self.init_purchase_orders_tab()

        # Make window responsive
        root.update_idletasks()
        root.minsize(1000, 620)

    # ---------- Utility helpers ----------
    def _load_image_if_exists(self, filename, size=None):
        """Try to load an image (PIL preferred), return PhotoImage or None."""
        try:
            with open(filename, 'rb') as f:
                data = f.read()
        except Exception:
            return None
        try:
            if PIL_AVAILABLE:
                img = Image.open(io.BytesIO(data))
                if size:
                    img = img.resize(size, Image.ANTIALIAS)
                ph = ImageTk.PhotoImage(img)
            else:
                # fallback: write bytes to PhotoImage if GIF/PNG readable by Tk
                ph = tk.PhotoImage(data=base64.b64encode(data))
            return ph
        except Exception:
            try:
                # fallback: try direct PhotoImage load
                ph = tk.PhotoImage(file=filename)
                return ph
            except Exception:
                return None

    def _maybe_set_tab_background(self, tab_frame, filename):
        img = self._load_image_if_exists(filename)
        if img:
            lbl = ttk.Label(tab_frame, image=img)
            lbl.image = img
            lbl.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._images[f'bg_{id(tab_frame)}'] = img
        else:
            # subtle fallback color
            tab_frame.configure(style='TFrame')

    def set_status(self, text, secs=4):
        """Set status bar text (does not block)."""
        self.status_var.set(text)
        # optional: after secs seconds, revert to Ready (non-blocking)
        try:
            self.root.after_cancel(getattr(self, "_status_after_id", None))
        except Exception:
            pass
        self._status_after_id = self.root.after(max(2000, int(secs*1000)), lambda: self.status_var.set("."))

    def _add_form_fields(self, parent, labels, row=0, padx=6, pady=6):
        """Create a horizontal series of label+entry pairs and return dict label->entry"""
        entries = {}
        form_frame = ttk.Frame(parent)
        form_frame.grid(row=row, column=0, sticky='ew', padx=12, pady=(12,6))
        form_frame.columnconfigure(tuple(range(len(labels))), weight=1)
        for idx, text in enumerate(labels):
            lbl = ttk.Label(form_frame, text=text)
            lbl.grid(row=0, column=idx, sticky='w', padx=4)
            ent = ttk.Entry(form_frame)
            ent.grid(row=1, column=idx, sticky='ew', padx=4, pady=2)
            entries[text] = ent
        return entries, form_frame

    def _add_tree_with_scroll(self, parent, columns, row=1):
        """Create a Treeview with a vertical scrollbar and return it."""
        container = ttk.Frame(parent)
        container.grid(row=row, column=0, sticky='nsew', padx=12, pady=(6,12))
        parent.rowconfigure(row, weight=1)
        parent.columnconfigure(0, weight=1)

        tree = ttk.Treeview(container, columns=columns, show='headings')
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor='w', stretch=True)
        vsb = ttk.Scrollbar(container, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns', padx=(4,0))
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        return tree

    # ---------------- Export helper ----------------
    def export_tree_to_excel(self, tree, table_name):
        """
        Export treeview contents to an Excel (.xlsx) if pandas + engine exist;
        otherwise falls back to CSV. Default filename includes table_name + timestamp
        to make it unique (no two tables will have same default file name).
        """
        # prepare data
        cols = list(tree["columns"])
        data = []
        for iid in tree.get_children():
            vals = tree.item(iid).get('values', ())
            # convert datetimes to string
            row_vals = []
            for v in vals:
                if isinstance(v, datetime):
                    row_vals.append(v.strftime("%Y-%m-%d %H:%M:%S"))
                elif v is None:
                    row_vals.append("")
                else:
                    row_vals.append(v)
            data.append(row_vals)

        # default unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"{table_name}_{timestamp}.xlsx"

        # ask where to save
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_filename,
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return  # user cancelled

        _, ext = os.path.splitext(path)
        ext = ext.lower()

        # Try pandas -> Excel first (if .xlsx requested), otherwise follow extension
        try:
            import pandas as pd
            df = pd.DataFrame(data, columns=cols)
            if ext == ".csv":
                df.to_csv(path, index=False)
                messagebox.showinfo("Export complete", f"Exported table to CSV:\n{path}")
            else:
                # default to Excel
                df.to_excel(path, index=False)
                messagebox.showinfo("Export complete", f"Exported table to Excel:\n{path}")
            return
        except Exception as e:
            # pandas or engine not available — fallback to CSV
            try:
                # if user selected .xlsx but pandas unavailable, switch to .csv in same directory
                if ext == ".xlsx" or ext == "":
                    path_csv = os.path.splitext(path)[0] + ".csv"
                else:
                    path_csv = path
                with open(path_csv, "w", newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(cols)
                    for row in data:
                        writer.writerow(["" if v is None else str(v) for v in row])
                messagebox.showinfo("Export complete (CSV fallback)", f"pandas/openpyxl not available.\nExported as CSV:\n{path_csv}")
            except Exception as e2:
                messagebox.showerror("Export failed", f"Failed to export table.\nError1: {e}\nError2: {e2}")

    # ---------------- Roles Tab ----------------
    def init_roles_tab(self):
        frame = self.roles_tab
        frame.columnconfigure(0, weight=1)
        labels = ["Role Name"]
        self.role_name_entry = ttk.Entry(frame)
        # use helper form
        entries, form = self._add_form_fields(frame, labels, row=0)
        self.role_name_entry = entries["Role Name"]

        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(row=0, column=0, sticky='ne', padx=12, pady=(0,120))
        add_btn = ttk.Button(buttons_frame, text="➕ Add Role", style='Accent.TButton', command=self.add_role)
        add_btn.grid(row=0, column=0, padx=6)
        refresh_btn = ttk.Button(buttons_frame, text="🔁 Refresh", command=self.load_roles)
        refresh_btn.grid(row=0, column=1, padx=6)
        export_btn = ttk.Button(buttons_frame, text="📥 Export", command=lambda: self.export_tree_to_excel(self.roles_tree, "roles"))
        export_btn.grid(row=0, column=2, padx=6)

        self.roles_tree = self._add_tree_with_scroll(frame, ("ID", "Name"), row=1)
        # set some column widths
        self.roles_tree.column("ID", width=70, stretch=False)
        self.load_roles()

    def load_roles(self):
        self.set_status("Loading roles...")
        for i in self.roles_tree.get_children():
            self.roles_tree.delete(i)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM roles")
            for row in cursor.fetchall():
                self.roles_tree.insert('', 'end', values=row)
            cursor.close()
            conn.close()
            self.set_status("Roles loaded", secs=2)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error loading roles", secs=6)

    def add_role(self):
        name = self.role_name_entry.get()
        if not name:
            messagebox.showerror("Error", "Role name is required")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO roles (name) VALUES (%s)", (name,))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Role added successfully")
            self.role_name_entry.delete(0, tk.END)
            self.load_roles()
            self.set_status("Added new role", secs=3)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error adding role", secs=6)

    # ---------------- Users Tab ----------------
    def init_users_tab(self):
        frame = self.users_tab
        frame.columnconfigure(0, weight=1)
        labels = ["Username", "Email", "Password Hash", "Full Name", "Role ID", "Org ID"]
        self.user_entries, _ = self._add_form_fields(frame, labels, row=0)
        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(row=0, column=0, sticky='ne', padx=12, pady=(0,120))
        add_btn = ttk.Button(buttons_frame, text="➕ Add User", style='Accent.TButton', command=self.add_user)
        add_btn.grid(row=0, column=0, padx=6)
        refresh_btn = ttk.Button(buttons_frame, text="🔁 Refresh", command=self.load_users)
        refresh_btn.grid(row=0, column=1, padx=6)
        export_btn = ttk.Button(buttons_frame, text="📥 Export", command=lambda: self.export_tree_to_excel(self.users_tree, "users"))
        export_btn.grid(row=0, column=2, padx=6)

        cols = ("ID", "Username", "Email", "Full Name", "Role ID", "Org ID", "Created At", "Last Login")
        self.users_tree = self._add_tree_with_scroll(frame, cols, row=1)
        self.users_tree.column("ID", width=70, stretch=False)
        self.load_users()

    def load_users(self):
        self.set_status("Loading users...")
        for i in self.users_tree.get_children():
            self.users_tree.delete(i)
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, email, full_name, role_id, organization_id, created_at, last_login FROM users")
            for row in cursor.fetchall():
                self.users_tree.insert('', 'end', values=(row['id'], row['username'], row['email'], row['full_name'], row['role_id'], row['organization_id'], row['created_at'], row['last_login']))
            cursor.close()
            conn.close()
            self.set_status("Users loaded", secs=2)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error loading users", secs=6)

    def add_user(self):
        data = {k: v.get() for k, v in self.user_entries.items()}
        if not data["Username"] or not data["Email"] or not data["Password Hash"] or not data["Role ID"]:
            messagebox.showerror("Error", "Required fields missing")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username,email,password_hash,full_name,role_id,organization_id)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (data["Username"], data["Email"], data["Password Hash"], data.get("Full Name"), int(data["Role ID"]), data.get("Org ID") or None))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "User added successfully")
            for e in self.user_entries.values():
                e.delete(0, tk.END)
            self.load_users()
            self.set_status("Added user", secs=3)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error adding user", secs=6)

    # ---------------- Drugs Tab ----------------
    def init_drugs_tab(self):
        frame = self.drugs_tab
        frame.columnconfigure(0, weight=1)
        labels = ["Name", "Generic Name", "Code", "Unit", "Reorder Level"]
        self.drug_entries, _ = self._add_form_fields(frame, labels, row=0)
        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(row=0, column=0, sticky='ne', padx=12, pady=(0,120))
        add_btn = ttk.Button(buttons_frame, text="➕ Add Drug", style='Accent.TButton', command=self.add_drug)
        add_btn.grid(row=0, column=0, padx=6)
        refresh_btn = ttk.Button(buttons_frame, text="🔁 Refresh", command=self.load_drugs)
        refresh_btn.grid(row=0, column=1, padx=6)
        export_btn = ttk.Button(buttons_frame, text="📥 Export", command=lambda: self.export_tree_to_excel(self.drugs_tree, "drugs"))
        export_btn.grid(row=0, column=2, padx=6)

        cols = ("ID", "Name", "Generic Name", "Code", "Unit", "Reorder Level", "Created At")
        self.drugs_tree = self._add_tree_with_scroll(frame, cols, row=1)
        self.drugs_tree.column("ID", width=70, stretch=False)
        self.load_drugs()

    def load_drugs(self):
        self.set_status("Loading drugs...")
        for i in self.drugs_tree.get_children():
            self.drugs_tree.delete(i)
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, generic_name, code, unit, reorder_level, created_at FROM drugs")
            for row in cursor.fetchall():
                self.drugs_tree.insert('', 'end', values=(row['id'], row['name'], row['generic_name'], row['code'], row['unit'], row['reorder_level'], row['created_at']))
            cursor.close()
            conn.close()
            self.set_status("Drugs loaded", secs=2)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error loading drugs", secs=6)

    def add_drug(self):
        data = {k: v.get() for k, v in self.drug_entries.items()}
        if not data["Name"] or not data["Unit"]:
            messagebox.showerror("Error", "Required fields missing")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drugs (name,generic_name,code,unit,reorder_level)
                VALUES (%s,%s,%s,%s,%s)
            """, (data["Name"], data.get("Generic Name"), data.get("Code"), data["Unit"], int(data.get("Reorder Level") or 0)))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Drug added successfully")
            for e in self.drug_entries.values():
                e.delete(0, tk.END)
            self.load_drugs()
            self.set_status("Added drug", secs=3)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error adding drug", secs=6)

    # ---------------- Vendors Tab ----------------
    def init_vendors_tab(self):
        frame = self.vendors_tab
        frame.columnconfigure(0, weight=1)
        labels = ["Name", "Contact Person", "Contact Email", "Rating"]
        self.vendor_entries, _ = self._add_form_fields(frame, labels, row=0)
        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(row=0, column=0, sticky='ne', padx=12, pady=(0,120))
        add_btn = ttk.Button(buttons_frame, text="➕ Add Vendor", style='Accent.TButton', command=self.add_vendor)
        add_btn.grid(row=0, column=0, padx=6)
        refresh_btn = ttk.Button(buttons_frame, text="🔁 Refresh", command=self.load_vendors)
        refresh_btn.grid(row=0, column=1, padx=6)
        export_btn = ttk.Button(buttons_frame, text="📥 Export", command=lambda: self.export_tree_to_excel(self.vendors_tree, "vendors"))
        export_btn.grid(row=0, column=2, padx=6)

        cols = ("ID", "Name", "Contact Person", "Contact Email", "Rating", "Created At")
        self.vendors_tree = self._add_tree_with_scroll(frame, cols, row=1)
        self.vendors_tree.column("ID", width=70, stretch=False)
        self.load_vendors()

    def load_vendors(self):
        self.set_status("Loading vendors...")
        for i in self.vendors_tree.get_children():
            self.vendors_tree.delete(i)
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, contact_person, contact_email, rating, created_at FROM vendors")
            for row in cursor.fetchall():
                self.vendors_tree.insert('', 'end', values=(row['id'], row['name'], row['contact_person'], row['contact_email'], row['rating'], row['created_at']))
            cursor.close()
            conn.close()
            self.set_status("Vendors loaded", secs=2)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error loading vendors", secs=6)

    def add_vendor(self):
        data = {k: v.get() for k, v in self.vendor_entries.items()}
        if not data["Name"]:
            messagebox.showerror("Error", "Name required")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vendors (name, contact_person, contact_email, rating)
                VALUES (%s,%s,%s,%s)
            """, (data["Name"], data.get("Contact Person"), data.get("Contact Email"), float(data.get("Rating") or 0)))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Vendor added successfully")
            for e in self.vendor_entries.values():
                e.delete(0, tk.END)
            self.load_vendors()
            self.set_status("Added vendor", secs=3)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error adding vendor", secs=6)

    # ---------------- Locations Tab ----------------
    def init_locations_tab(self):
        frame = self.locations_tab
        frame.columnconfigure(0, weight=1)
        labels = ["Name", "Type", "Address", "Contact"]
        self.location_entries, _ = self._add_form_fields(frame, labels, row=0)
        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(row=0, column=0, sticky='ne', padx=12, pady=(0,120))
        add_btn = ttk.Button(buttons_frame, text="➕ Add Location", style='Accent.TButton', command=self.add_location)
        add_btn.grid(row=0, column=0, padx=6)
        refresh_btn = ttk.Button(buttons_frame, text="🔁 Refresh", command=self.load_locations)
        refresh_btn.grid(row=0, column=1, padx=6)
        export_btn = ttk.Button(buttons_frame, text="📥 Export", command=lambda: self.export_tree_to_excel(self.locations_tree, "locations"))
        export_btn.grid(row=0, column=2, padx=6)

        cols = ("ID", "Name", "Type", "Address", "Contact")
        self.locations_tree = self._add_tree_with_scroll(frame, cols, row=1)
        self.locations_tree.column("ID", width=70, stretch=False)
        self.load_locations()

    def load_locations(self):
        self.set_status("Loading locations...")
        for i in self.locations_tree.get_children():
            self.locations_tree.delete(i)
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, type, address, contact FROM locations")
            for row in cursor.fetchall():
                self.locations_tree.insert('', 'end', values=(row['id'], row['name'], row['type'], row['address'], row['contact']))
            cursor.close()
            conn.close()
            self.set_status("Locations loaded", secs=2)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error loading locations", secs=6)

    def add_location(self):
        data = {k: v.get() for k, v in self.location_entries.items()}
        if not data["Name"] or not data["Type"]:
            messagebox.showerror("Error", "Name and Type required")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO locations (name, type, address, contact)
                VALUES (%s,%s,%s,%s)
            """, (data["Name"], data["Type"], data.get("Address"), data.get("Contact")))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Location added successfully")
            for e in self.location_entries.values():
                e.delete(0, tk.END)
            self.load_locations()
            self.set_status("Added location", secs=3)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error adding location", secs=6)

    # ---------------- Purchase Orders Tab ----------------
    def init_purchase_orders_tab(self):
        frame = self.purchase_orders_tab
        frame.columnconfigure(0, weight=1)
        labels = ["PO Number", "Created By", "Vendor ID", "Location ID", "Status", "Total Amount", "Expected Delivery"]
        self.po_entries, _ = self._add_form_fields(frame, labels, row=0)
        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(row=0, column=0, sticky='ne', padx=12, pady=(0,120))
        add_btn = ttk.Button(buttons_frame, text="➕ Add PO", style='Accent.TButton', command=self.add_po)
        add_btn.grid(row=0, column=0, padx=6)
        refresh_btn = ttk.Button(buttons_frame, text="🔁 Refresh", command=self.load_pos)
        refresh_btn.grid(row=0, column=1, padx=6)
        export_btn = ttk.Button(buttons_frame, text="📥 Export", command=lambda: self.export_tree_to_excel(self.po_tree, "purchase_orders"))
        export_btn.grid(row=0, column=2, padx=6)

        cols = ("ID", "PO Number", "Created By", "Vendor ID", "Location ID", "Status", "Total Amount", "Expected Delivery", "Created At")
        self.po_tree = self._add_tree_with_scroll(frame, cols, row=1)
        self.po_tree.column("ID", width=70, stretch=False)
        self.load_pos()

    def load_pos(self):
        self.set_status("Loading purchase orders...")
        for i in self.po_tree.get_children():
            self.po_tree.delete(i)
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, po_number, created_by, vendor_id, location_id, status, total_amount, expected_delivery_date, created_at FROM purchase_orders")
            for row in cursor.fetchall():
                self.po_tree.insert('', 'end', values=(row['id'], row['po_number'], row['created_by'], row['vendor_id'], row['location_id'], row['status'], row['total_amount'], row['expected_delivery_date'], row['created_at']))
            cursor.close()
            conn.close()
            self.set_status("Purchase orders loaded", secs=2)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error loading purchase orders", secs=6)

    def add_po(self):
        data = {k: v.get() for k, v in self.po_entries.items()}
        if not data["PO Number"] or not data["Created By"]:
            messagebox.showerror("Error", "PO Number and Created By required")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO purchase_orders (po_number, created_by, vendor_id, location_id, status, total_amount, expected_delivery_date)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                data["PO Number"], int(data["Created By"]), int(data.get("Vendor ID") or 0) or None,
                int(data.get("Location ID") or 0) or None, data.get("Status") or "CREATED",
                float(data.get("Total Amount") or 0), data.get("Expected Delivery") or None
            ))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Purchase Order added successfully")
            for e in self.po_entries.values():
                e.delete(0, tk.END)
            self.load_pos()
            self.set_status("Added purchase order", secs=3)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.set_status("Error adding purchase order", secs=6)


# ----------- Run App -----------
if __name__ == "__main__":
    root = tk.Tk()
    app = DrugInventoryApp(root)
    root.mainloop()
