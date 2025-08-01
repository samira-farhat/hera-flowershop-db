import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime

class ItemView(tk.Frame):
    def __init__(self, parent, db_config):
        super().__init__(parent)
        self.parent = parent
        self.db_config = db_config
        self.lavender = "#E6E6FA"
        self.configure(bg=self.lavender)

        # Search and Buttons Frame 
        search_frame = tk.Frame(self, bg=self.lavender)
        search_frame.pack(fill="x", padx=10, pady=(10, 0))

        tk.Label(search_frame, text="Search by Name:", bg=self.lavender).pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=(0, 5))
        search_btn = tk.Button(search_frame, text="Search", command=self.search_items)
        search_btn.pack(side="left", padx=(0, 10))
        tk.Button(search_frame, text="Clear", command=self.clear_search).pack(side="left", padx=5)

        add_btn = tk.Button(search_frame, text="Add Item", command=self.add_item)
        add_btn.pack(side="right")

        # Treeview Frame and Scrollbar 
        tree_frame= tk.Frame(self)
        tree_frame.pack(fill= "both", expand= True, padx= 10, pady= 10)
        
        scrollbar= ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        columns = (
            "Edit", "Item ID", "Name", "Type", "Arrival Date", "Discount",
            "Price", "Price Date", "Stock Quantity", "Status", "Suppliers", "Delete"
        )
        
        self.tree = ttk.Treeview(tree_frame, columns= columns, show="headings", yscrollcommand= scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command= self.tree.yview)

        for col in columns:
            if col in ("Edit", "Delete"):
                self.tree.heading(col, text="")
                self.tree.column(col, anchor="center", width=60)
            elif col == "Item ID":
                self.tree.heading(col, text="ID")
                self.tree.column(col, anchor="center", width=70)
            elif col == "Suppliers":
                self.tree.heading(col, text="Suppliers")
                self.tree.column(col, anchor="w", width=200)
            else:
                self.tree.heading(col, text=col)
                self.tree.column(col, anchor="center", width=100)

        self.tree.configure(cursor="hand2")
        self.tree.tag_configure("restock", foreground="red")
        self.tree.tag_configure("lowstock", foreground="#b22222")

        self.tree.bind("<Button-1>", self.handle_click)

        self.load_items()

    def connect_db(self):
        return mysql.connector.connect(
            host=self.db_config.get("host", "localhost"),
            user=self.db_config.get("user", "your_mysql_username"),
            password=self.db_config.get("password", "your_mysql_password"),
            database=self.db_config.get("database", "flowershop_management")
        )
        
    def clear_search(self):
        self.search_var.set("")
        self.load_items()

    def load_items(self):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    i.Item_id, i.Name, i.Type, i.Arrival_date, i.Item_discount,
                    i.Price_amount, i.Price_date, i.Stock_quantity,
                    GROUP_CONCAT(s.Name SEPARATOR ', ')
                FROM Item i
                LEFT JOIN Item_Supplier isr ON i.Item_id = isr.Item_id
                LEFT JOIN Supplier s ON isr.Supplier_id = s.Supplier_id
                GROUP BY i.Item_id
                ORDER BY i.Arrival_date DESC, i.Item_id DESC
            """)
            items = cursor.fetchall()
            conn.close()
            self.display_items(items)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def display_items(self, items):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for item in items:
            item_id, name, type_, arrival_date, discount, price, price_date, stock_qty, suppliers_str = item

            arrival_str = arrival_date.strftime("%Y-%m-%d") if arrival_date else ""
            price_date_str = price_date.strftime("%Y-%m-%d") if price_date else ""
            discount_pct = f"{discount * 100:.0f}%" if discount else "0%"
            suppliers_str= suppliers_str or "_"

            if stock_qty == 0:
                status = "RESTOCK"
                tag = "restock"
            elif stock_qty < 10:
                status = "Low Stock"
                tag = "lowstock"
            else:
                status = "OK"
                tag = ""

            self.tree.insert(
                "", "end",
                values=(
                    "🖉 edit",  
                    item_id, name, type_, arrival_str, discount_pct, f"{price:.2f}",
                    price_date_str, stock_qty, status, suppliers_str, "🗑️"
                ),
                tags=(f"id_{item_id}", tag)
            )

    def search_items(self):
        search_text = self.search_var.get().strip()
        if not search_text:
            messagebox.showinfo("Search", "Please enter a name to search.")
            return
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            query = ("""
                SELECT 
                    i.Item_id, i.Name, i.Type, i.Arrival_date, i.Item_discount,
                    i.Price_amount, i.Price_date, i.Stock_quantity,
                    GROUP_CONCAT(s.Name SEPARATOR ', ')
                FROM Item i
                LEFT JOIN Item_Supplier isr ON i.Item_id = isr.Item_id
                LEFT JOIN Supplier s ON isr.Supplier_id = s.Supplier_id
                WHERE i.Name LIKE %s
                GROUP BY i.Item_id
                ORDER BY i.Arrival_date DESC, i.Item_id DESC
            """)
            cursor.execute(query, (f"%{search_text}%",))
            results = cursor.fetchall()
            conn.close()

            if results:
                self.display_items(results)
            else:
                messagebox.showinfo("Search", f"No items found matching '{search_text}'")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def add_item(self):
        # Create the add item popup
        add_win = tk.Toplevel(self)
        add_win.title("Add New Item")
        add_win.geometry("400x450")
        add_win.configure(bg=self.lavender)

        labels = [
            "Name", "Type", "Arrival Date (YYYY-MM-DD)", "Discount (%)",
            "Price", "Price Date (YYYY-MM-DD)", "Stock Quantity"
        ]
        entries = []

        for label in labels:
            tk.Label(add_win, text=label + ":", bg=self.lavender).pack(pady=5)
            entry = tk.Entry(add_win)
            entry.pack()
            entries.append(entry)

        def save_new_item():
            new_values = [e.get().strip() for e in entries]

            if not all(new_values):
                messagebox.showwarning("Missing Info", "All fields are required.")
                return

            try:
                new_name = new_values[0]
                type_ = new_values[1]
                arrival_date = datetime.strptime(new_values[2], "%Y-%m-%d").date()
                discount = float(new_values[3]) / 100  
                price = float(new_values[4])
                price_date = datetime.strptime(new_values[5], "%Y-%m-%d").date()
                stock_qty = int(new_values[6])

                conn = self.connect_db()
                cursor = conn.cursor()

                # Check if item with same name exists
                cursor.execute("SELECT COUNT(*) FROM Item WHERE Name = %s", (new_name,))
                if cursor.fetchone()[0] > 0:
                    messagebox.showerror("Error", f"An item with name '{new_name}' already exists.")
                    conn.close()
                    return

                cursor.execute("""
                    INSERT INTO Item (Name, Type, Arrival_date, Item_discount, Price_amount, Price_date, Stock_quantity)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (new_name, type_, arrival_date, discount, price, price_date, stock_qty))
                conn.commit()
                conn.close()

                messagebox.showinfo("Success", f"Item '{new_name}' added successfully.")
                add_win.destroy()
                self.load_items()

            except Exception as e:
                messagebox.showerror("Error", f"Invalid input or database error:\n{e}")

        save_btn = tk.Button(add_win, text="Add Item", command=save_new_item)
        save_btn.pack(pady=20)

    def handle_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            row_id = self.tree.identify_row(event.y)
            col = self.tree.identify_column(event.x)

            if not row_id:
                return

            item_values = self.tree.item(row_id, "values")
            tags= self.tree.item(row_id, "tags")
            item_id_tag= tags[0]
            if not item_id_tag.startswith("id_"):
                return
            item_id= item_id_tag[3:]

            if col == "#1":  # Edit icon column
                self.edit_item(item_id)
            elif col == "#12":  # Delete icon column
                self.delete_item(item_id)
                
            print("Clicked column:", col, "item_id:", item_id)

    def delete_item(self, item_id):
        answer = messagebox.askyesno("Delete Item", f"Are you sure you want to delete this item?")
        if answer:
            try:
                conn = self.connect_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Item WHERE Item_id = %s", (item_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    messagebox.showwarning("Delete Failed", "Item not found or could not be deleted.")
                    
                conn.close()
                messagebox.showinfo("Deleted", "Item was deleted successfully.")
                self.load_items()
                
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Error: {err}")

    def edit_item(self, item_id):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Name, Type, Arrival_date, Item_discount, Price_amount, Price_date, Stock_quantity "
                "FROM Item WHERE Item_id = %s", (item_id,)
            )
            item = cursor.fetchone()
            conn.close()

            if not item:
                messagebox.showerror("Error", "No item found")
                return

            # Create the edit popup
            edit_win = tk.Toplevel(self)
            edit_win.title(f"Edit Item")
            edit_win.geometry("400x400")
            edit_win.configure(bg=self.lavender)

            labels = [
                "Name", "Type", "Arrival Date (YYYY-MM-DD)", "Discount (0.0 - 1.0)",
                "Price", "Price Date (YYYY-MM-DD)", "Stock Quantity"
            ]
            entries = []

            for idx, (label, value) in enumerate(zip(labels, item)):
                tk.Label(edit_win, text=label + ":", bg=self.lavender).pack(pady=(10 if idx == 0 else 5, 0))
                entry = tk.Entry(edit_win)
                entry.pack()
                if idx == 3:
                    entry.insert(0, str(float(value) * 100 if value is not None else ""))
                else:
                    entry.insert(0, str(value if value is not None else ""))

                entries.append(entry)

            def save_changes():
                new_values = [e.get().strip() for e in entries]

                if not all(new_values):
                    messagebox.showwarning("Missing Info", "All fields are required.")
                    return

                try:
                    new_name = new_values[0]
                    type_ = new_values[1]
                    arrival_date = datetime.strptime(new_values[2], "%Y-%m-%d").date()
                    discount = float(new_values[3]) / 100 
                    price = float(new_values[4])
                    price_date = datetime.strptime(new_values[5], "%Y-%m-%d").date()
                    stock_qty = int(new_values[6])

                    conn = self.connect_db()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE Item
                        SET Name=%s, Type=%s, Arrival_date=%s, Item_discount=%s,
                            Price_amount=%s, Price_date=%s, Stock_quantity=%s
                        WHERE Item_id=%s
                    """, (new_name, type_, arrival_date, discount, price, price_date, stock_qty, item_id))
                    conn.commit()
                    conn.close()

                    messagebox.showinfo("Success", "Item updated.")
                    edit_win.destroy()
                    self.load_items()

                except Exception as e:
                    messagebox.showerror("Error", f"Invalid input or database error:\n{e}")

            save_btn = tk.Button(edit_win, text="Save Changes", command=save_changes)
            save_btn.pack(pady=20)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")


# To test the ItemView Frame standalone
if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "Root",
        "database": "flowershop_management"
    }

    root = tk.Tk()
    root.title("Flower Shop Management - Items")
    root.geometry("950x500")
    item_view = ItemView(root, db_config)
    item_view.pack(fill="both", expand=True)
    root.mainloop()
