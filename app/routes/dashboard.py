from flask import Blueprint, render_template, session, redirect, url_for
from app.auth import login_required
from app.db import fetch_one, fetch_all, get_db_connection

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def home():
    # If the logged-in user is a mechanic, redirect to their jobs listing directly
    if session.get('role') == 'mechanic':
        return redirect(url_for('jobs.list_jobs'))
        
    try:
        # 1. Count active jobs
        active_jobs_query = "SELECT COUNT(*) AS active_jobs FROM service_job WHERE status IN ('Pending', 'In Progress')"
        active_jobs_res = fetch_one(active_jobs_query)
        active_jobs_count = active_jobs_res['active_jobs'] if active_jobs_res else 0
        
        # 2. Count low stock inventory items
        low_stock_query = "SELECT COUNT(*) AS low_stock_count FROM spare_part WHERE quantity_in_stock <= reorder_level"
        low_stock_res = fetch_one(low_stock_query)
        low_stock_count = low_stock_res['low_stock_count'] if low_stock_res else 0
        
        # 3. Sum current month revenue using stored procedure
        conn = None
        cursor = None
        monthly_revenue = 0.00
        monthly_invoice_count = 0
        try:
            print("[DEBUG] Executing monthly revenue cursor procedure...")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("CALL get_monthly_revenue_summary(@total_sales, @invoice_count)")
            cursor.execute("SELECT @total_sales, @invoice_count")
            result = cursor.fetchone()
            if result:
                monthly_revenue = float(result[0]) if result[0] is not None else 0.00
                monthly_invoice_count = int(result[1]) if result[1] is not None else 0
            print(f"[DEBUG] Monthly revenue fetched successfully: ₹{monthly_revenue}, count: {monthly_invoice_count}")
        except Exception as e:
            print(f"[DEBUG ERROR] Procedure execution failed: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            monthly_revenue = 0.00
            monthly_invoice_count = 0
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        
        # 4. Sum unpaid invoice balance totals
        unpaid_query = "SELECT COALESCE(SUM(grand_total), 0.00) AS unpaid_invoices FROM invoice WHERE payment_status = 'Unpaid'"
        unpaid_res = fetch_one(unpaid_query)
        unpaid_invoices = unpaid_res['unpaid_invoices'] if unpaid_res else 0.00
        
        # 5. Fetch recent 5 service jobs
        recent_jobs_query = """
            SELECT j.job_id, j.job_date, j.status, j.labour_charge, j.complaint,
                   v.registration_no, v.make, v.model,
                   c.full_name AS customer_name
            FROM service_job j
            JOIN vehicle v ON j.vehicle_id = v.vehicle_id
            JOIN customer c ON j.customer_id = c.customer_id
            ORDER BY j.job_id DESC
            LIMIT 5
        """
        recent_jobs = fetch_all(recent_jobs_query)
        
        # 6. Fetch top 5 low stock parts for alert list
        low_stock_items_query = """
            SELECT part_name, quantity_in_stock, reorder_level, category
            FROM spare_part
            WHERE quantity_in_stock <= reorder_level
            ORDER BY quantity_in_stock ASC
            LIMIT 5
        """
        low_stock_items = fetch_all(low_stock_items_query)
        
        # 7. Fetch data for Revenue Chart
        chart_revenue_query = """
            SELECT DATE_FORMAT(invoice_date, '%b %Y') AS month_name, SUM(grand_total) AS total_revenue
            FROM invoice
            GROUP BY YEAR(invoice_date), MONTH(invoice_date), month_name
            ORDER BY YEAR(invoice_date) ASC, MONTH(invoice_date) ASC
            LIMIT 6
        """
        revenue_chart_data = fetch_all(chart_revenue_query)
        revenue_labels = [row['month_name'] for row in revenue_chart_data]
        # Cover float conversion to prevent json serialization errors
        revenue_data = [float(row['total_revenue']) for row in revenue_chart_data]
        
        # 8. Fetch data for Job Distribution Chart
        chart_job_query = """
            SELECT status, COUNT(*) AS job_count 
            FROM service_job 
            GROUP BY status
        """
        job_chart_data = fetch_all(chart_job_query)
        job_labels = [row['status'] for row in job_chart_data]
        job_data = [row['job_count'] for row in job_chart_data]
        
    except Exception as e:
        print(f"Error executing dashboard queries: {e}")
        active_jobs_count = 0
        low_stock_count = 0
        monthly_revenue = 0.00
        unpaid_invoices = 0.00
        recent_jobs = []
        low_stock_items = []
        revenue_labels = []
        revenue_data = []
        job_labels = []
        job_data = []
        
    return render_template(
        'dashboard.html',
        active_jobs_count=active_jobs_count,
        low_stock_count=low_stock_count,
        monthly_revenue=monthly_revenue,
        unpaid_invoices=unpaid_invoices,
        recent_jobs=recent_jobs,
        low_stock_items=low_stock_items,
        revenue_labels=revenue_labels,
        revenue_data=revenue_data,
        job_labels=job_labels,
        job_data=job_data
    )
