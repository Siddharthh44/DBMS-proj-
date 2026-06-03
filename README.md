# Fender - Automobile Garage Management System
## DBMS Mini-Project (Flask + MySQL + Bootstrap 5)

Fender is a web-based workshop administration portal designed for car repair garages. The application supports customer directories, vehicle profiles, vendor inventory catalogs, service job sheets, and invoice billing. The interface features a global flat dark theme built with Bootstrap 5.

---

## 1. Project Objective & Academic Features
Fender is structured to demonstrate core database management system (DBMS) concepts for practical exams and viva evaluators:

- **Entity Relationship Model**: Models real-world entities (`user`, `customer`, `vehicle`, `supplier`, `spare_part`, `service_job`, `invoice`) with correct cardinality.
- **Relational Constraints**: Enforces primary keys, unique constraints, and referential actions (such as `ON DELETE CASCADE` and `ON DELETE RESTRICT`).
- **ACID Transactions**: Marking service jobs as complete runs an atomic SQL transaction which row-locks stock counts, verifies sufficiency (rolling back if inventory is lacking), decreases inventory, and generates bills simultaneously.
- **Dynamic Schema Inspector**: Queries MySQL `INFORMATION_SCHEMA.COLUMNS` dynamically to render a database structure explorer inside the application.
- **Normalization Review**: Serves as a case study for 1NF violations (composite JSON columns in job sheets) and 3NF violations (derived total figures in invoices).

---

## 2. Mandatory Tech Stack
- **Backend**: Python 3.x + Flask Web Framework
- **Database**: MySQL Community Server (v8.0+)
- **Frontend**: HTML5, CSS, Vanilla JS, Bootstrap 5, Bootstrap Icons, Chart.js
- **Database Driver**: `mysql-connector-python`
- **IDE & Client**: VS Code + MySQL Workbench

---

## 3. Step-by-Step Installation & Run Guide

### Step A: Initialize the MySQL Database
1. Launch **MySQL Workbench** (or MySQL CLI shell).
2. Open and execute the schema initialization script:
   [database/schema.sql](file:///c:/Users/siddharth/Desktop/fender/database/schema.sql)
3. Open and execute the seed data script:
   [database/sample_inserts.sql](file:///c:/Users/siddharth/Desktop/fender/database/sample_inserts.sql)
4. Confirm that the schema tables exist under the database `garage_db`.

### Step B: Configure Python Virtual Environment & Dependencies
1. Open a terminal inside the project root directory `fender/`.
2. Create and activate a Python virtual environment:
   ```powershell
   # On Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Install the required dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

### Step C: Configure Environment Variables
You can configure database credentials by setting environment variables in your terminal, or by creating a `.env` file at the root of the project:

```text
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=garage_db
DB_PORT=3306
SECRET_KEY=fender_secret_key
FLASK_DEBUG=True
```

### Step D: Run the Server
Start the Flask application using:
```powershell
python run.py
```
Open your browser and navigate to: **http://127.0.0.1:5000/**

### Step E: Monitor Live Database Activities (Recommended)
The system separates web application runtime logs from database transaction logs. You can monitor all raw SQL queries, INSERT/UPDATE/DELETE actions, transaction operations (START/COMMIT/ROLLBACK), and relational table snapshots live in a second terminal:

- **Windows PowerShell**:
  ```powershell
  Get-Content logs\db_logs.log -Wait
  ```

- **Git Bash / macOS / Linux**:
  ```bash
  tail -f logs/db_logs.log
  ```

---

## 4. Sample Login Accounts for Testing
The database includes predefined users representing different system roles. Log in using the credentials below:

| Username | Password | System Role | Accessible Views |
| :--- | :--- | :--- | :--- |
| **`owner1`** | `password` | Owner | Full access, Revenue charts, User meta, DBMS Showcase |
| **`manager1`** | `password` | Manager | Customers/vehicles, Inventory catalog, Supplier setup, Jobs |
| **`reception1`** | `password` | Receptionist | Intake registration, Customer registry, Invoice checkout |
| **`mechanic1`** | `password` | Mechanic | Technical job sheets queue (restricted to assigned jobs) |
| **`mechanic2`** | `password` | Mechanic | Technical job sheets queue (restricted to assigned jobs) |

---

## 5. Verification Checklist

1. **Foreign Key Restriction Test**:
   - Log in as `owner1` or `manager1` and go to **Supplies & Inventory**.
   - Navigate to the **Suppliers** tab and attempt to delete the supplier **AutoCare Supplies**.
   - Verify that the delete operation is rejected by the database and flashes a red alert warning showing constraint safety (`RESTRICT` rule).
2. **ACID Transaction Rollback Test**:
   - Log in as `mechanic1` and open the assigned job sheet.
   - Try completing the service job after adding a spare part with a quantity *greater* than what is in stock (e.g. 100 units of Spark Plugs).
   - Click **Complete & Generate Invoice**.
   - Verify that the transaction is rolled back, the inventory quantities are unchanged, no invoice is created, and the UI reports a red transaction abort alert.
3. **Success Transaction Path**:
   - Complete a service job sheet using parts that are in stock.
   - Verify that the inventory count is deducted, the job status changes to `Completed`, and an unpaid invoice is created. Settle the payment under **Invoices & Billing**.
