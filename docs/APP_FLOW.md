# Application Flow Document
## Project Name: Fender - Automobile Garage Management System

---

## 1. Authentication Flow
Fender uses session-based authentication to manage roles and access. The flow operates as follows:

```mermaid
sequenceDiagram
    actor User as User (Staff)
    participant Flask as Flask Server (auth.py)
    participant DB as MySQL Database (user table)

    User->>Flask: GET /login (Renders Login Page)
    User->>Flask: POST /login (username, password)
    Flask->>DB: SELECT user_id, role, full_name FROM user WHERE username = ? AND password = ?
    DB-->>Flask: Returns row or empty
    alt Credentials Valid
        Flask->>Flask: Set session variables (user_id, username, role, full_name)
        Flask->>User: Redirect to /dashboard with success flash
    else Credentials Invalid
        Flask->>User: Renders /login with error flash ("Invalid credentials")
    end
```

---

## 2. Global Navigation Flow
The layout features a sidebar that displays navigation options dynamically depending on the user's role:

```text
[Login Page]
     │
     └── Success ──> [Dashboard (Home)]
                          │
         ┌────────────────┴───────────────┐
         ▼                                ▼
  [Role-Based Sidebar]             [Top Navbar]
   ├── Owner:                      ├── Page Title
   │    ├── Dashboard               └── Logout Button
   │    ├── Customers & Vehicles
   │    ├── Suppliers & Inventory
   │    ├── Service Jobs
   │    ├── Invoices & Billing
   │    ├── DBMS Showcase (Viva Special)
   │    └── Analytics & Reports
   │
   ├── Manager:
   │    ├── Dashboard, Customers, Inventory, Service Jobs
   │
   ├── Receptionist:
   │    ├── Dashboard, Customers, Service Jobs, Invoices
   │
   └── Mechanic:
        └── My Assigned Jobs
```

---

## 3. CRUD Interaction Flow
Every standard database module (Customers, Suppliers, Spare Parts) follows a clean CRUD pattern using Bootstrap Modals to minimize page refreshes:

```mermaid
stateDiagram-v2
    [*] --> ViewList : GET /module (Read)
    ViewList --> SearchFilter : Enter search query / Filter
    SearchFilter --> ViewList : Refreshed Grid (Raw SQL LIKE query)
    
    ViewList --> ShowCreateModal : Click "Add New"
    ShowCreateModal --> SubmitCreateForm : Submit data
    SubmitCreateForm --> InsertSQL : POST /module/add (INSERT INTO...)
    InsertSQL --> ViewList : Success Flash
    InsertSQL --> ShowCreateModal : Constraint Failure (Unique error)

    ViewList --> ShowEditModal : Click "Edit" (Fetch row by ID)
    ShowEditModal --> SubmitEditForm : Submit updates
    SubmitEditForm --> UpdateSQL : POST /module/edit/id (UPDATE...)
    UpdateSQL --> ViewList : Success Flash

    ViewList --> TriggerDelete : Click "Delete"
    TriggerDelete --> DeleteSQL : POST /module/delete/id (DELETE FROM...)
    DeleteSQL --> ViewList : Success Flash (CASCADE or simple delete)
    DeleteSQL --> ViewList : Error Flash (RESTRICT constraint caught)
```

---

## 4. Service Job Lifecycle Flow
Service Jobs coordinate the core workflows on the shop floor. The status transitions guide this lifecycle:

```mermaid
stateDiagram-v2
    [*] --> Pending : Receptionist books job (complaints, customer, vehicle)
    Pending --> InProgress : Mechanic opens job sheet & begins diagnostics
    InProgress --> InProgress : Mechanic adds diagnostic notes, changes, & selects spare parts
    InProgress --> Completed : Mechanic enters labor charges & completes job (Triggers transaction)
    InProgress --> Cancelled : Customer cancels before completion
    Completed --> [*] : Invoice generated automatically (Unpaid -> Paid)
```

---

## 5. ACID Transaction Flow (Service Job Completion)
When a mechanic changes a service job status to `Completed`, the backend must perform a series of operations. Because this updates inventory quantities and creates financial records, it is wrapped inside a single **ACID Transaction**:

```mermaid
sequenceDiagram
    actor Mech as Mechanic / Staff
    participant Flask as Flask Server (jobs.py)
    participant DB as MySQL Database

    Mech->>Flask: POST /jobs/complete/id (Diagnosis, labor charge, parts used JSON)
    Flask->>DB: START TRANSACTION
    
    Note over Flask,DB: Step 1: Update the Service Job Details
    Flask->>DB: UPDATE service_job SET status = 'Completed', diagnosis = ?, labour_charge = ?, parts_used = ? WHERE job_id = ?
    DB-->>Flask: OK
    
    Note over Flask,DB: Step 2: Loop and verify Inventory for each part used
    loop For each part in parts_used JSON
        Flask->>DB: SELECT quantity_in_stock, part_name FROM spare_part WHERE part_id = ?
        DB-->>Flask: Stock Count
        alt Stock is Sufficient
            Flask->>DB: UPDATE spare_part SET quantity_in_stock = quantity_in_stock - ? WHERE part_id = ?
            DB-->>Flask: OK
        else Stock is Insufficient
            Flask->>DB: ROLLBACK TRANSACTION
            Flask-->>Mech: Error Alert ("Not enough Engine Oil in stock. Transaction aborted!")
        end
    end

    Note over Flask,DB: Step 3: Automatically Generate Invoice
    Flask->>DB: INSERT INTO invoice (job_id, customer_id, invoice_date, labour_total, parts_total, grand_total, payment_status) VALUES (?, ?, CURDATE(), ?, ?, ?, 'Unpaid')
    DB-->>Flask: OK
    
    Flask->>DB: COMMIT TRANSACTION
    DB-->>Flask: Transaction Committed Successfully
    Flask-->>Mech: Redirect /jobs with success alert ("Job marked complete, invoice generated.")
```

### ACID Concept Explanations for Viva:
- **Atomicity**: Either the job updates, the inventory parts are deducted, and the invoice is created together, or nothing happens. There can never be a completed job without an invoice or stock reduction.
- **Consistency**: The database transitions from one valid state to another. A part's stock level can never go negative because of the checks before subtraction.
- **Isolation**: Concurrent transactions do not overwrite each other's updates (MySQL handles this via Row-level locking on the `spare_part` table during selection).
- **Durability**: Once `COMMIT` returns, the records are written to disk and will survive system failures.

---

## 6. Invoice Settlement Flow
Once an invoice is created, it follows a simple collection workflow:
1. Receptionist views the **Unpaid Invoices** tab.
2. Clicks the **Collect Payment** action button.
3. A modal prompts for **Payment Method** (Cash, Card, UPI, Bank Transfer) and **Payment Status** (Paid or Partially Paid).
4. Submitting the form runs the query:
   ```sql
   UPDATE invoice 
   SET payment_status = %s, payment_method = %s 
   WHERE invoice_id = %s;
   ```
5. If marked as fully `Paid`, the invoice changes color indicators from red to green.
