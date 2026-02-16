"""
Tasks routes for LifeSync Dashboard.
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.task import Task

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


@tasks_bp.route('', methods=['GET'])
@login_required
def get_tasks():
    """Get all tasks for current user."""
    try:
        include_completed = request.args.get('completed', 'true').lower() == 'true'
        date_str = request.args.get('date')
        
        tasks = Task.get_all_by_user(
            current_user.id, 
            include_completed=include_completed,
            target_date=date_str
        )
        
        return jsonify({
            'success': True,
            'tasks': tasks
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch tasks: {str(e)}'
        }), 500


@tasks_bp.route('', methods=['POST'])
@login_required
def create_task():
    """Create a new task."""
    try:
        data = request.get_json()
        
        if not data or not data.get('title'):
            return jsonify({
                'success': False,
                'message': 'Task title is required'
            }), 400
        
        task = Task.create(
            user_id=current_user.id,
            title=data['title'],
            description=data.get('description'),
            due_date=data.get('due_date'),
            priority=data.get('priority', 'medium'),
            category=data.get('category', 'general')
        )
        
        return jsonify({
            'success': True,
            'message': 'Task created successfully',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to create task: {str(e)}'
        }), 500


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """Get a specific task."""
    try:
        task = Task.get_by_id(task_id)
        
        if not task or task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        return jsonify({
            'success': True,
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch task: {str(e)}'
        }), 500


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """Update a task."""
    try:
        task = Task.get_by_id(task_id)
        
        if not task or task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        data = request.get_json()
        task.update(**data)
        
        return jsonify({
            'success': True,
            'message': 'Task updated successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update task: {str(e)}'
        }), 500


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """Delete a task."""
    try:
        task = Task.get_by_id(task_id)
        
        if not task or task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        task.delete()
        
        return jsonify({
            'success': True,
            'message': 'Task deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to delete task: {str(e)}'
        }), 500


@tasks_bp.route('/<int:task_id>/complete', methods=['PATCH'])
@login_required
def toggle_task_complete(task_id):
    """Toggle task completion status."""
    try:
        task = Task.get_by_id(task_id)
        
        if not task or task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        is_completed = task.toggle_complete()
        
        return jsonify({
            'success': True,
            'message': 'Task status updated',
            'is_completed': is_completed,
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update task: {str(e)}'
        }), 500


@tasks_bp.route('/by-date/<date_str>', methods=['GET'])
@login_required
def get_tasks_by_date(date_str):
    """Get tasks for a specific date."""
    try:
        tasks = Task.get_by_date(current_user.id, date_str)
        stats = Task.get_stats_for_date(current_user.id, date_str)
        
        return jsonify({
            'success': True,
            'date': date_str,
            'tasks': tasks,
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch tasks: {str(e)}'
        }), 500


@tasks_bp.route('/dates', methods=['GET'])
@login_required
def get_dates_with_tasks():
    """Get all dates that have tasks with counts."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        dates = Task.get_dates_with_tasks(
            current_user.id, 
            start_date=start_date, 
            end_date=end_date
        )
        
        return jsonify({
            'success': True,
            'dates': dates
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch dates: {str(e)}'
        }), 500


@tasks_bp.route('/overdue', methods=['GET'])
@login_required
def get_overdue_tasks():
    """Get all overdue tasks (incomplete with past due dates)."""
    try:
        tasks = Task.get_overdue_tasks(current_user.id)
        
        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch overdue tasks: {str(e)}'
        }), 500


@tasks_bp.route('/no-date', methods=['GET'])
@login_required
def get_no_date_tasks():
    """Get all tasks without a due date (backlog)."""
    try:
        tasks = Task.get_no_date_tasks(current_user.id)
        
        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch backlog tasks: {str(e)}'
        }), 500


@tasks_bp.route('/all-organized', methods=['GET'])
@login_required
def get_all_organized_tasks():
    """Get all tasks organized by sections (overdue, dates, backlog) in one call."""
    try:
        organized_data = Task.get_all_organized(current_user.id)
        
        return jsonify({
            'success': True,
            'data': organized_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch tasks: {str(e)}'
        }), 500


@tasks_bp.route('/bulk-update-date', methods=['PATCH'])
@login_required
def bulk_update_task_date():
    """Update due date for multiple tasks at once."""
    try:
        data = request.get_json()
        
        if not data or not data.get('task_ids') or not data.get('new_date'):
            return jsonify({
                'success': False,
                'message': 'task_ids and new_date are required'
            }), 400
        
        # Verify all tasks belong to current user
        task_ids = data['task_ids']
        for task_id in task_ids:
            task = Task.get_by_id(task_id)
            if not task or task.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': f'Task {task_id} not found or unauthorized'
                }), 404
        
        updated_count = Task.bulk_update_date(task_ids, data['new_date'])
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} tasks',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update tasks: {str(e)}'
        }), 500

