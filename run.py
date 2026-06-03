import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env if present
load_dotenv()

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    
    print(f"Starting Fender Garage Management System on http://{host}:{port}/")
    app.run(host=host, port=port, debug=debug)
