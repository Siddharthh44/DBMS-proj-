# Fender Garage Management System: DBMS Theory + Project Mapping

This document maps DBMS theory directly to the actual Flask + MySQL Garage Management System implementation in this repository.

## Audit Basis

Inspected source files:

- `database/schema.sql`
- `database/triggers_procedures.sql`
- `database/sample_inserts.sql`
- `app/db.py`
- `app/__init__.py`
- `app/auth.py`
- `app/routes/dashboard.py`
- `app/routes/customers.py`
- `app/routes/inventory.py`
- `app/routes/jobs.py`
- `app/routes/billing.py`
- `app/routes/db_showcase.py`
- `templates/dashboard.html`
- `templates/db_showcase.html`
- `templates/jobs/edit.html`
- `README.md`

## Important Implementation Reality Check

The repository contains two definitions of advanced database objects:

1. `database/triggers_procedures.sql` is the static SQL script version.
2. `app/db.py` recreates `db_log`, all three triggers, and both stored procedures at application startup through `initialize_database_extensions()` and is therefore the live runtime definition.

This means viva answers should mention both, but if asked "what actually runs when the Flask app starts?", the answer is: the runtime objects created from `app/db.py` during `create_app()` in `app/__init__.py`.

Important runtime difference:

- `database/triggers_procedures.sql` defines `db_log(log_time, log_type, message)`.
- `app/db.py` recreates `db_log(event_type, table_name, reference_id, message, created_at)`.

So the live application behavior matches the `app/db.py` version, not the older SQL file shape.

## Project Snapshot

Core business tables:

- `user`
- `customer`
- `supplier`
- `vehicle`
- `spare_part`
- `service_job`
- `invoice`
- `db_log` for auditing advanced SQL behavior

Main workflows:

- Login and role-based access
- Customer and vehicle CRUD
- Supplier and spare-part inventory CRUD
- Service job creation, update, completion
- Automatic invoice generation on job completion
- Payment settlement
- Dashboard analytics
- DBMS showcase for metadata, triggers, and procedures

Role model:

- `owner`
- `manager`
- `mechanic`
- `receptionist`

------------------------------------------------------------
## MODULE 1
------------------------------------------------------------

## 1. Introduction to Databases

### 1. Concept Name

Introduction to Databases and why a DBMS is needed.

### 2. Simple Theory Explanation

A database is an organized collection of related data. A DBMS is the software layer that stores, retrieves, secures, and manages that data while enforcing rules such as constraints, transactions, and concurrent access control.

From a syllabus perspective, this project belongs to the modern relational-database phase of database applications. Historically, organizations moved from manual records and file-processing systems to DBMS-based systems because file systems made it hard to share data safely, avoid duplication, and maintain consistency across departments.

### 3. Where It Exists in This Project

This project uses MySQL as the DBMS and Flask as the application layer. The garage domain involves multiple related entities and multiple user roles, so a DBMS is necessary instead of plain files.

Actual implementation points:

- Schema definition in `database/schema.sql`
- Connection pool and query wrappers in `app/db.py`
- Multi-user workflows in route modules
- Role-controlled access in `app/auth.py`
- Shared analytics in `app/routes/dashboard.py`

Security and controlled access are visible through:

- `login_required` in `app/auth.py`
- `role_required([...])` in `app/auth.py`
- session-based role restrictions for owner, manager, mechanic, and receptionist

### 4. Real Table/Column Examples

- `customer(customer_id, full_name, phone, email, address)`
- `vehicle(vehicle_id, customer_id, registration_no, make, model, manufacture_year, mileage)`
- `service_job(job_id, vehicle_id, customer_id, user_id, job_date, complaint, diagnosis, parts_used, labour_charge, status)`
- `invoice(invoice_id, job_id, customer_id, grand_total, payment_status, payment_method)`

These tables show why the system needs structured relationships rather than separate files.

### 5. SQL Examples from Project

Example of central structured storage:

```sql
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
```

Example of cross-entity retrieval:

```sql
SELECT j.*, v.registration_no, v.make, v.model, c.full_name AS customer_name
FROM service_job j
JOIN vehicle v ON j.vehicle_id = v.vehicle_id
JOIN customer c ON j.customer_id = c.customer_id;
```

### 6. Flask Integration Explanation

Flask is the external application layer. Users do not talk to MySQL directly. They interact through forms and pages; Flask routes convert those actions into SQL using:

- `fetch_one()`
- `fetch_all()`
- `execute_write()`
- `get_db_connection()`

This creates centralized data access from `app/db.py`, rather than letting each route open its own raw unmanaged connections.

### 7. Viva Questions + Detailed Answers

Q1. Why does this Garage Management System require a DBMS?
A1. Because it manages interrelated data such as customers, vehicles, mechanics, service jobs, spare parts, suppliers, and invoices. A DBMS is needed to maintain relationships, prevent duplicates, support concurrent users, and ensure transaction safety during job completion and billing.

Q2. Why is a file system not enough for this project?
A2. A file system cannot easily enforce foreign keys, unique registration numbers, transaction rollback, or multi-table joins. This project depends on all of those. For example, completing a job updates inventory, updates the job, and inserts an invoice atomically, which is difficult to guarantee with text files.

Q3. What is centralized data handling here?
A3. All modules use the same MySQL database `garage_db`. Customers, inventory, jobs, invoices, and auditing all read from and write to one central store through `app/db.py`.

Q4. How is concurrency relevant in this project?
A4. Mechanics, receptionists, managers, and owners can act on related data. The job-completion transaction uses `SELECT ... FOR UPDATE` on spare parts so that stock updates do not conflict during concurrent access.

Q5. How is consistency preserved?
A5. Through primary keys, unique constraints, foreign keys, transaction rollback, and role-based workflow separation. Example: `invoice.job_id` is unique, so one service job cannot accidentally create multiple invoices.

Q6. How does this project reflect the history of database applications?
A6. It reflects the shift from isolated record keeping to centralized relational systems. Instead of separate customer files, inventory files, and billing files maintained manually, the garage stores all related operational data in one DBMS and queries it through SQL joins and transactions.

### 8. Common Examiner Follow-up Questions

- Why is `registration_no` unique?
- Why are invoices and jobs in separate tables?
- Why is supplier deletion not always simple?
- What would happen if two users updated the same stock row together?

### 9. Real Workflow Example from Project

Receptionist adds a customer and registers a vehicle. A job sheet is created and assigned to a mechanic. The mechanic updates diagnosis and parts used. When the job is completed, the system reduces spare-part stock, updates the job status, creates an invoice, and logs audit events. This end-to-end workflow is exactly why a DBMS is needed.

### 10. Important Technical Terms

DBMS, centralized data, concurrency, consistency, integrity, transaction, foreign key, uniqueness, role-based access, shared database.

## 2. Overview of Database Languages and Architectures

### 1. Concept Name

Database languages, data models, schemas, instances, three-schema architecture, and data independence.

### 2. Simple Theory Explanation

- A data model defines how data is organized. This project uses the relational model.
- A schema is the structural design of the database.
- An instance is the current stored data at a given moment.
- Three-schema architecture separates external view, conceptual design, and internal storage.
- Data independence means changes at one level should minimize effects on other levels.

### 3. Where It Exists in This Project

- Relational data model: `database/schema.sql`
- Schema: table definitions and constraints
- Instance: `database/sample_inserts.sql` and live MySQL rows
- External schema: Flask pages and role-specific views
- Conceptual schema: logical business entities and relationships
- Internal schema: MySQL storage objects, keys, indexes implied by PK/UNIQUE, and connection pooling

### 4. Real Table/Column Examples

Schema examples:

- `user.role` uses `ENUM`
- `vehicle.registration_no` uses `UNIQUE`
- `invoice.job_id` is both `FOREIGN KEY` and `UNIQUE`

Instance examples from sample data:

- User `owner1`
- Customer `Rahul Nair`
- Vehicle `KA01AB1234`
- Paid invoice rows for jobs `2`, `4`, and `7`

### 5. SQL Examples from Project

DDL:

```sql
CREATE TABLE IF NOT EXISTS invoice (
    invoice_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL UNIQUE,
    customer_id INT NOT NULL,
    invoice_date DATE NOT NULL,
    labour_total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    parts_total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    grand_total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    payment_status ENUM('Unpaid', 'Partially Paid', 'Paid') NOT NULL DEFAULT 'Unpaid',
    payment_method ENUM('Cash', 'Card', 'UPI', 'Bank Transfer') NOT NULL DEFAULT 'Cash'
);
```

DML:

```sql
INSERT INTO service_job (vehicle_id, customer_id, user_id, job_date, complaint, status)
VALUES (%s, %s, %s, %s, %s, 'Pending');
```

