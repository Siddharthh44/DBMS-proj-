import json
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.auth import login_required, role_required
from app.db import fetch_all, fetch_one, get_db_connection, execute_write, log_db_activity, log_select_query, print_table_snapshot
import mysql.connector

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/jobs', methods=['GET'])
@login_required
def list_jobs():
    role = session.get('role')
    user_id = session.get('user_id')
    
    # 1. Fetch service jobs based on role
    if role == 'mechanic':
        # Mechanics only see their own assigned jobs
        jobs_query = """
            SELECT j.*, v.registration_no, v.make, v.model, c.full_name AS customer_name, u.full_name AS mechanic_name
            FROM service_job j
            JOIN vehicle v ON j.vehicle_id = v.vehicle_id
            JOIN customer c ON j.customer_id = c.customer_id
            JOIN `user` u ON j.user_id = u.user_id
            WHERE j.user_id = %s
            ORDER BY j.job_id DESC
        """
        jobs = fetch_all(jobs_query, (user_id,))
    else:
        # Owner, Manager, Receptionist see all jobs
        jobs_query = """
            SELECT j.*, v.registration_no, v.make, v.model, c.full_name AS customer_name, u.full_name AS mechanic_name
            FROM service_job j
            JOIN vehicle v ON j.vehicle_id = v.vehicle_id
            JOIN customer c ON j.customer_id = c.customer_id
            JOIN `user` u ON j.user_id = u.user_id
            ORDER BY j.job_id DESC
        """
        jobs = fetch_all(jobs_query)
        
    # 2. Fetch drop-down selectors for job intake registration
    vehicles = fetch_all("SELECT vehicle_id, customer_id, registration_no, make, model FROM vehicle ORDER BY registration_no ASC")
    customers = fetch_all("SELECT customer_id, full_name, phone FROM customer ORDER BY full_name ASC")
    # Fetch users with role='mechanic'
    mechanics = fetch_all("SELECT user_id, full_name FROM `user` WHERE role = 'mechanic' ORDER BY full_name ASC")
    
    return render_template(
        'jobs/list.html',
        jobs=jobs,
        vehicles=vehicles,
        customers=customers,
        mechanics=mechanics
    )

@jobs_bp.route('/jobs/create', methods=['POST'])
@login_required
@role_required(['owner', 'manager', 'receptionist'])
def create_job():
    vehicle_id = request.form.get('vehicle_id')
    customer_id = request.form.get('customer_id')
    user_id = request.form.get('user_id')  # Mechanic assigned
    job_date = request.form.get('job_date')
    complaint = request.form.get('complaint')
    
    if not vehicle_id or not customer_id or not user_id or not job_date or not complaint:
        flash("All job intake fields are required.", "warning")
        return redirect(url_for('jobs.list_jobs'))
        
    query = """
        INSERT INTO service_job (vehicle_id, customer_id, user_id, job_date, complaint, status)
        VALUES (%s, %s, %s, %s, %s, 'Pending')
    """
    try:
        execute_write(query, (vehicle_id, customer_id, user_id, job_date, complaint))
        flash("New service job sheet has been created and assigned to the mechanic.", "success")
    except Exception as e:
        flash(f"Failed to create service job sheet. Error: {str(e)}", "danger")
        
    return redirect(url_for('jobs.list_jobs'))

@jobs_bp.route('/jobs/<int:job_id>/edit', methods=['GET'])
@login_required
def edit_job(job_id):
    # Fetch job details
    job_query = """
        SELECT j.*, v.registration_no, v.make, v.model, v.mileage, v.manufacture_year, c.full_name AS customer_name, c.phone AS customer_phone, u.full_name AS mechanic_name
        FROM service_job j
        JOIN vehicle v ON j.vehicle_id = v.vehicle_id
        JOIN customer c ON j.customer_id = c.customer_id
        JOIN `user` u ON j.user_id = u.user_id
        WHERE j.job_id = %s
    """
    job = fetch_one(job_query, (job_id,))
    if not job:
        flash("Service job sheet not found.", "warning")
        return redirect(url_for('jobs.list_jobs'))
        
    # Security: Mechanics should only edit their own jobs
    if session.get('role') == 'mechanic' and job['user_id'] != session.get('user_id'):
        flash("Security Alert: You are not authorized to edit jobs assigned to other technicians.", "danger")
        return redirect(url_for('jobs.list_jobs'))
        
    # Fetch active parts catalogue for parts selection
    parts = fetch_all("SELECT part_id, part_name, quantity_in_stock, selling_price, part_number FROM spare_part ORDER BY part_name ASC")
    
    return render_template('jobs/edit.html', job=job, parts=parts)

