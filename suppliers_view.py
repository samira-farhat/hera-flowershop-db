import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime

class SupplierView(tk.Frame):
    def __init__(self, parent, db_config):
        super().__init__(parent)
        self.parent = parent
        self.db_config = db_config
        self.lavender = "#E6E6FA"
        self.configure(bg=self.lavender)

        #  Search and Buttons Frame
        search_frame = tk.Frame(self, bg=self.lavender)
        search_frame.pack(fill="x", padx=10, pady=(10, 0))

        tk.Label(search_frame, text="Search by Name:", bg=self.lavender).pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=(0, 5))
        search_btn = tk.Button(search_frame, text="Search", command=self.search_suppliers)
        search_btn.pack(side="left", padx=(0, 10))
        tk.Button(search_frame, text="Clear", command=self.clear_search).pack(side="left", padx=5)

        add_btn = tk.Button(search_frame, text="Add Supplier", command=self.add_supplier)
        add_btn.pack(side="right")

        # Treeview Frame and Scrollbar
        tree_frame= tk.Frame(self)
        tree_frame.pack(fill= "both", expand= True, padx= 10, pady= 10)
        
        scrollbar= ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        columns = ("Edit", "Supplier ID", "Name", "Contact", "Items", "Delete")
        
        self.tree = ttk.Treeview(tree_frame, columns= columns, show="headings", yscrollcommand= scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command= self.tree.yview)

        for col in columns:
            if col in ("Edit", "Delete"):
                self.tree.heading(col, text="")
                self.tree.column(col, anchor="center", width=60)
            elif col == "Supplier ID":
                self.tree.heading(col, text="ID")
                self.tree.column(col, anchor="center", width=70)
            elif col == "Items":
                self.tree.heading(col, text="Items Supplied")
                self.tree.column(col, anchor="w", width=200)
            else:
                self.tree.heading(col, text=col)
                self.tree.column(col, anchor="center", width=100)

        self.tree.configure(cursor="hand2")
        self.tree.bind("<Button-1>", self.handle_click)

        self.load_suppliers()

    def connect_db(self):
        return mysql.connector.connect(
            host=self.db_config.get("host", "localhost"),
            user=self.db_config.get("user", "your_mysql_username"),
            password=self.db_config.get("password", "your_mysql_password"),
            database=self.db_config.get("database", "flowershop_management")
        )
        
    def clear_search(self):
        self.search_var.set("")
        self.load_suppliers()

    def load_suppliers(self):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.Supplier_id, s.Name, s.Contact,
                    GROUP_CONCAT(i.Name SEPARATOR ', ') AS Items
                FROM Supplier s
                LEFT JOIN Item_Supplier isup ON s.Supplier_id = isup.Supplier_id
                LEFT JOIN Item i ON isup.Item_id = i.Item_id
                GROUP BY s.Supplier_id
                ORDER BY s.Supplier_id DESC
            """)
            suppliers = cursor.fetchall()
            conn.close()
            self.display_suppliers(suppliers)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def display_suppliers(self, suppliers):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for supplier in suppliers:
            supplier_id, name, contact_, items_str= supplier
            
            if items_str is None:
                items_str= "_"

            self.tree.insert(
                "", "end",
                values=(
                    "🖉 edit",  
                    supplier_id, name, contact_, items_str, "🗑️"
                ),
                tags=(f"id_{supplier_id}")
            )

    def search_suppliers(self):
        search_text = self.search_var.get().strip()
        if not search_text:
            messagebox.showinfo("Search", "Please enter supplier name to search.")
            return
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            query = ("""
                SELECT s.Supplier_id, s.Name, s.Contact,
                    GROUP_CONCAT(i.Name SEPARATOR ', ') AS Items
                FROM Supplier s
                LEFT JOIN Item_Supplier isup ON s.Supplier_id = isup.Supplier_id
                LEFT JOIN Item i ON isup.Item_id = i.Item_id
                WHERE s.Name LIKE %s
                GROUP BY s.Supplier_id
                ORDER BY s.Supplier_id DESC
            """)
            cursor.execute(query, (f"%{search_text}%",))
            results = cursor.fetchall()
            conn.close()

            if results:
                self.display_suppliers(results)
            else:
                messagebox.showinfo("Search", f"No Suppliers found matching '{search_text}'")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def add_supplier(self):
        # Create the add supplier popup
        add_win = tk.Toplevel(self)
        add_win.title("Add New Supplier")
        add_win.geometry("400x600")
        add_win.configure(bg=self.lavender)

        labels = ["Name", "Contact"]
        entries = []

        for label in labels:
            tk.Label(add_win, text=label + ":", bg=self.lavender).pack(pady=5)
            entry = tk.Entry(add_win)
            entry.pack()
            entries.append(entry)
            
        # fetch items
        conn= self.connect_db()
        cursor= conn.cursor()
        cursor.execute("SELECT Item_id, Name FROM Item")
        items= cursor.fetchall()
        conn.close()
        
        tk.Label(add_win, text= "Select Items this Supplier provides:", bg= self.lavender).pack(pady= 5)
        
        item_vars= {}
        for item_id, item_name in items:
            var= tk.BooleanVar()
            tk.Checkbutton(add_win, text= item_name, variable= var, bg= self.lavender).pack(anchor='w')
            item_vars[item_id]= var

        def save_new_supplier():
            new_values = [e.get().strip() for e in entries]

            if not all(new_values):
                messagebox.showwarning("Missing Info", "All fields are required.")
                return

            try:
                new_name = new_values[0]
                contact_ = new_values[1]

                conn = self.connect_db()
                cursor = conn.cursor()

                # Check if item with same name exists
                cursor.execute("SELECT COUNT(*) FROM Supplier WHERE Name = %s", (new_name,))
                if cursor.fetchone()[0] > 0:
                    messagebox.showerror("Error", f"A Supplier with name '{new_name}' already exists.")
                    conn.close()
                    return

                cursor.execute("""
                    INSERT INTO Supplier (Name, Contact)
                    VALUES (%s, %s)
                """, (new_name, contact_))
                
                supplier_id= cursor.lastrowid
                
                # link with selected items
                for item_id, var in item_vars.items():
                    if var.get(): 
                        cursor.execute("""
                            INSERT INTO Item_Supplier (Item_id, Supplier_id)
                            VALUES (%s, %s)
                        """, (item_id, supplier_id))
                
                conn.commit()
                conn.close()

                messagebox.showinfo("Success", f"Supplier '{new_name}' added and linked to items successfully.")
                add_win.destroy()
                self.load_suppliers()

            except Exception as e:
                messagebox.showerror("Error", f"Invalid input or database error:\n{e}")

        save_btn = tk.Button(add_win, text="Add Supplier", command=save_new_supplier)
        save_btn.pack(pady=20)

    def handle_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            row_id = self.tree.identify_row(event.y)
            col = self.tree.identify_column(event.x)

            if not row_id:
                return

            supplier_values = self.tree.item(row_id, "values")
            tags= self.tree.item(row_id, "tags")
            item_id_tag= tags[0]
            if not item_id_tag.startswith("id_"):
                return
            supplier_id= item_id_tag[3:]

            if col == "#1":  # Edit icon column
                self.edit_supplier(supplier_id)
            elif col == "#6":  # Delete icon column
                self.delete_supplier(supplier_id)
                
            print("Clicked column:", col, "supplier_id:", supplier_id)

    def delete_supplier(self, supplier_id):
        answer = messagebox.askyesno("Delete Supplier", f"Are you sure you want to delete this supplier?")
        if answer:
            try:
                conn = self.connect_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Supplier WHERE Supplier_id = %s", (supplier_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    messagebox.showwarning("Delete Failed", "Supplier not found or could not be deleted.")
                    
                conn.close()
                messagebox.showinfo("Deleted", "Supplier was deleted successfully.")
                self.load_suppliers()
                
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Error: {err}")

    def edit_supplier(self, supplier_id):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Name, Contact FROM Supplier WHERE Supplier_id = %s", (supplier_id,)
            )
            supplier = cursor.fetchone()
            
            # fetch all items
            cursor.execute("SELECT Item_id, Name FROM Item")
            all_items= cursor.fetchall()
            
            # fetch linked items for this supplier
            cursor.execute(
                "SELECT Item_id FROM Item_Supplier WHERE Supplier_id = %s", (supplier_id,)
            )
            linked_item_ids= {row[0] for row in cursor.fetchall()}
            
            conn.close()
            

            if not supplier:
                messagebox.showerror("Error", "No supplier found")
                return

            # Create the edit popup
            edit_win = tk.Toplevel(self)
            edit_win.title(f"Edit Supplier")
            edit_win.geometry("400x600")
            edit_win.configure(bg=self.lavender)

            labels = ["Name", "Contact"]
            entries = []

            for idx, (label, value) in enumerate(zip(labels, supplier)):
                tk.Label(edit_win, text=label + ":", bg=self.lavender).pack(pady=(10 if idx == 0 else 5, 0))
                entry = tk.Entry(edit_win)
                entry.pack()
                entry.insert(0, str(value if value is not None else ""))
                entries.append(entry)
                
            # item checkboxes
            tk.Label(edit_win, text="Items Supplied:", bg=self.lavender).pack(pady=10)
            item_vars= {}
                
            for item_id, item_name in all_items:
                var= tk.BooleanVar(value=(item_id in linked_item_ids))
                tk.Checkbutton(edit_win, text= item_name, variable= var, bg= self.lavender).pack(anchor="w")
                item_vars[item_id]= var

            def save_changes():
                new_values = [e.get().strip() for e in entries]

                if not all(new_values):
                    messagebox.showwarning("Missing Info", "All fields are required.")
                    return

                try:
                    new_name = new_values[0]
                    contact_ = new_values[1]

                    conn = self.connect_db()
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        UPDATE Supplier
                        SET Name=%s, Contact=%s
                        WHERE Supplier_id=%s
                    """, (new_name, contact_, supplier_id))
                    
                    # clear any old links
                    cursor.execute("DELETE FROM Item_Supplier WHERE Supplier_id = %s", (supplier_id,))
                    
                    #insert updated links
                    for item_id, var in item_vars.items():
                        if var.get():
                            cursor.execute("""
                                INSERT INTO Item_Supplier (Item_id, Supplier_id)
                                VALUES (%s, %s)
                            """, (item_id, supplier_id))
                    
                    conn.commit()
                    conn.close()

                    messagebox.showinfo("Success", "Supplier updated and items linked.")
                    edit_win.destroy()
                    self.load_suppliers()

                except Exception as e:
                    messagebox.showerror("Error", f"Invalid input or database error:\n{e}")

            save_btn = tk.Button(edit_win, text="Save Changes", command=save_changes)
            save_btn.pack(pady=20)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")


# To test the SupplierView Frame standalone
if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "Root",
        "database": "flowershop_management"
    }

    root = tk.Tk()
    root.title("Flower Shop Management - Suppliers")
    root.geometry("950x500")
    supplier_view = SupplierView(root, db_config)
    supplier_view.pack(fill="both", expand=True)
    root.mainloop()