TCL:

```sql
START TRANSACTION;
COMMIT;
ROLLBACK;
```

Stored procedure call:

```sql
CALL get_monthly_revenue_summary(@total_sales, @invoice_count);
SELECT @total_sales, @invoice_count;
```

Metadata query:

```sql
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'garage_db';
```

### 6. Flask Integration Explanation

External schema mapping:

- Login page: users see only authentication fields
- Dashboard: managers/owners see aggregates, not full physical storage details
- Mechanic jobs page: mechanics see only assigned jobs
- Billing page: receptionists see invoice views and payment actions

Conceptual schema mapping:

- Flask routes think in business entities like customer, job, invoice, stock

Internal schema mapping:

- `app/db.py` manages pooling, connections, commits, rollbacks, and SQL logging

Physical vs logical data independence:

- Logical independence: UI pages do not need to know every column in every table. For example, dashboard queries can work without exposing full invoice details.
- Physical independence: Flask code does not depend on file organization or page layout inside MySQL. It depends on tables and SQL behavior, not storage blocks.

Limit:

- The app still has moderate coupling to the logical schema because route SQL names tables and columns explicitly.

### 7. Viva Questions + Detailed Answers

Q1. What is the data model used in this project?
A1. The project uses the relational model because data is stored in tables such as `customer`, `vehicle`, `service_job`, and `invoice`, and relationships are enforced using foreign keys.

Q2. What is the schema in this project?
A2. The schema is the structural definition in `database/schema.sql`, including table names, data types, primary keys, unique keys, enums, and foreign-key constraints.

Q3. What is an instance in this project?
A3. An instance is the current content stored in the tables. The sample inserted rows in `database/sample_inserts.sql` are one database instance, and live running data is another instance.

Q4. What is the external schema here?
A4. The external schema is the user-facing view through Flask templates and routes. For example, a mechanic sees assigned jobs, but not the schema browser or owner-only showcase page.

Q5. Does this project demonstrate all database languages?
A5. It demonstrates DDL, DML, query language, and TCL. It does not implement explicit DCL statements like `GRANT` or `REVOKE`; access control is handled in Flask sessions and decorators.

### 8. Common Examiner Follow-up Questions

- What is the difference between schema and instance?
- Which part of this project corresponds to conceptual schema?
- Is there any physical independence here?
- Why is Flask not considered the DBMS?

### 9. Real Workflow Example from Project

Owner opens `/showcase`. Flask executes an `INFORMATION_SCHEMA.COLUMNS` query and groups the metadata by table. The owner sees a schema browser, but the physical storage implementation remains hidden. This is a good project example of external view over conceptual structure.

### 10. Important Technical Terms

Relational model, schema, instance, DDL, DML, TCL, external schema, conceptual schema, internal schema, data independence, metadata.

## 3. Conceptual Data Modelling using ER

### 1. Concept Name

ER modelling, entity types, relationships, structural constraints, weak entities, specialization, and generalization.

### 2. Simple Theory Explanation

An ER model represents real-world objects as entities and connects them through relationships. Cardinality tells how many instances can be related. Weak entities depend on other entities for existence. Specialization/generalization models inheritance among entity types.

### 3. Where It Exists in This Project

The project exposes the ER structure in two places:

- The actual schema in `database/schema.sql`
- The ER diagram rendered in `templates/db_showcase.html`

### 4. Real Table/Column Examples

Entity types:

- `user`
- `customer`
- `vehicle`
- `supplier`
- `spare_part`
- `service_job`
- `invoice`

Relationships:

- Customer owns vehicle: `vehicle.customer_id -> customer.customer_id`
- Supplier supplies spare part: `spare_part.supplier_id -> supplier.supplier_id`
- Vehicle undergoes service job: `service_job.vehicle_id -> vehicle.vehicle_id`
- Customer requests service job: `service_job.customer_id -> customer.customer_id`
- Mechanic/user handles service job: `service_job.user_id -> user.user_id`
- Service job generates invoice: `invoice.job_id -> service_job.job_id`, plus `UNIQUE` on `invoice.job_id`

### 5. SQL Examples from Project

```sql
CONSTRAINT fk_job_vehicle
    FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id)
    ON DELETE RESTRICT,
CONSTRAINT fk_job_customer
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
    ON DELETE RESTRICT,
CONSTRAINT fk_job_user
    FOREIGN KEY (user_id) REFERENCES `user`(user_id)
    ON DELETE RESTRICT
```

And for 1:1 job-to-invoice:

```sql
job_id INT NOT NULL UNIQUE,
CONSTRAINT fk_invoice_job
    FOREIGN KEY (job_id) REFERENCES service_job(job_id)
```

### 6. Flask Integration Explanation

Flask routes use these relationships directly:

- `customers.py` joins `vehicle` with `customer`
- `jobs.py` joins `service_job`, `vehicle`, `customer`, and `user`
- `billing.py` joins `invoice`, `service_job`, `vehicle`, `customer`, and `user`
- `dashboard.py` aggregates over `invoice`, `service_job`, and `spare_part`

So the ER model is not only theoretical; it drives all major pages.

### 7. Viva Questions + Detailed Answers

Q1. What are the main entities in this project?
A1. The main entities are user, customer, vehicle, supplier, spare_part, service_job, and invoice. Each has its own primary key and stores a distinct business concept.

Q2. Explain the relationship between customer and vehicle.
A2. It is a one-to-many relationship. One customer can own multiple vehicles, but each vehicle row stores one `customer_id`, so each vehicle belongs to exactly one customer.

Q3. How is the service job to invoice relationship modeled?
A3. It is modeled as one-to-one by placing a `UNIQUE` constraint on `invoice.job_id`. This means one job can generate at most one invoice.

Q4. Is there a weak entity in this project?
A4. There is no strict textbook weak entity because all major tables have their own surrogate primary keys. The closest existence-dependent entity is `invoice`, because it cannot exist without a `service_job`, but it still has its own `invoice_id`.

Q5. Is specialization/generalization used?
A5. Not as separate subtype tables. Instead, different user categories are represented by `user.role` as an `ENUM`, so specialization is implemented logically, not with relational inheritance tables.

### 8. Common Examiner Follow-up Questions

- Why is invoice not a pure weak entity?
- Why is `user.role` an enum instead of separate subtype tables?
- What is the cardinality between supplier and spare_part?
- Why is `service_job` connected to both vehicle and customer?

### 9. Real Workflow Example from Project

Creating a service job uses the ER design in practice. The receptionist selects a vehicle, customer, and mechanic. That becomes one `service_job` row linking `vehicle_id`, `customer_id`, and `user_id`. When completed, one `invoice` row is generated for that `job_id`.

### 10. Important Technical Terms

Entity, relationship, cardinality, participation, foreign key, one-to-many, one-to-one, weak entity, specialization, generalization.

### Textual ER Diagram Description

- `CUSTOMER 1 --- N VEHICLE`
- `CUSTOMER 1 --- N SERVICE_JOB`
- `USER 1 --- N SERVICE_JOB`
- `VEHICLE 1 --- N SERVICE_JOB`
- `SUPPLIER 1 --- N SPARE_PART`
- `SERVICE_JOB 1 --- 1 INVOICE`
- `CUSTOMER 1 --- N INVOICE`

### Important Design Observation

The conceptual model for "parts used in a job" is not represented as a separate ER relationship table. Instead, it is stored as JSON in `service_job.parts_used`. This is a real design shortcut and a strong viva discussion point.

------------------------------------------------------------
## MODULE 2
------------------------------------------------------------

## 4. Relational Model

### 1. Concept Name

Relational model concepts, schemas, keys, constraints, update operations, transactions, and constraint violations.

### 2. Simple Theory Explanation

The relational model stores data as tables consisting of rows and columns. Keys identify tuples. Foreign keys connect relations. Constraints enforce validity. Update operations are insert, update, and delete. Transactions group multiple operations into one logical unit.

### 3. Where It Exists in This Project

Every core table in `database/schema.sql` is part of the relational model. CRUD routes in Flask execute insert, update, delete, and select operations against those relations.

### 4. Real Table/Column Examples

Primary keys:

- `user.user_id`
- `customer.customer_id`
- `vehicle.vehicle_id`
- `spare_part.part_id`
- `service_job.job_id`
- `invoice.invoice_id`

Candidate keys / unique attributes:

- `user.username`
- `vehicle.registration_no`
- `spare_part.part_number`
- `invoice.job_id`

Foreign keys:

- `vehicle.customer_id`
- `spare_part.supplier_id`
- `service_job.vehicle_id`
- `service_job.customer_id`
- `service_job.user_id`
- `invoice.job_id`
- `invoice.customer_id`

