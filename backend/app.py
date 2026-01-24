"""
Altron Dashboard - Flask Application Entry Point
"""
import os
from flask import Flask, send_from_directory, jsonify
from flask_login import LoginManager
from flask_cors import CORS
from config import Config
from models.user import User
from routes import auth_bp, habits_bp, tasks_bp, analytics_bp
from routes.reports import reports_bp

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config.from_object(Config)

# Enable CORS for development
CORS(app, supports_credentials=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'serve_login'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.get_by_id(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access."""
    return jsonify({
        'success': False,
        'message': 'Authentication required'
    }), 401


# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(habits_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(reports_bp)


# Serve frontend files
@app.route('/')
def serve_login():
    """Serve the login page."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/register')
def serve_register():
    """Serve the register page."""
    return send_from_directory(app.static_folder, 'register.html')


@app.route('/home')
def serve_home():
    """Serve the home page."""
    return send_from_directory(app.static_folder, 'home.html')


@app.route('/dashboard')
def serve_dashboard():
    """Serve the dashboard page."""
    return send_from_directory(app.static_folder, 'dashboard.html')


@app.route('/habits')
def serve_habits():
    """Serve the habits page."""
    return send_from_directory(app.static_folder, 'habits.html')


@app.route('/tasks')
def serve_tasks():
    """Serve the tasks page."""
    return send_from_directory(app.static_folder, 'tasks.html')


@app.route('/analytics')
def serve_analytics():
    """Serve the analytics page."""
    return send_from_directory(app.static_folder, 'analytics.html')


@app.route('/calendar')
def serve_calendar():
    """Serve the calendar page."""
    return send_from_directory(app.static_folder, 'calendar.html')


@app.route('/settings')
def serve_settings():
    """Serve the settings page."""
    return send_from_directory(app.static_folder, 'settings.html')


@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files."""
    return send_from_directory(os.path.join(app.static_folder, 'css'), filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files."""
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve asset files."""
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)


# Error handlers
@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500


from utils.scheduler import scheduler

# Start the background scheduler
scheduler.start()


if __name__ == '__main__':
    print("=" * 50)
    print("  Altron Dashboard")
    print("  Starting server at http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
