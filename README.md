# Garage Inventory & Service Management System

A recruiter-friendly full-stack garage operations project built with Flask and MySQL. The application manages customers, vehicles, spare parts, service jobs, and invoices through server-rendered pages backed by live database queries.

## Overview

This project demonstrates a traditional full-stack workflow without frontend frameworks. It connects a Flask backend to a MySQL database and renders dynamic Bootstrap and Tailwind-enhanced templates using Jinja2.

## Features

- Role-based login for owner, manager, mechanic, and receptionist users
- Dashboard with live counts for customers, vehicles, open jobs, low stock, and revenue
- Customer management with add and edit flows
- Vehicle management linked to customer records
- Inventory management for suppliers and spare parts
- Low-stock monitoring and stock level updates
- Service job creation with mechanic assignment and spare part usage tracking
- Invoice generation from service jobs with automatic total calculation
- Parameterized SQL queries for safer database interactions

## Tech Stack

- Backend: Python, Flask
- Database: MySQL
- Frontend: HTML, CSS, Bootstrap, Tailwind CSS, Jinja2

## Installation

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the example environment file:

```bash
copy .env.example .env
```

4. Update `.env` with your local MySQL credentials and Flask secret key.

## How To Run Locally

1. Create the MySQL database and tables:

```sql
SOURCE database/schema.sql;
```

2. Seed the sample data:

```sql
SOURCE database/sample_inserts.sql;
```

3. Start the Flask app:

```bash
python app.py
```

4. Open `http://127.0.0.1:5000` in your browser.

Demo seed users are included in `database/sample_inserts.sql`. The hashed records correspond to these development passwords:

- `owner1 / owner123`
- `manager1 / manager123`
- `mechanic1 / mechanic123`
- `reception1 / reception123`

## Folder Structure

```text
sparkplug-dbms/
|-- app.py
|-- requirements.txt
|-- .env.example
|-- database/
|   |-- schema.sql
|   `-- sample_inserts.sql
|-- docs/
|   `-- screenshots/
|-- static/
|   `-- css/
|       `-- styles.css
`-- templates/
    |-- base.html
    |-- login.html
    |-- dashboard.html
    |-- customers.html
    |-- vehicles.html
    |-- inventory.html
    |-- service_jobs.html
    `-- invoices.html
```

## Screenshots

Add portfolio screenshots to `docs/screenshots/` and replace these placeholders:

- Login page screenshot
- Dashboard screenshot
- Customers module screenshot
- Inventory module screenshot
- Service jobs and invoices screenshot

## Future Improvements

- Add password reset and stronger user administration flows
- Split routes into blueprints for larger-scale maintainability
- Add automated tests for core business flows
- Introduce database migrations for safer schema evolution
- Add printable invoice exports

## Notes

- Runtime secrets are not committed. Configuration is loaded from environment variables or a local `.env` file.
- The repository ignores virtual environments, cache files, logs, and build artifacts for cleaner Git history.
- The current structure keeps backend, templates, static assets, and database scripts separated without changing app behavior.