### 5. SQL Examples from Project

Insert:

```sql
INSERT INTO customer (full_name, phone, email, address)
VALUES (%s, %s, %s, %s)
```

Update:

```sql
UPDATE invoice
SET payment_status = %s, payment_method = %s
WHERE invoice_id = %s
```

Delete:

```sql
DELETE FROM vehicle WHERE vehicle_id = %s
```

Transaction-bound write sequence:

```sql
SELECT quantity_in_stock, selling_price, part_name
FROM spare_part
WHERE part_id = %s
FOR UPDATE
```

### 6. Flask Integration Explanation

Relational operations are exposed as application workflows:

- Customer CRUD in `customers.py`
- Vehicle add/delete in `customers.py`
- Supplier and part CRUD in `inventory.py`
- Job create/update in `jobs.py`
- Invoice read/pay in `billing.py`

The wrapper `execute_write()` handles single-statement commits and rollback-on-error. Multi-statement transactions use raw connection objects from `get_db_connection()`.

### 7. Viva Questions + Detailed Answers

Q1. What proves this project follows the relational model?
A1. Data is stored in normalized tables with rows, columns, keys, and foreign-key relationships. Operations are written as SQL over those relations, not as object-only in-memory structures.

Q2. Which constraint enforces one invoice per service job?
A2. `invoice.job_id` is marked `UNIQUE`, so at most one invoice row can exist for a given `service_job.job_id`.

Q3. What is a constraint violation example from this project?
A3. Inserting a second vehicle with the same `registration_no` violates the unique constraint on `vehicle.registration_no`. The route in `customers.py` catches MySQL error `1062`.

Q4. Give an example of transaction use in the relational model here.
A4. When a mechanic marks a job as completed, the route locks stock rows, deducts inventory, updates the job, inserts the invoice, and only then commits. If any step fails, the whole transaction rolls back.

Q5. What is the difference between delete cascade and the manual transaction delete used in Flask?
A5. `ON DELETE CASCADE` is a database-level automatic referential action, while the route-based deletions in `customers.py` and `inventory.py` are application-controlled multi-step cascades executed inside explicit transactions for demonstrative DBMS behavior.

### 8. Common Examiner Follow-up Questions

- Why is `ON DELETE CASCADE` only used on `vehicle.customer_id`?
- Why does the app still manually delete dependent rows if some cascade support already exists?
- What happens if invoice insertion fails after stock deduction?
- Which operations are autocommit-style and which are explicit transactions?

### 9. Real Workflow Example from Project

Vehicle deletion route:

1. Start transaction.
2. Read all service jobs for that vehicle.
3. Delete invoices for those jobs.
4. Delete service jobs.
5. Delete the vehicle.
6. Commit.

If any SQL error occurs, rollback restores the previous state.

### 10. Important Technical Terms

Relation, tuple, attribute, primary key, candidate key, foreign key, constraint, referential integrity, update operation, transaction.

### Table-by-Table Relational Summary

| Table | Primary Key | Important Alternate/Unique Key | Foreign Keys |
|---|---|---|---|
| `user` | `user_id` | `username` | none |
| `customer` | `customer_id` | none declared | none |
| `supplier` | `supplier_id` | none declared | none |
| `vehicle` | `vehicle_id` | `registration_no` | `customer_id` |
| `spare_part` | `part_id` | `part_number` | `supplier_id` |
| `service_job` | `job_id` | none declared | `vehicle_id`, `customer_id`, `user_id` |
| `invoice` | `invoice_id` | `job_id` | `job_id`, `customer_id` |
| `db_log` | `log_id` | none declared | none |

### Real Constraint Violation Cases in This Project

1. Duplicate vehicle registration number.
2. Duplicate spare part number.
3. Duplicate invoice for the same job.
4. Direct deletion of referenced parent rows would violate `RESTRICT`.
5. Completing a job with insufficient stock causes logical rollback before negative inventory can appear.

## 5. Relational Algebra

### 1. Concept Name

Unary, binary, aggregate, and grouping operations in relational algebra.

### 2. Simple Theory Explanation

Relational algebra is the formal procedural foundation behind SQL. Unary operations act on one relation, binary operations combine two relations, and aggregate/grouping operations summarize data.

### 3. Where It Exists in This Project

The project implements relational algebra through SQL queries in routes and dashboard analytics.

### 4. Real Table/Column Examples

Unary operation examples:

- Selection on `service_job.status`
- Projection on `customer.full_name, phone`

Binary operation examples:

- Join between `vehicle` and `customer`
- Join between `invoice`, `service_job`, `vehicle`, `customer`, and `user`

Aggregate/grouping examples:

- `COUNT(*)` for active jobs
- `SUM(grand_total)` for unpaid totals
- `GROUP BY status` for job chart
- `GROUP BY YEAR(invoice_date), MONTH(invoice_date)` for revenue chart

### 5. SQL Examples from Project

Selection:

```sql
SELECT COUNT(*) AS active_jobs
FROM service_job
WHERE status IN ('Pending', 'In Progress')
```

Projection:

```sql
SELECT customer_id, full_name, phone
FROM customer
ORDER BY full_name ASC
```

Join:

```sql
SELECT v.*, c.full_name AS owner_name
FROM vehicle v
JOIN customer c ON v.customer_id = c.customer_id
```

Grouping:

```sql
SELECT status, COUNT(*) AS job_count
FROM service_job
GROUP BY status
```

### 6. Flask Integration Explanation

Flask converts algebraic operations into user features:

- Search customer: selection
- Show vehicle owner: join
- Show billing receipt: multi-way join
- Build dashboard charts: aggregation and grouping

### 7. Viva Questions + Detailed Answers

Q1. Give one unary relational algebra operation used in this project.
A1. Selection is used in queries like `WHERE payment_status = 'Unpaid'` or `WHERE quantity_in_stock <= reorder_level`.

Q2. Give one binary operation used here.
A2. Join is used heavily. For example, `vehicle JOIN customer` is used to show owner names with vehicle records.

Q3. Which query demonstrates aggregate algebra?
A3. The dashboard query `SELECT status, COUNT(*) AS job_count FROM service_job GROUP BY status` shows grouping and aggregate count.

Q4. What is the relational algebra behind the receipt page?
A4. It is effectively a multi-way join across `invoice`, `customer`, `service_job`, `vehicle`, and `user`, followed by selection on one `job_id`.

### 8. Common Examiner Follow-up Questions

- What is the difference between selection and projection?
- Which project query is a join chain?
- Is union used anywhere?
- Is set difference explicitly used anywhere?

### 9. Real Workflow Example from Project

When the invoice receipt page loads, it selects one invoice by `job_id`, joins the invoice with the customer who pays, the service job that generated it, the vehicle serviced, and the mechanic assigned. That is the live operational use of relational algebra.

### 10. Important Technical Terms

Selection, projection, join, grouping, aggregation, relation, sigma, pi, theta join, multi-way join.

### Project-Specific Relational Algebra Expressions

1. Pending and in-progress jobs:

`sigma status in {'Pending', 'In Progress'} (service_job)`

2. Customer phone directory:

`pi full_name, phone (customer)`

3. Vehicles with owners:

`vehicle join vehicle.customer_id = customer.customer_id customer`

4. Invoice receipt:

`sigma invoice.job_id = J (invoice join service_job join vehicle join customer join user)`

5. Dashboard job distribution:

`gamma status; count(*) -> job_count (service_job)`

6. Revenue chart:

`gamma month(invoice_date); sum(grand_total) -> total_revenue (invoice)`

Note on absent operators:

- SQL `UNION`, `INTERSECT`, and `EXCEPT` are not implemented in the project.
- SQL views are also not implemented.

## 6. Mapping ER to Relational Design

### 1. Concept Name

Mapping ER entities and relationships into tables, keys, and associations.

### 2. Simple Theory Explanation

ER-to-relational mapping converts entity types into tables, attributes into columns, one-to-many relationships into foreign keys, one-to-one relationships into foreign keys with uniqueness, and many-to-many relationships into junction tables.

### 3. Where It Exists in This Project

The mapping is visible directly in `database/schema.sql`.

### 4. Real Table/Column Examples

Entity to table:

- `Customer` entity -> `customer` table
- `Vehicle` entity -> `vehicle` table
- `Service Job` entity -> `service_job` table

1:N relationship to foreign key:

- `customer` to `vehicle` -> `vehicle.customer_id`
- `supplier` to `spare_part` -> `spare_part.supplier_id`

1:1 relationship:

- `service_job` to `invoice` -> `invoice.job_id UNIQUE`

### 5. SQL Examples from Project

