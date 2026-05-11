USE garage_db;

INSERT INTO `user` (username, password, role, full_name, phone) VALUES
('owner1', 'scrypt:32768:8:1$J0PC9qtEL892mGaH$c316a70f8d78033b16a43610baabd8916e793b2c03fff79e2522e4ef3b1f1d6eeabb0afa170059e6268763b5b1a807ac18cf817781c754151b22bbb707606bcc', 'owner', 'Aarav Mehta', '9876500001'),
('manager1', 'scrypt:32768:8:1$yPqliYWgONJTkPOK$0eb73503d9dfd9c02f472700ecd962c70fa1e9ba681f83ca21ee52932d89d5204c3072c61b8f9f16f98d14b3145b5601bbb2fd563f43390b96bf8175d35c5db7', 'manager', 'Riya Sharma', '9876500002'),
('mechanic1', 'scrypt:32768:8:1$y8KP1QF0S09d3i6v$9a9a655b1e073317ccef95182532b12d7322f672ef8574e0be8d7518852df91502a1a073a62e579913b2d73e373f3ac0f09ce62e4ba1f3b16a8ce978ddf825f8', 'mechanic', 'Kabir Singh', '9876500003'),
('reception1', 'scrypt:32768:8:1$X7xiOBKnZyPGJeS5$f734c5db18b89ca5a66f2ea6b9012604d290bfc01f92c5149c67d91f8d3a57d85cde895a7e268dddcc5d90f5850efc4a70a9d487b56218222d720a0097a6aee4', 'receptionist', 'Neha Verma', '9876500004');

INSERT INTO customer (full_name, phone, email, address) VALUES
('Rahul Nair', '9001001001', 'rahul.nair@example.com', 'MG Road, Bengaluru'),
('Pooja Iyer', '9001001002', 'pooja.iyer@example.com', 'Anna Nagar, Chennai'),
('Vikram Das', '9001001003', 'vikram.das@example.com', 'Salt Lake, Kolkata');

INSERT INTO supplier (supplier_name, contact_person, phone, email) VALUES
('AutoCare Supplies', 'Sanjay Patel', '9011100001', 'sales@autocare.example'),
('Prime Parts Hub', 'Meera Joseph', '9011100002', 'orders@primeparts.example');

INSERT INTO vehicle (customer_id, registration_no, make, model, manufacture_yr, mileage) VALUES
(1, 'KA01AB1234', 'Hyundai', 'i20', 2021, 38500),
(2, 'TN10CD5678', 'Honda', 'City', 2019, 52200),
(3, 'WB08EF9012', 'Maruti Suzuki', 'Baleno', 2022, 18800);

INSERT INTO spare_part (
    supplier_id, part_name, part_number, category,
    quantity_in_stock, reorder_level, unit_cost, selling_price
) VALUES
(1, 'Engine Oil 5W30', 'EO-5W30-001', 'Lubricants', 24, 10, 650.00, 900.00),
(1, 'Air Filter', 'AF-1120', 'Filters', 6, 8, 220.00, 380.00),
(2, 'Brake Pad Set', 'BP-7788', 'Brakes', 12, 5, 1200.00, 1750.00),
(2, 'Spark Plug', 'SP-4321', 'Ignition', 18, 7, 180.00, 320.00);

INSERT INTO service_job (
    vehicle_id, customer_id, user_id, job_date, complaint, diagnosis,
    parts_used, labour_charge, status
) VALUES
(
    1, 1, 3, CURDATE(),
    'Engine noise during acceleration',
    'Recommended oil change and air filter replacement',
    '[{"part_id":1,"part_name":"Engine Oil 5W30","quantity":1,"unit_price":900.0,"line_total":900.0},{"part_id":2,"part_name":"Air Filter","quantity":1,"unit_price":380.0,"line_total":380.0}]',
    1200.00,
    'Completed'
);

INSERT INTO invoice (
    job_id, customer_id, invoice_date, labour_total, parts_total,
    grand_total, payment_status, payment_method
) VALUES
(1, 1, CURDATE(), 1200.00, 1280.00, 2480.00, 'Paid', 'UPI');
