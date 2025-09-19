import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import mysql.connector
import pandas as pd
from datetime import datetime
from fpdf import FPDF  # pip install fpdf

# ---------- Database Connection ----------
def get_connection():
    return mysql.connector.connect(
        host='localhost',
        database='drug_inventory',
        user='root',
        password='muskan'
    )

# ---------- Patient & Sales Window ----------
def open_patient_sales_window(root):
    win = tk.Toplevel(root)
    win.title("Patient & Pharmacy Sales")
    win.geometry("1100x750")
    win.minsize(1100, 750)
    win.configure(bg="#e6f0ff")
    win.columnconfigure(0, weight=1)
    win.rowconfigure(2, weight=1)

    # ---------- Background ----------
    bg_img = Image.open("C:\\Users\\muska\\Downloads\\background.png")
    bg_photo = ImageTk.PhotoImage(bg_img)
    bg_label = tk.Label(win, image=bg_photo)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    # ---------- Logo ----------
    logo_img = Image.open("C:\\Users\\muska\\Downloads\\logo.png").resize((50,50))
    logo_photo = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(win, image=logo_photo, bg="#e6f0ff")
    logo_label.grid(row=0, column=0, sticky="nw", padx=20, pady=10)

    # ---------- Title ----------
    title_label = tk.Label(win, text="Patient & Pharmacy Management",
                           font=("Arial", 24, "bold"), bg="#e6f0ff", fg="#003366")
    title_label.grid(row=0, column=0, sticky="nw", padx=90, pady=10)

    # ---------- Input Frame ----------
    input_frame = ttk.LabelFrame(win, text="Record Sale", padding=10)
    input_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
    input_frame.columnconfigure((0,1,2,3), weight=1)

    # Patient Details
    ttk.Label(input_frame, text="Patient ID:", font=("Arial",10,"bold")).grid(row=0,column=0,padx=10,pady=5,sticky="w")
    patient_entry = ttk.Entry(input_frame, width=25)
    patient_entry.grid(row=0,column=1,padx=10,pady=5,sticky="ew")

    ttk.Label(input_frame, text="Patient Name:", font=("Arial",10,"bold")).grid(row=0,column=2,padx=10,pady=5,sticky="w")
    patient_name_entry = ttk.Entry(input_frame, width=25)
    patient_name_entry.grid(row=0,column=3,padx=10,pady=5,sticky="ew")

    # Drug Dropdown
    ttk.Label(input_frame, text="Drug:", font=("Arial",10,"bold")).grid(row=1,column=0,padx=10,pady=5,sticky="w")
    drug_cb = ttk.Combobox(input_frame, width=30)
    drug_cb.grid(row=1,column=1,padx=10,pady=5,sticky="ew")

    # Batch Dropdown
    ttk.Label(input_frame, text="Batch:", font=("Arial",10,"bold")).grid(row=1,column=2,padx=10,pady=5,sticky="w")
    batch_cb = ttk.Combobox(input_frame, width=25)
    batch_cb.grid(row=1,column=3,padx=10,pady=5,sticky="ew")

    # Quantity
    ttk.Label(input_frame, text="Quantity:", font=("Arial",10,"bold")).grid(row=2,column=0,padx=10,pady=5,sticky="w")
    qty_entry = ttk.Entry(input_frame, width=25)
    qty_entry.grid(row=2,column=1,padx=10,pady=5,sticky="ew")

    # ---------- Load Drugs ----------
    def load_drugs():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM drugs")
        drugs = cursor.fetchall()
        conn.close()
        drug_cb["values"] = [f"{d[0]} - {d[1]}" for d in drugs]

    # ---------- Load Batches ----------
    def load_batches(event):
        if not drug_cb.get():
            return
        drug_id = drug_cb.get().split(" - ")[0]
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, batch_no, quantity FROM drug_batch WHERE drug_id=%s AND quantity>0", (drug_id,))
        batches = cursor.fetchall()
        conn.close()
        batch_cb["values"] = [f"{b[0]} - {b[1]} (Qty: {b[2]})" for b in batches]

    drug_cb.bind("<<ComboboxSelected>>", load_batches)

    # ---------- Record Sale ----------
    def record_sale():
        if not patient_entry.get() or not patient_name_entry.get() or not drug_cb.get() or not batch_cb.get() or not qty_entry.get():
            messagebox.showerror("Error", "All fields are required!")
            return
        drug_id = int(drug_cb.get().split(" - ")[0])
        batch_id = int(batch_cb.get().split(" - ")[0])
        patient_id = patient_entry.get()
        patient_name = patient_name_entry.get()
        try:
            qty = int(qty_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a number!")
            return

        conn = get_connection()
        cursor = conn.cursor()
        # Get default location
        cursor.execute("SELECT id FROM locations LIMIT 1")
        location_id = cursor.fetchone()[0]

        cursor.execute("SELECT quantity FROM drug_batch WHERE id=%s", (batch_id,))
        available = cursor.fetchone()[0]
        if qty > available:
            messagebox.showerror("Error","Not enough stock available!")
            conn.close()
            return
        
        dispensed_by_id = 7

        cursor.execute("""
            INSERT INTO consumption (drug_id, drug_batch_id, patient_id, reason, quantity, dispensed_by, timestamp, location_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (drug_id, batch_id, patient_id, "dispense", qty, dispensed_by_id, datetime.now(), location_id))

        cursor.execute("UPDATE drug_batch SET quantity=quantity-%s WHERE id=%s", (qty,batch_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success","Sale recorded successfully!")
        refresh_sales()

    # ---------- Sales History ----------
    history_frame = ttk.LabelFrame(win, text="Sales History", padding=10)
    history_frame.grid(row=2,column=0,columnspan=2,padx=20,pady=10,sticky="nsew")
    history_frame.columnconfigure(0, weight=1)
    history_frame.rowconfigure(0, weight=1)

    cols = ("ID","Drug","Batch","Patient ID","Patient Name","Quantity","Dispensed By","Date")
    sales_table = ttk.Treeview(history_frame, columns=cols, show="headings", selectmode="browse")
    for col in cols:
        sales_table.heading(col, text=col)
        sales_table.column(col, width=130, anchor="center")
    sales_table.grid(row=0,column=0,sticky="nsew")
    scroll = ttk.Scrollbar(history_frame, orient="vertical", command=sales_table.yview)
    sales_table.configure(yscroll=scroll.set)
    scroll.grid(row=0,column=1,sticky="ns")

    # ---------- Refresh ----------
    def refresh_sales():
        for row in sales_table.get_children():
            sales_table.delete(row)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id,d.name,b.batch_no,c.patient_id,c.patient_name,c.quantity,c.dispensed_by,c.timestamp
            FROM consumption c
            JOIN drugs d ON c.drug_id=d.id
            JOIN drug_batch b ON c.drug_batch_id=b.id
            WHERE c.reason='dispense'
            ORDER BY c.timestamp DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            sales_table.insert("", "end", values=r)

    # ---------- Export ----------
    def export_sales_excel():
        conn = get_connection()
        df = pd.read_sql("""
            SELECT c.id,d.name AS Drug,b.batch_no AS Batch,c.patient_id,c.patient_name AS Patient,c.quantity,
                   c.dispensed_by AS Dispensed_By,c.timestamp AS Date
            FROM consumption c
            JOIN drugs d ON c.drug_id=d.id
            JOIN drug_batch b ON c.drug_batch_id=b.id
            WHERE c.reason='dispense'
            ORDER BY c.timestamp DESC
        """, conn)
        conn.close()
        file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx")])
        if file:
            df.to_excel(file,index=False)
            messagebox.showinfo("Exported", f"Sales data exported to {file}")

    # ---------- Generate Bill ----------
    def generate_bill():
        selected = sales_table.focus()
        if not selected:
            messagebox.showerror("Error","Select a sale to generate bill.")
            return
        values = sales_table.item(selected,"values")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial","B",16)
        pdf.cell(0,10,"Pharmacy Bill",ln=True,align="C")
        pdf.ln(10)
        pdf.set_font("Arial","",12)
        labels = ["Sale ID","Drug","Batch","Patient ID","Patient Name","Quantity","Dispensed By","Date"]
        for i,label in enumerate(labels):
            pdf.cell(50,8,f"{label}:",border=0)
            pdf.cell(0,8,str(values[i]),ln=True)
        file = filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF files","*.pdf")])
        if file:
            pdf.output(file)
            messagebox.showinfo("Generated", f"Bill saved as {file}")

    # ---------- Buttons ----------
    btn_frame = tk.Frame(input_frame,bg="#e6f0ff")
    btn_frame.grid(row=3,column=0,columnspan=4,pady=10,sticky="ew")
    tk.Button(btn_frame,text="Record Sale",bg="#003366",fg="white",font=("Arial",11,"bold"),command=record_sale).pack(side="left",padx=10,ipadx=15,ipady=5)
    tk.Button(btn_frame,text="Refresh",bg="#0073e6",fg="white",font=("Arial",11,"bold"),command=refresh_sales).pack(side="left",padx=10,ipadx=15,ipady=5)
    tk.Button(btn_frame,text="Export to Excel",bg="#0073e6",fg="white",font=("Arial",11,"bold"),command=export_sales_excel).pack(side="left",padx=10,ipadx=15,ipady=5)
    tk.Button(btn_frame,text="Generate Bill",bg="#009933",fg="white",font=("Arial",11,"bold"),command=generate_bill).pack(side="left",padx=10,ipadx=15,ipady=5)

    # ---------- Initial Load ----------
    load_drugs()
    refresh_sales()

    # Keep image refs
    win.bg_photo = bg_photo
    win.logo_photo = logo_photo

    # Properly close
    def close_win():
        win.destroy()
        root.destroy()
    win.protocol("WM_DELETE_WINDOW", close_win)

# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    open_patient_sales_window(root)
    root.mainloop()
