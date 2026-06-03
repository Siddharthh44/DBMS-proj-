# Backend Schema Plan
## Project Name: Fender - Automobile Garage Management System

---

## 1. Application Architecture & File Roles
The backend uses a modular Flask Blueprint structure. This separation keeps the codebase clean, readable, and easy to explain during a project viva.

```text
app/
├── db.py                 # Core database driver & connection pooling
├── auth.py               # Route guards & user session management
└── routes/
    ├── dashboard.py      # Main dashboard aggregations
    ├── customers.py      # Customer/Vehicle CRUD database logic
    ├── inventory.py      # Supplier/Parts CRUD & stock alerts
    ├── jobs.py           # Job management & parts-deducting transaction
    ├── billing.py        # Invoices list, payment settlement
    └── db_showcase.py    # Concept review & ER visualization endpoints
```

---

## 2. Database Utility Layer (`app/db.py`)
This utility file defines reusable database interaction helpers, handling connection pool fetch, execution, mapping records to dictionaries, and connection cleanup.

```python
# app/db.py
import mysql.connector
from mysql.connector import pooling
import os
from contextlib import contextmanager

db_config = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "root_password"),
    "database": os.environ.get("DB_NAME", "garage_db"),
    "port": int(os.environ.get("DB_PORT", 3306))
}

# 1. Setup connection pool
try:
    db_pool = pooling.MySQLConnectionPool(
        pool_name="fender_pool",
        pool_size=5,
        pool_reset_session=True,
        **db_config
    )
except mysql.connector.Error as err:
    print(f"Error establishing DB connection pool: {err}")
    db_pool = None

# 2. Context manager for simple commands
@contextmanager
def get_db_connection():
    """Gets a connection from the pool and handles automatic close."""
    if not db_pool:
        raise Exception("Database Connection Pool is not initialized.")
    conn = db_pool.get_connection()
    try:
        yield conn
    finally:
        conn.close() # Released back to pool

# 3. Reusable helper: Select multiple rows
def fetch_all(query, params=None):
    """Executes a SELECT query and returns all matching rows as dictionaries."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        records = cursor.fetchall()
        cursor.close()
        return records

# 4. Reusable helper: Select single row
def fetch_one(query, params=None):
    """Executes a SELECT query and returns the first row as a dictionary (or None)."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        record = cursor.fetchone()
        cursor.close()
        return record

# 5. Reusable helper: Write queries (INSERT, UPDATE, DELETE)
def execute_write(query, params=None):
    """Executes an INSERT, UPDATE, or DELETE query and commits immediately."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            rowcount = cursor.rowcount
            lastrowid = cursor.lastrowid
            return {"rowcount": rowcount, "lastrowid": lastrowid}
        except mysql.connector.Error as err:
            conn.rollback()
            raise err
        finally:
            cursor.close()
```

---

## 3. Database Integrity & Role Guard Middleware (`app/auth.py`)
To manage security checks easily, custom Flask decorator functions wrap routing controllers to verify user sessions and role permissions:

