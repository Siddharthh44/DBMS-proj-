from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.auth import login_required, role_required
from app.db import fetch_all

db_showcase_bp = Blueprint('db_showcase', __name__)

@db_showcase_bp.route('/showcase', methods=['GET'])
@login_required
@role_required(['owner'])
def showcase():
    # Execute query to fetch metadata info about the garage_db schema dynamically
    try:
        metadata_query = """
            SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'garage_db'
            ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
        raw_metadata = fetch_all(metadata_query)
        
        # Group columns by table name for nice dashboard layout mapping
        db_tables = {}
        for col in raw_metadata:
            table = col['TABLE_NAME']
            if table not in db_tables:
                db_tables[table] = []
            db_tables[table].append(col)
            
    except Exception as e:
        print(f"[DEBUG ERROR] Error fetching schema metadata from INFORMATION_SCHEMA: {e}")
        db_tables = {}
        
    # Fetch live MySQL trigger execution logs
    try:
        db_logs = fetch_all("SELECT * FROM db_log ORDER BY log_id DESC LIMIT 15")
        print(f"[DEBUG] Fetching db_log. Row count fetched: {len(db_logs)}")
    except Exception as e:
        print(f"[DEBUG ERROR] Error fetching db_log entries: {e}")
        db_logs = []
        
    return render_template('db_showcase.html', db_tables=db_tables, db_logs=db_logs)


@db_showcase_bp.route('/showcase/procedure/revenue', methods=['POST'])
@login_required
@role_required(['owner'])
def run_revenue_procedure():
    from app.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Call procedure using cursor and aggregate out variables
        cursor.execute("CALL get_monthly_revenue_summary(@total_sales, @invoice_count)")
        cursor.execute("SELECT @total_sales, @invoice_count")
        result = cursor.fetchone()
        
        total_sales = float(result[0]) if result and result[0] is not None else 0.00
        invoice_count = int(result[1]) if result and result[1] is not None else 0
        
        print(f"[DEBUG] Procedure get_monthly_revenue_summary successful. Sales: {total_sales}, Invoices: {invoice_count}")
        flash(f"PROCEDURE EXECUTION SUCCESSFUL:<br>Aggregated paid invoice sales using a CURSOR loop successfully:<br>• <strong>Calculated Aggregate Revenue:</strong> ₹{total_sales:,.2f}<br>• <strong>Paid Invoice Transactions Checked:</strong> {invoice_count} records", "success")
    except Exception as e:
        print(f"[DEBUG ERROR] Stored Procedure get_monthly_revenue_summary failed: {e}")
        flash(f"Failed to execute Stored Procedure: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('db_showcase.showcase') + "#proc-section")


@db_showcase_bp.route('/showcase/procedure/lowstock', methods=['POST'])
@login_required
@role_required(['owner'])
def run_lowstock_procedure():
    from app.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Call cursor report procedure
        cursor.execute("CALL get_low_stock_report(@report_out)")
        cursor.execute("SELECT @report_out")
        result = cursor.fetchone()
        report_out = result[0] if result and result[0] is not None else "No report generated."
        
        print(f"[DEBUG] Procedure get_low_stock_report successful. Report length: {len(report_out)}")
        # Replace line breaks for clean rendering in browser alert
        html_report = report_out.replace("\n", "<br>")
        flash(f"PROCEDURE EXECUTION SUCCESSFUL:<br><div class='text-start monospace-view mt-2' style='font-size:0.8rem;'>{html_report}</div>", "success")
    except Exception as e:
        print(f"[DEBUG ERROR] Stored Procedure get_low_stock_report failed: {e}")
        flash(f"Failed to execute Stored Procedure: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('db_showcase.showcase') + "#proc-section")
