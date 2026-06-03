from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth import login_required, role_required
from app.db import fetch_all, fetch_one, execute_write, get_db_connection, log_db_activity, print_table_snapshot
import mysql.connector

customer_bp = Blueprint('customers', __name__)

@customer_bp.route('/customers', methods=['GET'])
@login_required
@role_required(['owner', 'manager', 'receptionist'])
def list_customers():
    search_query = request.args.get('search', '')
    
    # 1. Fetch customers based on search filter
    if search_query:
        query = """
            SELECT * FROM customer 
            WHERE full_name LIKE %s OR phone LIKE %s 
            ORDER BY full_name ASC
        """
        like_pattern = f"%{search_query}%"
        customers = fetch_all(query, (like_pattern, like_pattern))
    else:
        query = "SELECT * FROM customer ORDER BY full_name ASC"
        customers = fetch_all(query)
        
    # 2. Fetch vehicles along with their owner (customer) names
    vehicles_query = """
        SELECT v.*, c.full_name AS owner_name 
        FROM vehicle v
        JOIN customer c ON v.customer_id = c.customer_id
        ORDER BY v.vehicle_id DESC
    """
    vehicles = fetch_all(vehicles_query)
    
    return render_template(
        'customers/list.html', 
        customers=customers, 
        vehicles=vehicles,
        search_query=search_query
    )

@customer_bp.route('/customers/add', methods=['POST'])
@login_required
@role_required(['owner', 'manager', 'receptionist'])
def add_customer():
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    
    if not full_name or not phone:
        flash("Full name and Phone number are required fields.", "warning")
        return redirect(url_for('customers.list_customers'))
        
    query = """
        INSERT INTO customer (full_name, phone, email, address) 
        VALUES (%s, %s, %s, %s)
    """
    try:
        execute_write(query, (full_name, phone, email, address))
        flash(f"Customer '{full_name}' has been added successfully.", "success")
    except Exception as e:
        flash(f"Failed to add customer. Error: {str(e)}", "danger")
        
    return redirect(url_for('customers.list_customers'))

@customer_bp.route('/customers/edit/<int:customer_id>', methods=['POST'])
@login_required
@role_required(['owner', 'manager', 'receptionist'])
def edit_customer(customer_id):
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    
    if not full_name or not phone:
        flash("Full Name and Phone are required.", "warning")
        return redirect(url_for('customers.list_customers'))
        
    query = """
        UPDATE customer 
        SET full_name = %s, phone = %s, email = %s, address = %s 
        WHERE customer_id = %s
    """
    try:
        execute_write(query, (full_name, phone, email, address, customer_id))
        flash(f"Customer details for '{full_name}' updated successfully.", "success")
    except Exception as e:
        flash(f"Failed to update customer details. Error: {str(e)}", "danger")
        
    return redirect(url_for('customers.list_customers'))