```sql
CREATE TABLE IF NOT EXISTS spare_part (
    part_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    ...
    CONSTRAINT fk_part_supplier
        FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
        ON DELETE RESTRICT
);
```

```sql
CREATE TABLE IF NOT EXISTS invoice (
    invoice_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL UNIQUE,
    ...
    CONSTRAINT fk_invoice_job
        FOREIGN KEY (job_id) REFERENCES service_job(job_id)
);
```

### 6. Flask Integration Explanation

Each mapped relationship becomes usable in joins and forms:

- Customer page uses `customer` plus `vehicle`
- Job page uses `service_job` plus `vehicle`, `customer`, `user`
- Billing page uses `invoice` plus `service_job`, `vehicle`, `customer`, `user`

### 7. Viva Questions + Detailed Answers

Q1. How was the customer-to-vehicle ER relationship converted to the relational model?
A1. By placing `customer_id` as a foreign key inside the `vehicle` table, which is the standard mapping for a one-to-many relationship.

Q2. How was the service_job-to-invoice one-to-one relationship enforced?
A2. `invoice.job_id` is both a foreign key and a unique attribute. That allows only one invoice per service job.

Q3. Where is the many-to-many mapping for parts used in jobs?
A3. It is not implemented as a proper junction table. Instead, the project stores parts usage as JSON inside `service_job.parts_used`, which is a denormalized shortcut.

Q4. What would be the correct normalized association table?
A4. A proper design would create something like `service_job_parts(job_id, part_id, quantity, unit_price, line_total)`.

### 8. Common Examiner Follow-up Questions

- Why is JSON storage weaker than a junction table?
- What extra integrity does a junction table give?
- Why can invoice be called a one-to-one extension of service_job?

### 9. Real Workflow Example from Project

When a mechanic completes a job, the route inserts a new row into `invoice` using the completed `job_id`. That is a live example of how the relational design extends a service job with a one-to-one invoice entity.

### 10. Important Technical Terms

Mapping, foreign key, participation, one-to-many, one-to-one, junction table, association, denormalization, entity-to-table conversion.

------------------------------------------------------------
## MODULE 3
------------------------------------------------------------

## 7. Normalization

### 1. Concept Name

Functional dependencies, 1NF, 2NF, 3NF, BCNF, 4NF, 5NF, and multivalued dependencies.

### 2. Simple Theory Explanation

Normalization reduces redundancy and update anomalies by decomposing relations based on dependencies:

- 1NF: atomic values only
- 2NF: no partial dependency on composite keys
- 3NF: no transitive dependency among non-key attributes
- BCNF: every determinant should be a candidate key
- 4NF: remove multivalued dependencies
- 5NF: remove join dependencies that cause redundancy

### 3. Where It Exists in This Project

Normalization can be studied directly from:

- `database/schema.sql`
- `database/sample_inserts.sql`
- `templates/db_showcase.html`, which explicitly discusses normalization trade-offs

### 4. Real Table/Column Examples

#### Table-by-table normalization analysis

**`user`**

- Main FD: `user_id -> username, password, role, full_name, phone`
- Also `username -> user_id, password, role, full_name, phone` because `username` is unique
- 1NF: yes
- 2NF: yes, single-column key
- 3NF: yes
- BCNF: yes, since determinants are candidate keys

**`customer`**

- FD: `customer_id -> full_name, phone, email, address`
- 1NF: yes
- 2NF: yes
- 3NF: yes
- BCNF: yes under the implemented constraints
- Note: phone and email are not declared unique, so the system allows duplicate contact values

**`supplier`**

- FD: `supplier_id -> supplier_name, contact_person, phone, email`
- 1NF to BCNF: yes, given implemented attributes

**`vehicle`**

- FD: `vehicle_id -> customer_id, registration_no, make, model, manufacture_year, mileage`
- Also `registration_no -> vehicle_id, customer_id, make, model, manufacture_year, mileage`
- 1NF: yes
- 2NF: yes
- 3NF: yes
- BCNF: yes

**`spare_part`**

- FD: `part_id -> supplier_id, part_name, part_number, category, quantity_in_stock, reorder_level, unit_cost, selling_price`
- Also `part_number -> ...` because `part_number` is unique
- 1NF: yes
- 2NF: yes
- 3NF: yes
- BCNF: yes

**`service_job`**

- FD from surrogate key: `job_id -> vehicle_id, customer_id, user_id, job_date, complaint, diagnosis, parts_used, labour_charge, status`
- Hidden business FD: `vehicle_id -> customer_id` because each vehicle belongs to one customer
- 1NF: not strictly satisfied because `parts_used` stores a JSON array, not atomic values
- 2NF: not meaningfully discussed until 1NF is satisfied
- 3NF: also weakened by storing both `vehicle_id` and `customer_id`, creating potential transitive redundancy
- BCNF: not satisfied cleanly as implemented
- Strong viva point: this is the biggest normalization compromise in the project

**`invoice`**

- FD: `invoice_id -> job_id, customer_id, invoice_date, labour_total, parts_total, grand_total, payment_status, payment_method`
- Also `job_id -> invoice_id, customer_id, invoice_date, labour_total, parts_total, grand_total, payment_status, payment_method` because `job_id` is unique
- Derived FD: `(labour_total, parts_total) -> grand_total`
- Transitive business FD: `job_id -> customer_id`
- 1NF: yes
- 2NF: yes
- 3NF: not strict, because `grand_total` is derived and `customer_id` is redundant if job already identifies customer
- BCNF: not strict for the same reason
- This table is intentionally denormalized for convenience and faster billing queries

**`db_log`**

- FD: `log_id -> event_type, table_name, reference_id, message, created_at`
- 1NF to BCNF: yes for the runtime structure

### 5. SQL Examples from Project

1NF issue source:

```sql
parts_used LONGTEXT
```

Sample non-atomic value:

```sql
'[{"part_id":1,"part_name":"Engine Oil 5W30","quantity":1,"unit_price":900.0,"line_total":900.0}]'
```

Derived total source:

```sql
labour_total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
parts_total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
grand_total DECIMAL(10, 2) NOT NULL DEFAULT 0.00
```

### 6. Flask Integration Explanation

Flask reinforces some normalization choices and also exposes some compromises:

- `jobs/edit.html` constructs `parts_used_json` on the client side and posts it back as one JSON string
- `billing.py` parses the same JSON string to show invoice parts
- Because parts are not in a junction table, the app cannot enforce foreign-key integrity on each used-part line after storage

### 7. Viva Questions + Detailed Answers

Q1. Which table is the clearest 1NF violation in this project?
A1. `service_job`, because `parts_used` stores multiple parts and fields inside one `LONGTEXT` JSON value instead of atomic tuples.

Q2. Is the whole database fully normalized to 3NF?
A2. No. Most master tables are close to 3NF or BCNF, but `service_job` and `invoice` contain denormalized elements for simplicity and faster application development.

Q3. Why can `invoice` be said to violate strict 3NF?
A3. Because `grand_total` is derivable from `labour_total + parts_total`, and `customer_id` is redundant once `job_id` already identifies the related service job.

Q4. Why is `service_job.customer_id` redundant?
A4. Because `service_job.vehicle_id` points to `vehicle`, and `vehicle.customer_id` already identifies the owner. So storing `customer_id` again in `service_job` duplicates information and can create anomalies if values ever mismatch.

Q5. How would you normalize the parts-used design?
A5. Create a table like `service_job_parts(job_id, part_id, quantity, unit_price, line_total)` and remove the JSON array from `service_job.parts_used`.

### 8. Common Examiner Follow-up Questions

- Which tables are in BCNF?
- Why is denormalization sometimes acceptable?
- What anomalies can happen if `vehicle_id` and `customer_id` mismatch in `service_job`?
- Why is sample data not the same as perfect normalization?

### 9. Real Workflow Example from Project

When the mechanic adds parts on the job-edit page, the browser builds a JSON array and stores it into a hidden field. Flask writes that entire JSON array into `service_job.parts_used`. Later, the invoice receipt reads and parses that JSON. This is a working feature, but academically it is a normalization compromise.

### 10. Important Technical Terms

Functional dependency, atomicity, transitive dependency, multivalued dependency, BCNF, denormalization, update anomaly, redundancy, junction table.

### 4NF and 5NF Discussion for This Project

- Tables like `user`, `customer`, `supplier`, `vehicle`, and `spare_part` do not show visible multivalued dependencies, so 4NF concerns are minimal.
- `service_job.parts_used` hides a multivalued dependency inside JSON. If decomposed properly, 4NF analysis would become cleaner.
- 5NF is not a major live issue here because the schema does not decompose highly complex many-way relations into multiple joinable fragments.

### Honest Academic Defense

