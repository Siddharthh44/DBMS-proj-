# Product Requirements Document (PRD)
## Project Name: Fender - Automobile Garage Management System

---

## 1. Project Overview
**Fender** is a responsive, web-based Automobile Garage Management System designed as a DBMS mini-project. It serves as an administrative and operational dashboard for auto repair workshops. The system handles customer records, vehicle profiles, supplier relations, spare parts inventory, service job sheets, and invoices. 

Built with **Python (Flask)**, **MySQL**, and **Bootstrap 5 (Dark Mode)**, Fender demonstrates key database management system (DBMS) concepts—such as relational schemas, integrity constraints, ACID transactions, normalization trade-offs, and aggregation queries—through an interactive, visual interface.

---

## 2. Problem Statement
Small-to-medium automotive service centers struggle with manual tracking of:
1. **Disjointed Data**: Customer contact details, vehicle service logs, and billing statements are often recorded on paper or separate spreadsheets, leading to data loss and slow lookup speeds.
2. **Inventory Stockouts**: Mechanics often discover spare parts (like brake pads or oil filters) are out of stock only during active servicing, leading to project delays.
3. **Complex Job Management**: Coordinating which mechanic is diagnosing which vehicle, what parts they used, and how much labor was charged is prone to communication gaps and errors.
4. **Billing Inconsistencies**: Manually calculating invoice grand totals based on base labor fees plus variable spare parts costs often leads to calculation errors and unpaid records.

---

## 3. Objectives
- **Centralize Operations**: Store customers, vehicles, suppliers, parts inventory, service jobs, and invoices in a unified relational database.
- **Track Lifecycle**: Manage service jobs from registration (`Pending`) to active diagnostic work (`In Progress`) to billing (`Completed` or `Cancelled`).
- **Automate Billing**: Calculate invoice charges automatically by retrieving labor charges and the cost of parts used during service jobs.
- **Monitor Stock Levels**: Provide real-time stock counts and highlight low-stock parts using defined reorder levels.
- **Demonstrate DBMS Concepts**: Serve as an educational model for database topics (constraints, normalization levels, schema mappings, transactions, and SQL features) for college-level viva demonstrations.

---

## 4. User Roles and Access Control
Fender implements a lightweight, role-based user access structure mapped to the `user` table's `role` column:

| Role | Description | Access Rights / Dashboard Views |
| :--- | :--- | :--- |
| **Owner** | The shop owner who oversees business performance. | Full access to all modules, including advanced analytics dashboards, revenue charts, financial reports, inventory management, jobs, and user administration. |
| **Manager** | Oversees day-to-day operations and supplies. | Can manage customers, vehicles, suppliers, and parts inventory (including raising stock levels). Can assign mechanics to service jobs. |
| **Receptionist** | Handles intake, booking, and checkout. | Can create and edit customer and vehicle profiles, create new service jobs, update billing details, generate invoices, and log customer payments. |
| **Mechanic** | The workshop technician performing services. | Restricted view showing only assigned service jobs. Can update job status (e.g., from `In Progress` to `Completed`), record diagnosis details, and specify parts used. |

---

## 5. Functional Requirements

### 5.1 User Authentication
- **Simple Login**: Single-page form to log in using `username` and `password`.
- **Session Persistence**: Secure cookies holding session variables (`user_id`, `username`, `role`, `full_name`).
- **Role Redirection**: Automatic redirection to relevant default pages based on role upon successful login.
- **Session-Based Access**: Custom Flask route decorators to block access to admin panels or analytics if a user lacks the required role.

### 5.2 Customer & Vehicle Management
- **Customer Directory**: View, search (by name/phone), create, edit, and delete customer records.
- **Vehicle Profiles**: View and register vehicles under a specific customer.
- **Integrity Enforcement**: Prevent deletion of customers with active invoices or incomplete service jobs through database constraints (`ON DELETE RESTRICT`). Allow automatic vehicle removal if a customer is deleted without active records via cascade constraints (`ON DELETE CASCADE`).

### 5.3 Supplier & Inventory Management
- **Supplier Records**: Manage supplier profiles (supplier name, contact, phone, email) for procurement tracking.
- **Spare Parts Catalog**: CRUD interface for parts (name, part number, category, stock count, reorder level, unit cost, and selling price).
- **Stock Warnings**: Highlight parts in red on the dashboard and inventory view if their `quantity_in_stock` is less than or equal to their `reorder_level`.

