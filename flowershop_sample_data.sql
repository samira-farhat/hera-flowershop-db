-- Insert Items
INSERT INTO Item (Name, Type, Arrival_date, Item_discount, Price_amount, Price_date, Stock_quantity) VALUES
('Red Roses', 'Flower', '2025-04-01', 0.10, 5.99, '2025-04-01', 50),
('White Lilies', 'Flower', '2025-04-05', 0.15, 6.49, '2025-04-05', 40),
('Sunflowers', 'Flower', '2025-04-07', 0.05, 4.99, '2025-04-07', 30),
('Glass Vase', 'Product', '2025-04-03', 0.00, 12.99, '2025-04-03', 20),
('Greeting Card', 'Product', '2025-04-02', 0.20, 2.50, '2025-04-02', 100);

-- Insert Customers
INSERT INTO Customer (Name, Phone, Loyalty_points) VALUES
('Lana Rose', '789456123', 20),
('Sara White', '741852963', 10),
('James Black', '951753852', 35),
('Maya Blue', '321654987', 5),
('Leo Brown', '852963741', 50);

-- Insert Suppliers
INSERT INTO Supplier (Name, Contact) VALUES
('Bloom Supply Co.', '123456789'),
('Petal Partners', '111222333'),
('GreenThumb Goods', '444555666'),
('Sweet Delights Co.', '777888999'),
('Pottery World', '000123456');

-- Insert Employees
INSERT INTO Employee (Name, Contact_info, Position, Salary, Yearly_bonus) VALUES
('Omar Green', '987654321', 'Delivery', 4000.00, 500.00),
('Sara Bloom', '555123456', 'Florist', 3200.00, 300.00),
('Daniel Petal', '555987654', 'Cashier', 2800.00, 200.00),
('Nadine Leaf', '555654321', 'Manager', 5000.00, 800.00);

-- Insert Orders (Order_discount as percent or amount?)
INSERT INTO Order_and_Payment (Customer_id, Employee_id, Order_status, Order_discount, Payment_date, Payment_method, Amount_paid, Deposit, Budget, Receiver_address, Receiver_phone, Confirmation) VALUES
(1, 1, 'Pending', 10.00, '2025-05-01', 'Cash', 70.00, 30.00, 100.00, '123 Flower St', '123123123', TRUE),
(2, 1, 'Pending', 5.00, '2025-05-05', 'Credit Card', 50.00, 10.00, 60.00, '456 Rose Ave', '9876543210', TRUE);

-- Insert Deliveries
INSERT INTO Delivery (Order_id, Employee_id, Delivery_date, Delivery_time) VALUES
(1, 1, '2025-05-01', '10:00:00'),
(2, 2, '2025-05-05', '14:00:00');

-- Insert Item_Supplier relationships (assuming IDs start from 1)
INSERT INTO Item_Supplier (Item_id, Supplier_id) VALUES
(1, 1),
(1, 2),
(2, 2),
(3, 3),
(4, 4),
(5, 5);

-- Insert Orders_Items (linking orders and items, with quantities and unit prices)
INSERT INTO Orders_Items (Order_id, Item_id, Quantity, Unit_price) VALUES
(1, 1, 5, 5.99),
(1, 2, 3, 6.49),
(2, 3, 2, 4.99),
(2, 5, 1, 2.50);
