"""
Analytics routes for LifeSync Dashboard.
Provides real-time statistics and progress data.
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from utils.db import execute_query

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@analytics_bp.route('/daily', methods=['GET'])
@login_required
def get_daily_stats():
    """Get daily habit completion statistics."""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Get total active habits
        total_query = """
            SELECT COUNT(*) as total 
            FROM habits 
            WHERE user_id = %s AND is_active = TRUE
        """
        total_result = execute_query(total_query, (current_user.id,), fetch_one=True)
        total_habits = total_result['total'] if total_result else 0
        
        # Get completed habits for the date
        completed_query = """
            SELECT COUNT(DISTINCT hl.habit_id) as completed
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = %s AND hl.completed_date = %s AND h.is_active = TRUE
        """
        completed_result = execute_query(completed_query, (current_user.id, date_str), fetch_one=True)
        completed_habits = completed_result['completed'] if completed_result else 0
        
        # Calculate percentage
        percentage = round((completed_habits / total_habits * 100), 1) if total_habits > 0 else 0
        
        # Get task stats for the day
        task_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed
            FROM tasks 
            WHERE user_id = %s AND (due_date = %s OR (due_date IS NULL AND created_at::DATE = %s))
        """
        task_result = execute_query(task_query, (current_user.id, date_str, date_str), fetch_one=True)
        
        return jsonify({
            'success': True,
            'date': date_str,
            'habits': {
                'total': total_habits,
                'completed': completed_habits,
                'percentage': percentage
            },
            'tasks': {
                'total': task_result['total'] or 0,
                'completed': task_result['completed'] or 0,
                'percentage': round((task_result['completed'] or 0) / (task_result['total'] or 1) * 100, 1)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch daily stats: {str(e)}'
        }), 500


@analytics_bp.route('/weekly', methods=['GET'])
@login_required
def get_weekly_stats():
    """Get weekly habit completion statistics."""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Calculate week start (Monday) and end (Sunday)
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Get daily stats for each day of the week in one query
        query = """
            SELECT 
                hl.completed_date,
                COUNT(DISTINCT hl.habit_id) as completed
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = %s 
                AND hl.completed_date >= %s 
                AND hl.completed_date <= %s
                AND h.is_active = TRUE
            GROUP BY hl.completed_date
        """
        results = execute_query(query, (current_user.id, week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')), fetch_all=True)
        
        # Map results to dictionary for easy lookup
        stats_map = {str(row['completed_date']): row['completed'] for row in results}
        
        daily_stats = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_str = day.strftime('%Y-%m-%d')
            
            daily_stats.append({
                'date': day_str,
                'day_name': day.strftime('%a'),
                'completed': stats_map.get(day_str, 0)
            })
        
        # Get total active habits
        total_query = """
            SELECT COUNT(*) as total 
            FROM habits 
            WHERE user_id = %s AND is_active = TRUE
        """
        total_result = execute_query(total_query, (current_user.id,), fetch_one=True)
        total_habits = total_result['total'] if total_result else 0
        
        # Calculate weekly totals
        total_completed = sum(d['completed'] for d in daily_stats)
        max_possible = total_habits * 7
        weekly_percentage = round((total_completed / max_possible * 100), 1) if max_possible > 0 else 0
        
        return jsonify({
            'success': True,
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'total_habits': total_habits,
            'daily_stats': daily_stats,
            'weekly_total': total_completed,
            'weekly_percentage': weekly_percentage
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch weekly stats: {str(e)}'
        }), 500


@analytics_bp.route('/monthly', methods=['GET'])
@login_required
def get_monthly_stats():
    """Get monthly habit completion statistics."""
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        # Get total active habits
        total_query = """
            SELECT COUNT(*) as total 
            FROM habits 
            WHERE user_id = %s AND is_active = TRUE
        """
        total_result = execute_query(total_query, (current_user.id,), fetch_one=True)
        total_habits = total_result['total'] if total_result else 0
        
        # Get daily completion counts for the month
        daily_query = """
            SELECT 
                hl.completed_date,
                COUNT(DISTINCT hl.habit_id) as completed
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = %s 
                AND EXTRACT(YEAR FROM hl.completed_date) = %s 
                AND EXTRACT(MONTH FROM hl.completed_date) = %s
                AND h.is_active = TRUE
            GROUP BY hl.completed_date
            ORDER BY hl.completed_date
        """
        daily_results = execute_query(daily_query, (current_user.id, year, month), fetch_all=True)
        
        # Format daily data
        daily_data = {}
        for row in daily_results:
            date_key = str(row['completed_date'])
            daily_data[date_key] = {
                'completed': row['completed'],
                'percentage': round((row['completed'] / total_habits * 100), 1) if total_habits > 0 else 0
            }
        
        # Calculate monthly totals
        total_completed = sum(d['completed'] for d in daily_results)
        
        # Get number of days in month
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        max_possible = total_habits * days_in_month
        monthly_percentage = round((total_completed / max_possible * 100), 1) if max_possible > 0 else 0
        
        return jsonify({
            'success': True,
            'year': year,
            'month': month,
            'total_habits': total_habits,
            'days_in_month': days_in_month,
            'daily_data': daily_data,
            'monthly_total': total_completed,
            'monthly_percentage': monthly_percentage
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch monthly stats: {str(e)}'
        }), 500


@analytics_bp.route('/streaks', methods=['GET'])
@login_required
def get_streaks():
    """Get current and best streaks for habits."""
    try:
        # Get all habits with their completion logs
        habits_query = """
            SELECT id, name FROM habits 
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY sort_order, id
        """
        habits = execute_query(habits_query, (current_user.id,), fetch_all=True)
        
        # Get all completion logs for user in one query
        logs_query = """
            SELECT hl.habit_id, hl.completed_date 
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = %s AND h.is_active = TRUE
            ORDER BY hl.habit_id, hl.completed_date DESC
        """
        all_logs = execute_query(logs_query, (current_user.id,), fetch_all=True)
        
        # Group logs by habit_id
        logs_by_habit = {}
        for log in all_logs:
            hid = log['habit_id']
            if hid not in logs_by_habit:
                logs_by_habit[hid] = []
            logs_by_habit[hid].append(log['completed_date'])
            
        today = datetime.now().date()
        streaks = []
        
        for habit in habits:
            habit_id = habit['id']
            habit_logs = logs_by_habit.get(habit_id, [])
            
            if not habit_logs:
                streaks.append({
                    'habit_id': habit_id,
                    'habit_name': habit['name'],
                    'current_streak': 0,
                    'best_streak': 0
                })
                continue
                
            # Calculate current streak
            current_streak = 0
            check_date = today
            dates_set = set(habit_logs)
            
            while check_date in dates_set:
                current_streak += 1
                check_date -= timedelta(days=1)
            
            # If today not completed but yesterday was, check from yesterday
            if current_streak == 0:
                check_date = today - timedelta(days=1)
                while check_date in dates_set:
                    current_streak += 1
                    check_date -= timedelta(days=1)
            
            # Calculate best streak
            # habit_logs is already sorted DESC, so reverse for ASC
            sorted_dates = sorted(habit_logs)
            best_streak = 1
            temp_streak = 1
            
            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                    temp_streak += 1
                    best_streak = max(best_streak, temp_streak)
                else:
                    temp_streak = 1
            
            streaks.append({
                'habit_id': habit_id,
                'habit_name': habit['name'],
                'current_streak': current_streak,
                'best_streak': best_streak
            })
        
        # Calculate overall stats
        total_current = sum(s['current_streak'] for s in streaks)
        total_best = sum(s['best_streak'] for s in streaks)
        
        return jsonify({
            'success': True,
            'habits': streaks,
            'totals': {
                'total_current_streak': total_current,
                'total_best_streak': total_best
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch streaks: {str(e)}'
        }), 500


@analytics_bp.route('/overview', methods=['GET'])
@login_required
def get_overview():
    """Get overall progress overview for dashboard."""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get today's habit completion
        habit_query = """
            SELECT 
                (SELECT COUNT(*) FROM habits WHERE user_id = %s AND is_active = TRUE) as total,
                (SELECT COUNT(DISTINCT hl.habit_id) 
                 FROM habit_logs hl 
                 JOIN habits h ON hl.habit_id = h.id 
                 WHERE h.user_id = %s AND hl.completed_date = %s AND h.is_active = TRUE) as completed
        """
        habit_result = execute_query(habit_query, (current_user.id, current_user.id, today), fetch_one=True)
        
        # Get today's task completion
        task_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed
            FROM tasks 
            WHERE user_id = %s AND (due_date = %s OR due_date IS NULL)
        """
        task_result = execute_query(task_query, (current_user.id, today), fetch_one=True)
        
        # Calculate overall daily progress
        habit_total = habit_result['total'] if habit_result else 0
        habit_completed = habit_result['completed'] if habit_result else 0
        task_total = task_result['total'] or 0
        task_completed = task_result['completed'] or 0
        
        total_items = habit_total + task_total
        total_completed = habit_completed + task_completed
        overall_percentage = round((total_completed / total_items * 100), 1) if total_items > 0 else 0
        
        return jsonify({
            'success': True,
            'date': today,
            'habits': {
                'total': habit_total,
                'completed': habit_completed,
                'percentage': round((habit_completed / habit_total * 100), 1) if habit_total > 0 else 0
            },
            'tasks': {
                'total': task_total,
                'completed': task_completed,
                'percentage': round((task_completed / task_total * 100), 1) if task_total > 0 else 0
            },
            'overall': {
                'total': total_items,
                'completed': total_completed,
                'percentage': overall_percentage
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch overview: {str(e)}'
        }), 500


@analytics_bp.route('/dashboard-data', methods=['GET'])
@login_required
def get_dashboard_data():
    """Get all dashboard data in a single request for performance."""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 1. Overview Stats (Habits + Tasks)
        # Optimized query to get habit stats in one go
        habit_stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM habits WHERE user_id = %s AND is_active = TRUE) as total,
                (SELECT COUNT(DISTINCT hl.habit_id) 
                 FROM habit_logs hl 
                 JOIN habits h ON hl.habit_id = h.id 
                 WHERE h.user_id = %s AND hl.completed_date = %s AND h.is_active = TRUE) as completed
        """
        habit_stats = execute_query(habit_stats_query, (current_user.id, current_user.id, today), fetch_one=True)
        
        # Optimized query for task stats
        task_stats_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed
            FROM tasks 
            WHERE user_id = %s AND (due_date = %s OR due_date IS NULL)
        """
        task_stats = execute_query(task_stats_query, (current_user.id, today), fetch_one=True)
        
        # Calculate percentages
        h_total = habit_stats['total'] if habit_stats else 0
        h_comp = habit_stats['completed'] if habit_stats else 0
        t_total = task_stats['total'] or 0
        t_comp = task_stats['completed'] or 0
        
        total_items = h_total + t_total
        total_completed = h_comp + t_comp
        overall_pct = round((total_completed / total_items * 100), 1) if total_items > 0 else 0
        
        overview = {
            'date': today,
            'habits': {'total': h_total, 'completed': h_comp, 'percentage': round((h_comp / h_total * 100), 1) if h_total > 0 else 0},
            'tasks': {'total': t_total, 'completed': t_comp, 'percentage': round((t_comp / t_total * 100), 1) if t_total > 0 else 0},
            'overall': {'percentage': overall_pct}
        }

        # 2. Habits List (Today's status)
        habits_query = """
            SELECT h.id, h.name, h.color, h.icon,
                   CASE WHEN hl.id IS NOT NULL THEN TRUE ELSE FALSE END as is_completed
            FROM habits h
            LEFT JOIN habit_logs hl ON h.id = hl.habit_id AND hl.completed_date = %s
            WHERE h.user_id = %s AND h.is_active = TRUE
            ORDER BY h.sort_order, h.id
        """
        habits_list = execute_query(habits_query, (today, current_user.id), fetch_all=True)

        # 3. Tasks List (Today's tasks)
        tasks_query = """
            SELECT * FROM tasks 
            WHERE user_id = %s AND (due_date = %s OR due_date IS NULL)
            ORDER BY is_completed, priority DESC, created_at DESC
        """
        tasks_result = execute_query(tasks_query, (current_user.id, today), fetch_all=True)
        # Convert datetime objects to strings
        from models.task import Task
        tasks_list = [Task(**r).to_dict() for r in tasks_result]
        
        return jsonify({
            'success': True,
            'overview': overview,
            'habits': habits_list,
            'tasks': tasks_list
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to fetch dashboard data: {str(e)}'
        }), 500


@analytics_bp.route('/heatmap', methods=['GET'])
@login_required
def get_heatmap():
    """Get year-long daily completion data for heatmap calendar."""
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Get total active habits for the user
        total_query = """
            SELECT COUNT(*) as total 
            FROM habits 
            WHERE user_id = %s AND is_active = TRUE
        """
        total_result = execute_query(total_query, (current_user.id,), fetch_one=True)
        total_habits = total_result['total'] if total_result else 0
        
        # Get all completion data for the year
        query = """
            SELECT 
                hl.completed_date,
                COUNT(DISTINCT hl.habit_id) as completed
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = %s 
                AND EXTRACT(YEAR FROM hl.completed_date) = %s
                AND h.is_active = TRUE
            GROUP BY hl.completed_date
            ORDER BY hl.completed_date
        """
        results = execute_query(query, (current_user.id, year), fetch_all=True)
        
        # Format data for heatmap
        heatmap_data = []
        for row in results:
            percentage = round((row['completed'] / total_habits * 100), 1) if total_habits > 0 else 0
            heatmap_data.append({
                'date': str(row['completed_date']),
                'completed': row['completed'],
                'total': total_habits,
                'percentage': percentage
            })
        
        return jsonify({
            'success': True,
            'year': year,
            'total_habits': total_habits,
            'data': heatmap_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch heatmap data: {str(e)}'
        }), 500


@analytics_bp.route('/productivity-score', methods=['GET'])
@login_required
def get_productivity_score():
    """Calculate and return productivity scores over time."""
    try:
        period = request.args.get('period', 'month')  # week, month, year
        
        # Calculate date range based on period
        end_date = datetime.now()
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:  # month
            start_date = end_date - timedelta(days=30)
        
        # Get total active habits
        total_habits_query = """
            SELECT COUNT(*) as total 
            FROM habits 
            WHERE user_id = %s AND is_active = TRUE
        """
        total_habits_result = execute_query(total_habits_query, (current_user.id,), fetch_one=True)
        total_habits = total_habits_result['total'] if total_habits_result else 0
        
        # Get daily habit completion data
        habits_query = """
            SELECT 
                hl.completed_date,
                COUNT(DISTINCT hl.habit_id) as completed
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = %s 
                AND hl.completed_date >= %s 
                AND hl.completed_date <= %s
                AND h.is_active = TRUE
            GROUP BY hl.completed_date
        """
        habits_data = execute_query(habits_query, 
                                    (current_user.id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), 
                                    fetch_all=True)
        
        # Get daily task completion data
        tasks_query = """
            SELECT 
                DATE(COALESCE(completed_at, created_at)) as task_date,
                COUNT(*) as total_tasks,
                SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed_tasks
            FROM tasks 
            WHERE user_id = %s 
                AND DATE(COALESCE(completed_at, created_at)) >= %s 
                AND DATE(COALESCE(completed_at, created_at)) <= %s
            GROUP BY task_date
        """
        tasks_data = execute_query(tasks_query,
                                   (current_user.id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
                                   fetch_all=True)
        
        # Create lookup dictionaries
        habits_map = {str(row['completed_date']): row['completed'] for row in habits_data}
        tasks_map = {str(row['task_date']): {'total': row['total_tasks'], 'completed': row['completed_tasks']} 
                    for row in tasks_data}
        
        # Calculate productivity scores for each day
        scores = []
        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            
            # Habit score (60% weight)
            habit_completed = habits_map.get(date_str, 0)
            habit_score = (habit_completed / total_habits * 100) if total_habits > 0 else 0
            
            # Task score (40% weight)
            task_data = tasks_map.get(date_str, {'total': 0, 'completed': 0})
            task_score = (task_data['completed'] / task_data['total'] * 100) if task_data['total'] > 0 else 0
            
            # Combined productivity score
            productivity_score = round((habit_score * 0.6) + (task_score * 0.4), 1)
            
            scores.append({
                'date': date_str,
                'score': productivity_score,
                'habits_score': round(habit_score, 1),
                'tasks_score': round(task_score, 1)
            })
            
            current += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'period': period,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'scores': scores
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to calculate productivity scores: {str(e)}'
        }), 500


@analytics_bp.route('/correlations', methods=['GET'])
@login_required
def get_correlations():
    """Analyze correlations between habits (which habits are completed together)."""
    try:
        # Get all active habits
        habits_query = """
            SELECT id, name FROM habits 
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY name
        """
        habits = execute_query(habits_query, (current_user.id,), fetch_all=True)
        
        if len(habits) < 2:
            return jsonify({
                'success': True,
                'message': 'Need at least 2 habits for correlation analysis',
                'correlations': []
            }), 200
        
        # Get completion data for the last 60 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        logs_query = """
            SELECT hl.habit_id, hl.completed_date 
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = %s 
                AND h.is_active = TRUE
                AND hl.completed_date >= %s
                AND hl.completed_date <= %s
        """
        logs = execute_query(logs_query, 
                           (current_user.id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), 
                           fetch_all=True)
        
        # Build completion matrix
        habit_ids = [h['id'] for h in habits]
        completion_matrix = {hid: set() for hid in habit_ids}
        
        for log in logs:
            completion_matrix[log['habit_id']].add(str(log['completed_date']))
        
        # Calculate correlations between all habit pairs
        correlations = []
        for i, habit1 in enumerate(habits):
            for habit2 in habits[i+1:]:
                h1_id = habit1['id']
                h2_id = habit2['id']
                
                h1_dates = completion_matrix[h1_id]
                h2_dates = completion_matrix[h2_id]
                
                # Simple correlation: what percentage of days were both completed together
                if len(h1_dates) == 0 or len(h2_dates) == 0:
                    correlation = 0
                    days_compared = 0
                else:
                    both_completed = len(h1_dates & h2_dates)
                    either_completed = len(h1_dates | h2_dates)
                    correlation = round((both_completed / either_completed), 2) if either_completed > 0 else 0
                    days_compared = len(h1_dates | h2_dates)
                
                correlations.append({
                    'habit1': habit1['name'],
                    'habit1_id': h1_id,
                    'habit2': habit2['name'],
                    'habit2_id': h2_id,
                    'correlation': correlation,
                    'days_compared': days_compared
                })
        
        # Sort by correlation strength
        correlations.sort(key=lambda x: x['correlation'], reverse=True)
        
        return jsonify({
            'success': True,
            'correlations': correlations,
            'analysis_period': 60
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to calculate correlations: {str(e)}'
        }), 500


@analytics_bp.route('/habit-strength', methods=['GET'])
@login_required
def get_habit_strength():
    """Calculate habit strength metrics (consistency, completion rate, etc.)."""
    try:
        # Get all active habits
        habits_query = """
            SELECT id, name FROM habits 
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY name
        """
        habits = execute_query(habits_query, (current_user.id,), fetch_all=True)
        
        # Get completion data for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        logs_query = """
            SELECT hl.habit_id, hl.completed_date 
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = %s 
                AND h.is_active = TRUE
                AND hl.completed_date >= %s
            ORDER BY hl.habit_id, hl.completed_date DESC
        """
        logs = execute_query(logs_query, 
                           (current_user.id, start_date.strftime('%Y-%m-%d')), 
                           fetch_all=True)
        
        # Group logs by habit
        logs_by_habit = {}
        for log in logs:
            hid = log['habit_id']
            if hid not in logs_by_habit:
                logs_by_habit[hid] = []
            logs_by_habit[hid].append(log['completed_date'])
        
        # Calculate metrics for each habit
        strengths = []
        today = datetime.now().date()
        
        for habit in habits:
            hid = habit['id']
            habit_logs = logs_by_habit.get(hid, [])
            
            # Completion rate (last 30 days)
            completion_rate = round((len(habit_logs) / 30 * 100), 1)
            
            # Calculate current streak
            current_streak = 0
            check_date = today
            dates_set = set(habit_logs)
            
            while check_date in dates_set:
                current_streak += 1
                check_date -= timedelta(days=1)
            
            # If today not completed but yesterday was
            if current_streak == 0:
                check_date = today - timedelta(days=1)
                while check_date in dates_set:
                    current_streak += 1
                    check_date -= timedelta(days=1)
            
            # Calculate best streak (all time)
            all_logs_query = """
                SELECT completed_date FROM habit_logs 
                WHERE habit_id = %s
                ORDER BY completed_date
            """
            all_logs = execute_query(all_logs_query, (hid,), fetch_all=True)
            
            best_streak = 1
            if len(all_logs) > 0:
                sorted_dates = sorted([log['completed_date'] for log in all_logs])
                temp_streak = 1
                for i in range(1, len(sorted_dates)):
                    if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                        temp_streak += 1
                        best_streak = max(best_streak, temp_streak)
                    else:
                        temp_streak = 1
            else:
                best_streak = 0
            
            # Consistency score (0-100): weighted metric
            # 50% completion rate, 30% current streak (max 30 days), 20% best streak (max 100 days)
            streak_factor = min(current_streak / 30, 1) * 30
            best_streak_factor = min(best_streak / 100, 1) * 20
            consistency_score = round(completion_rate * 0.5 + streak_factor + best_streak_factor)
            
            strengths.append({
                'habit_id': hid,
                'habit_name': habit['name'],
                'completion_rate': completion_rate,
                'current_streak': current_streak,
                'best_streak': best_streak,
                'consistency_score': consistency_score
            })
        
        # Sort by consistency score
        strengths.sort(key=lambda x: x['consistency_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'habits': strengths,
            'analysis_period': 30
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to calculate habit strength: {str(e)}'
        }), 500


@analytics_bp.route('/comparison', methods=['GET'])
@login_required
def get_comparison():
    """Get month-over-month comparison statistics."""
    try:
        # Default to current month vs previous month
        now = datetime.now()
        month1 = request.args.get('month1', now.month, type=int)
        year1 = request.args.get('year1', now.year, type=int)
        
        # Calculate previous month
        if month1 == 1:
            month2 = 12
            year2 = year1 - 1
        else:
            month2 = month1 - 1
            year2 = year1
        
        month2 = request.args.get('month2', month2, type=int)
        year2 = request.args.get('year2', year2, type=int)
        
        # Get total active habits
        total_habits_query = """
            SELECT COUNT(*) as total 
            FROM habits 
            WHERE user_id = %s AND is_active = TRUE
        """
        total_habits_result = execute_query(total_habits_query, (current_user.id,), fetch_one=True)
        total_habits = total_habits_result['total'] if total_habits_result else 0
        
        def get_period_stats(year, month):
            # Get habit completion for the month
            habits_query = """
                SELECT COUNT(DISTINCT hl.habit_id) as total_completions
                FROM habit_logs hl
                JOIN habits h ON hl.habit_id = h.id
                WHERE h.user_id = %s 
                    AND EXTRACT(YEAR FROM hl.completed_date) = %s
                    AND EXTRACT(MONTH FROM hl.completed_date) = %s
                    AND h.is_active = TRUE
            """
            habits_result = execute_query(habits_query, (current_user.id, year, month), fetch_one=True)
            
            # Get task completion for the month
            tasks_query = """
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed_tasks
                FROM tasks 
                WHERE user_id = %s 
                    AND (EXTRACT(YEAR FROM due_date) = %s AND EXTRACT(MONTH FROM due_date) = %s)
            """
            tasks_result = execute_query(tasks_query, (current_user.id, year, month), fetch_one=True)
            
            import calendar
            days_in_month = calendar.monthrange(year, month)[1]
            
            return {
                'year': year,
                'month': month,
                'month_name': calendar.month_name[month],
                'habits_completed': habits_result['total_completions'] if habits_result else 0,
                'total_habits': total_habits,
                'tasks_total': tasks_result['total_tasks'] or 0,
                'tasks_completed': tasks_result['completed_tasks'] or 0,
                'days_in_month': days_in_month
            }
        
        period1 = get_period_stats(year1, month1)
        period2 = get_period_stats(year2, month2)
        
        # Calculate changes
        def calculate_change(new, old):
            if old == 0:
                return 100 if new > 0 else 0
            return round(((new - old) / old * 100), 1)
        
        comparison = {
            'habits_change': calculate_change(period1['habits_completed'], period2['habits_completed']),
            'tasks_change': calculate_change(period1['tasks_completed'], period2['tasks_completed'])
        }
        
        return jsonify({
            'success': True,
            'period1': period1,
            'period2': period2,
            'comparison': comparison
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to generate comparison: {str(e)}'
        }), 500


@analytics_bp.route('/export-data', methods=['GET'])
@login_required
def get_export_data():
    """Get comprehensive data for CSV export."""
    try:
        start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Get all habits
        habits_query = """
            SELECT id, name FROM habits 
            WHERE user_id = %s AND is_active = TRUE
        """
        habits = execute_query(habits_query, (current_user.id,), fetch_all=True)
        habits_dict = {h['id']: h['name'] for h in habits}
        
        # Get habit logs
        logs_query = """
            SELECT hl.habit_id, hl.completed_date 
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = %s 
                AND hl.completed_date >= %s
                AND hl.completed_date <= %s
            ORDER BY hl.completed_date
        """
        logs = execute_query(logs_query, (current_user.id, start_date, end_date), fetch_all=True)
        
        # Get tasks
        tasks_query = """
            SELECT title, is_completed, priority, due_date, created_at, completed_at
            FROM tasks 
            WHERE user_id = %s 
                AND created_at::DATE >= %s
                AND created_at::DATE <= %s
            ORDER BY created_at
        """
        tasks = execute_query(tasks_query, (current_user.id, start_date, end_date), fetch_all=True)
        
        # Format habit logs
        habit_logs_formatted = [{
            'date': str(log['completed_date']),
            'habit_name': habits_dict.get(log['habit_id'], 'Unknown'),
            'status': 'Completed'
        } for log in logs]
        
        # Format tasks
        tasks_formatted = [{
            'date': str(task['due_date'] or task['created_at']),
            'title': task['title'],
            'status': 'Completed' if task['is_completed'] else 'Pending',
            'priority': task['priority']
        } for task in tasks]
        
        return jsonify({
            'success': True,
            'start_date': start_date,
            'end_date': end_date,
            'habit_logs': habit_logs_formatted,
            'tasks': tasks_formatted
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch export data: {str(e)}'
        }), 500