This project is good for viva because it shows both good normalization and deliberate academic trade-offs:

- Strong normalization in master tables
- Demonstrative denormalization in transactional tables
- A clear upgrade path to a more formal design

## 8. SQL

### 1. Concept Name

DDL, constraints, retrieval queries, insert/update/delete operations, and additional SQL features.

### 2. Simple Theory Explanation

SQL is the language used to define, query, and modify relational databases. Major categories include:

- DDL: schema creation
- DML/query: `SELECT`, `INSERT`, `UPDATE`, `DELETE`
- TCL: transaction control
- Procedural SQL: triggers and stored procedures

### 3. Where It Exists in This Project

- DDL: `database/schema.sql`
- Procedural SQL: `database/triggers_procedures.sql` and runtime creation in `app/db.py`
- DML/query: route files
- TCL: explicit transaction code in routes

### 4. Real Table/Column Examples

Constraint examples:

- `user.username UNIQUE`
- `vehicle.registration_no UNIQUE`
- `spare_part.part_number UNIQUE`
- `invoice.job_id UNIQUE`
- `NOT NULL` across essential columns
- `ENUM` for `role`, `status`, `payment_status`, `payment_method`
- `FOREIGN KEY` relations

### 5. SQL Examples from Project

DDL:

```sql
CREATE DATABASE IF NOT EXISTS garage_db;
USE garage_db;
```

Retrieval:

```sql
SELECT i.*, c.full_name AS customer_name, c.phone AS customer_phone,
       v.registration_no, v.make, v.model, j.job_date
FROM invoice i
JOIN customer c ON i.customer_id = c.customer_id
JOIN service_job j ON i.job_id = j.job_id
JOIN vehicle v ON j.vehicle_id = v.vehicle_id
ORDER BY i.invoice_id DESC
```

Update:

```sql
UPDATE spare_part
SET quantity_in_stock = quantity_in_stock + %s
WHERE part_id = %s
```

Delete:

```sql
DELETE FROM supplier WHERE supplier_id = %s
```

Aggregate:

```sql
SELECT COALESCE(SUM(grand_total), 0.00) AS unpaid_invoices
FROM invoice
WHERE payment_status = 'Unpaid'
```

### 6. Flask Integration Explanation

Each route corresponds to SQL categories:

- `customers.py`: insert, update, delete, select
- `inventory.py`: insert, update, delete, select
- `jobs.py`: insert, update, transaction control, row locking
- `billing.py`: select and update
- `dashboard.py`: aggregates and grouped analytics
- `db_showcase.py`: metadata query and stored procedure calls

### 7. Viva Questions + Detailed Answers

Q1. Which SQL categories are demonstrated by this project?
A1. DDL, DML, query language, TCL, triggers, and stored procedures. DCL is not explicitly implemented with GRANT/REVOKE statements.

Q2. Is `ALTER TABLE` used?
A2. No. The schema is defined using `CREATE TABLE`, and runtime advanced objects are recreated programmatically. There is no explicit `ALTER TABLE` statement in the inspected project files.

Q3. Is `CHECK` constraint used?
A3. No explicit `CHECK` constraint is declared. Instead, the project uses `NOT NULL`, `UNIQUE`, `ENUM`, foreign keys, and Flask-side validation to enforce rules.

Q4. What additional SQL features beyond basic CRUD are present?
A4. `ENUM`, `COALESCE`, `DATE_FORMAT`, `CURDATE`, `FOR UPDATE`, metadata queries through `INFORMATION_SCHEMA`, triggers, stored procedures, and OUT variables.

### 8. Common Examiner Follow-up Questions

- Why use `ENUM` for job status?
- Why use `COALESCE` in unpaid invoice sum?
- Why are parameterized placeholders `%s` used?
- Why is there no explicit SQL view?

### 9. Real Workflow Example from Project

On the billing page, the system retrieves invoices using joins, then updates the same invoice row when payment is settled. This shows read and write SQL in one module using the same relational state.

### 10. Important Technical Terms

DDL, DML, TCL, parameterized query, aggregate, join, enum, constraint, metadata query, procedural SQL.

### Concepts Not Implemented and How to Say It in Viva

- `ALTER TABLE`: not present in the current codebase
- `CHECK`: not declared in schema
- SQL `VIEW`: not implemented
- SQL `ASSERTION`: not implemented

Good defense line:

"This project focuses on core relational design, transactions, triggers, and stored procedures. Some advanced SQL constructs like SQL views and assertions are not implemented in the current version."

------------------------------------------------------------
## MODULE 4
------------------------------------------------------------

## 9. Advanced SQL

### 1. Concept Name

Complex queries, assertions, action triggers, and views.

### 2. Simple Theory Explanation

Advanced SQL extends basic CRUD with richer query logic, automatic actions through triggers, derived presentation objects like views, and integrity constructs like assertions.

### 3. Where It Exists in This Project

Implemented:

- Complex joins and aggregates
- Action triggers
- Stored procedures
- Metadata queries

Not implemented:

- SQL views
- SQL assertions

### 4. Real Table/Column Examples

Complex retrieval:

- Invoice receipt joins 5 tables
- Revenue chart groups invoice totals by month
- Job distribution groups by status
- Schema showcase queries `INFORMATION_SCHEMA.COLUMNS`

Trigger tables involved:

- `service_job`
- `spare_part`
- `invoice`
- `db_log`

### 5. SQL Examples from Project

Trigger 1:

```sql
CREATE TRIGGER trg_job_completion_audit
AFTER UPDATE ON service_job
FOR EACH ROW
BEGIN
    IF OLD.status <> 'Completed' AND NEW.status = 'Completed' THEN
        INSERT INTO db_log (...)
    END IF;
END
```

Trigger 2:

```sql
CREATE TRIGGER trg_low_stock_alert
AFTER UPDATE ON spare_part
FOR EACH ROW
BEGIN
    IF NEW.quantity_in_stock <= NEW.reorder_level
       AND OLD.quantity_in_stock > NEW.reorder_level THEN
        INSERT INTO db_log (...)
    END IF;
END
```

Trigger 3:

```sql
CREATE TRIGGER trg_invoice_insert_audit
AFTER INSERT ON invoice
FOR EACH ROW
BEGIN
    INSERT INTO db_log (...)
END
```

### 6. Flask Integration Explanation

- `dashboard.py` uses advanced grouped queries and a stored procedure
- `db_showcase.py` displays trigger logs and executes stored procedures
- `jobs.py` triggers database-side logging indirectly when a job is completed and an invoice is inserted

### 7. Viva Questions + Detailed Answers

Q1. Which advanced SQL features are actually implemented in this project?
A1. Triggers, stored procedures, grouped aggregates, metadata queries, row locking, and multi-table joins are implemented. SQL views and assertions are not.

Q2. Explain `trg_job_completion_audit`.
A2. It is an `AFTER UPDATE` trigger on `service_job`. It checks whether a row changed from a non-completed status to `Completed`. If so, it inserts an audit message into `db_log`.

Q3. Explain `trg_low_stock_alert`.
A3. It is an `AFTER UPDATE` trigger on `spare_part`. It fires when stock crosses from above reorder level to at-or-below reorder level. It logs a low-stock warning.

Q4. Explain `trg_invoice_insert_audit`.
A4. It is an `AFTER INSERT` trigger on `invoice`. Whenever a new invoice row is inserted, it automatically logs invoice generation into `db_log`.

Q5. Are SQL views used for dashboard analytics?
A5. No. The dashboard uses direct SQL queries and one stored procedure. There is no `CREATE VIEW` statement in the inspected project.

### 8. Common Examiner Follow-up Questions

- Why are triggers useful here?
- Why use `AFTER UPDATE` instead of `BEFORE UPDATE`?
- Why is the low-stock condition based on threshold crossing?
- Could the dashboard have been built with views?

### 9. Real Workflow Example from Project

When a mechanic completes a service job:

1. Flask updates `service_job.status` to `Completed`.
2. `trg_job_completion_audit` writes a completion event.
3. Flask inserts an `invoice`.
4. `trg_invoice_insert_audit` writes an invoice event.
5. If stock fell to or below reorder level, `trg_low_stock_alert` also logs a warning.

That one workflow shows all three triggers interacting with application logic.

### 10. Important Technical Terms

Trigger, `AFTER UPDATE`, `AFTER INSERT`, old row, new row, audit log, grouped aggregate, metadata query, event-driven SQL.

### Trigger Lifecycle Explanation

**`trg_job_completion_audit`**

- Event: update on `service_job`
- Timing: after update
- Condition: status changed to `Completed`
- Effect: insert audit row into `db_log`

**`trg_low_stock_alert`**

