import os
import datetime
import logging
import mysql.connector
from mysql.connector import pooling

# Read database credentials from environment variables with safe defaults
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_NAME = os.environ.get("DB_NAME", "garage_db")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

db_config = {
    "host": DB_HOST,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "port": DB_PORT
}

# Safely create logs directory
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(LOGS_DIR):
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
    except Exception as e:
        pass

# Initialize dedicated DB Logger
db_logger = logging.getLogger("db_activity")
db_logger.setLevel(logging.INFO)
if db_logger.handlers:
    db_logger.handlers.clear()

log_file_path = os.path.join(LOGS_DIR, "db_logs.log")
try:
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    db_logger.addHandler(file_handler)
except Exception as e:
    print(f"Warning: Failed to create FileHandler for database logging: {e}")

# Create connection pool
db_pool = None
try:
    db_pool = pooling.MySQLConnectionPool(
        pool_name="fender_pool",
        pool_size=5,
        pool_reset_session=True,
        **db_config
    )
    print("Database Connection Pool initialized successfully.")
except mysql.connector.Error as err:
    print(f"CRITICAL Warning: Failed to create database connection pool. Error: {err}")
    print("Verify that MySQL is running and your connection details are correct.")


# ==========================================
# SQL Logging & Snapshot Activity Utility
# ==========================================

def detect_table_and_action(query):
    """Utility function to parse table name and action from SQL queries."""
    query_clean = " ".join(query.strip().split())
    query_upper = query_clean.upper()
    action = "UNKNOWN"
    table = "UNKNOWN"
    
    if query_upper.startswith("INSERT"):
        action = "INSERT"
        parts = query_clean.split()
        for i, p in enumerate(parts):
            if p.upper() in ["INTO", "INSERT"]:
                if i + 1 < len(parts):
                    next_val = parts[i+1].strip("`()").split("(")[0]
                    if next_val.upper() != "INTO":
                        table = next_val
                        break
                    elif i + 2 < len(parts):
                        table = parts[i+2].strip("`()").split("(")[0]
                        break
    elif query_upper.startswith("UPDATE"):
        action = "UPDATE"
        parts = query_clean.split()
        for i, p in enumerate(parts):
            if p.upper() == "UPDATE" and i + 1 < len(parts):
                table = parts[i+1].strip("`")
                break
    elif query_upper.startswith("DELETE"):
        action = "DELETE"
        parts = query_clean.split()
        for i, p in enumerate(parts):
            if p.upper() == "FROM" and i + 1 < len(parts):
                table = parts[i+1].strip("`")
                break
    elif query_upper.startswith("SELECT"):
        action = "SELECT"
        parts = query_clean.split()
        for i, p in enumerate(parts):
            if p.upper() == "FROM" and i + 1 < len(parts):
                table = parts[i+1].strip("`")
                break
                
    return action, table


def format_ascii_table(rows):
    """Formats list of dictionaries into a clean MySQL Workbench style ASCII table."""
    if not rows:
        return "+---------------------+\n| No records found    |\n+---------------------+"
    headers = list(rows[0].keys())
    col_widths = {h: len(str(h)) for h in headers}
    
    # Track max character length for aligning columns
    for row in rows:
        for h in headers:
            val = row.get(h)
            val_str = str(val if val is not None else 'NULL')
            # Truncate extremely long columns (like parts JSON arrays) for neat terminal presentation
            if len(val_str) > 40:
                val_str = val_str[:37] + "..."
            if len(val_str) > col_widths[h]:
                col_widths[h] = len(val_str)
                
    # Build lines and separators
    top_line = "+" + "+".join("-" * (col_widths[h] + 2) for h in headers) + "+"
    header_line = "|" + "|".join(f" {str(h):<{col_widths[h]}} " for h in headers) + "|"
    sep_line = top_line
    
    lines = [top_line, header_line, sep_line]
    for row in rows:
        row_cells = []
        for h in headers:
            val = row.get(h)
            val_str = str(val if val is not None else 'NULL')
            if len(val_str) > 40:
                val_str = val_str[:37] + "..."
            row_cells.append(f" {val_str:<{col_widths[h]}} ")
        lines.append("|" + "|".join(row_cells) + "|")
    lines.append(top_line)
    return "\n".join(lines)


def print_table_snapshot(table_name):
    """Executes a DESC SELECT limit query to display the latest updates inside the log file."""
    PK_MAP = {
        "user": "user_id",
        "customer": "customer_id",
        "supplier": "supplier_id",
        "vehicle": "vehicle_id",
        "spare_part": "part_id",
        "service_job": "job_id",
        "invoice": "invoice_id"
    }
    
    clean_table = table_name.lower().strip("`").replace("`user`","user").replace("`user","user")
    pk = PK_MAP.get(clean_table)
    if not pk:
        return
        
    query = f"SELECT * FROM `{clean_table}` ORDER BY `{pk}` DESC LIMIT 5"
    try:
        # Note: Bypasses logging to prevent infinite loops during snapshot print
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        db_logger.info("\n[UPDATED TABLE SNAPSHOT]")
        db_logger.info(format_ascii_table(rows))
    except Exception as e:
        db_logger.info(f"\n[UPDATED TABLE SNAPSHOT] Error fetching snapshot: {str(e)}")


