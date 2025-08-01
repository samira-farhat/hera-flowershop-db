DROP DATABASE IF EXISTS flowershop_management;
CREATE DATABASE flowershop_management;
USE flowershop_management;

CREATE TABLE Item (
    Item_id INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100),
    Type VARCHAR(50),
    Arrival_date DATE,
    Item_discount DECIMAL(5,2),
    Price_amount DECIMAL(10,2),
    Price_date DATE,
    Stock_quantity INT DEFAULT 0
);

CREATE TABLE Customer (
    Customer_id INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100),
    Phone VARCHAR(20),
    Loyalty_points INT DEFAULT 0
);

CREATE TABLE Supplier (
    Supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100),
    Contact VARCHAR(100)
);

CREATE TABLE Employee (
    Employee_id INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100),
    Contact_info VARCHAR(100),
    Position VARCHAR(50),
    Salary DECIMAL(10,2),
    Yearly_bonus DECIMAL(10,2)
);

CREATE TABLE Order_and_Payment (
    Order_id INT AUTO_INCREMENT PRIMARY KEY,
    Customer_id INT,
    Employee_id INT,
    Order_status VARCHAR(50),
    Order_discount DECIMAL(5,2),
    Payment_date DATE,
    Payment_method VARCHAR(50),
    Amount_paid DECIMAL(10,2),
    Deposit DECIMAL(10,2),
    Budget DECIMAL(10,2),
    Receiver_address VARCHAR(200),
    Receiver_phone VARCHAR(20),
    Confirmation BOOLEAN,
    FOREIGN KEY (Customer_id) REFERENCES Customer(Customer_id),
    FOREIGN KEY (Employee_id) REFERENCES Employee(Employee_id)
);

CREATE TABLE Delivery (
    Delivery_id INT AUTO_INCREMENT PRIMARY KEY,
    Order_id INT,
    Employee_id INT,
    Delivery_date DATE,
    Delivery_time TIME,
    FOREIGN KEY (Order_id) REFERENCES Order_and_Payment(Order_id),
    FOREIGN KEY (Employee_id) REFERENCES Employee(Employee_id)
);

CREATE TABLE Item_Supplier (
    Item_id INT,
    Supplier_id INT,
    PRIMARY KEY (Item_id, Supplier_id),
    FOREIGN KEY (Item_id) REFERENCES Item(Item_id),
    FOREIGN KEY (Supplier_id) REFERENCES Supplier(Supplier_id)
);

CREATE TABLE Orders_Items (
    Order_id INT,
    Item_id INT,
    Quantity INT,
    Unit_price DECIMAL(10,2),
    PRIMARY KEY (Order_id, Item_id),
    FOREIGN KEY (Order_id) REFERENCES Order_and_Payment(Order_id),
    FOREIGN KEY (Item_id) REFERENCES Item(Item_id)
);