- Event: update on `spare_part`
- Timing: after update
- Condition: stock crosses threshold from safe to low
- Effect: insert low-stock warning into `db_log`

**`trg_invoice_insert_audit`**

- Event: insert on `invoice`
- Timing: after insert
- Condition: always on invoice insert
- Effect: insert audit row into `db_log`

### Assertion and View Status

- SQL assertion: not implemented
- SQL view: not implemented

Safe viva answer:

"The project uses triggers and direct queries instead of SQL views or assertions. Assertions are absent, and integrity is enforced using foreign keys, unique constraints, application validation, and transaction logic."

## 10. Transaction Processing

### 1. Concept Name

Transaction concepts, ACID properties, recoverability, serializability, and SQL transaction support.

### 2. Simple Theory Explanation

A transaction is a logical unit of work that must be all-or-nothing. ACID means:

- Atomicity: either everything happens or nothing happens
- Consistency: database rules remain valid
- Isolation: concurrent transactions do not interfere incorrectly
- Durability: once committed, changes persist

### 3. Where It Exists in This Project

Single-statement transactional wrappers:

- `execute_write()` in `app/db.py`

Explicit multi-statement transactions:

- `jobs.update_job()` when status becomes `Completed`
- `customers.delete_customer()`
- `customers.delete_vehicle()`
- `inventory.delete_supplier()`

### 4. Real Table/Column Examples

Job-completion transaction touches:

- `spare_part.quantity_in_stock`
- `service_job.status`
- `service_job.diagnosis`
- `service_job.parts_used`
- `service_job.labour_charge`
- `invoice.job_id`
- `invoice.customer_id`
- `invoice.grand_total`

Deletion transaction examples:

- `customer`, `vehicle`, `service_job`, `invoice`
- `vehicle`, `service_job`, `invoice`
- `supplier`, `spare_part`

### 5. SQL Examples from Project

Core transactional locking query:

```sql
SELECT quantity_in_stock, selling_price, part_name
FROM spare_part
WHERE part_id = %s
FOR UPDATE
```

Inventory deduction:

```sql
UPDATE spare_part
SET quantity_in_stock = quantity_in_stock - %s
WHERE part_id = %s
```

Job finalization:

```sql
UPDATE service_job
SET status = 'Completed', diagnosis = %s, parts_used = %s, labour_charge = %s
WHERE job_id = %s
```

Invoice generation:

```sql
INSERT INTO invoice (job_id, customer_id, invoice_date, labour_total, parts_total, grand_total, payment_status, payment_method)
VALUES (%s, %s, CURDATE(), %s, %s, %s, 'Unpaid', 'Cash')
```

### 6. Flask Integration Explanation

Flask explicitly manages transaction boundaries by calling:

- `conn.start_transaction()`
- `conn.commit()`
- `conn.rollback()`

The app also writes transaction audit traces to `logs/db_logs.log` using `log_db_activity()`, so the transaction story is visible not only in code but also in logging.

### 7. Viva Questions + Detailed Answers

Q1. Where is the most important transaction in this project?
A1. In `jobs.update_job()` when a job is marked `Completed`. It locks spare-part rows, validates stock, deducts inventory, updates the job sheet, creates the invoice, and then commits. On failure, it rolls back all steps.

Q2. How is atomicity achieved?
A2. All related writes are executed inside one explicit transaction. If any step fails, `rollback()` is called, so no partial stock deduction, partial job update, or partial invoice insertion remains.

Q3. How is consistency preserved?
A3. The route checks stock before deduction, prevents duplicate invoices for the same `job_id`, and relies on foreign keys and unique constraints. This ensures the database does not end up with impossible states such as negative stock or duplicate invoices for one job.

Q4. How is isolation addressed?
A4. The route uses `SELECT ... FOR UPDATE` on each spare-part row, which row-locks the inventory record during the transaction. This reduces concurrent race conditions when two users might update stock for the same part.

Q5. How is durability achieved?
A5. After `conn.commit()`, MySQL permanently records the change, assuming the transactional engine persists the commit. The project relies on MySQL's transaction support for this.

Q6. Is serializability explicitly configured?
A6. No. The code does not set the transaction isolation level to `SERIALIZABLE`. It improves isolation through row locks, but full serializability is not explicitly declared in application code.

Q7. What is recoverability in this project?
A7. Recoverability means uncommitted changes should not become visible as permanent committed state. If stock deduction succeeds but invoice insert fails, rollback restores the pre-transaction state, so the database recovers to a valid earlier state.

### 8. Common Examiner Follow-up Questions

- What exactly rolls back on insufficient stock?
- Why check for an existing invoice before insert?
- Why use `FOR UPDATE`?
- Is every route a transaction?
- What happens if commit is never reached?

### 9. Real Workflow Example from Project

#### Detailed service-completion transaction flow

1. Mechanic submits the job edit form with status `Completed`.
2. Flask loads the target `service_job`.
3. Flask starts an explicit transaction.
4. Flask checks whether an invoice already exists for that job.
5. Flask parses `parts_used_json`.
6. For each part:
   - row-lock the `spare_part` row using `FOR UPDATE`
   - verify enough stock exists
   - deduct `quantity_in_stock`
   - accumulate line totals
7. Flask computes `grand_total = labour_charge + parts_total`.
8. Flask updates the `service_job` row to `Completed`.
9. Flask inserts a new `invoice`.
10. MySQL triggers fire on the update and insert.
11. Flask commits.
12. Logging snapshots are written.

If any error happens in steps 4 to 10, Flask rolls back and the database returns to the pre-transaction state.

### 10. Important Technical Terms

ACID, row lock, `FOR UPDATE`, commit, rollback, atomicity, isolation, recoverability, concurrency control, transaction boundary.

### Extremely Detailed ACID Mapping

**Atomicity**

- Demonstrated most clearly in job completion.
- Either stock is deducted, job is completed, and invoice is created together, or none of them persist.
- Also demonstrated in manual cascading deletes for customer, vehicle, and supplier removal.

**Consistency**

- Unique keys prevent duplicate identities.
- Foreign keys prevent orphan relations.
- Pre-insert invoice existence check prevents duplicate billing for one job.
- Stock validation prevents illogical negative quantity.

**Isolation**

- `SELECT ... FOR UPDATE` locks the targeted spare-part row until commit or rollback.
- This is important if multiple users work on overlapping stock.
- The project does not explicitly set isolation level, so the exact isolation semantics depend on MySQL defaults.

**Durability**

- After successful commit, the state remains in MySQL.
- The project also logs committed activity in `logs/db_logs.log`, which is useful as an operational trace, although the real durability guarantee comes from the DBMS, not the log file.

### Concrete Rollback Scenarios from the Code

1. Insufficient stock for one of the selected parts.
2. The selected part ID no longer exists.
3. An invoice already exists for the target service job.
4. A database error occurs during dependent deletes.
5. Any unexpected exception after transaction start but before commit.

### Recoverability and Serializability: Honest Academic Answer

Recoverability is clearly supported because failed multi-step workflows call `rollback()` before commit. Serializability is not explicitly guaranteed because the application never sets serializable isolation level, but row-level locking through `FOR UPDATE` provides stronger isolation than a naive concurrent update design.

------------------------------------------------------------
## SPECIAL SECTION - ADVANCED DBMS FEATURES
------------------------------------------------------------

## 11. Cursor-Based Procedures, Procedural SQL, Handlers, Loops, Fetch, Audit Logging, Dashboard Integration

### 1. Concept Name

MySQL procedural SQL with cursors, loops, handlers, OUT parameters, and database-side automation.

### 2. Simple Theory Explanation

Stored procedures allow logic to run inside the DBMS. Cursors iterate row by row. Handlers define what happens when cursor fetches are exhausted or errors occur. OUT parameters return computed results to callers.

### 3. Where It Exists in This Project

Live runtime definitions are installed from `app/db.py`:

- `get_monthly_revenue_summary`
- `get_low_stock_report`
- `trg_job_completion_audit`
- `trg_low_stock_alert`
- `trg_invoice_insert_audit`
- `db_log`

Procedures are executed from:

- `app/routes/dashboard.py`
- `app/routes/db_showcase.py`

### 4. Real Table/Column Examples

Procedure 1 reads:

- `invoice.grand_total`
- `invoice.payment_status`
- `invoice.invoice_date`

Procedure 2 reads:

- `spare_part.part_name`
- `spare_part.quantity_in_stock`
- `spare_part.reorder_level`

Trigger logging writes:

- `db_log.event_type`
- `db_log.table_name`
- `db_log.reference_id`
- `db_log.message`
- `db_log.created_at`

### 5. SQL Examples from Project

Cursor declaration:

