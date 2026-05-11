import json
import os
from datetime import date
from functools import wraps
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from mysql.connector import Error, connect
from werkzeug.security import check_password_hash


BASE_DIR = Path(__file__).resolve().parent


def load_env_file(env_path):
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        cleaned_key = key.strip()
        cleaned_value = value.strip().strip('"').strip("'")
        os.environ.setdefault(cleaned_key, cleaned_value)


load_env_file(BASE_DIR / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-in-production")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "garage_db"),
}

ROLE_LABELS = {
    "owner": "Owner",
    "manager": "Manager",
    "mechanic": "Mechanic",
    "receptionist": "Receptionist",
}

WRITE_ROLES = {"owner", "manager", "receptionist"}
INVENTORY_ROLES = {"owner", "manager"}
JOB_ROLES = {"owner", "manager", "mechanic", "receptionist"}


def get_db_connection():
    return connect(**DB_CONFIG)


def fetch_all(query, params=None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def fetch_one(query, params=None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def execute_query(query, params=None):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, params or ())
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                flash("Please sign in to continue.", "warning")
                return redirect(url_for("login"))
            if g.user["role"] not in roles:
                flash("You do not have permission to perform that action.", "danger")
                return redirect(url_for("dashboard"))
            return view(**kwargs)

        return wrapped_view

    return decorator


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id:
        try:
            g.user = fetch_one(
                "SELECT user_id, username, role, full_name, phone FROM `user` WHERE user_id = %s",
                (user_id,),
            )
        except Error:
            g.user = None


@app.context_processor
def inject_globals():
    return {
        "current_user": g.user,
        "role_labels": ROLE_LABELS,
        "write_roles": WRITE_ROLES,
        "inventory_roles": INVENTORY_ROLES,
        "job_roles": JOB_ROLES,
    }


@app.template_filter("currency")
def currency_filter(value):
    value = value if value is not None else 0
    return f"Rs. {float(value):,.2f}"


def verify_password(raw_password, stored_password):
    if stored_password.startswith(("pbkdf2:", "scrypt:")):
        return check_password_hash(stored_password, raw_password)
    return raw_password == stored_password


def decode_parts(parts_used):
    if not parts_used:
        return []
    try:
        payload = json.loads(parts_used)
    except (TypeError, json.JSONDecodeError):
        return []

    parts = []
    for item in payload:
        parts.append(
            {
                "part_id": item.get("part_id"),
                "part_name": item.get("part_name", "Unknown Part"),
                "quantity": int(item.get("quantity", 0)),
                "unit_price": float(item.get("unit_price", 0)),
                "line_total": float(item.get("line_total", 0)),
            }
        )
    return parts


def parts_summary(parts_used):
    items = decode_parts(parts_used)
    if not items:
        return "No spare parts used"
    return ", ".join(f"{item['part_name']} x {item['quantity']}" for item in items)


def parts_total(parts_used):
    return round(sum(item["line_total"] for item in decode_parts(parts_used)), 2)


def collect_part_lines(form_data):
    part_items = []
    seen_part_ids = set()

    for index in range(1, 4):
        part_id = form_data.get(f"part_{index}")
        quantity = form_data.get(f"qty_{index}")

        if not part_id or not quantity:
            continue

        try:
            part_id = int(part_id)
            quantity = int(quantity)
        except ValueError:
            raise ValueError("Part and quantity values must be valid numbers.")

        if quantity <= 0:
            raise ValueError("Part quantity must be greater than zero.")

        if part_id in seen_part_ids:
            raise ValueError("Please select each spare part only once per service job.")

        seen_part_ids.add(part_id)
        part_items.append({"part_id": part_id, "quantity": quantity})

    return part_items


def enrich_jobs(job_rows):
    for job in job_rows:
        job["parts_breakdown"] = decode_parts(job.get("parts_used"))
        job["parts_summary"] = parts_summary(job.get("parts_used"))
        job["parts_total"] = parts_total(job.get("parts_used"))
    return job_rows


def enrich_invoices(invoice_rows):
    for invoice in invoice_rows:
        invoice["parts_summary"] = parts_summary(invoice.get("parts_used"))
    return invoice_rows


def fetch_dashboard_data():
    stats = {
        "total_customers": fetch_one("SELECT COUNT(*) AS total FROM customer")["total"],
        "total_vehicles": fetch_one("SELECT COUNT(*) AS total FROM vehicle")["total"],
        "open_jobs": fetch_one(
            "SELECT COUNT(*) AS total FROM service_job WHERE status IN ('Pending', 'In Progress')"
        )["total"],
        "low_stock_count": fetch_one(
            "SELECT COUNT(*) AS total FROM spare_part WHERE quantity_in_stock <= reorder_level"
        )["total"],
        "total_revenue": fetch_one(
            "SELECT COALESCE(SUM(grand_total), 0) AS total FROM invoice WHERE payment_status = 'Paid'"
        )["total"],
    }

    recent_jobs = fetch_all(
        """
        SELECT sj.job_id, sj.job_date, sj.status, c.full_name AS customer_name,
               v.registration_no, u.full_name AS mechanic_name
        FROM service_job sj
        JOIN customer c ON c.customer_id = sj.customer_id
        JOIN vehicle v ON v.vehicle_id = sj.vehicle_id
        JOIN `user` u ON u.user_id = sj.user_id
        ORDER BY sj.job_date DESC, sj.job_id DESC
        LIMIT 5
        """
    )

    low_stock_parts = fetch_all(
        """
        SELECT part_name, part_number, quantity_in_stock, reorder_level
        FROM spare_part
        WHERE quantity_in_stock <= reorder_level
        ORDER BY quantity_in_stock ASC, part_name ASC
        LIMIT 5
        """
    )

    return stats, recent_jobs, low_stock_parts


@app.route("/")
def home():
    if g.user:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("login.html")

        try:
            user = fetch_one("SELECT * FROM `user` WHERE username = %s", (username,))
        except Error as exc:
            flash(f"Database connection failed: {exc}", "danger")
            return render_template("login.html")

        if not user or not verify_password(password, user["password"]):
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["user_id"]
        flash(f"Welcome back, {user['full_name']}.", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    try:
        stats, recent_jobs, low_stock_parts = fetch_dashboard_data()
    except Error as exc:
        flash(f"Unable to load dashboard data: {exc}", "danger")
        stats, recent_jobs, low_stock_parts = {
            "total_customers": 0,
            "total_vehicles": 0,
            "open_jobs": 0,
            "low_stock_count": 0,
            "total_revenue": 0,
        }, [], []

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        stats=stats,
        recent_jobs=recent_jobs,
        low_stock_parts=low_stock_parts,
    )


@app.route("/customers", methods=["GET", "POST"])
@login_required
def customers():
    if request.method == "POST":
        if g.user["role"] not in WRITE_ROLES:
            flash("You do not have permission to add customers.", "danger")
            return redirect(url_for("customers"))

        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()

        if not full_name or not phone:
            flash("Customer name and phone are required.", "danger")
            return redirect(url_for("customers"))

        try:
            execute_query(
                """
                INSERT INTO customer (full_name, phone, email, address)
                VALUES (%s, %s, %s, %s)
                """,
                (full_name, phone, email or None, address or None),
            )
            flash("Customer added successfully.", "success")
        except Error as exc:
            flash(f"Unable to add customer: {exc}", "danger")

        return redirect(url_for("customers"))

    edit_customer = None
    try:
        customers_data = fetch_all(
            """
            SELECT c.customer_id, c.full_name, c.phone, c.email, c.address,
                   COUNT(v.vehicle_id) AS vehicle_count
            FROM customer c
            LEFT JOIN vehicle v ON v.customer_id = c.customer_id
            GROUP BY c.customer_id, c.full_name, c.phone, c.email, c.address
            ORDER BY c.customer_id DESC
            """
        )
        edit_id = request.args.get("edit", type=int)
        if edit_id:
            edit_customer = fetch_one(
                "SELECT * FROM customer WHERE customer_id = %s",
                (edit_id,),
            )
    except Error as exc:
        flash(f"Unable to load customers: {exc}", "danger")
        customers_data = []

    return render_template(
        "customers.html",
        active_page="customers",
        customers=customers_data,
        edit_customer=edit_customer,
    )


@app.route("/customers/<int:customer_id>/update", methods=["POST"])
@roles_required("owner", "manager", "receptionist")
def update_customer(customer_id):
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()

    if not full_name or not phone:
        flash("Customer name and phone are required.", "danger")
        return redirect(url_for("customers", edit=customer_id))

    try:
        execute_query(
            """
            UPDATE customer
            SET full_name = %s, phone = %s, email = %s, address = %s
            WHERE customer_id = %s
            """,
            (full_name, phone, email or None, address or None, customer_id),
        )
        flash("Customer updated successfully.", "success")
    except Error as exc:
        flash(f"Unable to update customer: {exc}", "danger")

    return redirect(url_for("customers"))


@app.route("/vehicles", methods=["GET", "POST"])
@login_required
def vehicles():
    if request.method == "POST":
        if g.user["role"] not in WRITE_ROLES:
            flash("You do not have permission to add vehicles.", "danger")
            return redirect(url_for("vehicles"))

        customer_id = request.form.get("customer_id", type=int)
        registration_no = request.form.get("registration_no", "").strip().upper()
        make = request.form.get("make", "").strip()
        model = request.form.get("model", "").strip()
        manufacture_yr = request.form.get("manufacture_yr", type=int)
        mileage = request.form.get("mileage", type=int)

        if not all([customer_id, registration_no, make, model, manufacture_yr is not None, mileage is not None]):
            flash("All vehicle fields are required.", "danger")
            return redirect(url_for("vehicles"))

        try:
            execute_query(
                """
                INSERT INTO vehicle (
                    customer_id, registration_no, make, model, manufacture_yr, mileage
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (customer_id, registration_no, make, model, manufacture_yr, mileage),
            )
            flash("Vehicle added successfully.", "success")
        except Error as exc:
            flash(f"Unable to add vehicle: {exc}", "danger")

        return redirect(url_for("vehicles"))

    edit_vehicle = None
    try:
        vehicle_rows = fetch_all(
            """
            SELECT v.*, c.full_name AS customer_name, c.phone AS customer_phone
            FROM vehicle v
            JOIN customer c ON c.customer_id = v.customer_id
            ORDER BY v.vehicle_id DESC
            """
        )
        customer_rows = fetch_all("SELECT customer_id, full_name FROM customer ORDER BY full_name")
        edit_id = request.args.get("edit", type=int)
        if edit_id:
            edit_vehicle = fetch_one("SELECT * FROM vehicle WHERE vehicle_id = %s", (edit_id,))
    except Error as exc:
        flash(f"Unable to load vehicles: {exc}", "danger")
        vehicle_rows, customer_rows = [], []

    return render_template(
        "vehicles.html",
        active_page="vehicles",
        vehicles=vehicle_rows,
        customers=customer_rows,
        edit_vehicle=edit_vehicle,
    )


@app.route("/vehicles/<int:vehicle_id>/update", methods=["POST"])
@roles_required("owner", "manager", "receptionist")
def update_vehicle(vehicle_id):
    customer_id = request.form.get("customer_id", type=int)
    registration_no = request.form.get("registration_no", "").strip().upper()
    make = request.form.get("make", "").strip()
    model = request.form.get("model", "").strip()
    manufacture_yr = request.form.get("manufacture_yr", type=int)
    mileage = request.form.get("mileage", type=int)

    if not all([customer_id, registration_no, make, model, manufacture_yr is not None, mileage is not None]):
        flash("All vehicle fields are required.", "danger")
        return redirect(url_for("vehicles", edit=vehicle_id))

    try:
        execute_query(
            """
            UPDATE vehicle
            SET customer_id = %s, registration_no = %s, make = %s, model = %s,
                manufacture_yr = %s, mileage = %s
            WHERE vehicle_id = %s
            """,
            (customer_id, registration_no, make, model, manufacture_yr, mileage, vehicle_id),
        )
        flash("Vehicle updated successfully.", "success")
    except Error as exc:
        flash(f"Unable to update vehicle: {exc}", "danger")

    return redirect(url_for("vehicles"))


@app.route("/inventory", methods=["GET", "POST"])
@login_required
def inventory():
    if request.method == "POST":
        if g.user["role"] not in INVENTORY_ROLES:
            flash("You do not have permission to update inventory.", "danger")
            return redirect(url_for("inventory"))

        form_type = request.form.get("form_type")

        try:
            if form_type == "supplier":
                supplier_name = request.form.get("supplier_name", "").strip()
                contact_person = request.form.get("contact_person", "").strip()
                phone = request.form.get("phone", "").strip()
                email = request.form.get("email", "").strip()

                if not supplier_name:
                    flash("Supplier name is required.", "danger")
                    return redirect(url_for("inventory"))

                execute_query(
                    """
                    INSERT INTO supplier (supplier_name, contact_person, phone, email)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (supplier_name, contact_person or None, phone or None, email or None),
                )
                flash("Supplier added successfully.", "success")

            elif form_type == "part":
                supplier_id = request.form.get("supplier_id", type=int)
                part_name = request.form.get("part_name", "").strip()
                part_number = request.form.get("part_number", "").strip().upper()
                category = request.form.get("category", "").strip()
                quantity_in_stock = request.form.get("quantity_in_stock", type=int)
                reorder_level = request.form.get("reorder_level", type=int)
                unit_cost = request.form.get("unit_cost", type=float)
                selling_price = request.form.get("selling_price", type=float)

                required_values = [
                    supplier_id,
                    part_name,
                    part_number,
                    category,
                    quantity_in_stock is not None,
                    reorder_level is not None,
                    unit_cost is not None,
                    selling_price is not None,
                ]
                if not all(required_values):
                    flash("Please complete all spare part fields.", "danger")
                    return redirect(url_for("inventory"))

                execute_query(
                    """
                    INSERT INTO spare_part (
                        supplier_id, part_name, part_number, category,
                        quantity_in_stock, reorder_level, unit_cost, selling_price
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        supplier_id,
                        part_name,
                        part_number,
                        category,
                        quantity_in_stock,
                        reorder_level,
                        unit_cost,
                        selling_price,
                    ),
                )
                flash("Spare part added successfully.", "success")

            else:
                flash("Unknown inventory action.", "danger")

        except Error as exc:
            flash(f"Unable to update inventory: {exc}", "danger")

        return redirect(url_for("inventory"))

    try:
        suppliers = fetch_all("SELECT * FROM supplier ORDER BY supplier_name")
        parts = fetch_all(
            """
            SELECT sp.*, s.supplier_name,
                   (sp.quantity_in_stock <= sp.reorder_level) AS is_low_stock
            FROM spare_part sp
            JOIN supplier s ON s.supplier_id = sp.supplier_id
            ORDER BY sp.part_id DESC
            """
        )
        low_stock_parts = [part for part in parts if part["is_low_stock"]]
    except Error as exc:
        flash(f"Unable to load inventory data: {exc}", "danger")
        suppliers, parts, low_stock_parts = [], [], []

    return render_template(
        "inventory.html",
        active_page="inventory",
        suppliers=suppliers,
        parts=parts,
        low_stock_parts=low_stock_parts,
    )


@app.route("/inventory/<int:part_id>/stock", methods=["POST"])
@roles_required("owner", "manager")
def update_stock(part_id):
    quantity_in_stock = request.form.get("quantity_in_stock", type=int)
    reorder_level = request.form.get("reorder_level", type=int)

    if quantity_in_stock is None or reorder_level is None:
        flash("Stock quantity and reorder level are required.", "danger")
        return redirect(url_for("inventory"))

    try:
        execute_query(
            """
            UPDATE spare_part
            SET quantity_in_stock = %s, reorder_level = %s
            WHERE part_id = %s
            """,
            (quantity_in_stock, reorder_level, part_id),
        )
        flash("Stock levels updated successfully.", "success")
    except Error as exc:
        flash(f"Unable to update stock: {exc}", "danger")

    return redirect(url_for("inventory"))


@app.route("/service-jobs", methods=["GET", "POST"])
@login_required
def service_jobs():
    if request.method == "POST":
        if g.user["role"] not in JOB_ROLES:
            flash("You do not have permission to create service jobs.", "danger")
            return redirect(url_for("service_jobs"))

        vehicle_id = request.form.get("vehicle_id", type=int)
        customer_id = request.form.get("customer_id", type=int)
        user_id = request.form.get("user_id", type=int)
        job_date = request.form.get("job_date") or date.today().isoformat()
        complaint = request.form.get("complaint", "").strip()
        diagnosis = request.form.get("diagnosis", "").strip()
        labour_charge = request.form.get("labour_charge", type=float)
        status = request.form.get("status", "Pending")

        if not all([vehicle_id, customer_id, user_id, complaint, labour_charge is not None]):
            flash("Vehicle, customer, mechanic, complaint, and labour charge are required.", "danger")
            return redirect(url_for("service_jobs"))

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT vehicle_id, customer_id FROM vehicle WHERE vehicle_id = %s",
                (vehicle_id,),
            )
            vehicle = cursor.fetchone()
            if not vehicle or vehicle["customer_id"] != customer_id:
                raise ValueError("Selected vehicle does not belong to the selected customer.")

            selected_parts = collect_part_lines(request.form)
            enriched_parts = []
            for selected_part in selected_parts:
                cursor.execute(
                    """
                    SELECT part_id, part_name, quantity_in_stock, selling_price
                    FROM spare_part
                    WHERE part_id = %s
                    """,
                    (selected_part["part_id"],),
                )
                part = cursor.fetchone()
                if not part:
                    raise ValueError("One of the selected spare parts was not found.")
                if part["quantity_in_stock"] < selected_part["quantity"]:
                    raise ValueError(
                        f"Not enough stock for {part['part_name']}. Available: {part['quantity_in_stock']}."
                    )

                line_total = round(float(part["selling_price"]) * selected_part["quantity"], 2)
                enriched_parts.append(
                    {
                        "part_id": part["part_id"],
                        "part_name": part["part_name"],
                        "quantity": selected_part["quantity"],
                        "unit_price": float(part["selling_price"]),
                        "line_total": line_total,
                    }
                )

            cursor.execute(
                """
                INSERT INTO service_job (
                    vehicle_id, customer_id, user_id, job_date, complaint,
                    diagnosis, parts_used, labour_charge, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    vehicle_id,
                    customer_id,
                    user_id,
                    job_date,
                    complaint,
                    diagnosis or None,
                    json.dumps(enriched_parts) if enriched_parts else None,
                    labour_charge,
                    status,
                ),
            )

            for item in enriched_parts:
                cursor.execute(
                    """
                    UPDATE spare_part
                    SET quantity_in_stock = quantity_in_stock - %s
                    WHERE part_id = %s
                    """,
                    (item["quantity"], item["part_id"]),
                )

            connection.commit()
            flash("Service job created and inventory updated successfully.", "success")
        except (Error, ValueError) as exc:
            connection.rollback()
            flash(f"Unable to create service job: {exc}", "danger")
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("service_jobs"))

    try:
        jobs = fetch_all(
            """
            SELECT sj.*, c.full_name AS customer_name, v.registration_no, v.make, v.model,
                   u.full_name AS mechanic_name
            FROM service_job sj
            JOIN customer c ON c.customer_id = sj.customer_id
            JOIN vehicle v ON v.vehicle_id = sj.vehicle_id
            JOIN `user` u ON u.user_id = sj.user_id
            ORDER BY sj.job_date DESC, sj.job_id DESC
            """
        )
        jobs = enrich_jobs(jobs)
        customers_data = fetch_all("SELECT customer_id, full_name FROM customer ORDER BY full_name")
        vehicles_data = fetch_all(
            """
            SELECT vehicle_id, customer_id, registration_no, make, model
            FROM vehicle
            ORDER BY registration_no
            """
        )
        mechanics = fetch_all(
            """
            SELECT user_id, full_name
            FROM `user`
            WHERE role = 'mechanic'
            ORDER BY full_name
            """
        )
        parts = fetch_all(
            """
            SELECT part_id, part_name, quantity_in_stock, selling_price
            FROM spare_part
            ORDER BY part_name
            """
        )
    except Error as exc:
        flash(f"Unable to load service jobs: {exc}", "danger")
        jobs, customers_data, vehicles_data, mechanics, parts = [], [], [], [], []

    return render_template(
        "service_jobs.html",
        active_page="service_jobs",
        jobs=jobs,
        customers=customers_data,
        vehicles=vehicles_data,
        mechanics=mechanics,
        parts=parts,
        today=date.today().isoformat(),
    )