```python
# app/auth.py
from functools import wraps
from flask import session, redirect, url_for, flash, abort

def login_required(f):
    """Decorator to block unauthenticated requests."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Decorator to restrict access to specific system roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in allowed_roles:
                flash("Access Denied: You do not have permission to view this section.", "danger")
                return redirect(url_for('dashboard.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

---

## 4. Route Mapping and Key SQL Queries
Below is the mapping of core application routes to their corresponding raw SQL queries:

### 4.1 Dashboard Routes (`app/routes/dashboard.py`)
Provides aggregated counts and quick alert warnings for the home page.
- **Get Metrics**:
  ```sql
  -- Count active service jobs
  SELECT COUNT(*) AS active_jobs FROM service_job WHERE status IN ('Pending', 'In Progress');
  
  -- Count spare parts running below safety stock level
  SELECT COUNT(*) AS low_stock_count FROM spare_part WHERE quantity_in_stock <= reorder_level;
  
  -- Sum monthly revenue
  SELECT COALESCE(SUM(grand_total), 0.00) AS monthly_revenue 
  FROM invoice 
  WHERE MONTH(invoice_date) = MONTH(CURDATE()) AND YEAR(invoice_date) = YEAR(CURDATE());
  
  -- Sum unpaid invoices totals
  SELECT COALESCE(SUM(grand_total), 0.00) AS unpaid_invoices FROM invoice WHERE payment_status = 'Unpaid';
  ```
- **List Alert Panels**:
  ```sql
  -- Get low stock items list
  SELECT part_name, quantity_in_stock, reorder_level FROM spare_part WHERE quantity_in_stock <= reorder_level LIMIT 5;
  ```

### 4.2 Customer & Vehicle CRUD (`app/routes/customers.py`)
Manages standard relational parent-child entities.
- **Search Customers**:
  ```sql
  SELECT * FROM customer 
  WHERE full_name LIKE %s OR phone LIKE %s 
  ORDER BY full_name ASC;
  ```
- **Create Customer**:
  ```sql
  INSERT INTO customer (full_name, phone, email, address) VALUES (%s, %s, %s, %s);
  ```
- **Update Customer**:
  ```sql
  UPDATE customer SET full_name = %s, phone = %s, email = %s, address = %s WHERE customer_id = %s;
  ```
- **Delete Customer**:
  ```sql
  -- Will fail with code 1451 if customer has referenced invoices/jobs due to RESTRICT rule
  DELETE FROM customer WHERE customer_id = %s;
  ```
- **Create Vehicle** (linked to Customer):
  ```sql
  INSERT INTO vehicle (customer_id, registration_no, make, model, manufacture_year, mileage) 
  VALUES (%s, %s, %s, %s, %s, %s);
  ```
- **Delete Vehicle**:
  ```sql
  -- Cascade delete rule does not apply since jobs refer to vehicle ID with RESTRICT constraint
  DELETE FROM vehicle WHERE vehicle_id = %s;
  ```

### 4.3 Supplier & Inventory CRUD (`app/routes/inventory.py`)
Tracks stock supplies and alerts.
- **Get Inventory**:
  ```sql
  SELECT p.*, s.supplier_name 
  FROM spare_part p
  JOIN supplier s ON p.supplier_id = s.supplier_id
  ORDER BY p.part_name ASC;
  ```
- **Insert Spare Part**:
  ```sql
  INSERT INTO spare_part (supplier_id, part_name, part_number, category, quantity_in_stock, reorder_level, unit_cost, selling_price) 
  VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
  ```
- **Update Stock Level (Reorder)**:
  ```sql
  UPDATE spare_part SET quantity_in_stock = quantity_in_stock + %s WHERE part_id = %s;
  ```

### 4.4 Invoicing & Payments (`app/routes/billing.py`)
Handles financial checkout.
- **Get Invoice Details with Joins**:
  ```sql
  SELECT i.*, c.full_name AS customer_name, c.phone AS customer_phone, j.complaint, j.diagnosis 
  FROM invoice i
  JOIN customer c ON i.customer_id = c.customer_id
  JOIN service_job j ON i.job_id = j.job_id
  WHERE i.invoice_id = %s;
  ```
- **Process Invoice Settlement**:
  ```sql
  UPDATE invoice SET payment_status = %s, payment_method = %s WHERE invoice_id = %s;
  ```

---

## 5. ACID Transaction Implementation: Service Job Completion
Completing a job is a critical database transaction. It requires updating the service job sheet, checking inventory levels, deducting matching quantities, and generating a corresponding customer invoice.

Here is the exact implementation structure for the transaction logic inside `app/routes/jobs.py`:

```python
# app/routes/jobs.py
import json
from flask import Blueprint, request, redirect, url_for, flash
from app.db import get_db_connection
import mysql.connector

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/jobs/<int:job_id>/complete', methods=['POST'])
def complete_service_job(job_id):
    diagnosis = request.form.get("diagnosis")
    labour_charge = float(request.form.get("labour_charge", 0.0))
    
    # parts_used is sent as JSON from frontend list, e.g.
    # [{"part_id": 1, "part_name": "Engine Oil", "quantity": 2, "unit_price": 900.00, "line_total": 1800.00}]
    parts_used_str = request.form.get("parts_used_json", "[]")
    parts_list = json.loads(parts_used_str)
    
    # Calculate parts total cost
    parts_total = sum(item["line_total"] for item in parts_list)
    grand_total = labour_charge + parts_total
    
    # Establish connection manually to manage transaction bounds
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Step 1: Start explicit transaction
        conn.start_transaction()
        
        # Step 2: Fetch job details to get customer ID
        cursor.execute("SELECT customer_id FROM service_job WHERE job_id = %s", (job_id,))
        job_row = cursor.fetchone()
        if not job_row:
            raise Exception("Service job sheet not found.")
        customer_id = job_row["customer_id"]
        
        # Step 3: Deduct parts quantities from spare_part inventory
        for part in parts_list:
            part_id = part["part_id"]
            qty_needed = int(part["quantity"])
            
            # Select with Row Lock to prevent concurrent race conditions (Isolation)
            cursor.execute(
                "SELECT quantity_in_stock, part_name FROM spare_part WHERE part_id = %s FOR UPDATE", 
                (part_id,)
            )
            part_row = cursor.fetchone()
            
            if not part_row:
                raise Exception(f"Part ID {part_id} does not exist.")
            
            current_stock = part_row["quantity_in_stock"]
            if current_stock < qty_needed:
                # Trigger abort condition: Not enough inventory
                raise Exception(f"Insufficient stock for '{part_row['part_name']}'. In stock: {current_stock}, Requested: {qty_needed}.")
                
            # Perform update
            cursor.execute(
                "UPDATE spare_part SET quantity_in_stock = quantity_in_stock - %s WHERE part_id = %s",
                (qty_needed, part_id)
            )
            
        # Step 4: Update the service job status and diagnosis details
        cursor.execute(
            """UPDATE service_job 
               SET status = 'Completed', diagnosis = %s, parts_used = %s, labour_charge = %s 
               WHERE job_id = %s""",
            (diagnosis, parts_used_str, labour_charge, job_id)
        )
        
        # Step 5: Automatically generate matching Invoice record
        cursor.execute(
            """INSERT INTO invoice (job_id, customer_id, invoice_date, labour_total, parts_total, grand_total, payment_status) 
               VALUES (%s, %s, CURDATE(), %s, %s, %s, 'Unpaid')""",
            (job_id, customer_id, labour_charge, parts_total, grand_total)
        )
        
        # If all steps succeeded, commit transaction
        conn.commit()
        flash("Service Job marked completed. Invoice generated successfully.", "success")
        
    except Exception as e:
        # Roll back ALL database changes if ANY error occurred (Atomicity / Consistency)
        conn.rollback()
        flash(f"Transaction Aborted: {str(e)}", "danger")
        
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('jobs.list_jobs'))
```