```sql
DECLARE inv_cursor CURSOR FOR
    SELECT grand_total FROM invoice
    WHERE payment_status = 'Paid'
    AND MONTH(invoice_date) = MONTH(CURDATE())
    AND YEAR(invoice_date) = YEAR(CURDATE());
```

Handler:

```sql
DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
```

Loop and fetch:

```sql
read_loop: LOOP
    FETCH inv_cursor INTO inv_amount;
    IF done THEN
        LEAVE read_loop;
    END IF;
    SET cur_sales = cur_sales + inv_amount;
    SET cur_count = cur_count + 1;
END LOOP;
```

OUT parameter return:

```sql
SET total_sales = cur_sales;
SET invoice_count = cur_count;
```

### 6. Flask Integration Explanation

Dashboard integration:

- Calls `CALL get_monthly_revenue_summary(@total_sales, @invoice_count)`
- Reads `SELECT @total_sales, @invoice_count`
- Shows current-month revenue KPI

Showcase integration:

- Calls both procedures from owner-only buttons
- Renders returned values as flash messages
- Also shows live `db_log` trigger outputs

### 7. Viva Questions + Detailed Answers

Q1. Why use a cursor in `get_monthly_revenue_summary` instead of only `SUM()`?
A1. Academically, it demonstrates cursor handling, loop control, OUT parameters, and DBMS procedural logic. In practice, a single aggregate query could compute the same result more simply, but this project intentionally showcases advanced DBMS syllabus concepts.

Q2. What does the `CONTINUE HANDLER FOR NOT FOUND` do?
A2. It sets the `done` flag when the cursor reaches the end of its result set. That allows the loop to terminate cleanly after the last row is fetched.

Q3. How are OUT parameters used by Flask?
A3. Flask first calls the procedure with session variables such as `@total_sales`, then executes a `SELECT` on those variables to retrieve the final values into Python.

Q4. What is the educational value of `get_low_stock_report`?
A4. It demonstrates row-by-row cursor processing, string building inside procedural SQL, and returning a formatted result through an OUT parameter rather than a normal result set.

Q5. How does audit logging work here?
A5. It is database-side automation. Triggers on `service_job`, `spare_part`, and `invoice` automatically insert human-readable messages into `db_log`, and the Flask showcase page displays those logs.

### 8. Common Examiner Follow-up Questions

- Could `get_monthly_revenue_summary` be replaced by one aggregate query?
- Why is a handler needed in cursor logic?
- Why use OUT parameters instead of returning a result set?
- What is the difference between Flask logs and `db_log`?

### 9. Real Workflow Example from Project

Seed data includes three paid invoices:

- Job 2: `3250.00`
- Job 4: `2800.00`
- Job 7: `1700.00`

If these rows are in the current month, `get_monthly_revenue_summary` loops over them and returns:

- `total_sales = 7750.00`
- `invoice_count = 3`

Seed data also contains low-stock part:

- `Air Filter`: stock `6`, reorder level `8`

So `get_low_stock_report` would produce a report line for `Air Filter`.

### 10. Important Technical Terms

Stored procedure, cursor, handler, fetch, loop, OUT parameter, session variable, audit log, procedural SQL, trigger event.

### Step-by-Step Cursor Flow: `get_monthly_revenue_summary`

1. Initialize `done = FALSE`, `cur_sales = 0`, `cur_count = 0`.
2. Declare a cursor over paid invoices in the current month.
3. Declare a `CONTINUE HANDLER` to set `done = TRUE` when no more rows remain.
4. Open cursor.
5. Fetch one `grand_total` into `inv_amount`.
6. If `done` became true, leave loop.
7. Otherwise add amount to `cur_sales` and increment `cur_count`.
8. Repeat until exhausted.
9. Close cursor.
10. Assign OUT parameters.

### Step-by-Step Cursor Flow: `get_low_stock_report`

1. Initialize output text header.
2. Open cursor over parts where `quantity_in_stock <= reorder_level`.
3. Fetch `part_name`, `quantity_in_stock`, `reorder_level`.
4. Append one formatted line to the report.
5. Count how many low-stock parts were found.
6. If none were found, return the "all above reorder limits" message.
7. Return final report text through `report_out`.

### Important Live Behavior Note

The showcase page expects `db_log` columns named `event_type`, `reference_id`, and `created_at`, which confirms that the runtime `app/db.py` version of `db_log` is the live one used by the application.

------------------------------------------------------------
## PROJECT-SPECIFIC WORKFLOW MAPPING
------------------------------------------------------------

## End-to-End Workflow 1: Customer and Vehicle Registration

1. User logs in.
2. Receptionist/manager/owner opens `/customers`.
3. Customer is inserted into `customer`.
4. Vehicle is inserted into `vehicle` with `customer_id`.
5. Unique registration number prevents duplicates.

DBMS concepts shown:

- Insert operations
- Foreign keys
- Unique constraints
- Role-based access

## End-to-End Workflow 2: Service Job Intake

1. Receptionist/manager/owner opens `/jobs`.
2. Selects customer, vehicle, and mechanic.
3. Inserts a row into `service_job` with status `Pending`.

DBMS concepts shown:

- Insert into transaction table
- Relationship usage among customer, vehicle, and user
- Data entry validation

## End-to-End Workflow 3: Job Completion and Invoice Generation

1. Mechanic edits assigned job.
2. Chooses parts and labour.
3. Submits with status `Completed`.
4. Transaction starts.
5. Stock rows are locked and validated.
6. Stock is deducted.
7. Service job is updated.
8. Invoice row is inserted.
9. Triggers log completion/invoice/low-stock events.
10. Transaction commits.

DBMS concepts shown:

- ACID transaction
- Row-level locking
- Trigger firing
- Derived billing totals
- Multi-table consistency

## End-to-End Workflow 4: Billing and Payment Settlement

1. Receptionist/owner opens `/invoices`.
2. Joins fetch billing records with customer and vehicle details.
3. Opens receipt page for one job.
4. Payment status and method are updated on `invoice`.

DBMS concepts shown:

- Multi-table join
- Update operation
- Enums for payment fields

## End-to-End Workflow 5: Dashboard and Analytics

1. Owner/manager loads `/dashboard`.
2. Queries count active jobs.
3. Queries count low-stock items.
4. Calls revenue stored procedure.
5. Queries unpaid totals.
6. Queries recent jobs.
7. Queries grouped revenue and job charts.

DBMS concepts shown:

- Aggregation
- Grouping
- Stored procedures
- Analytical SQL

------------------------------------------------------------
## IMPORTANT ACADEMIC OBSERVATIONS AND DEFENSE POINTS
------------------------------------------------------------

## Strengths

1. Clear relational entity set for a realistic domain.
2. Proper use of PK, FK, UNIQUE, and `ENUM`.
3. Explicit transaction control for critical workflow.
4. Real triggers and real stored procedures.
5. A schema-inspector page backed by `INFORMATION_SCHEMA`.
6. Good viva value because the project shows both strong design and discussable trade-offs.

## Honest Limitations

1. `service_job.parts_used` is not normalized.
2. `service_job.customer_id` duplicates data derivable from `vehicle_id`.
3. `invoice.customer_id` duplicates data derivable from `job_id`.
4. `invoice.grand_total` is a derived stored value.
5. No SQL view implementation.
6. No SQL assertion implementation.
7. No explicit `CHECK` constraints.
8. No explicit isolation level setting.

## Very Good Viva Defense Sentence

"This project intentionally balances textbook normalization with implementation simplicity. Core master data is strongly relational, while `service_job.parts_used` and invoice totals are denormalized to keep workflow implementation simple for an academic mini-project and to create meaningful DBMS discussion points."

## Another Very Good Viva Defense Sentence

"The most important DBMS demonstration is not only CRUD. It is the transaction-safe job completion workflow, where stock deduction, service completion, invoice generation, and trigger-based logging all interact inside one controlled unit of work."

------------------------------------------------------------
## 50+ VIVA QUESTIONS WITH DETAILED ANSWERS
------------------------------------------------------------

1. What is the database name used in this project?
Answer: The database is `garage_db`, created in `database/schema.sql`.

2. Which DBMS is used?
Answer: MySQL is used as the DBMS, while Flask is only the application framework.

3. What are the main business tables?
Answer: `user`, `customer`, `supplier`, `vehicle`, `spare_part`, `service_job`, and `invoice`.

4. Why is `user` written with backticks in SQL?
Answer: Because `user` can conflict with SQL naming contexts, so backticks make the identifier explicit.

5. Which column ensures unique login identity?
Answer: `user.username` is unique.

6. Which column ensures unique vehicle identity from the real world?
Answer: `vehicle.registration_no` is unique.