def log_db_activity(action, table, query, params, status="SUCCESS", error_msg=None):
    """Logs action updates, SQL statements, parameters, timestamps, and table snaps to logs/db_logs.log."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines = []
    log_lines.append("\n" + "=" * 60)
    log_lines.append(f"[TIMESTAMP] {now}")
    log_lines.append(f"[ACTION]    {action}")
    log_lines.append(f"[TABLE]     {table}")
    log_lines.append(f"\n[QUERY]\n{query.strip()}")
    if params:
        log_lines.append(f"\n[PARAMS]\n{params}")
        
    if error_msg:
        log_lines.append(f"\n[ERROR MESSAGE]\n{error_msg}")
        
    log_lines.append(f"\n[STATUS]    {status}")
    log_lines.append("=" * 60 + "\n")
    
    db_logger.info("\n".join(log_lines))
    
    if status == "SUCCESS" and action in ["INSERT", "UPDATE", "DELETE"] and table != "UNKNOWN":
        print_table_snapshot(table)


def log_select_query(query, params):
    """Optional lightweight select logging to display queries and params."""
    action, table = detect_table_and_action(query)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_logger.info(f"[{now}] [SELECT] Table: {table} | Query: {query.strip().splitlines()[0]}... | Params: {params}")


# ==========================================
# Core Database Connection Wrappers
# ==========================================

def get_db_connection():
    """Gets a connection from the pool and returns a raw pooled connection object."""
    global db_pool
    if not db_pool:
        try:
            db_pool = pooling.MySQLConnectionPool(
                pool_name="fender_pool",
                pool_size=5,
                pool_reset_session=True,
                **db_config
            )
        except mysql.connector.Error as err:
            raise Exception(f"Database Connection Pool is not initialized. Error: {err}")
            
    return db_pool.get_connection()


def fetch_all(query, params=None):
    """Executes a SELECT query and returns all matching rows as dictionaries."""
    log_select_query(query, params)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        records = cursor.fetchall()
        return records
    finally:
        cursor.close()
        conn.close()


def fetch_one(query, params=None):
    """Executes a SELECT query and returns the first row as a dictionary (or None)."""
    log_select_query(query, params)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        record = cursor.fetchone()
        return record
    finally:
        cursor.close()
        conn.close()


def execute_write(query, params=None):
    """Executes an INSERT, UPDATE, or DELETE query and commits immediately."""
    action, table = detect_table_and_action(query)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        rowcount = cursor.rowcount
        lastrowid = cursor.lastrowid
        log_db_activity(action, table, query, params, status="SUCCESS")
        return {"rowcount": rowcount, "lastrowid": lastrowid}
    except mysql.connector.Error as err:
        conn.rollback()
        log_db_activity(action, table, query, params, status="ROLLBACK / ERROR", error_msg=str(err))
        raise err
    finally:
        cursor.close()
        conn.close()


def initialize_database_extensions():
    """Initializes the db_log table, AFTER/BEFORE triggers, and cursor stored procedures in MySQL with explicit debugging."""
    print("Installing DB extensions...")
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Drop the old table if exists to update schema dynamically
        print("Dropping old db_log table if exists to refresh schema...")
        cursor.execute("DROP TABLE IF EXISTS db_log")
        
        # 1. Create logging table db_log with new schema
        print("Creating db_log table...")
        create_table_stmt = """
        CREATE TABLE db_log (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            event_type VARCHAR(50) NOT NULL,
            table_name VARCHAR(50) NOT NULL,
            reference_id INT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_stmt)
        print("db_log table created or verified successfully.")

        # 2. Install Trigger 1: trg_job_completion_audit
        print("Installing trigger trg_job_completion_audit...")
        cursor.execute("DROP TRIGGER IF EXISTS trg_job_completion_audit")
        cursor.execute("""
        CREATE TRIGGER trg_job_completion_audit
        AFTER UPDATE ON service_job
        FOR EACH ROW
        BEGIN
            IF OLD.status <> 'Completed' AND NEW.status = 'Completed' THEN
                INSERT INTO db_log (event_type, table_name, reference_id, message)
                VALUES (
                    'JOB_COMPLETED', 
                    'service_job', 
                    NEW.job_id, 
                    CONCAT('Service Job completed. Mechanic ID: ', NEW.user_id, ', Labour Charge: ₹', NEW.labour_charge)
                );
            END IF;
        END
        """)
        print("Trigger trg_job_completion_audit installed successfully.")

        # 3. Install Trigger 2: trg_low_stock_alert
        print("Installing trigger trg_low_stock_alert...")
        cursor.execute("DROP TRIGGER IF EXISTS trg_low_stock_alert")
        cursor.execute("""
        CREATE TRIGGER trg_low_stock_alert
        AFTER UPDATE ON spare_part
        FOR EACH ROW
        BEGIN
            IF NEW.quantity_in_stock <= NEW.reorder_level AND OLD.quantity_in_stock > NEW.reorder_level THEN
                INSERT INTO db_log (event_type, table_name, reference_id, message)
                VALUES (
                    'LOW_STOCK', 
                    'spare_part', 
                    NEW.part_id, 
                    CONCAT('Warning: Spare part "', NEW.part_name, '" (Part #', NEW.part_number, ') has reached a low-stock level! Remaining: ', NEW.quantity_in_stock, ' units.')
                );
            END IF;
        END
        """)
        print("Trigger trg_low_stock_alert installed successfully.")

        # 4. Install Trigger 3: trg_invoice_insert_audit
        print("Installing trigger trg_invoice_insert_audit...")
        cursor.execute("DROP TRIGGER IF EXISTS trg_invoice_insert_audit")
        cursor.execute("""
        CREATE TRIGGER trg_invoice_insert_audit
        AFTER INSERT ON invoice
        FOR EACH ROW
        BEGIN
            INSERT INTO db_log (event_type, table_name, reference_id, message)
            VALUES (
                'INVOICE_GENERATED', 
                'invoice', 
                NEW.invoice_id, 
                CONCAT('New invoice generated. Invoice ID: #', NEW.invoice_id, ' for Service Job #', NEW.job_id, '. Grand Total: ₹', NEW.grand_total, ', Payment Status: ', NEW.payment_status)
            );
        END
        """)
        print("Trigger trg_invoice_insert_audit installed successfully.")

        # 5. Install Stored Procedure 1: get_monthly_revenue_summary
        print("Installing Stored Procedure get_monthly_revenue_summary...")
        cursor.execute("DROP PROCEDURE IF EXISTS get_monthly_revenue_summary")
        cursor.execute("""
        CREATE PROCEDURE get_monthly_revenue_summary(OUT total_sales DECIMAL(10,2), OUT invoice_count INT)
        BEGIN
            DECLARE done INT DEFAULT FALSE;
            DECLARE inv_amount DECIMAL(10,2);
            DECLARE cur_sales DECIMAL(10,2) DEFAULT 0.00;
            DECLARE cur_count INT DEFAULT 0;
            
            DECLARE inv_cursor CURSOR FOR 
                SELECT grand_total FROM invoice 
                WHERE payment_status = 'Paid'
                AND MONTH(invoice_date) = MONTH(CURDATE())
                AND YEAR(invoice_date) = YEAR(CURDATE());
                
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
        END
        """)
        print("Stored procedure get_monthly_revenue_summary installed successfully.")

        # 6. Install Stored Procedure 2: get_low_stock_report
        print("Installing Stored Procedure get_low_stock_report...")
        cursor.execute("DROP PROCEDURE IF EXISTS get_low_stock_report")
        cursor.execute("""
        CREATE PROCEDURE get_low_stock_report(OUT report_out TEXT)
        BEGIN
            DECLARE done INT DEFAULT FALSE;
            DECLARE p_name VARCHAR(100);
            DECLARE p_qty INT;
            DECLARE p_reorder INT;
            DECLARE report_text TEXT DEFAULT 'LOW STOCK INVENTORY REPORT:\\n===========================\\n';
            DECLARE found_any INT DEFAULT 0;
            
            DECLARE parts_cursor CURSOR FOR 
                SELECT part_name, quantity_in_stock, reorder_level 
                FROM spare_part 
                WHERE quantity_in_stock <= reorder_level;
                
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
            
            OPEN parts_cursor;
            
            read_loop: LOOP
                FETCH parts_cursor INTO p_name, p_qty, p_reorder;
                IF done THEN
                    LEAVE read_loop;
                END IF;
                
                SET report_text = CONCAT(report_text, '- ', p_name, ': ', p_qty, ' units left (Reorder safety: ', p_reorder, ')\\n');
                SET found_any = found_any + 1;
            END LOOP;
            
            CLOSE parts_cursor;
            
            IF found_any = 0 THEN
                SET report_text = CONCAT(report_text, 'All spare parts are currently above reorder limits.\\n');
            END IF;
            
            SET report_out = report_text;
        END
        """)
        print("Stored procedure get_low_stock_report installed successfully.")
        
        conn.commit()
        print("All database extensions (db_log table, triggers, stored procedures) installed successfully.")
        
    except mysql.connector.Error as err:
        print(f"CRITICAL ERROR auto-installing database extensions: {err}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
