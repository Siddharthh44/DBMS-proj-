from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth import login_required, role_required
from app.db import fetch_all, fetch_one, execute_write, get_db_connection, log_db_activity, print_table_snapshot
import mysql.connector

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory', methods=['GET'])
@login_required
@role_required(['owner', 'manager'])
def list_inventory():
    # 1. Fetch all spare parts and join supplier details
    parts_query = """
        SELECT p.*, s.supplier_name 
        FROM spare_part p
        JOIN supplier s ON p.supplier_id = s.supplier_id
        ORDER BY p.part_name ASC
    """
    parts = fetch_all(parts_query)
    
    # 2. Fetch all suppliers
    suppliers_query = "SELECT * FROM supplier ORDER BY supplier_name ASC"
    suppliers = fetch_all(suppliers_query)
    
    return render_template(
        'inventory/list.html',
        parts=parts,
        suppliers=suppliers
    )

@inventory_bp.route('/parts/add', methods=['POST'])
@login_required
@role_required(['owner', 'manager'])
def add_part():
    supplier_id = request.form.get('supplier_id')
    part_name = request.form.get('part_name')
    part_number = request.form.get('part_number', '').strip().upper()
    category = request.form.get('category')
    quantity_in_stock = int(request.form.get('quantity_in_stock', 0))
    reorder_level = int(request.form.get('reorder_level', 0))
    unit_cost = float(request.form.get('unit_cost', 0.00))
    selling_price = float(request.form.get('selling_price', 0.00))
    
    if not supplier_id or not part_name or not part_number:
        flash("Supplier, Part Name and Part Number are required.", "warning")
        return redirect(url_for('inventory.list_inventory'))
        
    query = """
        INSERT INTO spare_part (supplier_id, part_name, part_number, category, quantity_in_stock, reorder_level, unit_cost, selling_price)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        execute_write(query, (supplier_id, part_name, part_number, category, quantity_in_stock, reorder_level, unit_cost, selling_price))
        flash(f"Spare part '{part_name} ({part_number})' has been cataloged successfully.", "success")
    except mysql.connector.Error as err:
        if err.errno == 1062:
            flash(f"Database Alert: A part with Part Number '{part_number}' is already registered in the system.", "danger")
        else:
            flash(f"Database Error: {err.msg}", "danger")
    except Exception as e:
        flash(f"Failed to catalog spare part. Error: {str(e)}", "danger")
        
    return redirect(url_for('inventory.list_inventory') + "#parts-pane")

@inventory_bp.route('/parts/edit/<int:part_id>', methods=['POST'])
@login_required
@role_required(['owner', 'manager'])
def edit_part(part_id):
    supplier_id = request.form.get('supplier_id')
    part_name = request.form.get('part_name')
    part_number = request.form.get('part_number', '').strip().upper()
    category = request.form.get('category')
    reorder_level = int(request.form.get('reorder_level', 0))
    unit_cost = float(request.form.get('unit_cost', 0.00))
    selling_price = float(request.form.get('selling_price', 0.00))
    
    if not supplier_id or not part_name or not part_number:
        flash("Supplier, Part Name and Part Number are required.", "warning")
        return redirect(url_for('inventory.list_inventory'))
        
    query = """
        UPDATE spare_part 
        SET supplier_id = %s, part_name = %s, part_number = %s, category = %s, 
            reorder_level = %s, unit_cost = %s, selling_price = %s 
        WHERE part_id = %s
    """
    try:
        execute_write(query, (supplier_id, part_name, part_number, category, reorder_level, unit_cost, selling_price, part_id))
        flash(f"Details for part '{part_name}' updated successfully.", "success")
    except Exception as e:
        flash(f"Failed to update part details. Error: {str(e)}", "danger")
        
    return redirect(url_for('inventory.list_inventory') + "#parts-pane")

@inventory_bp.route('/parts/stock/add/<int:part_id>', methods=['POST'])
@login_required
@role_required(['owner', 'manager'])
def add_part_stock(part_id):
    qty_to_add = int(request.form.get('qty_to_add', 0))
    
    if qty_to_add <= 0:
        flash("Restock quantity must be positive.", "warning")
        return redirect(url_for('inventory.list_inventory'))
        
    query = "UPDATE spare_part SET quantity_in_stock = quantity_in_stock + %s WHERE part_id = %s"
    try:
        execute_write(query, (qty_to_add, part_id))
        part = fetch_one("SELECT part_name FROM spare_part WHERE part_id = %s", (part_id,))
        flash(f"Successfully added {qty_to_add} units of '{part['part_name']}' to stock.", "success")
    except Exception as e:
        flash(f"Failed to update stock levels. Error: {str(e)}", "danger")
        
    return redirect(url_for('inventory.list_inventory') + "#parts-pane")

@inventory_bp.route('/suppliers/add', methods=['POST'])
@login_required
@role_required(['owner', 'manager'])
def add_supplier():
    supplier_name = request.form.get('supplier_name')
    contact_person = request.form.get('contact_person')
    phone = request.form.get('phone')
    email = request.form.get('email')
    
    if not supplier_name:
        flash("Supplier Name is a required field.", "warning")
        return redirect(url_for('inventory.list_inventory') + "#suppliers-pane")
        
    query = """
        INSERT INTO supplier (supplier_name, contact_person, phone, email) 
        VALUES (%s, %s, %s, %s)
    """
    try:
        execute_write(query, (supplier_name, contact_person, phone, email))
        flash(f"Supplier '{supplier_name}' has been added successfully.", "success")
    except Exception as e:
        flash(f"Failed to add supplier. Error: {str(e)}", "danger")
        
    return redirect(url_for('inventory.list_inventory') + "#suppliers-pane")

@inventory_bp.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
@login_required
@role_required(['owner', 'manager'])
def delete_supplier(supplier_id):
    supplier = fetch_one("SELECT supplier_name FROM supplier WHERE supplier_id = %s", (supplier_id,))
    if not supplier:
        flash("Supplier not found.", "warning")
        return redirect(url_for('inventory.list_inventory') + "#suppliers-pane")
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        log_db_activity("START TRANSACTION", "NONE", "START TRANSACTION", None)
        conn.start_transaction()
        
        # 1. Delete all spare parts linked to this supplier
        delete_parts_query = "DELETE FROM spare_part WHERE supplier_id = %s"
        log_db_activity("DELETE (TRANSACTION)", "spare_part", delete_parts_query, (supplier_id,))
        cursor.execute(delete_parts_query, (supplier_id,))
        
        # 2. Delete supplier itself
        delete_supplier_query = "DELETE FROM supplier WHERE supplier_id = %s"
        log_db_activity("DELETE (TRANSACTION)", "supplier", delete_supplier_query, (supplier_id,))
        cursor.execute(delete_supplier_query, (supplier_id,))
        
        conn.commit()
        log_db_activity("COMMIT", "NONE", "COMMIT TRANSACTION", None, status="SUCCESS")
        print_table_snapshot("spare_part")
        print_table_snapshot("supplier")
        
        flash(f"Supplier '{supplier['supplier_name']}' and all their cataloged spare parts have been deleted successfully via a safe cascading transaction.", "success")
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
        flash(f"Failed to delete supplier: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('inventory.list_inventory') + "#suppliers-pane")
