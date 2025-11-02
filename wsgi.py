"""
WSGI entry point for production deployment with Gunicorn
"""
import os
from web.dashboard import app, socketio

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