@jobs_bp.route('/jobs/<int:job_id>/update', methods=['POST'])
@login_required
def update_job(job_id):
    role = session.get('role')
    user_id = session.get('user_id')
    
    # 1. Fetch current job
    job = fetch_one("SELECT * FROM service_job WHERE job_id = %s", (job_id,))
    if not job:
        flash("Job not found.", "warning")
        return redirect(url_for('jobs.list_jobs'))
        
    # Security check for mechanics
    if role == 'mechanic' and job['user_id'] != user_id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('jobs.list_jobs'))
        
    status = request.form.get('status')
    diagnosis = request.form.get('diagnosis')
    labour_charge = float(request.form.get('labour_charge', 0.00))
    parts_used_str = request.form.get('parts_used_json', '[]')
    
    if status == 'Completed':
        # Run ACID Transaction
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        redirect_to_edit = False
        try:
            # Start explicit transaction bounds
            log_db_activity("START TRANSACTION", "NONE", "START TRANSACTION", None)
            conn.start_transaction()
            
            # Check if invoice already exists for safety
            log_select_query("SELECT invoice_id FROM invoice WHERE job_id = %s", (job_id,))
            cursor.execute("SELECT invoice_id FROM invoice WHERE job_id = %s", (job_id,))
            if cursor.fetchone():
                raise Exception("An invoice already exists for this service job.")
                
            parts_list = json.loads(parts_used_str)
            parts_total = 0.00
            
            # 1. Process inventory deduction and compute line totals
            for part in parts_list:
                part_id = part['part_id']
                qty_needed = int(part['quantity'])
                
                # Fetch stock level with row-lock to prevent race conditions
                log_select_query("SELECT quantity_in_stock, selling_price, part_name FROM spare_part WHERE part_id = %s FOR UPDATE", (part_id,))
                cursor.execute(
                    "SELECT quantity_in_stock, selling_price, part_name FROM spare_part WHERE part_id = %s FOR UPDATE",
                    (part_id,)
                )
                part_row = cursor.fetchone()
                if not part_row:
                    raise Exception(f"Catalog part ID {part_id} does not exist.")
                    
                current_stock = part_row['quantity_in_stock']
                if current_stock < qty_needed:
                    # Stock-out abort criteria
                    raise Exception(f"Not enough stock for '{part_row['part_name']}'. Current stock: {current_stock}, Needed: {qty_needed}.")
                    
                # Deduct inventory count
                part_update_query = "UPDATE spare_part SET quantity_in_stock = quantity_in_stock - %s WHERE part_id = %s"
                log_db_activity("UPDATE (TRANSACTION)", "spare_part", part_update_query, (qty_needed, part_id))
                cursor.execute(part_update_query, (qty_needed, part_id))
                
                line_total = float(part_row['selling_price']) * qty_needed
                parts_total += line_total
                
            grand_total = labour_charge + parts_total
            
            # 2. Update service job sheet
            job_update_query = """UPDATE service_job 
                   SET status = 'Completed', diagnosis = %s, parts_used = %s, labour_charge = %s 
                   WHERE job_id = %s"""
            log_db_activity("UPDATE (TRANSACTION)", "service_job", job_update_query, (diagnosis, parts_used_str, labour_charge, job_id))
            cursor.execute(job_update_query, (diagnosis, parts_used_str, labour_charge, job_id))
            
            # 3. Create invoice receipt record
            invoice_insert_query = """INSERT INTO invoice (job_id, customer_id, invoice_date, labour_total, parts_total, grand_total, payment_status, payment_method)
                   VALUES (%s, %s, CURDATE(), %s, %s, %s, 'Unpaid', 'Cash')"""
            log_db_activity("INSERT (TRANSACTION)", "invoice", invoice_insert_query, (job_id, job['customer_id'], labour_charge, parts_total, grand_total))
            cursor.execute(invoice_insert_query, (job_id, job['customer_id'], labour_charge, parts_total, grand_total))
            
            # Commit the transaction
            conn.commit()
            log_db_activity("COMMIT", "NONE", "COMMIT TRANSACTION", None, status="SUCCESS")
            print_table_snapshot("spare_part")
            print_table_snapshot("service_job")
            print_table_snapshot("invoice")
            flash(f"Service Job #{job_id} successfully marked complete. Invoice generated automatically.", "success")
            
        except Exception as e:
            # Transaction aborted: ROLLBACK all operations to preserve database consistency
            try:
                conn.rollback()
                log_db_activity("ROLLBACK", "NONE", "ROLLBACK TRANSACTION", None, status="ROLLBACK / ERROR", error_msg=str(e))
            except Exception as rollback_err:
                print(f"Error during rollback: {rollback_err}")
            flash(f"Transaction Rollback Alert: {str(e)}", "danger")
            redirect_to_edit = True
        finally:
            cursor.close()
            conn.close()
            
        if redirect_to_edit:
            return redirect(url_for('jobs.edit_job', job_id=job_id))
            
    else:
        # Regular update (Non-completed state e.g., In Progress or Cancelled)
        query = """
            UPDATE service_job 
            SET status = %s, diagnosis = %s, labour_charge = %s, parts_used = %s 
            WHERE job_id = %s
        """
        try:
            execute_write(query, (status, diagnosis, labour_charge, parts_used_str, job_id))
            flash(f"Service Job #{job_id} sheet updated successfully.", "success")
        except Exception as e:
            flash(f"Failed to update job sheet. Error: {str(e)}", "danger")
            
    return redirect(url_for('jobs.list_jobs'))
