import tkinter as tk
from PIL import Image, ImageTk  
from items_view import ItemView
from customers_view import CustomerView
from suppliers_view import SupplierView
from orders_view import OrderView


class HERAGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HERA Database")
        self.root.state('zoomed')  # Fullscreen
        self.root.configure(bg="black")

        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "Root",
            "database": "flowershop_management"
        }

        # === Colors ===
        self.lavender = "#B593BB"
        self.lavender_dark = "#9a7fb5"
        self.bg_black = "black"
        self.active_bg = "#A0799F"
        self.inactive_bg = self.lavender

        # === Sidebar Frame ===
        self.sidebar = tk.Frame(root, bg=self.lavender, width=300)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # === Load and display logo image ===
        self.load_logo()

        # === Main Content Area ===
        self.content = tk.Frame(root, bg=self.bg_black)
        self.content.pack(side="right", expand=True, fill="both")

        # === Sidebar Buttons ===
        self.buttons = {}  # to keep references to buttons

        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Items", self.show_items),
            ("Customers", self.show_customers),
            ("Suppliers", self.show_suppliers),
            ("Orders", self.show_orders),
            ("Exit", root.quit)
        ]

        for text, command in buttons:
            btn = tk.Button(
                self.sidebar,
                text=text,
                font=("Arial", 18, "bold"),
                fg="black",
                bg=self.inactive_bg,
                bd=0,
                activebackground=self.active_bg,
                command=lambda c=command, b=text: self.on_button_click(c, b)
            )
            btn.pack(fill="x", pady=10, padx=10)
            self.buttons[text] = btn

        self.active_button = None
        self.on_button_click(self.show_dashboard, "Dashboard")  # Default selection

    def load_logo(self):
        # Open the image using PIL
        image = Image.open("assets/logo.jpeg")

        # Resize the image to fit nicely (e.g., 150x150)
        image = image.resize((250, 200), Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        self.logo_img = ImageTk.PhotoImage(image)

        # Create a label for the logo and pack it on the sidebar top
        logo_label = tk.Label(self.sidebar, image=self.logo_img, bg=self.lavender)
        logo_label.pack(pady=20)

    def on_button_click(self, command, button_text):
        # Reset all buttons to inactive bg
        for btn in self.buttons.values():
            btn.config(bg=self.inactive_bg)

        # Highlight the clicked button
        self.buttons[button_text].config(bg=self.active_bg)

        # Run the associated command to show content
        command()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_content()
        tk.Label(self.content, text="Welcome to HERA Database",
                 font=("Arial", 24), fg=self.lavender, bg=self.bg_black).place(relx=0.5, rely=0.5, anchor="center")

    def show_items(self):
        self.clear_content()
        self.items_view = ItemView(self.content, self.db_config)
        self.items_view.pack(fill="both", expand=True)
        
    def show_customers(self):
        self.clear_content()
        self.customers_view = CustomerView(self.content, self.db_config)
        self.customers_view.pack(fill="both", expand=True)
        
    def show_suppliers(self):
        self.clear_content()
        self.suppliers_view = SupplierView(self.content, self.db_config)
        self.suppliers_view.pack(fill="both", expand=True)
        
    def show_orders(self):
        self.clear_content()
        self.orders_view = OrderView(self.content, self.db_config)
        self.orders_view.pack(fill="both", expand=True)
        

    def placeholder(self):
        self.clear_content()
        tk.Label(self.content, text="Section coming soon...",
                 font=("Arial", 20), fg=self.lavender, bg=self.bg_black).place(relx=0.5, rely=0.5, anchor="center")


if __name__ == "__main__":
    root = tk.Tk()
    app = HERAGUI(root)
    root.mainloop()
