"""
Habits routes for LifeSync Dashboard.
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.habit import Habit

habits_bp = Blueprint('habits', __name__, url_prefix='/api/habits')


@habits_bp.route('', methods=['GET'])
@login_required
def get_habits():
    """Get all habits for current user."""
    try:
        active_only = request.args.get('active', 'true').lower() == 'true'
        habits = Habit.get_all_by_user(current_user.id, active_only=active_only)
        return jsonify({
            'success': True,
            'habits': habits
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch habits: {str(e)}'
        }), 500


@habits_bp.route('', methods=['POST'])
@login_required
def create_habit():
    """Create a new habit."""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Habit name is required'
            }), 400
        
        habit = Habit.create(
            user_id=current_user.id,
            name=data['name'],
            description=data.get('description'),
            color=data.get('color', '#4CAF50'),
            icon=data.get('icon', '✓')
        )
        
        return jsonify({
            'success': True,
            'message': 'Habit created successfully',
            'habit': habit.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to create habit: {str(e)}'
        }), 500


@habits_bp.route('/<int:habit_id>', methods=['GET'])
@login_required
def get_habit(habit_id):
    """Get a specific habit."""
    try:
        habit = Habit.get_by_id(habit_id)
        
        if not habit or habit.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Habit not found'
            }), 404
        
        return jsonify({
            'success': True,
            'habit': habit.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch habit: {str(e)}'
        }), 500


@habits_bp.route('/<int:habit_id>', methods=['PUT'])
@login_required
def update_habit(habit_id):
    """Update a habit."""
    try:
        habit = Habit.get_by_id(habit_id)
        
        if not habit or habit.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Habit not found'
            }), 404
        
        data = request.get_json()
        habit.update(**data)
        
        return jsonify({
            'success': True,
            'message': 'Habit updated successfully',
            'habit': habit.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update habit: {str(e)}'
        }), 500


@habits_bp.route('/<int:habit_id>', methods=['DELETE'])
@login_required
def delete_habit(habit_id):
    """Delete a habit."""
    try:
        habit = Habit.get_by_id(habit_id)
        
        if not habit or habit.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Habit not found'
            }), 404
        
        habit.delete()
        
        return jsonify({
            'success': True,
            'message': 'Habit deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to delete habit: {str(e)}'
        }), 500


@habits_bp.route('/<int:habit_id>/toggle', methods=['POST'])
@login_required
def toggle_habit(habit_id):
    """Toggle habit completion for a specific date."""
    try:
        habit = Habit.get_by_id(habit_id)
        
        if not habit or habit.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Habit not found'
            }), 404
        
        data = request.get_json()
        date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        result = Habit.toggle_completion(habit_id, date_str)
        
        return jsonify({
            'success': True,
            'message': 'Habit toggled successfully',
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to toggle habit: {str(e)}'
        }), 500


@habits_bp.route('/logs', methods=['GET'])
@login_required
def get_habit_logs():
    """Get habit completion logs for a specific month."""
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        logs = Habit.get_logs_for_month(current_user.id, year, month)
        
        return jsonify({
            'success': True,
            'year': year,
            'month': month,
            'habits': logs
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch habit logs: {str(e)}'
        }), 500


@habits_bp.route('/status', methods=['GET'])
@login_required
def get_habits_status():
    """Get completion status for all habits on a specific date."""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        habits = Habit.get_completion_status(current_user.id, date_str)
        
        return jsonify({
            'success': True,
            'date': date_str,
            'habits': habits
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch habits status: {str(e)}'
        }), 500
