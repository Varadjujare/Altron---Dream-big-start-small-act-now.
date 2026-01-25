"""
Authentication routes for LifeSync Dashboard.
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Username, email, and password are required'
            }), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate username length
        if len(username) < 3 or len(username) > 50:
            return jsonify({
                'success': False,
                'message': 'Username must be between 3 and 50 characters'
            }), 400
        
        # Validate password length
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 6 characters'
            }), 400
        
        # Check if user already exists
        if User.get_by_email(email):
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 409
        
        if User.get_by_username(username):
            return jsonify({
                'success': False,
                'message': 'Username already taken'
            }), 409
        
        # Create user
        user = User.create(username, email, password)
        
        # Send welcome email (non-blocking)
        try:
            from utils.email_service import email_service
            import threading
            if email_service.is_configured:
                # Run in a separate thread to not block the response
                email_thread = threading.Thread(
                    target=email_service.send_welcome_email,
                    args=(email, username)
                )
                email_thread.daemon = True
                email_thread.start()
        except Exception as email_error:
            print(f"⚠️ Failed to initiate welcome email: {email_error}")
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user."""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Find user by email
        user = User.get_by_email(email)
        
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        # Login user with Flask-Login
        login_user(user, remember=data.get('remember', False))
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Login failed: {str(e)}'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user."""
    try:
        logout_user()
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Logout failed: {str(e)}'
        }), 500


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged in user."""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), 200


@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        }), 200
    return jsonify({
        'authenticated': False
    }), 200


@auth_bp.route('/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get user preferences."""
    return jsonify({
        'success': True,
        'preferences': {
            'theme': current_user.theme_preference
        }
    }), 200


@auth_bp.route('/preferences', methods=['PUT'])
@login_required
def update_preferences():
    """Update user preferences."""
    try:
        data = request.get_json()
        
        if 'theme' in data:
            theme = data['theme']
            if theme not in ['light', 'dark']:
                return jsonify({
                    'success': False,
                    'message': 'Invalid theme value'
                }), 400
            current_user.update_theme(theme)
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated',
            'preferences': {
                'theme': current_user.theme_preference
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update preferences: {str(e)}'
        }), 500