@app.route("/service-jobs/<int:job_id>/update", methods=["POST"])
@roles_required("owner", "manager", "mechanic", "receptionist")
def update_service_job(job_id):
    user_id = request.form.get("user_id", type=int)
    status = request.form.get("status", "").strip()

    if not user_id or not status:
        flash("Mechanic and status are required.", "danger")
        return redirect(url_for("service_jobs"))

    try:
        execute_query(
            """
            UPDATE service_job
            SET user_id = %s, status = %s
            WHERE job_id = %s
            """,
            (user_id, status, job_id),
        )
        flash("Service job updated successfully.", "success")
    except Error as exc:
        flash(f"Unable to update service job: {exc}", "danger")

    return redirect(url_for("service_jobs"))


@app.route("/invoices", methods=["GET", "POST"])
@login_required
def invoices():
    if request.method == "POST":
        if g.user["role"] not in WRITE_ROLES:
            flash("You do not have permission to generate invoices.", "danger")
            return redirect(url_for("invoices"))

        job_id = request.form.get("job_id", type=int)
        payment_status = request.form.get("payment_status", "Unpaid")
        payment_method = request.form.get("payment_method", "Cash")

        if not job_id:
            flash("Please choose a service job to invoice.", "danger")
            return redirect(url_for("invoices"))

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT sj.job_id, sj.customer_id, sj.labour_charge, sj.parts_used
                FROM service_job sj
                WHERE sj.job_id = %s
                """,
                (job_id,),
            )
            job = cursor.fetchone()
            if not job:
                raise ValueError("Selected service job was not found.")

            cursor.execute("SELECT invoice_id FROM invoice WHERE job_id = %s", (job_id,))
            if cursor.fetchone():
                raise ValueError("An invoice already exists for this service job.")

            labour_total = float(job["labour_charge"] or 0)
            calculated_parts_total = parts_total(job["parts_used"])
            grand_total = round(labour_total + calculated_parts_total, 2)

            cursor.execute(
                """
                INSERT INTO invoice (
                    job_id, customer_id, invoice_date, labour_total,
                    parts_total, grand_total, payment_status, payment_method
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    job_id,
                    job["customer_id"],
                    date.today().isoformat(),
                    labour_total,
                    calculated_parts_total,
                    grand_total,
                    payment_status,
                    payment_method,
                ),
            )
            connection.commit()
            flash("Invoice generated successfully.", "success")
        except (Error, ValueError) as exc:
            connection.rollback()
            flash(f"Unable to generate invoice: {exc}", "danger")
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("invoices"))

    try:
        invoice_rows = fetch_all(
            """
            SELECT i.*, c.full_name AS customer_name, sj.job_date, sj.status AS job_status,
                   sj.parts_used, sj.complaint
            FROM invoice i
            JOIN customer c ON c.customer_id = i.customer_id
            JOIN service_job sj ON sj.job_id = i.job_id
            ORDER BY i.invoice_date DESC, i.invoice_id DESC
            """
        )
        invoice_rows = enrich_invoices(invoice_rows)
        uninvoiced_jobs = fetch_all(
            """
            SELECT sj.job_id, sj.job_date, c.full_name AS customer_name,
                   v.registration_no, sj.labour_charge, sj.parts_used
            FROM service_job sj
            JOIN customer c ON c.customer_id = sj.customer_id
            JOIN vehicle v ON v.vehicle_id = sj.vehicle_id
            LEFT JOIN invoice i ON i.job_id = sj.job_id
            WHERE i.invoice_id IS NULL
            ORDER BY sj.job_date DESC, sj.job_id DESC
            """
        )
        for job in uninvoiced_jobs:
            job["estimated_parts_total"] = parts_total(job.get("parts_used"))
            job["estimated_grand_total"] = round(
                float(job["labour_charge"] or 0) + job["estimated_parts_total"],
                2,
            )
    except Error as exc:
        flash(f"Unable to load invoices: {exc}", "danger")
        invoice_rows, uninvoiced_jobs = [], []

    return render_template(
        "invoices.html",
        active_page="invoices",
        invoices=invoice_rows,
        uninvoiced_jobs=uninvoiced_jobs,
    )


@app.route("/invoices/<int:invoice_id>/payment", methods=["POST"])
@roles_required("owner", "manager", "receptionist")
def update_invoice_payment(invoice_id):
    payment_status = request.form.get("payment_status", "").strip()
    payment_method = request.form.get("payment_method", "").strip()

    if not payment_status or not payment_method:
        flash("Payment status and method are required.", "danger")
        return redirect(url_for("invoices"))

    try:
        execute_query(
            """
            UPDATE invoice
            SET payment_status = %s, payment_method = %s
            WHERE invoice_id = %s
            """,
            (payment_status, payment_method, invoice_id),
        )
        flash("Invoice payment details updated successfully.", "success")
    except Error as exc:
        flash(f"Unable to update invoice payment: {exc}", "danger")

    return redirect(url_for("invoices"))


if __name__ == "__main__":
    app.run(debug=True)
