import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth import login_required, role_required
from app.db import fetch_all, fetch_one, execute_write

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/invoices', methods=['GET'])
@login_required
@role_required(['owner', 'receptionist'])
def list_invoices():
    # Fetch all invoices joining customer and vehicle registration details
    query = """
        SELECT i.*, c.full_name AS customer_name, c.phone AS customer_phone,
               v.registration_no, v.make, v.model, j.job_date
        FROM invoice i
        JOIN customer c ON i.customer_id = c.customer_id
        JOIN service_job j ON i.job_id = j.job_id
        JOIN vehicle v ON j.vehicle_id = v.vehicle_id
        ORDER BY i.invoice_id DESC
    """
    invoices = fetch_all(query)
    
    return render_template('billing/list.html', invoices=invoices)

@billing_bp.route('/invoices/receipt/<int:job_id>', methods=['GET'])
@login_required
def receipt_invoice(job_id):
    # Fetch detailed invoice with customer, vehicle and job details
    invoice_query = """
        SELECT i.*, c.full_name AS customer_name, c.phone AS customer_phone, c.email AS customer_email, c.address AS customer_address,
               v.registration_no, v.make, v.model, v.manufacture_year, v.mileage,
               j.diagnosis, j.complaint, j.parts_used, u.full_name AS mechanic_name
        FROM invoice i
        JOIN customer c ON i.customer_id = c.customer_id
        JOIN service_job j ON i.job_id = j.job_id
        JOIN vehicle v ON j.vehicle_id = v.vehicle_id
        JOIN `user` u ON j.user_id = u.user_id
        WHERE i.job_id = %s
    """
    invoice = fetch_one(invoice_query, (job_id,))
    if not invoice:
        flash("Billing invoice not found.", "warning")
        return redirect(url_for('dashboard.home'))
        
    # Deserialize parts used JSON list
    try:
        parts_list = json.loads(invoice['parts_used'] or '[]')
    except Exception as e:
        print(f"Error parsing parts JSON in receipt: {e}")
        parts_list = []
        
    return render_template('billing/receipt.html', invoice=invoice, parts_list=parts_list)

@billing_bp.route('/invoices/pay/<int:invoice_id>', methods=['POST'])
@login_required
@role_required(['owner', 'receptionist'])
def settle_payment(invoice_id):
    payment_status = request.form.get('payment_status')
    payment_method = request.form.get('payment_method')
    
    if not payment_status or not payment_method:
        flash("Payment status and payment method are required.", "warning")
        return redirect(url_for('billing.list_invoices'))
        
    query = """
        UPDATE invoice 
        SET payment_status = %s, payment_method = %s 
        WHERE invoice_id = %s;
    """
    try:
        execute_write(query, (payment_status, payment_method, invoice_id))
        flash(f"Invoice #{invoice_id} payment status updated to '{payment_status}' using '{payment_method}'.", "success")
    except Exception as e:
        flash(f"Failed to update payment status. Error: {str(e)}", "danger")
        
    return redirect(url_for('billing.list_invoices'))