### 5.4 Service Job Tracking
- **Job Intake**: Create service jobs linking a vehicle and customer to an assigned user (mechanic) with a job date and customer complaint.
- **Diagnostic Flow**: Mechanics update the job status, input the technical diagnosis, specify labor charges, and select parts used from the inventory.
- **Parts Serialization**: Store consumed parts within the `parts_used` column as a JSON array (`part_id`, `part_name`, `quantity`, `unit_price`, `line_total`).

### 5.5 Invoicing & Payments
- **Automatic Billing Generation**: Completing a service job triggers the generation of an invoice.
- **Calculation Formula**:
  $$\text{Grand Total} = \text{Labour Total} + \text{Parts Total}$$
  where Parts Total is calculated from the parts list in the service job.
- **Payment Lifecycle**: Recovers billing status through 'Unpaid', 'Partially Paid', and 'Paid' states, noting payment methods (Cash, Card, UPI, Bank Transfer).

### 5.6 Analytics & Reports
- **Stat Cards**: Display KPIs (Active Jobs, Low Stock Items, Monthly Revenue, Unpaid Invoices).
- **Revenue Analytics**: Visual bar and line charts representing monthly revenue trends and payment status distributions.
- **Inventory Metrics**: Doughnut chart representing parts breakdown by category.

---

## 6. Non-Functional Requirements
- **Global Dark Theme**: Dark background (`#121212`) matching terminal consoles and IDE layouts to provide a clean, modern aesthetic.
- **Responsive Layout**: Designed using Bootstrap 5 fluid grids, making the admin portal usable on desktop monitors, shop floor tablets, and mobile devices.
- **Database Portability**: Runs on standard MySQL Community Server (v8.0+), executing raw SQL strings to maximize educational clarity for database examiners.
- **Security Limitations (Academic Context)**: Highlighting simplicity for educational purposes. Passwords are saved in plain text, and JWT/hash libraries are omitted as per college project guidelines.

---

## 7. DBMS Concepts Covered

### Module-1: Database Architecture & ER Modeling
- **Three-Schema Architecture**: Logical schema defined via DDL tables; Internal schema mapped to MySQL's storage engine; External views represented by specific Flask template dashboards.
- **Entity sets & Relationships**: Entity types mapped to tables; Relationships mapped using foreign keys.
- **Entity Relation (ER) Diagram mapping**: Explaining 1-to-N relationships (Customer to Vehicles) and 1-to-1 relationships (Service Job to Invoice) conceptually.

### Module-2: Relational Integrity & Mapping
- **Key Constraints**: Primary keys (`customer_id`, `vehicle_id`, etc.) ensure entity integrity. Unique constraints (`registration_no`, `part_number`) enforce domain constraints.
- **Referential Integrity**: Managed using explicit SQL constraints:
  - `ON DELETE CASCADE` (deleting a customer automatically removes their vehicles).
  - `ON DELETE RESTRICT` (preventing deletion of a supplier if their spare parts are still referenced).
- **Constraint Violations**: Visual Flask warning alerts when users attempt to violate referential constraints (e.g. trying to delete an assigned mechanic).

### Module-3: Schema Normalization & SQL Queries
- **First Normal Form (1NF) Violation Case Study**: Storing `parts_used` as a JSON array in the `service_job` table. This serves as an excellent discussion topic for normalization, showing how it violates 1NF (non-atomic values) to simplify schema depth, and how it could be normalized into a standard junction table.
- **Third Normal Form (3NF) Violation Case Study**: Storing `grand_total`, `labour_total`, and `parts_total` in the `invoice` table. These derived columns represent transitive dependencies, denormalized intentionally to reduce complex query overhead during checkout.
- **Aggregations & Groupings**: Using `SUM`, `COUNT`, `GROUP BY`, and `ORDER BY` to generate analytics charts and low-stock listings.

### Module-4: Transactions & Concurrent Support
- **ACID Transaction Booking**: Completing a service job uses transaction boundaries (`START TRANSACTION` ... `COMMIT` / `ROLLBACK`):
  1. Deducts parts quantities from the `spare_part` table.
  2. Inserts an invoice record.
  3. Updates job status to 'Completed'.
  4. If any single step fails (e.g., if a part's stock runs below zero), the database rolls back all operations to maintain ACID compliance.
- **Views & Subqueries**: Complex dashboard queries utilizing subqueries and relational joins.
