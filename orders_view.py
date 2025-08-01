import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

class OrderView(tk.Frame):
    def __init__(self, parent, db_config):
        super().__init__(parent)
        self.parent = parent
        self.db_config = db_config
        self.lavender = "#E6E6FA"
        self.configure(bg=self.lavender)

        # Search and Buttons Frame 
        
        search_frame = tk.Frame(self, bg=self.lavender)
        search_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        # first: 
        
        search_row = tk.Frame(search_frame, bg=self.lavender)
        search_row.pack(fill="x")

        tk.Label(search_row, text="Search by Customer Name:", bg=self.lavender).pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_row, textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=(0, 5))
        search_btn = tk.Button(search_row, text="Search", command=self.search_orders)
        search_btn.pack(side="left", padx=(0, 10))

        tk.Button(search_row, text="Clear", command=self.clear_search).pack(side="left", padx=5)
        
        add_order_btn = tk.Button(search_row, text="➕ New Order", command=self.add_order)
        add_order_btn.pack(side="right", padx=(10, 0))

        
        # second:
        
        filter_row = tk.Frame(search_frame, bg=self.lavender)
        filter_row.pack(fill="x", pady=(10, 0)) 
        
        tk.Label(filter_row, text="Filter Orders by Status:", bg=self.lavender).pack(side="left", padx=(0, 5))
        self.status_var= tk.StringVar()
        self.status_var.set("All")
        self.status_filter = ttk.Combobox(filter_row, textvariable= self.status_var, values=["All", "Pending", "Processing", "Completed", "Cancelled"], state="readonly", width=12)
        self.status_filter.bind("<<ComboboxSelected>>", self.on_status_change)
        self.status_filter.pack(side="left", padx=5)

        # Treeview Frame and Scrollbar 
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")

        columns = ("Edit", "Order ID", "Customer Name", "Budget", "Total Price", "Deposit", "Remaining Payment", "Order Status", "Confirmation", "Delete")

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar.config(command=self.tree.yview)

        for col in columns:
            if col in ("Edit", "Delete"):
                self.tree.heading(col, text="")
                self.tree.column(col, anchor="center", width=60)
            elif col == "Order ID":
                self.tree.heading(col, text="Order ID")
                self.tree.column(col, anchor="center", width=80)
            elif col == "Confirmation":
                self.tree.heading(col, text="Confirmation")
                self.tree.column(col, anchor="center", width=100)
            elif col == "Remaining Payment":
                self.tree.heading(col, text="Remaining Payment")
                self.tree.column(col, anchor="center", width=120)
            else:
                self.tree.heading(col, text=col)
                self.tree.column(col, anchor="center", width=120)

        self.tree.configure(cursor="hand2")
        self.tree.bind("<Button-1>", self.handle_click)

        self.load_orders()

    def connect_db(self):
        return mysql.connector.connect(
            host=self.db_config.get("host", "localhost"),
            user=self.db_config.get("user", "root"),
            password=self.db_config.get("password", ""),
            database=self.db_config.get("database", "flowershop_management")
        )
        
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.status_filter.set("All")
        self.load_orders()

    def load_orders(self):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            query = """
                SELECT
                    o.Order_id,
                    c.Name,
                    o.Budget,
                    SUM(oi.Quantity * oi.Unit_price * (1 - i.Item_discount)) - IFNULL(o.Order_discount, 0) AS Total_Price,
                    o.Deposit,
                    GREATEST(
                        (SUM(oi.Quantity * oi.Unit_price * (1 - i.Item_discount)) - IFNULL(o.Order_discount, 0)) - o.Deposit,
                        0
                    ) AS Remaining_Payment,
                    o.Order_status,
                    o.Confirmation
                FROM Order_and_Payment o
                JOIN Customer c ON o.Customer_id = c.Customer_id
                JOIN Orders_Items oi ON o.Order_id = oi.Order_id
                JOIN Item i ON oi.Item_id = i.Item_id
                GROUP BY o.Order_id, c.Name, o.Budget, o.Deposit, o.Order_discount, o.Order_status, o.Confirmation
                ORDER BY o.Order_id DESC
            """
            cursor.execute(query)
            orders = cursor.fetchall()
            conn.close()

            self.display_orders(orders)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def display_orders(self, orders):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for order in orders:
            (order_id, customer_name, budget, total_price, deposit, remaining_payment, order_status, confirmation) = order
            
            status_color_tag = f"status_{order_status.lower().replace(' ', '_')}"
            self.tree.insert(
                "", "end",
                values=(
                    "🖉 edit",
                    order_id,
                    customer_name,
                    f"{budget:.2f}",
                    f"{total_price:.2f}",
                    f"{deposit:.2f}",
                    f"{remaining_payment:.2f}",
                    order_status,
                    "Yes" if confirmation else "No",
                    "🗑️"
                ),
                tags=(f"id_{order_id}", status_color_tag)
            )
            
        self.tree.tag_configure("status_pending", background="#FFFACD")       # light yellow
        self.tree.tag_configure("status_completed", background="#DFFFD6")     # light green
        self.tree.tag_configure("status_cancelled", background="#FFD6D6")     # light red/pink
        self.tree.tag_configure("status_processing", background="#E0F0FF")    # light blue

    def search_orders(self):
        search_text = self.search_var.get().strip()
        if not search_text:
            messagebox.showinfo("Search", "Please enter a customer name to search.")
            return

        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            query = """
                SELECT
                    o.Order_id,
                    c.Name,
                    o.Budget,
                    SUM(oi.Quantity * oi.Unit_price * (1 - i.Item_discount)) - IFNULL(o.Order_discount, 0) AS Total_Price,
                    o.Deposit,
                    GREATEST(
                        (SUM(oi.Quantity * oi.Unit_price * (1 - i.Item_discount)) - IFNULL(o.Order_discount, 0)) - o.Deposit, 
                        0
                    ) AS Remaining_Payment,
                    o.Order_status,
                    o.Confirmation
                FROM Order_and_Payment o
                JOIN Customer c ON o.Customer_id = c.Customer_id
                JOIN Orders_Items oi ON o.Order_id = oi.Order_id
                JOIN Item i ON oi.Item_id = i.Item_id
                WHERE c.Name LIKE %s
                GROUP BY o.Order_id, c.Name, o.Budget, o.Deposit, o.Order_discount, o.Order_status, o.Confirmation
                ORDER BY o.Order_id DESC
            """
            cursor.execute(query, (f"%{search_text}%",))
            orders = cursor.fetchall()
            conn.close()

            if orders:
                self.display_orders(orders)
            else:
                messagebox.showinfo("Search", f"No orders found for customer '{search_text}'")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
            
    def on_status_change(self, event):
        selected_status = self.status_filter.get()
        if selected_status == "All":
            self.load_orders()
        else:
            self.load_orders_filtered(selected_status)

            
    def load_orders_filtered(self, status):
        
        try: 
            
            conn= self.connect_db()
            cursor= conn.cursor()
        
            query= """
                SELECT
                    o.Order_id,
                    c.Name,
                    o.Budget,
                    SUM(oi.Quantity * oi.Unit_price * (1 - i.Item_discount)) - IFNULL(o.Order_discount, 0) AS Total_Price,
                    o.Deposit,
                    GREATEST(
                        (SUM(oi.Quantity * oi.Unit_price * (1 - i.Item_discount)) - IFNULL(o.Order_discount, 0)) - o.Deposit,
                        0
                    ) AS Remaining_Payment,
                    o.Order_status,
                    o.Confirmation
                FROM Order_and_Payment o
                JOIN Customer c ON o.Customer_id = c.Customer_id
                JOIN Orders_Items oi ON o.Order_id = oi.Order_id
                JOIN Item i ON oi.Item_id = i.Item_id
                WHERE o.Order_status = %s
                GROUP BY o.Order_id, c.Name, o.Budget, o.Deposit, o.Order_discount, o.Order_status, o.Confirmation
                ORDER BY o.Order_id DESC
            """
        
            cursor.execute(query, (status,))
            orders= cursor.fetchall()
            conn.close()
            
            self.display_orders(orders)
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")
        
            
    def add_order(self):

        # --- Step 1: Customer Search/Add ---
        cust_win = tk.Toplevel(self)
        cust_win.title("Add New Order - Step 1: Customer Info")
        cust_win.geometry("400x400")
        cust_win.configure(bg=self.lavender)

        tk.Label(cust_win, text="Search Customer by Name or Phone:", bg=self.lavender).pack(pady=(10,5))
        search_var = tk.StringVar()
        search_entry = tk.Entry(cust_win, textvariable=search_var)
        search_entry.pack(pady=5, fill="x", padx=10)

        search_results_frame = tk.Frame(cust_win, bg=self.lavender)
        search_results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        selected_customer = {"id": None}

        def search_customer():
            query_text = search_var.get().strip()
            for widget in search_results_frame.winfo_children():
                widget.destroy()

            if not query_text:
                tk.Label(search_results_frame, text="Enter a name or phone to search.", bg=self.lavender).pack()
                return

            try:
                conn = self.connect_db()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT Customer_id, Name, Phone FROM Customer
                    WHERE Name LIKE %s OR Phone LIKE %s
                """, (f"%{query_text}%", f"%{query_text}%"))
                results = cursor.fetchall()
                conn.close()

                if not results:
                    tk.Label(search_results_frame, text="No customers found.", bg=self.lavender).pack()
                    return

                # Show results with radiobuttons to select customer
                selected_cust_var = tk.IntVar(value=0)

                def on_select():
                    selected_customer["id"] = selected_cust_var.get()

                for idx, (cid, name, phone) in enumerate(results):
                    rb = tk.Radiobutton(
                        search_results_frame,
                        text=f"{name} | {phone} (ID: {cid})",
                        variable=selected_cust_var,
                        value=cid,
                        bg=self.lavender,
                        anchor="w",
                        command=on_select,
                    )
                    rb.pack(fill="x", anchor="w")

            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Error: {err}")

        tk.Button(cust_win, text="Search", command=search_customer).pack(pady=5)

        # New customer inputs (name + phone)
        tk.Label(cust_win, text="Or add New Customer:", bg=self.lavender, font=("Arial", 10, "bold")).pack(pady=(10,2))

        new_name_var = tk.StringVar()
        new_phone_var = tk.StringVar()
        tk.Label(cust_win, text="Name:", bg=self.lavender).pack(anchor="w", padx=10)
        new_name_entry = tk.Entry(cust_win, textvariable=new_name_var)
        new_name_entry.pack(fill="x", padx=10)

        tk.Label(cust_win, text="Phone:", bg=self.lavender).pack(anchor="w", padx=10, pady=(5,0))
        new_phone_entry = tk.Entry(cust_win, textvariable=new_phone_var)
        new_phone_entry.pack(fill="x", padx=10)

        def step1_next():
            cust_id = selected_customer.get("id")
            customer_name = new_name_var.get().strip()
            customer_phone = new_phone_var.get().strip()

            if not cust_id and (not customer_name or not customer_phone):
                messagebox.showwarning("Input Required", "Please select a customer or enter name and phone for a new customer.")
                return

            cust_win.withdraw()
            step2_order_items(cust_id, customer_name, customer_phone, cust_win)

        tk.Button(cust_win, text="Next", command=step1_next).pack(pady=10)

        # --- Step 2: Order Items ---
        def step2_order_items(customer_id, customer_name, customer_phone, cust_win):
            items_win = tk.Toplevel(self)
            items_win.title("Add New Order - Step 2: Order Items")
            items_win.geometry("700x400")
            items_win.configure(bg=self.lavender)

            tk.Label(items_win, text="Add Items to Order:", bg=self.lavender, font=("Arial", 12, "bold")).pack(pady=10)

            # Treeview for order items
            columns = ("Item ID", "Item Name", "Quantity", "Price", "Item Discount", "Total")
            tree = ttk.Treeview(items_win, columns=columns, show="headings", height=10)
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor="center", width=100)
                tree.pack(fill="both", expand=True, padx=10)

            # Form to add items by Item ID and Quantity
            form_frame = tk.Frame(items_win, bg=self.lavender)
            form_frame.pack(pady=10)

            tk.Label(form_frame, text="Select Item:", bg=self.lavender).grid(row=0, column=0, padx=5, sticky="e")
            item_var = tk.StringVar()
            item_dropdown = ttk.Combobox(form_frame, textvariable=item_var, width=40, state="readonly")
            item_dropdown.grid(row=0, column=1, columnspan=2, padx=5)

                # Load in-stock items into dropdown
            try:
                conn = self.connect_db()
                cursor = conn.cursor()
                cursor.execute("SELECT Item_id, Name, Price_amount, Item_discount FROM Item WHERE Stock_quantity > 0 ORDER BY Name ASC")
                available_items = cursor.fetchall()
                conn.close()

                item_map = {
                    f"{name} (${price:.2f}) (ID: {iid})": (iid, name, price, discount)
                    for iid, name, price, discount in available_items
                }

                item_dropdown["values"] = list(item_map.keys())
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Error loading items: {err}")

            tk.Label(form_frame, text="Quantity:", bg=self.lavender).grid(row=0, column=2, padx=5, sticky="e")
            quantity_var = tk.StringVar(value="1")
            quantity_entry = tk.Entry(form_frame, textvariable=quantity_var, width=10)
            quantity_entry.grid(row=0, column=3, padx=5)

            added_items = []

            def add_item():
                item_label = item_var.get()
                if item_label not in item_map:
                    messagebox.showerror("Selection Error", "Please select a valid item.")
                    return
                iid, name, price_amount, discount = item_map[item_label]
                qty_str = quantity_var.get().strip()
                if not iid or not qty_str.isdigit() or int(qty_str) <= 0:
                    messagebox.showwarning("Input Error", "Please enter valid Item ID and positive Quantity.")
                    return
                qty = int(qty_str)

                try:
                    conn = self.connect_db()
                    cursor = conn.cursor()
                    cursor.execute("SELECT Name, Price_amount, Item_discount FROM Item WHERE Item_id = %s", (iid,))
                    res = cursor.fetchone()
                    conn.close()
                    if not res:
                        messagebox.showerror("Error", f"No item found with ID {iid}.")
                        return

                    name, price_amount, discount = res
                    total_price = qty * price_amount * (1 - discount)

                    # Append to treeview and local list
                    tree.insert("", "end", values=(iid, name, qty, f"{price_amount:.2f}", f"{discount:.2%}", f"{total_price:.2f}"))
                    added_items.append({"item_id": iid, "quantity": qty, "unit_price": price_amount, "discount": discount})

                    # Clear entries
                    quantity_var.set("1")
                except mysql.connector.Error as err:
                    messagebox.showerror("Database Error", f"Error: {err}")

            add_item_btn = tk.Button(form_frame, text="Add Item", command=add_item)
            add_item_btn.grid(row=0, column=4, padx=10)
            
            def remove_selected_item():
                selected = tree.selection()
                if not selected:
                    messagebox.showwarning("No Selection", "Please select an item to remove.")
                    return

                for sel in selected:
                    values = tree.item(sel)["values"]
                    tree.delete(sel)

                    # remove from added_items as well
                    item_id = values[0]
                    quantity = int(values[2])
                    for i, item in enumerate(added_items):
                        if item["item_id"] == item_id and item["quantity"] == quantity:
                            del added_items[i]
                            break

            tk.Button(form_frame, text="Remove Selected", command=remove_selected_item).grid(row=0, column=5, padx=5)


            def step2_next():
                if not added_items:
                    messagebox.showwarning("Input Required", "Add at least one item to the order.")
                    return
                
                items_win.withdraw()
                step3_order_details(customer_id, customer_name, customer_phone ,added_items, items_win)


            def go_back_to_step1():
                items_win.destroy()
                cust_win.deiconify()  
                
            nav_frame = tk.Frame(items_win, bg=self.lavender)
            nav_frame.pack(pady=10)

            tk.Button(nav_frame, text="Back", command=go_back_to_step1).pack(side=tk.LEFT, padx=(20, 5))
            tk.Button(nav_frame, text="Next", command=step2_next).pack(side=tk.RIGHT, padx=(5, 20))



        # --- Step 3: Order Details ---
        def step3_order_details(customer_id, customer_name, customer_phone ,order_items, items_win):
            details_win = tk.Toplevel(self)
            details_win.title("Add New Order - Step 3: Order Details")
            details_win.geometry("400x600")
            details_win.configure(bg=self.lavender)

            tk.Label(details_win, text="Enter Order Details:", bg=self.lavender, font=("Arial", 12, "bold")).pack(pady=10)

            budget_var = tk.StringVar(value="0")
            deposit_var = tk.StringVar(value="0")
            discount_var = tk.StringVar(value="0")
            payment_method_var = tk.StringVar(value="Cash")
            status_var = tk.StringVar(value="Pending")
            confirmation_var = tk.BooleanVar(value=False)

            def create_labeled_entry(parent, label, var):
                tk.Label(parent, text=label, bg=self.lavender).pack(anchor="w", padx=10, pady=(5,0))
                e = tk.Entry(parent, textvariable=var)
                e.pack(fill="x", padx=10)
                return e

            create_labeled_entry(details_win, "Budget:", budget_var)
            create_labeled_entry(details_win, "Deposit:", deposit_var)
            create_labeled_entry(details_win, "Order Discount (%):", discount_var)
            
            # Receiver info
            tk.Label(details_win, text="Receiver Address:", bg=self.lavender).pack(anchor="w", padx=10, pady=(10,0))
            receiver_address_entry = tk.Entry(details_win)
            receiver_address_entry.pack(fill="x", padx=10)

            tk.Label(details_win, text="Receiver Phone:", bg=self.lavender).pack(anchor="w", padx=10, pady=(10,0))
            receiver_phone_entry = tk.Entry(details_win)
            receiver_phone_entry.pack(fill="x", padx=10)

            # Payment method dropdown
            tk.Label(details_win, text="Payment Method:", bg=self.lavender).pack(anchor="w", padx=10, pady=(10,0))
            payment_options = ["Cash", "Credit Card", "Whish", "OMT", "Bank Transfer", "Other"]
            payment_combo = ttk.Combobox(details_win, textvariable=payment_method_var, values=payment_options, state="readonly")
            payment_combo.pack(fill="x", padx=10)
            

            # Order status dropdown
            tk.Label(details_win, text="Order Status:", bg=self.lavender).pack(anchor="w", padx=10, pady=(10,0))
            status_options = ["Pending", "Processing", "Completed", "Cancelled"]
            status_combo = ttk.Combobox(details_win, textvariable=status_var, values=status_options, state="readonly")
            status_combo.pack(fill="x", padx=10)

            # Confirmation checkbox
            confirm_check = tk.Checkbutton(details_win, text="Confirmed", variable=confirmation_var, bg=self.lavender)
            confirm_check.pack(pady=10)

            def save_order():
                nonlocal customer_id
                
                try:
                    budget = float(budget_var.get())
                    deposit = float(deposit_var.get())
                    order_discount = float(discount_var.get())
                except ValueError:
                    messagebox.showerror("Input Error", "Budget, Deposit, and Discount must be valid numbers.")
                    return

                payment_method = payment_method_var.get()
                order_status = status_var.get()
                confirmation = confirmation_var.get()
                receiver_address = receiver_address_entry.get()
                receiver_phone = receiver_phone_entry.get()

                # Calculate total price from order_items
                total_price = sum(float(item["quantity"]) * float(item["unit_price"]) * (1 - float(item["discount"])) for item in order_items)
                
                # Apply order discount as percentage
                total_price_after_discount = total_price * (1 - (order_discount / 100))
                remaining_payment = max(total_price_after_discount - deposit, 0)


                try:
                    conn = self.connect_db()
                    cursor = conn.cursor()
                    
                    if not customer_id: 
                        if not customer_name or not customer_phone:
                            messagebox.showerror("Input Error", "Customer name and phone are required.")
                            return 
                        
                        cursor.execute("""
                            SELECT Customer_id FROM Customer WHERE Name = %s AND Phone = %s
                        """, (customer_name, customer_phone))
                        customer= cursor.fetchone()
                        
                        if customer: 
                            customer_id= customer[0]
                        else: 
                            cursor.execute("""
                                INSERT INTO Customer (Name, Phone) VALUES (%s, %s)
                            """, (customer_name, customer_phone))
                            
                            customer_id= cursor.lastrowid
                        

                    # Insert order_and_payment
                    cursor.execute("""
                        INSERT INTO Order_and_Payment
                        (Customer_id, Employee_id, Order_status, Order_discount, Payment_date, Payment_method,
                        Total_price, Budget, Deposit, Confirmation, Receiver_address, Receiver_phone)
                    VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)
                    """, (customer_id, 4, order_status, order_discount, payment_method, total_price_after_discount, budget,
                            deposit, int(confirmation_var.get()), receiver_address, receiver_phone ))
                    order_id = cursor.lastrowid

                    # Insert Orders_Items
                    for item in order_items:
                        
                        item_id= item["item_id"]
                        quantity= int(item["quantity"])
                        unit_price= item["unit_price"]
                        
                        # check stock for each item before placing the order
                        
                        cursor.execute("SELECT Stock_quantity, Name FROM Item WHERE Item_id = %s", (item_id,))
                        result = cursor.fetchone()

                        if result is None:
                            messagebox.showerror("Error", f"Item ID: {item_id} not found.")
                            conn.rollback()
                            conn.close()
                            return
                        
                        stock_available, item_name = result[0], result[1]
                        
                        if quantity > stock_available:
                            messagebox.showerror("Stock Error", f"Only {stock_available} units in stock for {item_name}. You tried to order {quantity}.")
                            conn.rollback()
                            conn.close()
                            return
                        
                        # insert Orders_Items and update stock
                        
                        cursor.execute("""
                            INSERT INTO Orders_Items (Order_id, Item_id, Quantity, Unit_price)
                            VALUES (%s, %s, %s, %s)
                        """, (order_id, item_id, quantity, unit_price))
                            
                        # decrease stock
                        cursor.execute("""
                            UPDATE Item SET Stock_quantity = Stock_quantity - %s WHERE Item_id = %s
                        """, (quantity, item_id))
                        
                    
                    # award loyalty points if fully paid
                    if deposit >= total_price_after_discount:
                        points_to_add= int(total_price_after_discount // 10) # assuming 10$ = 1 point
                        cursor.execute("""
                            UPDATE Customer
                            SET Loyalty_points = Loyalty_points + %s
                            WHERE Customer_id = %s
                        """, (points_to_add, customer_id))
                    
                    conn.commit()
                    conn.close()

                    messagebox.showinfo("Success", f"Order #{order_id} added successfully!")
                    details_win.destroy()
                    self.load_orders()

                except mysql.connector.Error as err:
                    messagebox.showerror("Database Error", f"Error saving order: {err}")


            def go_back_to_step2():
                details_win.destroy()
                items_win.deiconify()
                
            nav_frame = tk.Frame(details_win, bg=self.lavender)
            nav_frame.pack(pady=10)

            tk.Button(nav_frame, text="Back", command=go_back_to_step2).pack(side=tk.LEFT, padx=(20, 5))
            tk.Button(nav_frame, text="Save Order", command=save_order).pack(side=tk.RIGHT, padx=(5, 20))

    def handle_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)

        if not row_id:
            return

        order_values = self.tree.item(row_id, "values")
        tags = self.tree.item(row_id, "tags")
        item_id_tag = tags[0]
        if not item_id_tag.startswith("id_"):
            return
        order_id = item_id_tag[3:]

        if col == "#1":  # Edit column
            self.edit_order(order_id)
        elif col == "#10":  # Delete column
            self.delete_order(order_id)
        elif col == "#2":  # Order ID column clicked
            self.show_order_details(order_id)

    def delete_order(self, order_id):
        answer = messagebox.askyesno("Delete Order", f"Are you sure you want to delete order {order_id}?")
        if answer:
            try:
                conn = self.connect_db()
                cursor = conn.cursor()
                
                # get items and quantities from the order to return to stock
                cursor.execute("""
                    SELECT Item_id, Quantity 
                    FROM Orders_Items 
                    WHERE Order_id = %s
                """, (order_id,))
                items= cursor.fetchall()
                
                # return quantities to stock
                for item_id, quantity in items:
                    cursor.execute("""
                        UPDATE Item
                        SET Stock_quantity = Stock_quantity + %s
                        WHERE Item_id = %s
                    """, (quantity, item_id))
                    
                # get order total and customer id
                cursor.execute("""
                    SELECT Total_price, Customer_id
                    FROM Order_and_Payment
                    WHERE Order_id = %s
                """, (order_id,))
                result= cursor.fetchone()
                
                if result:
                    total_price, customer_id = result
                    
                    # adjust loyalty points (assuming 10$ = 1 point)
                    loyalty_points_to_deduct= int(total_price // 10)
                    cursor.execute("""
                        UPDATE Customer
                        SET Loyalty_points = GREATEST(Loyalty_points - %s, 0)
                        WHERE Customer_id = %s
                    """, (loyalty_points_to_deduct, customer_id))
                    
                # delete order
                cursor.execute("DELETE FROM Order_and_Payment WHERE Order_id = %s", (order_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Deleted", "Order was deleted successfully.")
                self.load_orders()
                
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Error: {err}")

    def edit_order(self, order_id):
        
        if not order_id:
            selected= self.tree.focus()
            
            if not selected:
                messagebox.showwarning("Select Order", "Please select an order to edit.")
                return
            
            order_id= self.tree.item(selected, "values")[0]
        

        # load existing order data
        try:
            conn = self.connect_db()
            cursor = conn.cursor(dictionary=True)

            # get order + customer info
            cursor.execute("""
                SELECT o.Order_id, o.Customer_id, c.Name AS Customer_name, c.Phone AS Customer_phone,
                   o.Budget, o.Deposit, o.Order_discount, o.Payment_method, o.Order_status,
                   o.Confirmation, o.Receiver_address, o.Receiver_phone
                FROM Order_and_Payment o
                JOIN Customer c ON o.Customer_id = c.Customer_id
                WHERE o.Order_id = %s
            """, (order_id,))
            order_info = cursor.fetchone()

            # get order items
            cursor.execute("""
                SELECT oi.Item_id, i.Name, oi.Quantity, oi.Unit_price, i.Item_discount, i.Stock_quantity
                FROM Orders_Items oi
                JOIN Item i ON oi.Item_id = i.Item_id
                WHERE oi.Order_id = %s
            """, (order_id,))
            order_items = cursor.fetchall()
            
            conn.close()
        except mysql.connector.Error as err:
            messagebox.showerror("DB Error", f"Failed to load order info: {err}")
            return

        if not order_info:
            messagebox.showerror("Error", "Order not found.")
            return

        original_items = {item['Item_id']: item['Quantity'] for item in order_items}

        # create edit window 
        edit_win = tk.Toplevel(self)
        edit_win.title(f"Edit Order #{order_id}")
        edit_win.geometry("750x770")
        edit_win.configure(bg=self.lavender)

        tk.Label(edit_win, text=f"Customer: {order_info['Customer_name']} (ID: {order_info['Customer_id']})",
            bg=self.lavender, font=("Arial", 12, "bold")).pack(pady=10)

        # treeview for order items
        columns = ("Item ID", "Item Name", "Quantity", "Unit Price", "Discount", "Total")
        tree = ttk.Treeview(edit_win, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=100)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        # insert existing items
        for item in order_items:
            total_price = item['Quantity'] * item['Unit_price'] * (1 - item['Item_discount'])
            tree.insert("", "end", values=(
                item['Item_id'], item['Name'], item['Quantity'], f"{item['Unit_price']:.2f}",
                f"{item['Item_discount']:.2%}", f"{total_price:.2f}"
        ))

        # add item form
        form_frame = tk.Frame(edit_win, bg=self.lavender)
        form_frame.pack(pady=5)

        tk.Label(form_frame, text="Select Item:", bg=self.lavender).grid(row=0, column=0, padx=5, sticky="e")
        item_var = tk.StringVar()
        item_dropdown = ttk.Combobox(form_frame, textvariable=item_var, width=40, state="readonly")
        item_dropdown.grid(row=0, column=1, columnspan=2, padx=5)

        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT Item_id, Name, Price_amount, Item_discount, Stock_quantity FROM Item ORDER BY Name ASC")
            available_items = cursor.fetchall()
            conn.close()

            item_map = {
                f"{name} (${price:.2f}) (ID: {item_id})": (item_id, name, price, stock, status)
                for item_id, name, price, stock, status in available_items
            }
            item_dropdown["values"] = list(item_map.keys())
        except mysql.connector.Error as err:
            messagebox.showerror("DB Error", f"Failed loading items: {err}")

        tk.Label(form_frame, text="Quantity:", bg=self.lavender).grid(row=0, column=3, padx=5, sticky="e")
        quantity_var = tk.StringVar(value="1")
        quantity_entry = tk.Entry(form_frame, textvariable=quantity_var, width=10)
        quantity_entry.grid(row=0, column=4, padx=5)

        def add_item():
            item_label = item_var.get()
            if item_label not in item_map:
                messagebox.showerror("Selection Error", "Please select a valid item.")
                return
            iid, name, price_amount, discount, stock = item_map[item_label]
            qty_str = quantity_var.get().strip()
            if not qty_str.isdigit() or int(qty_str) <= 0:
                messagebox.showwarning("Input Error", "Quantity must be a positive integer.")
                return
            qty = int(qty_str)

            # calculate current quantity in treeview
            current_qty = 0
            for child in tree.get_children():
                vals = tree.item(child, "values")
                if int(vals[0]) == iid:
                    current_qty = int(vals[2])
                    break

            if qty + current_qty > stock:
                messagebox.showerror("Stock Error", f"Only {stock} units in stock for {name}.")
                return

            # update quantity if exists, else add new row
            for child in tree.get_children():
                vals = tree.item(child, "values")
                if int(vals[0]) == iid:
                    new_qty = current_qty + qty
                    total_price = new_qty * price_amount * (1 - discount)
                    tree.item(child, values=(iid, name, new_qty, f"{price_amount:.2f}", f"{discount:.2%}", f"{total_price:.2f}"))
                    return

            # insert new item row
            total_price = qty * price_amount * (1 - discount)
            tree.insert("", "end", values=(iid, name, qty, f"{price_amount:.2f}", f"{discount:.2%}", f"{total_price:.2f}"))
            
        def remove_selected_item():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("No selection", "Please select an item to remove.")
                return
            tree.delete(selected)

        add_item_btn= tk.Button(form_frame, text="Add Item", command=add_item)
        add_item_btn.grid(row=0, column=5, padx=10)
        
        remove_item_btn= tk.Button(form_frame, text="Remove Item", command=remove_selected_item)
        remove_item_btn.grid(row=0, column=6, padx=10)


        # order details entries 
        budget_var = tk.StringVar(value=str(order_info['Budget']))
        deposit_var = tk.StringVar(value=str(order_info['Deposit']))
        discount_var = tk.StringVar(value=str(order_info['Order_discount']))
        payment_method_var = tk.StringVar(value=order_info.get('Payment_method', 'Cash'))
        status_var = tk.StringVar(value=order_info['Order_status'])
        confirmation_var = tk.BooleanVar(value=bool(order_info['Confirmation']))
        receiver_address_var = tk.StringVar(value=order_info.get('Receiver_address', ''))
        receiver_phone_var = tk.StringVar(value=order_info.get('Receiver_phone', ''))
        

        def create_labeled_entry(parent, label, var):
            tk.Label(parent, text=label, bg=self.lavender).pack(anchor="w", padx=10, pady=(5, 0))
            e = tk.Entry(parent, textvariable=var)
            e.pack(fill="x", padx=10)
            return e

        create_labeled_entry(edit_win, "Budget:", budget_var)
        create_labeled_entry(edit_win, "Deposit:", deposit_var)
        create_labeled_entry(edit_win, "Order Discount (%):", discount_var)
        create_labeled_entry(edit_win, "Receiver Address:", receiver_address_var)
        create_labeled_entry(edit_win, "Receiver Phone:", receiver_phone_var)

        # payment method dropdown
        tk.Label(edit_win, text="Payment Method:", bg=self.lavender).pack(anchor="w", padx=10, pady=(10, 0))
        payment_options = ["Cash", "Credit Card", "Whish", "OMT", "Bank Transfer", "Other"]
        payment_combo = ttk.Combobox(edit_win, textvariable=payment_method_var, values=payment_options, state="readonly")
        payment_combo.pack(fill="x", padx=10)

        # order status dropdown
        tk.Label(edit_win, text="Order Status:", bg=self.lavender).pack(anchor="w", padx=10, pady=(10, 0))
        status_options = ["Pending", "Processing", "Completed", "Cancelled"]
        status_combo = ttk.Combobox(edit_win, textvariable=status_var, values=status_options, state="readonly")
        status_combo.pack(fill="x", padx=10)

        # confirmation checkbox
        confirm_check = tk.Checkbutton(edit_win, text="Confirmed", variable=confirmation_var, bg=self.lavender)
        confirm_check.pack(pady=10)
        
        # If order is cancelled, disable editing
        if order_info['Order_status'] == "Cancelled":
            tree.configure(selectmode="none")  # Disable item selection in treeview
            for widget in edit_win.winfo_children():
                if isinstance(widget, tk.Entry) or isinstance(widget, ttk.Combobox):
                    widget.configure(state="disabled")
            confirm_check.configure(state="disabled")
            add_item_btn.configure(state="disabled")
            remove_item_btn.configure(state="disabled")
            tk.Label(edit_win, text="This order has been cancelled and cannot be edited.", 
                    fg="red", bg=self.lavender).pack(pady=10)

        # save edited order 
        def save_edit():
            try:
                
                def parse_float(value):
                    try:
                        return float(value.replace(',', '').strip())
                    except Exception:
                        raise ValueError("Invalid number format")
                
                budget = parse_float(budget_var.get())
                deposit = parse_float(deposit_var.get())
                order_discount = parse_float(discount_var.get())
                if not (0 <= order_discount <= 100):
                    messagebox.showerror("Input Error", "Discount must be between 0 and 100.")
                    return
                
            except ValueError:
                messagebox.showerror("Input Error", "Budget, Deposit, and Discount must be valid numbers.")
                return

            payment_method = payment_method_var.get()
            order_status = status_var.get()
            confirmation = confirmation_var.get()
            receiver_address = receiver_address_var.get()
            receiver_phone = receiver_phone_var.get()

            # collect updated items from treeview
            updated_items = []
            for child in tree.get_children():
                vals = tree.item(child, "values")
                iid = int(vals[0])
                qty = int(vals[2])
                unit_price = float(vals[3])
                discount = float(vals[4].strip('%')) / 100
                updated_items.append({"item_id": iid, "quantity": qty, "unit_price": unit_price, "discount": discount})

            # calculate total price after discount
            total_price = sum(item['quantity'] * item['unit_price'] * (1 - item['discount']) for item in updated_items)
            total_price_after_discount = total_price * (1 - (order_discount / 100))
            
                    
            try:
                conn = self.connect_db()
                cursor = conn.cursor()
                
                # get old total price and customer id before any updates
                cursor.execute("""
                    SELECT Total_price, Customer_id, Deposit
                    FROM Order_and_Payment WHERE Order_id = %s
                """, (order_id,))
                
                result= cursor.fetchone()
                if not result:
                    messagebox.showerror("Error", "Order not found for loyalty update.")
                    conn.close()
                    return 
                
                prev_total, customer_id, deposit_old= result
                
                old_loyalty_points = int(prev_total // 10) if deposit_old >= prev_total else 0
                
                # always subtract previously awarded loyalty points if any
                cursor.execute("""
                    UPDATE Customer 
                    SET Loyalty_points = GREATEST(Loyalty_points - %s, 0)
                    WHERE Customer_id = %s
                """, (old_loyalty_points, customer_id))

                
                # check if order was changed to "Cancelled"
                if order_status == "Cancelled":
                    
                    cursor.execute("SELECT Item_id, Quantity FROM Orders_Items WHERE Order_id = %s", (order_id,))
                    
                    for item_id, qty in cursor.fetchall():
                        cursor.execute("UPDATE Item SET Stock_quantity = Stock_quantity + %s WHERE Item_id = %s", (qty, item_id))

                    #cursor.execute("DELETE FROM Orders_Items WHERE Order_id = %s", (order_id,))
                    
                    cursor.execute("""
                        UPDATE Order_and_Payment
                        SET Budget=%s, Deposit=%s, Order_discount=%s, Payment_method=%s,
                            Order_status=%s, Confirmation=%s, Receiver_address=%s, Receiver_phone=%s,
                            Total_price = 0
                        WHERE Order_id = %s
                    """, (budget, deposit, order_discount, payment_method, order_status, int(confirmation),
                        receiver_address, receiver_phone, order_id))
                    
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("Order Cancelled", "Order cancelled and reverted successfully.")
                    
                    edit_win.destroy()
                    self.load_orders()
            
                    return
                    
                # update order info
                cursor.execute("""
                    UPDATE Order_and_Payment
                    SET Budget=%s, Deposit=%s, Order_discount=%s, Payment_method=%s,
                        Order_status=%s, Confirmation=%s, Receiver_address=%s, Receiver_phone=%s
                    WHERE Order_id= %s
                """, (budget, deposit, order_discount, payment_method,
                    order_status, int(confirmation), receiver_address, receiver_phone, order_id))
                
                cursor.execute("SELECT Item_id, Quantity FROM Orders_Items WHERE Order_id = %s", (order_id,))
                original = {iid: qty for iid, qty in cursor.fetchall()}

                updated = {item['item_id']: item for item in updated_items}
                
                # adjust stock and Orders_Items
                for iid in set(original) | set(updated):
                    old_qty = original.get(iid, 0)
                    new_qty = updated.get(iid, {}).get("quantity", 0)
                    diff = new_qty - old_qty
                    if diff != 0:
                        cursor.execute("UPDATE Item SET Stock_quantity = Stock_quantity - %s WHERE Item_id = %s", (diff, iid))

                    if old_qty and not new_qty:
                        cursor.execute("DELETE FROM Orders_Items WHERE Order_id = %s AND Item_id = %s", (order_id, iid))
                    elif new_qty and not old_qty:
                        data = updated[iid]
                        cursor.execute("""
                            INSERT INTO Orders_Items (Order_id, Item_id, Quantity, Unit_price)
                            VALUES (%s, %s, %s, %s)
                        """, (order_id, iid, data['quantity'], data['unit_price']))
                    elif old_qty and new_qty:
                        cursor.execute("""
                            UPDATE Orders_Items SET Quantity = %s WHERE Order_id = %s AND Item_id = %s
                        """, (new_qty, order_id, iid))
                        
                # loyalty points (only if fully paid)
                
                if int(confirmation) == 1 and deposit >= total_price_after_discount:
                    new_points = int(total_price_after_discount // 10)
                    cursor.execute("UPDATE Customer SET Loyalty_points = Loyalty_points + %s WHERE Customer_id = %s",
                           (new_points, customer_id))

                cursor.execute("UPDATE Order_and_Payment SET Total_price = %s WHERE Order_id = %s",
                       (total_price_after_discount, order_id))

                conn.commit()
                conn.close()

                messagebox.showinfo("Success", f"Order #{order_id} updated successfully!")
                edit_win.destroy()
                self.load_orders()


            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Database error: {err}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(edit_win, text="Save Changes", command=save_edit).pack(pady=20)

    def show_order_details(self, order_id):
        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            # Get order and customer details
            cursor.execute("""
                SELECT o.Order_id, o.Customer_id, o.Employee_id, o.Order_status, o.Order_discount, o.Payment_date,
                       o.Payment_method, o.Budget, o.Deposit, o.Receiver_address, o.Receiver_phone, o.Confirmation,
                       c.Name, c.Phone, c.Loyalty_points
                FROM Order_and_Payment o
                JOIN Customer c ON o.Customer_id = c.Customer_id
                WHERE o.Order_id = %s
            """, (order_id,))
            order_customer = cursor.fetchone()

            if not order_customer:
                messagebox.showerror("Error", f"No details found for order {order_id}")
                return

            # Get order items details
            cursor.execute("""
                SELECT i.Name, oi.Quantity, oi.Unit_price, i.Item_discount
                FROM Orders_Items oi
                JOIN Item i ON oi.Item_id = i.Item_id
                WHERE oi.Order_id = %s
            """, (order_id,))
            items = cursor.fetchall()

            conn.close()

            # Create a new window to show details
            detail_win = tk.Toplevel(self)
            detail_win.title(f"Order Details - ID {order_id}")
            detail_win.geometry("700x500")
            detail_win.configure(bg=self.lavender)

            # Display customer and order info
            labels = [
                ("Order ID", order_customer[0]),
                ("Customer ID", order_customer[1]),
                ("Employee ID", order_customer[2]),
                ("Order Status", order_customer[3]),
                ("Order Discount", order_customer[4]),
                ("Payment Date", order_customer[5]),
                ("Payment Method", order_customer[6]),
                ("Budget", order_customer[7]),
                ("Deposit", order_customer[8]),
                ("Receiver Address", order_customer[9]),
                ("Receiver Phone", order_customer[10]),
                ("Confirmation", "Yes" if order_customer[11] else "No"),
                ("Customer Name", order_customer[12]),
                ("Customer Phone", order_customer[13]),
                ("Loyalty Points", order_customer[14])
            ]

            row = 0
            for label, value in labels:
                tk.Label(detail_win, text=f"{label}:", bg=self.lavender, anchor="w", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", padx=10, pady=2)
                tk.Label(detail_win, text=str(value), bg=self.lavender, anchor="w", font=("Arial", 10)).grid(row=row, column=1, sticky="w", padx=10, pady=2)
                row += 1

            # Separator
            ttk.Separator(detail_win, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
            row += 1

            # Items Label
            tk.Label(detail_win, text="Ordered Items:", bg=self.lavender, font=("Arial", 11, "bold")).grid(row=row, column=0, sticky="w", padx=10)
            row += 1

            # Items Treeview
            columns = ("Item Name", "Quantity", "Unit Price", "Item Discount", "Total Price")
            tree = ttk.Treeview(detail_win, columns=columns, show="headings", height=8)
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor="center", width=120)
            tree.grid(row=row, column=0, columnspan=2, sticky="nsew", padx=10)

            # Insert item data
            for item in items:
                name, qty, unit_price, discount = item
                total = qty * unit_price * (1 - discount)
                tree.insert("", "end", values=(name, qty, f"{unit_price:.2f}", f"{discount:.2%}", f"{total:.2f}"))

            detail_win.grid_rowconfigure(row, weight=1)
            detail_win.grid_columnconfigure(1, weight=1)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")



# For testing standalone:
if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "Root",  
        "database": "flowershop_management"
    }

    root = tk.Tk()
    root.title("Flower Shop Management - Orders")
    root.geometry("1100x500")
    order_view = OrderView(root, db_config)
    order_view.pack(fill="both", expand=True)
    root.mainloop()