@customer_bp.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
@role_required(['owner', 'manager', 'receptionist'])
def delete_customer(customer_id):
    customer = fetch_one("SELECT full_name FROM customer WHERE customer_id = %s", (customer_id,))
    if not customer:
        flash("Customer not found.", "warning")
        return redirect(url_for('customers.list_customers'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        log_db_activity("START TRANSACTION", "NONE", "START TRANSACTION", None)
        conn.start_transaction()
        
        # 1. Delete invoices linked to customer
        delete_invoices_query = "DELETE FROM invoice WHERE customer_id = %s"
        log_db_activity("DELETE (TRANSACTION)", "invoice", delete_invoices_query, (customer_id,))
        cursor.execute(delete_invoices_query, (customer_id,))
        
        # 2. Delete service jobs linked to customer
        delete_jobs_query = "DELETE FROM service_job WHERE customer_id = %s"
        log_db_activity("DELETE (TRANSACTION)", "service_job", delete_jobs_query, (customer_id,))
        cursor.execute(delete_jobs_query, (customer_id,))
        
        # 3. Delete vehicles linked to customer
        delete_vehicles_query = "DELETE FROM vehicle WHERE customer_id = %s"
        log_db_activity("DELETE (TRANSACTION)", "vehicle", delete_vehicles_query, (customer_id,))
        cursor.execute(delete_vehicles_query, (customer_id,))
        
        # 4. Delete customer record itself
        delete_customer_query = "DELETE FROM customer WHERE customer_id = %s"
        log_db_activity("DELETE (TRANSACTION)", "customer", delete_customer_query, (customer_id,))
        cursor.execute(delete_customer_query, (customer_id,))
        
        conn.commit()
        log_db_activity("COMMIT", "NONE", "COMMIT TRANSACTION", None, status="SUCCESS")
        print_table_snapshot("invoice")
        print_table_snapshot("service_job")
        print_table_snapshot("vehicle")
        print_table_snapshot("customer")
        
        flash(f"Customer '{customer['full_name']}' and all their dependent vehicle, job, and invoice records have been deleted successfully via a safe cascading transaction.", "success")
    except mysql.connector.Error as err:
        try:
            conn.rollback()
            log_db_activity("ROLLBACK", "NONE", "ROLLBACK TRANSACTION", None, status="ROLLBACK / ERROR", error_msg=str(err))
        except Exception as rollback_err:
            print(f"Error during rollback: {rollback_err}")
        flash(f"DBMS Constraint Alert: Deletion rolled back. Database Error: {err.msg}", "danger")
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        flash(f"Failed to delete customer: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('customers.list_customers'))

@customer_bp.route('/vehicles/add', methods=['POST'])
@login_required
@role_required(['owner', 'manager', 'receptionist'])
def add_vehicle():
    customer_id = request.form.get('customer_id')
    registration_no = request.form.get('registration_no', '').strip().upper()
    make = request.form.get('make')
    model = request.form.get('model')
    manufacture_year = request.form.get('manufacture_year')
    mileage = request.form.get('mileage', 0)
    
    if not customer_id or not registration_no or not make or not model or not manufacture_year:
        flash("All fields are required to register a vehicle.", "warning")
        return redirect(url_for('customers.list_customers'))
        
    query = """
        INSERT INTO vehicle (customer_id, registration_no, make, model, manufacture_year, mileage) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        execute_write(query, (customer_id, registration_no, make, model, manufacture_year, mileage))
        flash(f"Vehicle '{make} {model} ({registration_no})' registered successfully.", "success")
    except mysql.connector.Error as err:
        if err.errno == 1062: # Duplicate entry for Unique Key registration_no
            flash(f"Database Alert: A vehicle with Registration Number '{registration_no}' is already registered in the system.", "danger")
        else:
            flash(f"Database Error: {err.msg}", "danger")
    except Exception as e:
        flash(f"Failed to register vehicle. Error: {str(e)}", "danger")
        
    return redirect(url_for('customers.list_customers'))

@customer_bp.route('/vehicles/delete/<int:vehicle_id>', methods=['POST'])
@login_required
@role_required(['owner', 'manager', 'receptionist'])
def delete_vehicle(vehicle_id):
    vehicle = fetch_one("SELECT registration_no FROM vehicle WHERE vehicle_id = %s", (vehicle_id,))
    if not vehicle:
        flash("Vehicle not found.", "warning")
        return redirect(url_for('customers.list_customers') + "#vehicles-pane")
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        log_db_activity("START TRANSACTION", "NONE", "START TRANSACTION", None)
        conn.start_transaction()
        
        # Fetch all job IDs linked to the vehicle
        cursor.execute("SELECT job_id FROM service_job WHERE vehicle_id = %s", (vehicle_id,))
        jobs = cursor.fetchall()
        job_ids = [j['job_id'] for j in jobs]
        
        if job_ids:
            # 1. Delete invoices linked to those jobs
            format_ids = ','.join(['%s'] * len(job_ids))
            delete_invoices_query = f"DELETE FROM invoice WHERE job_id IN ({format_ids})"
            log_db_activity("DELETE (TRANSACTION)", "invoice", delete_invoices_query, tuple(job_ids))
            cursor.execute(delete_invoices_query, tuple(job_ids))
            
            # 2. Delete service jobs
            delete_jobs_query = "DELETE FROM service_job WHERE vehicle_id = %s"
            log_db_activity("DELETE (TRANSACTION)", "service_job", delete_jobs_query, (vehicle_id,))
            cursor.execute(delete_jobs_query, (vehicle_id,))
        
        # 3. Delete the vehicle itself
        delete_vehicle_query = "DELETE FROM vehicle WHERE vehicle_id = %s"
        log_db_activity("DELETE (TRANSACTION)", "vehicle", delete_vehicle_query, (vehicle_id,))
        cursor.execute(delete_vehicle_query, (vehicle_id,))
        
        conn.commit()
        log_db_activity("COMMIT", "NONE", "COMMIT TRANSACTION", None, status="SUCCESS")
        print_table_snapshot("invoice")
        print_table_snapshot("service_job")
        print_table_snapshot("vehicle")
        
        flash(f"Vehicle '{vehicle['registration_no']}' and all its active service job sheets and invoices have been deleted successfully via a safe cascading transaction.", "success")
    except mysql.connector.Error as err:
        try:
            conn.rollback()
            log_db_activity("ROLLBACK", "NONE", "ROLLBACK TRANSACTION", None, status="ROLLBACK / ERROR", error_msg=str(err))
        except Exception as rollback_err:
            print(f"Error during rollback: {rollback_err}")
        flash(f"DBMS Constraint Alert: Deletion rolled back. Database Error: {err.msg}", "danger")
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        flash(f"Failed to delete vehicle: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('customers.list_customers') + "#vehicles-pane")