7. Which column ensures unique inventory catalog identity?
Answer: `spare_part.part_number` is unique.

8. Which constraint enforces one invoice per job?
Answer: `invoice.job_id` is unique and also a foreign key to `service_job.job_id`.

9. Why is `vehicle.customer_id` a foreign key?
Answer: It models that every vehicle belongs to a valid customer already stored in `customer`.

10. What is the cardinality between customer and vehicle?
Answer: One-to-many. A customer may own multiple vehicles.

11. What is the cardinality between supplier and spare_part?
Answer: One-to-many. A supplier can supply many parts.

12. What is the cardinality between service_job and invoice?
Answer: One-to-one, implemented through `invoice.job_id UNIQUE`.

13. Which table stores transaction-like operational work?
Answer: `service_job` stores the garage job workflow state.

14. Which table stores billing results?
Answer: `invoice` stores billing totals, payment status, and payment method.

15. How are mechanics modeled in the schema?
Answer: They are rows in the `user` table with `role = 'mechanic'`.

16. Is specialization implemented through separate tables?
Answer: No. Role specialization is represented through an `ENUM` in `user.role`.

17. What is the most important transaction in the system?
Answer: Completing a service job in `jobs.update_job()`.

18. Why is `FOR UPDATE` used?
Answer: To lock inventory rows while stock is being checked and updated, reducing concurrency anomalies.

19. What happens if stock is not enough for a selected part?
Answer: The route raises an exception and rolls back the entire job-completion transaction.

20. What happens if an invoice already exists for the job?
Answer: The route aborts and rolls back, preventing duplicate billing for the same job.

21. How is atomicity demonstrated?
Answer: Stock deduction, job completion, and invoice insertion are committed together or rolled back together.

22. How is consistency demonstrated?
Answer: Constraints plus application checks keep the database from entering invalid states.

23. How is isolation demonstrated?
Answer: Through row locking with `SELECT ... FOR UPDATE`.

24. How is durability demonstrated?
Answer: After commit, the resulting rows stay stored in MySQL.

25. What is the purpose of `db_log`?
Answer: It stores automatic trigger-generated audit events for advanced DBMS demonstration.

26. Which trigger logs job completion?
Answer: `trg_job_completion_audit`.

27. Which trigger logs low stock?
Answer: `trg_low_stock_alert`.

28. Which trigger logs invoice generation?
Answer: `trg_invoice_insert_audit`.

29. When exactly does `trg_job_completion_audit` fire?
Answer: After an update on `service_job`, only when status changes to `Completed`.

30. Why is the low-stock trigger condition not simply `quantity_in_stock <= reorder_level`?
Answer: It also checks that the old value was above reorder level, so it fires on crossing the threshold instead of every later update.

31. Which stored procedure computes dashboard revenue?
Answer: `get_monthly_revenue_summary`.

32. Which stored procedure generates a text report?
Answer: `get_low_stock_report`.

33. Why is a cursor used in `get_monthly_revenue_summary`?
Answer: Mainly to demonstrate cursor syntax, handlers, loops, and OUT parameters for academic purposes.

34. What does the cursor handler do?
Answer: It sets `done = TRUE` when there are no more rows to fetch.

35. How does Flask retrieve OUT parameter values?
Answer: It calls the procedure with MySQL session variables like `@total_sales` and then selects those variables.

36. Does the project implement SQL views?
Answer: No. The dashboard uses direct queries instead.

37. Does the project implement SQL assertions?
Answer: No. Integrity is enforced by constraints, triggers, and application logic.

38. Does the project implement `CHECK` constraints?
Answer: No explicit `CHECK` appears in the schema.

39. Which page demonstrates metadata querying?
Answer: The DB showcase page at `/showcase`, which queries `INFORMATION_SCHEMA.COLUMNS`.

40. Which route demonstrates grouped analytics?
Answer: `dashboard.home()` with revenue grouping by month and job grouping by status.

41. Which route demonstrates a multi-way join for operational output?
Answer: `billing.receipt_invoice()` joins invoice, customer, service_job, vehicle, and user.

42. Which route demonstrates a search filter?
Answer: `customers.list_customers()` uses `LIKE` on customer name and phone.

43. Which table has the clearest 1NF violation?
Answer: `service_job`, because `parts_used` stores a JSON array.

44. Why is `service_job.parts_used` a 1NF issue?
Answer: Because one column contains multiple structured values instead of one atomic value.

45. How would you fix the 1NF issue?
Answer: Create a separate `service_job_parts` table with one row per part used in a job.

46. Why is `invoice.grand_total` academically debatable?
Answer: Because it is derivable from `labour_total + parts_total`, so it introduces redundancy.

47. Why is `service_job.customer_id` also debatable?
Answer: Because the vehicle already points to the customer, so customer can be derived from vehicle.

48. Why is `invoice.customer_id` also debatable?
Answer: Because `job_id` already identifies the service job, which already knows the customer.

49. Are master tables better normalized than transaction tables here?
Answer: Yes. `user`, `customer`, `supplier`, `vehicle`, and `spare_part` are much cleaner than `service_job` and `invoice`.

50. What is the role of `execute_write()` in `app/db.py`?
Answer: It executes one write statement, commits on success, rolls back on error, and logs the activity.

51. Why does the project use parameterized queries with `%s`?
Answer: To pass values safely and cleanly through the MySQL connector rather than building raw SQL strings for user inputs.

52. What is connection pooling in this project?
Answer: `MySQLConnectionPool` in `app/db.py` reuses database connections so the app does not create a brand-new connection for every query from scratch.

53. Does the application have DB-level role permissions?
Answer: Not through MySQL `GRANT` statements in the codebase. Role access is enforced in Flask using session-based decorators.

54. Which decorator blocks unauthenticated users?
Answer: `login_required`.

55. Which decorator restricts routes by business role?
Answer: `role_required`.

56. Why is the showcase page owner-only?
Answer: Because it exposes internal schema and advanced DBMS components, which is treated as an administrative view.

57. Is the sample data perfectly aligned with the business workflow?
Answer: Not fully. Sample inserts create invoice rows even for jobs that are `Pending` or `In Progress`, while the live application logic creates invoices only when jobs are completed.

58. Why is that mismatch useful in viva?
Answer: Because it lets you distinguish between static seeding data and runtime business rules enforced by the application transaction flow.

59. If the examiner asks "Where do triggers live?", what is the best answer?
Answer: The project stores reference trigger SQL in `database/triggers_procedures.sql`, but the live Flask app recreates them from `app/db.py` at startup.

60. If the examiner asks "What is the best DBMS feature shown by this project?", what should you say?
Answer: The best feature is the transaction-safe job completion workflow combining row locking, rollback, automatic invoice generation, and trigger-based audit logging.

------------------------------------------------------------
## SHORT EXAMINER-READY DEFENSE ANSWERS
------------------------------------------------------------

### If asked: "Why did you use JSON in `parts_used` if it violates normalization?"

Answer:
"I used JSON for implementation simplicity in a mini-project, but I understand that it is not ideal from a normalization perspective. In a production-grade design, I would replace it with a `service_job_parts` junction table."

### If asked: "Where is concurrency control in your project?"

Answer:
"Concurrency control appears in the job-completion transaction, where each required spare-part row is fetched using `FOR UPDATE` before stock deduction."

### If asked: "What is the difference between trigger logs and application logs?"

Answer:
"Trigger logs are written into the MySQL table `db_log` by database triggers. Application SQL logs are written to `logs/db_logs.log` by Python code in `app/db.py`."

### If asked: "Why not use a single SQL aggregate instead of a cursor procedure?"

Answer:
"A single aggregate would be simpler, but the cursor procedure is intentionally included to demonstrate advanced DBMS syllabus concepts like cursors, handlers, loops, and OUT parameters."

### If asked: "What part of this project is not textbook-perfect?"

Answer:
"The main compromises are the JSON `parts_used` field and some stored derived or redundant fields in transactional tables. I can clearly explain those trade-offs and the normalized redesign."

------------------------------------------------------------
## CONCLUSION
------------------------------------------------------------

This project is a strong DBMS mini-project because it demonstrates:

1. Relational schema design with real entities and keys.
2. CRUD workflows across multiple modules.
3. Referential integrity and uniqueness enforcement.
4. Explicit transaction processing with rollback.
5. Trigger-based audit logging.
6. Cursor-based stored procedures.
7. Dashboard analytics using SQL aggregates.
8. Metadata inspection using `INFORMATION_SCHEMA`.
9. Normalization strengths and honest weaknesses that are easy to defend in viva.

The best academic takeaway is that the project does not only "use a database"; it actively demonstrates how DBMS concepts behave inside a realistic workflow.
