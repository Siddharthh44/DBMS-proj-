-- ========================================================
-- ADVANCED DATABASE CONCEPTS: TRIGGERS & PROCEDURES
-- Fender - Automobile Garage Management System
-- ========================================================
-- This script defines:
-- 1. A lightweight table `db_log` for auditing trigger executions.
-- 2. Three real, functional AFTER/BEFORE triggers for auditing.
-- 3. Two cursor-based stored procedures showing loop iterations.
-- ========================================================

USE garage_db;

-- --------------------------------------------------------
-- TABLE: db_log (Lightweight auditing table)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS db_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    log_type VARCHAR(50) NOT NULL, -- e.g., 'JOB_COMPLETION', 'LOW_STOCK', 'INVOICE_GENERATED'
    message TEXT NOT NULL
);

-- --------------------------------------------------------
-- TRIGGER 1: trg_job_completion_audit (AFTER UPDATE)
-- Fired when a job status is updated to 'Completed'
-- --------------------------------------------------------
DROP TRIGGER IF EXISTS trg_job_completion_audit;
DELIMITER //
CREATE TRIGGER trg_job_completion_audit
AFTER UPDATE ON service_job
FOR EACH ROW
BEGIN
    IF OLD.status <> 'Completed' AND NEW.status = 'Completed' THEN
        INSERT INTO db_log (log_type, message)
        VALUES (
            'JOB_COMPLETION', 
            CONCAT('Service Job #', NEW.job_id, ' completed. Labour charge: ₹', NEW.labour_charge, '. Assigned mechanic ID: ', NEW.user_id)
        );
    END IF;
END //
DELIMITER ;

-- --------------------------------------------------------
-- TRIGGER 2: trg_low_stock_alert (AFTER UPDATE)
-- Fired when a spare part quantity falls below/at safety level
-- --------------------------------------------------------
DROP TRIGGER IF EXISTS trg_low_stock_alert;
DELIMITER //
CREATE TRIGGER trg_low_stock_alert
AFTER UPDATE ON spare_part
FOR EACH ROW
BEGIN
    IF NEW.quantity_in_stock <= NEW.reorder_level AND OLD.quantity_in_stock > NEW.reorder_level THEN
        INSERT INTO db_log (log_type, message)
        VALUES (
            'LOW_STOCK', 
            CONCAT('Warning: Spare part "', NEW.part_name, '" (Part #', NEW.part_number, ') has reached a low-stock level! Available: ', NEW.quantity_in_stock, ' units (Reorder level: ', NEW.reorder_level, ').')
        );
    END IF;
END //
DELIMITER ;

-- --------------------------------------------------------
-- TRIGGER 3: trg_invoice_insert_audit (AFTER INSERT)
-- Fired when a new invoice is created on job completion
-- --------------------------------------------------------
DROP TRIGGER IF EXISTS trg_invoice_insert_audit;
DELIMITER //
CREATE TRIGGER trg_invoice_insert_audit
AFTER INSERT ON invoice
FOR EACH ROW
BEGIN
    INSERT INTO db_log (log_type, message)
    VALUES (
        'INVOICE_GENERATED', 
        CONCAT('Invoice generated. Invoice ID: #', NEW.invoice_id, ' for Service Job #', NEW.job_id, '. Grand total billing: ₹', NEW.grand_total, '.')
    );
END //
DELIMITER ;

-- --------------------------------------------------------
-- STORED PROCEDURE 1: get_monthly_revenue_summary (CURSOR-BASED)
-- Aggregates paid invoice grand totals using cursor loops
-- --------------------------------------------------------
DROP PROCEDURE IF EXISTS get_monthly_revenue_summary;
DELIMITER //
CREATE PROCEDURE get_monthly_revenue_summary(OUT total_sales DECIMAL(10,2), OUT invoice_count INT)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE inv_amount DECIMAL(10,2);
    DECLARE cur_sales DECIMAL(10,2) DEFAULT 0.00;
    DECLARE cur_count INT DEFAULT 0;
    
    -- Declare the cursor for paid invoices
    DECLARE inv_cursor CURSOR FOR 
        SELECT grand_total FROM invoice WHERE payment_status = 'Paid'
        AND MONTH(invoice_date) = MONTH(CURDATE())
        AND YEAR(invoice_date) = YEAR(CURDATE());
        
    -- Declare continue handler for cursor exhaustion
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN inv_cursor;
    
    read_loop: LOOP
        FETCH inv_cursor INTO inv_amount;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        SET cur_sales = cur_sales + inv_amount;
        SET cur_count = cur_count + 1;
    END LOOP;
    
    CLOSE inv_cursor;
    
    SET total_sales = cur_sales;
    SET invoice_count = cur_count;
END //
DELIMITER ;

-- --------------------------------------------------------
-- STORED PROCEDURE 2: get_low_stock_report (CURSOR-BASED)
-- Compiles a formatted multi-line low-stock report string using cursor loops
-- --------------------------------------------------------
DROP PROCEDURE IF EXISTS get_low_stock_report;
DELIMITER //
CREATE PROCEDURE get_low_stock_report(OUT report_out TEXT)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE p_name VARCHAR(100);
    DECLARE p_qty INT;
    DECLARE p_reorder INT;
    DECLARE report_text TEXT DEFAULT 'LOW STOCK INVENTORY REPORT:\n===========================\n';
    DECLARE found_any INT DEFAULT 0;
    
    -- Declare cursor for parts that are at or below reorder level
    DECLARE parts_cursor CURSOR FOR 
        SELECT part_name, quantity_in_stock, reorder_level 
        FROM spare_part 
        WHERE quantity_in_stock <= reorder_level;
        
    -- Declare continue handler for cursor exhaustion
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN parts_cursor;
    
    read_loop: LOOP
        FETCH parts_cursor INTO p_name, p_qty, p_reorder;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        SET report_text = CONCAT(report_text, '- ', p_name, ': ', p_qty, ' units left (Reorder safety: ', p_reorder, ')\n');
        SET found_any = found_any + 1;
    END LOOP;
    
    CLOSE parts_cursor;
    
    IF found_any = 0 THEN
        SET report_text = CONCAT(report_text, 'All spare parts are currently above reorder limits.\n');
    END IF;
    
    SET report_out = report_text;
END //
DELIMITER ;
