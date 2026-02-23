from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
from app.utils.logging_config import setup_logging

# Setup logging
setup_logging()

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key-for-testing')

# Import routes after app is created to avoid circular imports
from app.routes import register_routes
register_routes(app)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=(os.getenv('FLASK_ENV') == 'development'))