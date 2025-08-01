import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime

class CustomerView(tk.Frame):
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
        search_btn = tk.Button(search_frame, text="Search", command=self.search_customers)
        search_btn.pack(side="left", padx=(0, 10))
        
        monthly_btn= tk.Button(search_frame, text= "This Month's Customers", command= self.show_monthly_customers)
        monthly_btn.pack(side= "left", padx= (10, 5))
        
        new_customers_btn= tk.Button(search_frame, text= "New this Month", command= self.show_new_customers)
        new_customers_btn.pack(side= "left", padx= (5, 0))


        # Treeview Frame and Scrollbar 
        tree_frame= tk.Frame(self)
        tree_frame.pack(fill= "both", expand= True, padx= 10, pady= 10)
        
        scrollbar= ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        columns = ("Edit", "Customer ID", "Name", "Phone", "Loyalty Points", "Delete")
        
        self.tree = ttk.Treeview(tree_frame, columns= columns, show="headings", yscrollcommand= scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command= self.tree.yview)

        for col in columns:
            if col in ("Edit", "Delete"):
                self.tree.heading(col, text="")
                self.tree.column(col, anchor="center", width=60)
            elif col == "Customer ID":
                self.tree.heading(col, text="ID")
                self.tree.column(col, anchor="center", width=80)
            else:
                self.tree.heading(col, text=col)
                self.tree.column(col, anchor="center", width=120)

        self.tree.configure(cursor="hand2")

        self.tree.bind("<Button-1>", self.handle_click)

        self.load_customers()

    def connect_db(self):
        return mysql.connector.connect(
            host=self.db_config.get("host", "localhost"),
            user=self.db_config.get("user", "your_mysql_username"),
            password=self.db_config.get("password", "your_mysql_password"),
            database=self.db_config.get("database", "flowershop_management")
        )

    def load_customers(self):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Customer_id, Name, Phone, Loyalty_points FROM Customer ORDER BY Customer_id DESC"
            )
            customers = cursor.fetchall()
            conn.close()
            self.display_customers(customers)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def display_customers(self, customers):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for customer in customers:
            customer_id, name, phone_, loyalty_pnts= customer

            self.tree.insert(
                "", "end",
                values=(
                    "🖉 edit",  
                    customer_id, name, phone_, loyalty_pnts, "🗑️"
                ),
                tags=(f"id_{customer_id}",)
            )

    def search_customers(self):
        search_text = self.search_var.get().strip()
        if not search_text:
            messagebox.showinfo("Search", "Please enter a customer name to search.")
            return
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            query = ("""
                SELECT
                    c.Customer_id,
                    c.Name,
                    o.Order_id,
                    o.Payment_date,
                    o.Total_price,
                    GROUP_CONCAT(CONCAT(i.Name, ' (', oi.Quantity, ')') SEPARATOR ', ') AS Items,
                    o.Order_status
                FROM Customer c
                JOIN Order_and_Payment o ON c.Customer_id = o.Customer_id
                JOIN Orders_Items oi ON o.Order_id = oi.Order_id
                JOIN Item i ON oi.Item_id = i.Item_id
                WHERE c.Name LIKE %s
                GROUP BY c.Customer_id, c.Name, o.Order_id, o.Payment_date, o.Total_price, o.Order_status
                ORDER BY o.Payment_date DESC
            """)
            cursor.execute(query, (f"%{search_text}%",))
            results = cursor.fetchall()
            conn.close()

            if results:
                self.show_order_history_window(results)
            else:
                messagebox.showinfo("Search", f"No orders found for '{search_text}'")
            

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
            
    def show_order_history_window(self, data):
        
        result_win= tk.Toplevel(self)
        result_win.title("Customer Order History")
        result_win.geometry("1500x400")
        result_win.configure(bg= self.lavender)
        
        result_win.protocol("WM_DELETE_WINDOW", lambda: self.on_history_close(result_win))
                
        columns= ["Customer ID", "Customer Name", "Order ID", "Payment Date", "Total Price", "Items", "Status"]
        tree= ttk.Treeview(result_win, columns= columns, show="headings")
                
        for col in columns:
            tree.heading(col, text= col)
            tree.column(col, anchor="center", width= 120)
                    
        for row in data:
            *order_data, status = row
            display_status = "❌" if status == "Cancelled" else "✓"
            tree.insert("", "end", values= (*order_data, display_status), tags=(status,))

        tree.tag_configure("Cancelled", background="#FFD6D6")

                    
        tree.pack(fill= "both", expand= True) 
    
    def on_history_close(self, window):
        window.destroy()
        self.search_var.set("")  

    def show_monthly_customers(self):
        try:
            conn= self.connect_db()
            cursor= conn.cursor()
            cursor.execute("""
                SELECT DISTINCT c.Customer_id, c.Name, c.Phone, c.Loyalty_points
                FROM Customer c
                JOIN Order_and_Payment o ON c.Customer_id = o.Customer_id
                WHERE MONTH(o.Payment_date) = MONTH(CURRENT_DATE())
                AND YEAR(o.Payment_date) = YEAR(CURRENT_DATE())
                ORDER BY c.Name
            """)
            
            customers= cursor.fetchall()
            conn.close()
            
            if customers:
                self.show_customer_list_window("Customers with Orders This Month", customers)
            else:
                messagebox.showinfo("This Month's Customers", "No customers with orders this month")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"{err}")
            
    
    def show_new_customers(self):
        try:
            conn= self.connect_db()
            cursor= conn.cursor()
            cursor.execute("""
                SELECT c.Customer_id, c.Name, c.Phone, c.Loyalty_points
                FROM Customer c
                WHERE c.Customer_id IN (
                    SELECT o.Customer_id
                    FROM Order_and_Payment o
                    GROUP BY o.Customer_id
                    HAVING MONTH(MIN(o.Payment_date)) = MONTH(CURRENT_DATE())
                        AND YEAR(MIN(o.Payment_date)) = YEAR(CURRENT_DATE())
                )
                ORDER BY c.Name             
            """)
            customers= cursor.fetchall()
            conn.close()
            
            if customers:
                self.show_customer_list_window("New Customers This Month", customers)
            else:
                messagebox.showinfo("New Customers This Month", "No new customers this month")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"{err}")
            
    def show_customer_list_window(self, title, customers):
        result_win= tk.Toplevel(self)
        result_win.title(title)
        result_win.geometry("500x400")
        result_win.configure(bg= self.lavender)
        
        columns = ["#", "Name", "Phone", "Loyalty Points"]
        tree= ttk.Treeview(result_win, columns= columns, show= "headings")
        
        for col in columns:
            tree.heading(col, text= col)
            tree.column(col, anchor= "center", width= 100)
            
        for idx, cust in enumerate(customers, start=1):
            _,name, phone, points = cust
            
            tree.insert("", "end", values= (idx, name, phone, points))
            
        tree.pack(fill= "both", expand= True)
            

    def handle_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            row_id = self.tree.identify_row(event.y)
            col = self.tree.identify_column(event.x)

            if not row_id:
                return

            customer_values = self.tree.item(row_id, "values")
            tags= self.tree.item(row_id, "tags")
            item_id_tag= tags[0]
            if not item_id_tag.startswith("id_"):
                return
            customer_id= item_id_tag[3:]

            if col == "#1":  # Edit icon column
                self.edit_customer(customer_id)
            elif col == "#6":  # Delete icon column
                self.delete_customer(customer_id)
                
            print("Clicked column:", col, "customer_id:", customer_id)

    def delete_customer(self, customer_id):
        answer = messagebox.askyesno("Delete Customer", f"Are you sure you want to delete this customer?")
        if answer:
            try:
                conn = self.connect_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Customer WHERE Customer_id = %s", (customer_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    messagebox.showwarning("Delete Failed", "Customer not found or could not be deleted.")
                    
                conn.close()
                messagebox.showinfo("Deleted", "Customer was deleted successfully.")
                self.load_customers()
                
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Error: {err}")

    def edit_customer(self, customer_id):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Name, Phone, Loyalty_points FROM Customer WHERE Customer_id = %s", (customer_id,)
            )
            item = cursor.fetchone()
            conn.close()

            if not item:
                messagebox.showerror("Error", "No customer found")
                return

            # Create the edit popup
            edit_win = tk.Toplevel(self)
            edit_win.title(f"Edit Customer")
            edit_win.geometry("400x400")
            edit_win.configure(bg=self.lavender)

            labels = [
                "Name", "Phone", "Loyalty Points"
            ]
            
            entries = []

            for idx, (label, value) in enumerate(zip(labels, item)):
                tk.Label(edit_win, text=label + ":", bg=self.lavender).pack(pady=(10 if idx == 0 else 5, 0))
                entry = tk.Entry(edit_win)
                entry.pack()
                entry.insert(0, str(value if value is not None else ""))
                entries.append(entry)

            def save_changes():
                new_values = [e.get().strip() for e in entries]

                if not all(new_values):
                    messagebox.showwarning("Missing Info", "All fields are required.")
                    return

                try:
                    new_name = new_values[0]
                    phone_ = new_values[1]
                    loyalty_pnts = int(new_values[2])

                    conn = self.connect_db()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE Customer
                        SET Name=%s, Phone=%s, Loyalty_points=%s
                        WHERE Customer_id=%s
                    """, (new_name, phone_, loyalty_pnts, customer_id))
                    conn.commit()
                    conn.close()

                    messagebox.showinfo("Success", "Customer updated.")
                    edit_win.destroy()
                    self.load_customers()

                except Exception as e:
                    messagebox.showerror("Error", f"Invalid input or database error:\n{e}")

            save_btn = tk.Button(edit_win, text="Save Changes", command=save_changes)
            save_btn.pack(pady=20)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")


# To test the CustomerView Frame standalone
if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "Root",
        "database": "flowershop_management"
    }

    root = tk.Tk()
    root.title("Flower Shop Management - Customers")
    root.geometry("950x500")
    customer_view = CustomerView(root, db_config)
    customer_view.pack(fill="both", expand=True)
    root.mainloop()

