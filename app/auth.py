from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db import fetch_one

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator to block unauthenticated requests."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Decorator to restrict access to specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in allowed_roles:
                flash("Access Denied: You do not have permission to view this section.", "danger")
                return redirect(url_for('dashboard.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple plain-text query as per specifications (viva-friendly academic project)
        query = "SELECT user_id, username, role, full_name FROM user WHERE username = %s AND password = %s"
        try:
            user = fetch_one(query, (username, password))
            if user:
                # Store user details in session
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['full_name'] = user['full_name']
                
                flash(f"Welcome back, {user['full_name']}!", "success")
                return redirect(url_for('dashboard.home'))
            else:
                flash("Invalid username or password. Please try again.", "danger")
        except Exception as e:
            flash(f"Database connection error: {str(e)}", "danger")
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have successfully logged out.", "info")
    return redirect(url_for('auth.login'))
