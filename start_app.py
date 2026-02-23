"""
Startup script for Secure AI Studio
This script provides an easy way to start the application
"""

import os
import sys
from app.main import app

def main():
    """
    Main function to start the Secure AI Studio application
    """
    print("🚀 Starting Secure AI Studio...")
    print("🛡️  Security measures active")
    print("💰 Budget controls active") 
    print("🔒 LGPD compliance active")
    print("")
    print("Application is ready at: http://localhost:5000")
    print("Press CTRL+C to stop the application")
    print("")
    
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the Flask application
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=(os.environ.get('FLASK_ENV') == 'development')
        )
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()