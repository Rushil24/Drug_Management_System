import os
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import mysql.connector
import pandas as pd
from PIL import Image, ImageTk

# ----------------- CONFIG -----------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "muskan",
    "database": "drug_inventory"
}

LOGO_PATH = "C:\\Users\\muska\\Downloads\\logo.png"
BACKGROUND_PATH = "C:\\Users\\muska\\Downloads\\background.png"
EXPORT_DIR = os.getcwd()

# ----------------- DB HELPERS -----------------
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def ensure_patients_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patients (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      patient_code VARCHAR(64) UNIQUE,
      full_name VARCHAR(255),
      gender ENUM('Male','Female','Other') DEFAULT 'Male',
      dob DATE,
      phone VARCHAR(32),
      email VARCHAR(255),
      address TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """)
    conn.commit()
    cur.close()
    conn.close()

# ----------------- VALIDATION -----------------
EMAIL_RE = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
PHONE_RE = re.compile(r"^\+?\d{7,15}$")

def validate_patient_inputs(name, phone, email, dob):
    if not name or len(name.strip()) < 2:
        return False, "Full name is required (min 2 characters)."
    if phone and not PHONE_RE.match(phone.strip()):
        return False, "Phone must contain only digits (7-15 digits). Add country code if needed."
    if email and not EMAIL_RE.match(email.strip()):
        return False, "Enter a valid email address."
    if dob:
        try:
            datetime.strptime(dob, "%Y-%m-%d")
        except ValueError:
            return False, "DOB must be in YYYY-MM-DD format."
    return True, ""

# ----------------- UI MODULE -----------------
class PatientModule:
    def __init__(self, master):
        ensure_patients_table()
        self.master = master
        self.master.title("Patient Module")
        self.master.geometry("1100x720")
        self.master.configure(bg="#f3f6fb")
        self.master.bind("<Configure>", self.on_resize)  # Responsive resizing

        # Styles
        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#0b3d91")
        style.configure("Card.TFrame", background="white", relief="flat")
        style.configure("Accent.TButton", background="#0b74d9")

        # Load background
        try:
            self.bg_img = Image.open(BACKGROUND_PATH)
            self.bg_photo = ImageTk.PhotoImage(self.bg_img.resize((1100, 720)))
            self.bg_label = tk.Label(self.master, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except:
            self.bg_label = None

        # Header
        self.header_frame = ttk.Frame(self.master, padding=12, style="Card.TFrame")
        self.header_frame.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.1)

        try:
            logo_img = Image.open(LOGO_PATH).resize((56, 56))
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            tk.Label(self.header_frame, image=self.logo_photo, bg="white").place(relx=0.01, rely=0.1)
        except:
            tk.Label(self.header_frame, text="[Logo]", font=("Segoe UI", 12, "bold"), bg="white").place(relx=0.01, rely=0.25)

        ttk.Label(self.header_frame, text="Patient Management", style="Header.TLabel").place(relx=0.08, rely=0.2)
       # ttk.Label(self.header_frame, text="Maintain patient records — patient_code links with Sales/Dispense",
       #           font=("Segoe UI", 9)).place(relx=0.08, rely=0.65)

        # Form Card
        self.form_card = ttk.Frame(self.master, style="Card.TFrame")
        self.form_card.place(relx=0.01, rely=0.13, relwidth=0.4, relheight=0.82)

        ttk.Label(self.form_card, text="Add / Update Patient", font=("Segoe UI", 12, "bold")).place(relx=0.04, rely=0.02)

        # Variables
        self.patient_code_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.gender_var = tk.StringVar(value="Male")
        self.dob_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.address_text = None

        # Form fields
        self.create_form_fields()

        # List Card
        self.list_card = ttk.Frame(self.master, style="Card.TFrame")
        self.list_card.place(relx=0.42, rely=0.13, relwidth=0.56, relheight=0.82)

        # Search Row
        ttk.Label(self.list_card, text="Search (Name / Code / Phone):").place(relx=0.02, rely=0.02)
        self.search_var = tk.StringVar()
        ttk.Entry(self.list_card, textvariable=self.search_var).place(relx=0.02, rely=0.07, relwidth=0.48)
        ttk.Button(self.list_card, text="Search", command=self.search_patients).place(relx=0.52, rely=0.07, relwidth=0.12)
        ttk.Button(self.list_card, text="Show All", command=self.fetch_patients).place(relx=0.66, rely=0.07, relwidth=0.12)
        ttk.Button(self.list_card, text="Export to Excel", command=self.export_to_excel).place(relx=0.80, rely=0.07, relwidth=0.18)

        # Treeview
        cols = ("ID", "Code", "Name", "Gender", "DOB", "Phone", "Email", "Address", "Created At")
        self.tree = ttk.Treeview(self.list_card, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            if c in ("ID", "Gender", "DOB", "Phone"):
                self.tree.column(c, width=80, anchor="center")
            elif c == "Code":
                self.tree.column(c, width=100, anchor="center")
            elif c == "Created At":
                self.tree.column(c, width=140, anchor="center")
            else:
                self.tree.column(c, width=160, anchor="w")
        self.tree.place(relx=0.02, rely=0.15, relwidth=0.96, relheight=0.83)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.fetch_patients()
        self.master.get_selected_patient = self.get_selected_patient

    def create_form_fields(self):
        # Patient Code
        ttk.Label(self.form_card, text="Patient Code").place(relx=0.04, rely=0.08)
        ttk.Entry(self.form_card, textvariable=self.patient_code_var).place(relx=0.35, rely=0.08, relwidth=0.45)
        ttk.Button(self.form_card, text="Generate", command=self.generate_code).place(relx=0.82, rely=0.08, relwidth=0.12)

        # Name
        ttk.Label(self.form_card, text="Full Name").place(relx=0.04, rely=0.15)
        ttk.Entry(self.form_card, textvariable=self.name_var).place(relx=0.04, rely=0.2, relwidth=0.9)

        # Gender & DOB
        ttk.Label(self.form_card, text="Gender").place(relx=0.04, rely=0.28)
        ttk.Combobox(self.form_card, values=["Male","Female","Other"], textvariable=self.gender_var,
                     state="readonly").place(relx=0.04, rely=0.33, relwidth=0.4)
        ttk.Label(self.form_card, text="DOB (YYYY-MM-DD)").place(relx=0.52, rely=0.28)
        ttk.Entry(self.form_card, textvariable=self.dob_var).place(relx=0.52, rely=0.33, relwidth=0.42)

        # Phone & Email
        ttk.Label(self.form_card, text="Phone").place(relx=0.04, rely=0.42)
        ttk.Entry(self.form_card, textvariable=self.phone_var).place(relx=0.04, rely=0.47, relwidth=0.4)
        ttk.Label(self.form_card, text="Email").place(relx=0.52, rely=0.42)
        ttk.Entry(self.form_card, textvariable=self.email_var).place(relx=0.52, rely=0.47, relwidth=0.42)

        # Address
        ttk.Label(self.form_card, text="Address").place(relx=0.04, rely=0.55)
        self.address_text = tk.Text(self.form_card, wrap="word", bd=1, relief="solid")
        self.address_text.place(relx=0.04, rely=0.60, relwidth=0.9, relheight=0.2)

        # Form buttons
        ttk.Button(self.form_card, text="Add", command=self.add_patient).place(relx=0.04, rely=0.85, relwidth=0.2)
        ttk.Button(self.form_card, text="Update", command=self.update_patient).place(relx=0.28, rely=0.85, relwidth=0.2)
        ttk.Button(self.form_card, text="Clear", command=self.clear_form).place(relx=0.52, rely=0.85, relwidth=0.2)
        ttk.Button(self.form_card, text="Delete", command=self.delete_patient).place(relx=0.76, rely=0.85, relwidth=0.2)

    def on_resize(self, event):
        # Resize background
        if self.bg_label and self.bg_img:
            w, h = event.width, event.height
            resized_bg = self.bg_img.resize((w, h))
            self.bg_photo = ImageTk.PhotoImage(resized_bg)
            self.bg_label.configure(image=self.bg_photo)

    # ----------------- FULL METHODS -----------------
    def generate_code(self):
        self.patient_code_var.set("P" + datetime.now().strftime("%Y%m%d%H%M%S"))

    def clear_form(self):
        self.patient_code_var.set("")
        self.name_var.set("")
        self.gender_var.set("Male")
        self.dob_var.set("")
        self.phone_var.set("")
        self.email_var.set("")
        self.address_text.delete("1.0", tk.END)
        for sel in self.tree.selection():
            self.tree.selection_remove(sel)

    def add_patient(self):
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        email = self.email_var.get().strip()
        dob = self.dob_var.get().strip()
        ok, msg = validate_patient_inputs(name, phone, email, dob)
        if not ok:
            messagebox.showerror("Validation error", msg)
            return

        code = self.patient_code_var.get().strip() or ("P" + datetime.now().strftime("%Y%m%d%H%M%S"))
        addr = self.address_text.get("1.0", tk.END).strip() or None
        gender = self.gender_var.get()

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO patients (patient_code, full_name, gender, dob, phone, email, address)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (code, name, gender, dob if dob else None, phone if phone else None, email if email else None, addr))
            conn.commit()
            messagebox.showinfo("Success", "Patient added successfully.")
            self.fetch_patients()
            self.clear_form()
        except mysql.connector.IntegrityError as e:
            messagebox.showerror("DB error", f"Patient code must be unique. ({e})")
        except Exception as e:
            messagebox.showerror("DB error", str(e))
        finally:
            cur.close()
            conn.close()

    def fetch_patients(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, patient_code, full_name, gender, dob, phone, email, address, created_at
            FROM patients
            ORDER BY created_at DESC
            LIMIT 1000
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            dob = r[4].strftime("%Y-%m-%d") if r[4] else ""
            created = r[8].strftime("%Y-%m-%d %H:%M:%S") if r[8] else ""
            address = (r[7][:80] + "...") if r[7] and len(r[7]) > 90 else (r[7] or "")
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], dob, r[5] or "", r[6] or "", address, created))

    def on_tree_select(self, event):
        self.populate_form_from_selection()

    def populate_form_from_selection(self):
        sel = self.tree.focus()
        if not sel: return
        vals = self.tree.item(sel, "values")
        self.patient_code_var.set(vals[1] or "")
        self.name_var.set(vals[2] or "")
        self.gender_var.set(vals[3] or "Male")
        self.dob_var.set(vals[4] or "")
        self.phone_var.set(vals[5] or "")
        self.email_var.set(vals[6] or "")
        pid = vals[0]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT address FROM patients WHERE id=%s", (pid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        full_addr = row[0] if row and row[0] else ""
        self.address_text.delete("1.0", tk.END)
        self.address_text.insert(tk.END, full_addr)

    def get_selected_patient(self):
        sel = self.tree.focus()
        if not sel: return None
        vals = self.tree.item(sel, "values")
        pid = vals[0]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, patient_code, full_name, gender, dob, phone, email, address, created_at
            FROM patients WHERE id=%s
        """, (pid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row: return None
        return {
            "id": row[0],
            "code": row[1],
            "name": row[2],
            "gender": row[3],
            "dob": row[4].strftime("%Y-%m-%d") if row[4] else None,
            "phone": row[5],
            "email": row[6],
            "address": row[7],
            "created_at": row[8].strftime("%Y-%m-%d %H:%M:%S") if row[8] else None
        }

    def update_patient(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showerror("Select", "Select a patient to update from the list.")
            return
        vals = self.tree.item(sel, "values")
        pid = vals[0]
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        email = self.email_var.get().strip()
        dob = self.dob_var.get().strip()
        ok, msg = validate_patient_inputs(name, phone, email, dob)
        if not ok:
            messagebox.showerror("Validation error", msg)
            return
        code = self.patient_code_var.get().strip()
        addr = self.address_text.get("1.0", tk.END).strip()
        gender = self.gender_var.get()
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE patients SET patient_code=%s, full_name=%s, gender=%s, dob=%s, phone=%s, email=%s, address=%s
                WHERE id=%s
            """, (code if code else None, name, gender, dob if dob else None, phone if phone else None, email if email else None, addr if addr else None, pid))
            conn.commit()
            messagebox.showinfo("Success", "Patient updated.")
            self.fetch_patients()
        except mysql.connector.IntegrityError as e:
            messagebox.showerror("DB error", f"Patient code must be unique. ({e})")
        except Exception as e:
            messagebox.showerror("DB error", str(e))
        finally:
            cur.close(); conn.close()

    def delete_patient(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showerror("Select", "Select a patient to delete from the list.")
            return
        vals = self.tree.item(sel, "values")
        pid = vals[0]
        confirm = messagebox.askyesno("Confirm delete", f"Delete patient: {vals[2]} (Code: {vals[1]}) ?\nThis action cannot be undone.")
        if not confirm: return
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM patients WHERE id=%s", (pid,))
            conn.commit()
            messagebox.showinfo("Deleted", "Patient deleted successfully.")
            self.fetch_patients()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("DB error", str(e))
        finally:
            cur.close(); conn.close()

    def search_patients(self):
        q = (self.search_var.get() or "").strip()
        if not q:
            self.fetch_patients()
            return
        like = f"%{q}%"
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, patient_code, full_name, gender, dob, phone, email, address, created_at
            FROM patients
            WHERE full_name LIKE %s OR patient_code LIKE %s OR phone LIKE %s
            ORDER BY created_at DESC
            LIMIT 500
        """, (like, like, like))
        rows = cur.fetchall()
        cur.close(); conn.close()
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            dob = r[4].strftime("%Y-%m-%d") if r[4] else ""
            created = r[8].strftime("%Y-%m-%d %H:%M:%S") if r[8] else ""
            address = (r[7][:80] + "...") if r[7] and len(r[7]) > 90 else (r[7] or "")
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], dob, r[5] or "", r[6] or "", address, created))

    def export_to_excel(self):
        conn = get_connection()
        try:
            df = pd.read_sql("""
                SELECT id AS ID, patient_code AS Code, full_name AS Name, gender AS Gender,
                       dob AS DOB, phone AS Phone, email AS Email, address AS Address, created_at AS CreatedAt
                FROM patients
                ORDER BY created_at DESC
            """, conn)
            filename = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                    initialdir=EXPORT_DIR,
                                                    filetypes=[("Excel files","*.xlsx")],
                                                    title="Save patient list as")
            if filename:
                df.to_excel(filename, index=False)
                messagebox.showinfo("Exported", f"Patient data exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error exporting", str(e))
        finally:
            conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = PatientModule(root)
    root.mainloop()
