CREATE DATABASE IF NOT EXISTS garage_db;
USE garage_db;

CREATE TABLE IF NOT EXISTS `user` (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('owner', 'manager', 'mechanic', 'receptionist') NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    address VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS supplier (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS vehicle (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    registration_no VARCHAR(30) NOT NULL UNIQUE,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    manufacture_year INT NOT NULL,
    mileage INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_vehicle_customer
        FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS spare_part (
    part_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    part_name VARCHAR(100) NOT NULL,
    part_number VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(50),
    quantity_in_stock INT NOT NULL DEFAULT 0,
    reorder_level INT NOT NULL DEFAULT 0,
    unit_cost DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    selling_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    CONSTRAINT fk_part_supplier
        FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS service_job (
    job_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    customer_id INT NOT NULL,
    user_id INT NOT NULL,
    job_date DATE NOT NULL,
    complaint TEXT NOT NULL,
    diagnosis TEXT,
    parts_used LONGTEXT,
    labour_charge DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    status ENUM('Pending', 'In Progress', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Pending',
    CONSTRAINT fk_job_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_job_customer
        FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_job_user
        FOREIGN KEY (user_id) REFERENCES `user`(user_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS invoice (
    invoice_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL UNIQUE,
    customer_id INT NOT NULL,
    invoice_date DATE NOT NULL,
    labour_total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    parts_total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    grand_total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    payment_status ENUM('Unpaid', 'Partially Paid', 'Paid') NOT NULL DEFAULT 'Unpaid',
    payment_method ENUM('Cash', 'Card', 'UPI', 'Bank Transfer') NOT NULL DEFAULT 'Cash',
    CONSTRAINT fk_invoice_job
        FOREIGN KEY (job_id) REFERENCES service_job(job_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_invoice_customer
        FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
        ON DELETE RESTRICT
);
