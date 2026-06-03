USE garage_db;
INSERT INTO `user` (username, password, role, full_name, phone) VALUES
('owner1', 'password', 'owner', 'Aarav Mehta', '9876500001'),
('manager1', 'password', 'manager', 'Riya Sharma', '9876500002'),
('reception1','password', 'receptionist', 'Neha Verma', '9876500003'),
('mechanic1', 'password', 'mechanic', 'Kabir Singh', '9876500004'),
('mechanic2', 'password', 'mechanic', 'Arjun Rao', '9876500005'),
('mechanic3','password', 'mechanic', 'Dev Malhotra', '9876500006'),
('mechanic4', 'password', 'mechanic', 'Rohan Kulkarni', '9876500007');
INSERT INTO customer (full_name, phone, email, address) VALUES
('Rahul Nair', '9001001001', 'rahul.nair@example.com', 'MG Road, Bengaluru'),
('Pooja Iyer', '9001001002', 'pooja.iyer@example.com', 'Anna Nagar, Chennai'),
('Vikram Das', '9001001003', 'vikram.das@example.com', 'Salt Lake, Kolkata'),
('Sneha Kapoor', '9001001004', 'sneha.kapoor@example.com', 'Andheri, Mumbai'),
('Aditya Menon', '9001001005', 'aditya.menon@example.com', 'Kakkanad, Kochi'),
('Meera Joshi', '9001001006', 'meera.joshi@example.com', 'Banjara Hills, Hyderabad'),
('Karthik Reddy', '9001001007', 'karthik.reddy@example.com', 'Whitefield, Bengaluru');
INSERT INTO supplier (supplier_name, contact_person, phone, email) VALUES
('AutoCare Supplies', 'Sanjay Patel', '9011100001', 'sales@autocare.example'),
('Prime Parts Hub', 'Meera Joseph', '9011100002', 'orders@primeparts.example'),
('SpeedX Components', 'Rohit Sharma', '9011100003', 'support@speedx.example'),
('Elite Auto Parts', 'Anjali Nair', '9011100004', 'elite@autoparts.example'),
('Turbo Garage Supplies', 'Vivek Rao', '9011100005', 'contact@turbo.example'),
('DrivePro Distributors', 'Amit Verma', '9011100006', 'sales@drivepro.example'),
('MotoTech India', 'Kiran Das', '9011100007', 'info@mototech.example');
INSERT INTO vehicle (
    customer_id, registration_no, make, model,
    manufacture_year, mileage
) VALUES
(1, 'KA01AB1234', 'Hyundai', 'i20', 2021, 38500),
(2, 'TN10CD5678', 'Honda', 'City', 2019, 52200),
(3, 'WB08EF9012', 'Maruti Suzuki', 'Baleno', 2022, 18800),
(4, 'MH12GH3456', 'Toyota', 'Innova', 2020, 64100),
(5, 'KL07JK7890', 'Kia', 'Seltos', 2023, 11200),
(6, 'TS09LM2468', 'Mahindra', 'XUV700', 2022, 27600),
(7, 'KA05NP1357', 'Tata', 'Nexon', 2021, 33400);
INSERT INTO spare_part (
    supplier_id, part_name, part_number, category,
    quantity_in_stock, reorder_level,
    unit_cost, selling_price
) VALUES
(1, 'Engine Oil 5W30', 'EO-5W30-001', 'Lubricants', 24, 10, 650.00, 900.00),
(1, 'Air Filter', 'AF-1120', 'Filters', 6, 8, 220.00, 380.00),
(2, 'Brake Pad Set', 'BP-7788', 'Brakes', 12, 5, 1200.00, 1750.00),
(2, 'Spark Plug', 'SP-4321', 'Ignition', 18, 7, 180.00, 320.00),
(3, 'Coolant', 'CL-9090', 'Cooling', 15, 5, 300.00, 500.00),
(4, 'Battery 12V', 'BT-5656', 'Electrical', 8, 3, 4200.00, 5600.00),
(5, 'Clutch Plate', 'CP-8787', 'Transmission', 5, 2, 2500.00, 3400.00);
INSERT INTO service_job (
    vehicle_id, customer_id, user_id,
    job_date, complaint, diagnosis,
    parts_used, labour_charge, status
) VALUES(
    1, 1, 4, CURDATE(),
    'Engine noise during acceleration',
    'Recommended oil change and air filter replacement',
    '[{"part_id":1,"part_name":"Engine Oil 5W30","quantity":1,"unit_price":900.0,"line_total":900.0}]',
    1200.00,
    'Completed'
),(
    2, 2, 5, CURDATE(),
    'Brake vibration issue',
    'Brake pads worn out and replaced',
    '[{"part_id":3,"part_name":"Brake Pad Set","quantity":1,"unit_price":1750.0,"line_total":1750.0}]',
    1500.00,
    'Completed'
),(
    3, 3, 6, CURDATE(),
    'Engine misfire',
    'Spark plugs replaced',
    '[{"part_id":4,"part_name":"Spark Plug","quantity":4,"unit_price":320.0,"line_total":1280.0}]',
    1000.00,
    'In Progress'
),(
    4, 4, 7, CURDATE(),
    'Overheating issue',
    'Coolant leakage fixed and coolant replaced',
    '[{"part_id":5,"part_name":"Coolant","quantity":2,"unit_price":500.0,"line_total":1000.0}]',
    1800.00,
    'Completed'
),(
    5, 5, 4, CURDATE(),
    'Battery draining quickly',
    'Battery replaced',
    '[{"part_id":6,"part_name":"Battery 12V","quantity":1,"unit_price":5600.0,"line_total":5600.0}]',
    900.00,
    'Pending'
),(
    6, 6, 5, CURDATE(),
    'Clutch slipping',
    'Clutch plate replaced',
    '[{"part_id":7,"part_name":"Clutch Plate","quantity":1,"unit_price":3400.0,"line_total":3400.0}]',
    2200.00,
    'Completed'
),(
    7, 7, 6, CURDATE(),
    'Regular vehicle servicing',
    'General inspection and oil service completed',
    '[{"part_id":1,"part_name":"Engine Oil 5W30","quantity":1,"unit_price":900.0,"line_total":900.0}]',
    800.00,
    'Completed'
);
INSERT INTO invoice (
    job_id, customer_id, invoice_date,
    labour_total, parts_total,
    grand_total, payment_status,
    payment_method
) VALUES
(1, 1, CURDATE(), 1200.00, 900.00, 2100.00, 'Unpaid', 'UPI'),
(2, 2, CURDATE(), 1500.00, 1750.00, 3250.00, 'Paid', 'Card'),
(3, 3, CURDATE(), 1000.00, 1280.00, 2280.00, 'Partially Paid', 'Cash'),
(4, 4, CURDATE(), 1800.00, 1000.00, 2800.00, 'Paid', 'UPI'),
(5, 5, CURDATE(), 900.00, 5600.00, 6500.00, 'Unpaid', 'Cash'),
(6, 6, CURDATE(), 2200.00, 3400.00, 5600.00, 'Partially Paid', 'Cash'),
(7, 7, CURDATE(), 800.00, 900.00, 1700.00, 'Paid', 'UPI');