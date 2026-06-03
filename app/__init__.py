import os
from flask import Flask, render_template

def create_app():
    # Use template_folder and static_folder parameters explicitly to target project root structure
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )
    
    # Configure session secret key
    app.secret_key = os.environ.get("SECRET_KEY", "fender_garage_secret_key_12345")
    
    # Auto-initialize database triggers and stored procedures
    from app.db import initialize_database_extensions
    initialize_database_extensions()
    
    # Register blueprints
    from app.routes.dashboard import dashboard_bp
    from app.routes.customers import customer_bp
    from app.routes.inventory import inventory_bp
    from app.routes.jobs import jobs_bp
    from app.routes.billing import billing_bp
    from app.routes.db_showcase import db_showcase_bp
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(db_showcase_bp)
    
    # Register auth blueprints separately
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    # Custom error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
        
    return app
