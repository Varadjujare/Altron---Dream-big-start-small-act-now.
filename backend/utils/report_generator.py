"""
Altron - Report Generator Module
Generates weekly and monthly progress reports for users.
"""

import os
import datetime
from typing import Dict, Any, Optional
from utils.db import get_db_connection

# Try to import weasyprint for PDF generation (optional)
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("⚠️ WeasyPrint not installed. PDF generation will be disabled.")
    print("   Install with: pip install weasyprint")


class ReportGenerator:
    """Generates user progress reports."""
    
    def __init__(self):
        self.reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Fetch user details from database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {"id": row[0], "username": row[1], "email": row[2]}
        return None
    
    def get_productivity_scores(self, user_id: int, start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
        """Calculate daily productivity scores for the period."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        scores = []
        current_date = start_date
        
        while current_date <= end_date:
            # Get habits for the day
            cursor.execute("""
                SELECT COUNT(DISTINCT h.id) as total_habits
                FROM habits h
                WHERE h.user_id = %s AND h.is_active = TRUE
            """, (user_id,))
            total_habits = cursor.fetchone()[0] or 1
            
            cursor.execute("""
                SELECT COUNT(DISTINCT hl.habit_id) as completed
                FROM habit_logs hl
                JOIN habits h ON hl.habit_id = h.id
                WHERE h.user_id = %s AND hl.completed_date = %s AND h.is_active = TRUE
            """, (user_id, current_date.isoformat()))
            completed_habits = cursor.fetchone()[0] or 0
            
            habit_score = round((completed_habits / max(total_habits, 1)) * 100, 1)
            
            # Get tasks for the day
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed
                FROM tasks
                WHERE user_id = %s AND (due_date = %s OR (due_date IS NULL AND created_at::DATE = %s))
            """, (user_id, current_date.isoformat(), current_date.isoformat()))
            task_row = cursor.fetchone()
            total_tasks = task_row[0] or 1
            completed_tasks = task_row[1] or 0
            
            task_score = round((completed_tasks / max(total_tasks, 1)) * 100, 1)
            
            # Weighted productivity score (60% habits, 40% tasks)
            productivity_score = round((habit_score * 0.6) + (task_score * 0.4), 1)
            
            scores.append({
                "date": current_date.isoformat(),
                "score": productivity_score,
                "habit_score": habit_score,
                "task_score": task_score
            })
            
            current_date += datetime.timedelta(days=1)
        
        conn.close()
        
        avg_score = round(sum(s["score"] for s in scores) / max(len(scores), 1), 1)
        
        return {
            "scores": scores,
            "average_score": avg_score,
            "best_day": max(scores, key=lambda x: x["score"]) if scores else None,
            "worst_day": min(scores, key=lambda x: x["score"]) if scores else None
        }
    
    def get_habit_strength(self, user_id: int) -> Dict[str, Any]:
        """Calculate habit strength metrics."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name FROM habits
            WHERE user_id = %s AND is_active = TRUE
        """, (user_id,))
        habits = cursor.fetchall()
        
        habit_strengths = []
        
        for habit_id, habit_name in habits:
            # Get total days the habit has existed
            cursor.execute("""
                SELECT MIN(completed_date) FROM habit_logs WHERE habit_id = %s
            """, (habit_id,))
            first_log = cursor.fetchone()[0]
            
            if not first_log:
                continue
            
            days_tracked = (datetime.date.today() - first_log).days + 1
            
            # Get completion count
            cursor.execute("""
                SELECT COUNT(*) FROM habit_logs WHERE habit_id = %s
            """, (habit_id,))
            completion_count = cursor.fetchone()[0] or 0
            
            completion_rate = round((completion_count / max(days_tracked, 1)) * 100, 1)
            
            # Calculate streaks
            cursor.execute("""
                SELECT completed_date FROM habit_logs
                WHERE habit_id = %s
                ORDER BY completed_date DESC
            """, (habit_id,))
            logs = [row[0] for row in cursor.fetchall()]
            
            current_streak = 0
            best_streak = 0
            temp_streak = 0
            
            if logs:
                # Current streak
                expected_date = datetime.date.today()
                for log_date in logs:
                    if log_date == expected_date or log_date == expected_date - datetime.timedelta(days=1):
                        current_streak += 1
                        expected_date = log_date - datetime.timedelta(days=1)
                    else:
                        break
                
                # Best streak
                for i, log_date in enumerate(logs):
                    if i == 0:
                        temp_streak = 1
                    else:
                        prev_date = logs[i-1]
                        if (prev_date - log_date).days == 1:
                            temp_streak += 1
                        else:
                            best_streak = max(best_streak, temp_streak)
                            temp_streak = 1
                best_streak = max(best_streak, temp_streak)
            
            # Consistency score (0-100)
            consistency_score = round(min(
                (completion_rate * 0.5) +
                (min(current_streak / 7, 1) * 30) +
                (min(best_streak / 14, 1) * 20),
                100
            ))
            
            habit_strengths.append({
                "habit_name": habit_name,
                "completion_rate": completion_rate,
                "current_streak": current_streak,
                "best_streak": best_streak,
                "consistency_score": consistency_score
            })
        
        conn.close()
        
        # Sort by consistency score
        habit_strengths.sort(key=lambda x: x["consistency_score"], reverse=True)
        
        return {"habits": habit_strengths}
    
    def get_correlations(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Calculate habit correlations."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        start_date = datetime.date.today() - datetime.timedelta(days=days)
        
        # Get all habits
        cursor.execute("""
            SELECT id, name FROM habits
            WHERE user_id = %s AND is_active = TRUE
        """, (user_id,))
        habits = cursor.fetchall()
        
        if len(habits) < 2:
            conn.close()
            return {"correlations": [], "message": "Need at least 2 habits to analyze correlations"}
        
        correlations = []
        
        # Check each pair of habits
        for i, (habit1_id, habit1_name) in enumerate(habits):
            for habit2_id, habit2_name in habits[i+1:]:
                # Get days where both were completed
                cursor.execute("""
                    SELECT COUNT(DISTINCT hl1.completed_date)
                    FROM habit_logs hl1
                    JOIN habit_logs hl2 ON hl1.completed_date = hl2.completed_date
                    WHERE hl1.habit_id = %s AND hl2.habit_id = %s
                    AND hl1.completed_date >= %s
                """, (habit1_id, habit2_id, start_date.isoformat()))
                both_completed = cursor.fetchone()[0] or 0
                
                # Get total days either was completed
                cursor.execute("""
                    SELECT COUNT(DISTINCT completed_date)
                    FROM habit_logs
                    WHERE habit_id IN (%s, %s) AND completed_date >= %s
                """, (habit1_id, habit2_id, start_date.isoformat()))
                either_completed = cursor.fetchone()[0] or 1
                
                correlation = both_completed / max(either_completed, 1)
                
                if correlation >= 0.3 and both_completed >= 3:
                    correlations.append({
                        "habit1": habit1_name,
                        "habit2": habit2_name,
                        "correlation": correlation,
                        "days_together": both_completed
                    })
        
        conn.close()
        
        # Sort by correlation strength
        correlations.sort(key=lambda x: x["correlation"], reverse=True)
        
        return {
            "correlations": correlations,
            "analysis_period": days
        }
    
    def get_heatmap_data(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get heatmap activity data for the period."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days-1)
        
        cursor.execute("""
            SELECT COUNT(*) FROM habits WHERE user_id = %s AND is_active = TRUE
        """, (user_id,))
        total_habits = cursor.fetchone()[0] or 1
        
        heatmap_data = []
        current_date = start_date
        
        while current_date <= end_date:
            cursor.execute("""
                SELECT COUNT(DISTINCT hl.habit_id) as completed
                FROM habit_logs hl
                JOIN habits h ON hl.habit_id = h.id
                WHERE h.user_id = %s AND hl.completed_date = %s AND h.is_active = TRUE
            """, (user_id, current_date.isoformat()))
            
            completed = cursor.fetchone()[0] or 0
            percentage = round((completed / max(total_habits, 1)) * 100)
            
            # Level for heatmap (0-4)
            if percentage == 0:
                level = 0
            elif percentage <= 25:
                level = 1
            elif percentage <= 50:
                level = 2
            elif percentage <= 75:
                level = 3
            else:
                level = 4
            
            heatmap_data.append({
                "date": current_date.isoformat(),
                "completed": completed,
                "total": total_habits,
                "percentage": percentage,
                "level": level
            })
            
            current_date += datetime.timedelta(days=1)
        
        conn.close()
        
        return {"data": heatmap_data}
    
    def get_comparison_stats(self, user_id: int, period: str = "weekly") -> Dict[str, Any]:
        """Compare current period with previous period."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.date.today()
        
        if period == "weekly":
            days = 7
        else:  # monthly
            days = 30
        
        # Current period
        current_start = today - datetime.timedelta(days=days)
        current_end = today
        
        # Previous period
        previous_start = current_start - datetime.timedelta(days=days)
        previous_end = current_start
        
        def get_period_stats(start, end):
            cursor.execute("""
                SELECT COUNT(*) FROM habit_logs hl
                JOIN habits h ON hl.habit_id = h.id
                WHERE h.user_id = %s AND hl.completed_date >= %s AND hl.completed_date < %s
            """, (user_id, start.isoformat(), end.isoformat()))
            habits_completed = cursor.fetchone()[0] or 0
            
            cursor.execute("""
                SELECT SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END)
                FROM tasks
                WHERE user_id = %s AND created_at >= %s AND created_at < %s
            """, (user_id, start.isoformat(), end.isoformat()))
            tasks_completed = cursor.fetchone()[0] or 0
            
            return habits_completed, tasks_completed
        
        current_habits, current_tasks = get_period_stats(current_start, current_end)
        previous_habits, previous_tasks = get_period_stats(previous_start, previous_end)
        
        conn.close()
        
        # Calculate percentage changes
        habits_change = round(((current_habits - previous_habits) / max(previous_habits, 1)) * 100) if previous_habits > 0 else 0
        tasks_change = round(((current_tasks - previous_tasks) / max(previous_tasks, 1)) * 100) if previous_tasks > 0 else 0
        
        return {
            "current": {
                "habits": current_habits,
                "tasks": current_tasks
            },
            "previous": {
                "habits": previous_habits,
                "tasks": previous_tasks
            },
            "changes": {
                "habits": habits_change,
                "tasks": tasks_change
            }
        }
    
    def get_weekly_stats(self, user_id: int) -> Dict[str, Any]:
        """Calculate statistics for the last 7 days."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=7)
        
        # Get habit completion stats
        cursor.execute("""
            SELECT COUNT(*) as total_completions
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = %s AND hl.completed_date >= %s
        """, (user_id, week_ago.isoformat()))
        habit_completions = cursor.fetchone()[0] or 0
        
        # Get total habits
        cursor.execute("SELECT COUNT(*) FROM habits WHERE user_id = %s", (user_id,))
        total_habits = cursor.fetchone()[0] or 1
        
        # Calculate consistency (completions / (habits * 7 days))
        expected_completions = total_habits * 7
        consistency = round((habit_completions / max(expected_completions, 1)) * 100)
        
        # Get task stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed
            FROM tasks 
            WHERE user_id = %s AND created_at >= %s
        """, (user_id, week_ago.isoformat()))
        task_row = cursor.fetchone()
        tasks_total = task_row[0] or 0
        tasks_completed = task_row[1] or 0
        
        # Get daily breakdown for chart
        daily_stats = []
        for i in range(7):
            day = week_ago + datetime.timedelta(days=i+1)
            cursor.execute("""
                SELECT COUNT(*) FROM habit_logs hl
                JOIN habits h ON hl.habit_id = h.id
                WHERE h.user_id = %s AND hl.completed_date = %s
            """, (user_id, day.isoformat()))
            count = cursor.fetchone()[0] or 0
            percentage = round((count / max(total_habits, 1)) * 100)
            daily_stats.append({
                "date": day.strftime("%a"),
                "completions": count,
                "percentage": percentage
            })
        
        # Get habit-wise breakdown
        cursor.execute("""
            SELECT h.name, h.color, COUNT(hl.id) as completions
            FROM habits h
            LEFT JOIN habit_logs hl ON h.id = hl.habit_id AND hl.completed_date >= %s
            WHERE h.user_id = %s
            GROUP BY h.id
        """, (week_ago.isoformat(), user_id))
        habits_breakdown = []
        for row in cursor.fetchall():
            habits_breakdown.append({
                "name": row[0],
                "color": row[1],
                "completions": row[2] or 0,
                "out_of": 7
            })
        
        conn.close()
        
        return {
            "period": "weekly",
            "start_date": week_ago.strftime("%b %d"),
            "end_date": today.strftime("%b %d, %Y"),
            "consistency": min(consistency, 100),
            "tasks_completed": tasks_completed,
            "tasks_total": tasks_total,
            "habit_completions": habit_completions,
            "total_habits": total_habits,
            "daily_stats": daily_stats,
            "habits_breakdown": habits_breakdown,
            "best_day": max(daily_stats, key=lambda x: x["percentage"])["date"] if daily_stats else "N/A"
        }
    
    def get_monthly_stats(self, user_id: int) -> Dict[str, Any]:
        """Calculate statistics for the last 30 days."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.date.today()
        month_ago = today - datetime.timedelta(days=30)
        
        # Similar to weekly but for 30 days
        cursor.execute("""
            SELECT COUNT(*) as total_completions
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = %s AND hl.completed_date >= %s
        """, (user_id, month_ago.isoformat()))
        habit_completions = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM habits WHERE user_id = %s", (user_id,))
        total_habits = cursor.fetchone()[0] or 1
        
        expected_completions = total_habits * 30
        consistency = round((habit_completions / max(expected_completions, 1)) * 100)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed
            FROM tasks 
            WHERE user_id = %s AND created_at >= %s
        """, (user_id, month_ago.isoformat()))
        task_row = cursor.fetchone()
        tasks_total = task_row[0] or 0
        tasks_completed = task_row[1] or 0
        
        # Weekly breakdown for monthly chart
        weekly_stats = []
        for week in range(4):
            week_start = month_ago + datetime.timedelta(days=week*7)
            week_end = week_start + datetime.timedelta(days=7)
            cursor.execute("""
                SELECT COUNT(*) FROM habit_logs hl
                JOIN habits h ON hl.habit_id = h.id
                WHERE h.user_id = %s AND hl.completed_date >= %s AND hl.completed_date < %s
            """, (user_id, week_start.isoformat(), week_end.isoformat()))
            count = cursor.fetchone()[0] or 0
            weekly_stats.append({
                "week": f"Week {week + 1}",
                "completions": count,
                "percentage": round((count / max(total_habits * 7, 1)) * 100)
            })
        
        # Get habit-wise breakdown
        cursor.execute("""
            SELECT h.name, h.color, COUNT(hl.id) as completions
            FROM habits h
            LEFT JOIN habit_logs hl ON h.id = hl.habit_id AND hl.completed_date >= %s
            WHERE h.user_id = %s
            GROUP BY h.id
        """, (month_ago.isoformat(), user_id))
        habits_breakdown = []
        for row in cursor.fetchall():
            habits_breakdown.append({
                "name": row[0],
                "color": row[1],
                "completions": row[2] or 0,
                "out_of": 30
            })
        
        conn.close()
        
        return {
            "period": "monthly",
            "start_date": month_ago.strftime("%b %d"),
            "end_date": today.strftime("%b %d, %Y"),
            "consistency": min(consistency, 100),
            "tasks_completed": tasks_completed,
            "tasks_total": tasks_total,
            "habit_completions": habit_completions,
            "total_habits": total_habits,
            "weekly_stats": weekly_stats,
            "habits_breakdown": habits_breakdown
        }
    
    def generate_html_report(self, user_id: int, period: str = "weekly") -> str:
        """Generate comprehensive HTML content for the report with advanced analytics."""
        user = self.get_user_data(user_id)
        if not user:
            return "<p>User not found</p>"
        
        # Get basic stats
        if period == "weekly":
            stats = self.get_weekly_stats(user_id)
            title = "Weekly Progress Report"
            chart_data = stats.get("daily_stats", [])
            days = 7
        else:
            stats = self.get_monthly_stats(user_id)
            title = "Monthly Progress Report"
            chart_data = stats.get("weekly_stats", [])
            days = 30
        
        # Get advanced analytics data
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=days)
        
        try:
            productivity_data = self.get_productivity_scores(user_id, start_date, today)
            habit_strength_data = self.get_habit_strength(user_id)
            correlations_data = self.get_correlations(user_id, days=days)
            comparison_data = self.get_comparison_stats(user_id, period=period)
            
            if period == "monthly":
                heatmap_data = self.get_heatmap_data(user_id, days=30)
            else:
                heatmap_data = None
        except Exception as e:
            print(f"⚠️ Error fetching advanced analytics: {e}")
            # Use empty data if analytics fail
            productivity_data = {"scores": [], "average_score": 0}
            habit_strength_data = {"habits": []}
            correlations_data = {"correlations": []}
            comparison_data = {"changes": {"habits": 0, "tasks": 0}}
            heatmap_data = None
        
        # =========================
        # PERIOD COMPARISON SECTION
        # =========================
        comparison_html = ""
        if comparison_data and comparison_data.get("changes"):
            habits_change = comparison_data["changes"]["habits"]
            tasks_change = comparison_data["changes"]["tasks"]
            
            habits_arrow = "↑" if habits_change >= 0 else "↓"
            tasks_arrow = "↑" if tasks_change >= 0 else "↓"
            habits_color = "#22c55e" if habits_change >= 0 else "#ef4444"
            tasks_color = "#22c55e" if tasks_change >= 0 else "#ef4444"
            
            comparison_html = f'''
          <!-- Period Comparison -->
          <tr>
            <td style="background: #171a2f; border: 1px solid #2a2f55; border-radius: 14px; padding: 20px;">
              <div style="font-weight: bold; margin-bottom: 16px; color: #e5e7eb; font-size: 14px;">📊 Period Comparison</div>
              <table width="100%" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" width="50%" style="border-right: 1px solid #2a2f55; padding: 12px;">
                    <div style="font-size: 24px; font-weight: bold; color: {habits_color}; margin-bottom: 4px;">{habits_arrow} {abs(habits_change)}%</div>
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af;">Habits vs Last {period.title()}</div>
                  </td>
                  <td align="center" width="50%" style="padding: 12px;">
                    <div style="font-size: 24px; font-weight: bold; color: {tasks_color}; margin-bottom: 4px;">{tasks_arrow} {abs(tasks_change)}%</div>
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af;">Tasks vs Last {period.title()}</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr><td height="20"></td></tr>
'''
        
        # =========================
        # PRODUCTIVITY SCORE SECTION
        # =========================
        productivity_html = ""
        if productivity_data and productivity_data.get("average_score"):
            avg_score = productivity_data["average_score"]
            score_color = "#22c55e" if avg_score >= 70 else "#f59e0b" if avg_score >= 50 else "#ef4444"
            score_trend = "Excellent!" if avg_score >= 70 else "Good progress" if avg_score >= 50 else "Room for improvement"
            
            productivity_html = f'''
          <!-- Productivity Score -->
          <tr>
            <td style="background: #171a2f; border: 1px solid #2a2f55; border-radius: 14px; padding: 20px;">
              <div style="font-weight: bold; margin-bottom: 12px; color: #e5e7eb; font-size: 14px;">📈 Productivity Score</div>
              <table width="100%" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <div style="font-size: 36px; font-weight: bold; color: {score_color}; margin-bottom: 8px;">{avg_score}%</div>
                    <div style="font-size: 12px; color: #9ca3af; margin-bottom: 4px;">Average Productivity</div>
                    <div style="font-size: 11px; color: {score_color};">{score_trend}</div>
                  </td>
                </tr>
              </table>
              <div style="margin-top: 12px; padding: 12px; background: rgba(0, 255, 136, 0.05); border-radius: 8px; font-size: 11px; color: #9ca3af;">
                📊 Weighted: 60% Habits + 40% Tasks
              </div>
            </td>
          </tr>
          <tr><td height="20"></td></tr>
'''
        
        # =========================
        # HABIT STRENGTH SECTION
        # =========================
        habit_strength_html = ""
        if habit_strength_data and habit_strength_data.get("habits"):
            top_habits = habit_strength_data["habits"][:5]  # Top 5
            strength_rows = ""
            
            for habit in top_habits:
                score = habit["consistency_score"]
                score_color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
                badge_text = "Strong" if score >= 70 else "Moderate" if score >= 40 else "Weak"
                
                strength_rows += f'''
                <tr>
                  <td style="padding: 12px; border-bottom: 1px solid #2a2f55;">
                    <div style="color: #e5e7eb; font-weight: 600; margin-bottom: 4px;">{habit['habit_name']}</div>
                    <div style="font-size: 11px; color: #9ca3af;">
                      🔥 {habit['current_streak']} days | 🏆 Best: {habit['best_streak']} days
                    </div>
                  </td>
                  <td align="right" style="padding: 12px; border-bottom: 1px solid #2a2f55;">
                    <div style="background: {score_color}; color: #ffffff; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: bold; display: inline-block;">
                      {score}/100
                    </div>
                    <div style="font-size: 10px; color: {score_color}; margin-top: 4px;">{badge_text}</div>
                  </td>
                </tr>'''
            
            habit_strength_html = f'''
          <!-- Habit Strength -->
          <tr>
            <td style="background: #171a2f; border: 1px solid #2a2f55; border-radius: 14px; padding: 20px;">
              <div style="font-weight: bold; margin-bottom: 12px; color: #e5e7eb; font-size: 14px;">💪 Habit Strength Analysis</div>
              <table width="100%" border="0" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
                {strength_rows if strength_rows else '<tr><td align="center" style="padding: 20px; color: #9ca3af;">No habits to analyze yet</td></tr>'}
              </table>
            </td>
          </tr>
          <tr><td height="20"></td></tr>
'''
        
        # =========================
        # PROGRESS CHART  (EXISTING)
        # =========================
        chart_rows_html = ""
        chart_rows_html += '<tr>'
        for d in chart_data:
            pct_value = d["percentage"]
            color = "#22c55e" if pct_value >= 80 else "#00d9ff" if pct_value >= 50 else "#f59e0b"
            chart_rows_html += f'''
            <td valign="bottom" style="padding: 0 4px; height: 160px;">
                <div style="background: {color}; width: 100%; height: {max(pct_value, 2)}%; border-radius: 6px 6px 0 0; min-height: 4px; position: relative;" title="{pct_value}%">
                    <div style="position: absolute; top: -20px; width: 100%; text-align: center; color: #e5e7eb; font-size: 10px; font-weight: bold;">{pct_value}%</div>
                </div>
            </td>'''
        chart_rows_html += '</tr><tr>'
        for d in chart_data:
            label = d.get("date") or d.get("week", "")
            chart_rows_html += f'<td align="center" style="padding-top: 8px; color: #9ca3af; font-size: 11px;">{label}</td>'
        chart_rows_html += '</tr>'
        
        best_day_name = stats.get('best_day', 'N/A')
        
        # =========================
        # HABIT BREAKDOWN (EXISTING)
        # =========================
        habits_html = ""
        for h in stats.get("habits_breakdown", []):
            completion_rate = round((h["completions"] / max(h["out_of"], 1)) * 100)
            status_color = "#22c55e" if completion_rate >= 80 else "#f59e0b" if completion_rate >= 50 else "#ef4444"
            trend = "Excellent" if completion_rate >= 80 else "Stable" if completion_rate >= 50 else "Need Improvement"
            arrow = "⬆" if completion_rate >= 50 else "⬇"
            habits_html += f'''<tr>
                <td style="padding: 12px; border-bottom: 1px solid #2a2f55; color: #e5e7eb;">{h['name']}</td>
                <td style="padding: 12px; border-bottom: 1px solid #2a2f55; color: #e5e7eb;">{h['completions']} / {h['out_of']} ({completion_rate}%)</td>
                <td style="padding: 12px; border-bottom: 1px solid #2a2f55; color: {status_color}; font-weight: 600;">{arrow} {trend}</td>
            </tr>'''
        
        # =========================
        # CORRELATIONS SECTION
        # =========================
        correlations_html = ""
        if correlations_data and correlations_data.get("correlations"):
            top_corr = correlations_data["correlations"][:5]  # Top 5
            corr_rows = ""
            
            for corr in top_corr:
                percentage = round(corr["correlation"] * 100)
                bar_color = "#39d353" if percentage >= 70 else "#26a641" if percentage >= 50 else "#006d32"
                
                corr_rows += f'''
                <tr>
                  <td style="padding: 10px; border-bottom: 1px solid #2a2f55;">
                    <div style="color: #e5e7eb; font-size: 13px;">
                      <span style="font-weight: 600;">{corr['habit1']}</span>
                      <span style="color: #9ca3af;"> ↔ </span>
                      <span style="font-weight: 600;">{corr['habit2']}</span>
                    </div>
                    <div style="background: #2a2f55; height: 6px; border-radius: 3px; margin-top: 6px; overflow: hidden;">
                      <div style="background: {bar_color}; height: 100%; width: {percentage}%;"></div>
                    </div>
                  </td>
                  <td align="right" style="padding: 10px; border-bottom: 1px solid #2a2f55;">
                    <div style="color: {bar_color}; font-weight: bold; font-size: 14px;">{percentage}%</div>
                  </td>
                </tr>'''
            
            correlations_html = f'''
          <!-- Correlations -->
          <tr>
            <td style="background: #171a2f; border: 1px solid #2a2f55; border-radius: 14px; padding: 20px;">
              <div style="font-weight: bold; margin-bottom: 12px; color: #e5e7eb; font-size: 14px;">🔗 Habit Correlations</div>
              <div style="font-size: 11px; color: #9ca3af; margin-bottom: 12px;">Habits you tend to complete together</div>
              <table width="100%" border="0" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
                {corr_rows}
              </table>
            </td>
          </tr>
          <tr><td height="20"></td></tr>
'''
        
        # =========================
        # HEATMAP SECTION (Monthly Only)
        # =========================
        heatmap_html = ""
        if period == "monthly" and heatmap_data and heatmap_data.get("data"):
            # Create visual heatmap using emoji blocks
            heatmap_visual = ""
            data = heatmap_data["data"]
            
            # Group by weeks (7 days each)
            for week_start in range(0, len(data), 7):
                week_data = data[week_start:week_start+7]
                week_html = '<tr>'
                for day in week_data:
                    level = day["level"]
                    # Use emoji blocks for email compatibility
                    if level == 0:
                        emoji = "⬜"  # No activity
                    elif level == 1:
                        emoji = "🟩"  # Low
                    elif level == 2:
                        emoji = "🟩🟩"  # Medium-low
                    elif level == 3:
                        emoji = "🟩🟩🟩"  # Medium-high
                    else:
                        emoji = "✅"  # High
                    
                    tooltip = f"{day['completed']}/{day['total']} habits ({day['percentage']}%)"
                    week_html += f'<td align="center" style="padding: 2px;" title="{tooltip}">{emoji}</td>'
                week_html += '</tr>'
                heatmap_visual += week_html
            
            heatmap_html = f'''
          <!-- Heatmap -->
          <tr>
            <td style="background: #171a2f; border: 1px solid #2a2f55; border-radius: 14px; padding: 20px;">
              <div style="font-weight: bold; margin-bottom: 12px; color: #e5e7eb; font-size: 14px;">📅 30-Day Activity Heatmap</div>
              <table border="0" cellpadding="0" cellspacing="0" style="margin: 0 auto; font-size: 16px;">
                {heatmap_visual}
              </table>
              <div style="margin-top: 12px; text-align: center;">
                <span style="font-size: 11px; color: #9ca3af;">
                  ⬜ None | 🟩 Low | 🟩🟩 Medium | ✅ High
                </span>
              </div>
            </td>
          </tr>
          <tr><td height="20"></td></tr>
'''
        
        # =========================
        # COMPLETE HTML TEMPLATE
        # =========================
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Altron {title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0f1220; font-family: Helvetica, Arial, sans-serif;">
  
  <!-- Main Container -->
  <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #0f1220; width: 100%;">
    <tr>
      <td align="center" style="padding: 24px;">
        
        <!-- Content Wrapper -->
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; color: #e5e7eb;">
          
          <!-- Header -->
          <tr>
            <td style="padding-bottom: 24px;">
              <h1 style="margin: 0; font-size: 24px; color: #e5e7eb;">🎯 Altron {title}</h1>
              <div style="color: #9ca3af; font-size: 14px; margin-top: 4px;">{stats['start_date']} – {stats['end_date']}</div>
            </td>
          </tr>

          {comparison_html}

          <!-- Overview Cards -->
          <tr>
            <td style="background: #171a2f; border: 1px solid #2a2f55; border-radius: 14px; padding: 24px;">
              <table width="100%" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" width="33%">
                    <div style="font-size: 28px; font-weight: bold; color: #22c55e; margin-bottom: 4px;">{stats['consistency']}%</div>
                    <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af;">Consistency</div>
                  </td>
                  <td align="center" width="33%" style="border-left: 1px solid #2a2f55; border-right: 1px solid #2a2f55;">
                    <div style="font-size: 28px; font-weight: bold; color: #00d9ff; margin-bottom: 4px;">{stats['tasks_completed']}</div>
                    <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af;">Tasks</div>
                  </td>
                  <td align="center" width="33%">
                    <div style="font-size: 28px; font-weight: bold; color: #f59e0b; margin-bottom: 4px;">{stats['habit_completions']}</div>
                    <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af;">Check-ins</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr><td height="20"></td></tr>

          {productivity_html}

          <!-- Progress Chart -->
          <tr>
            <td style="background: #171a2f; border: 1px solid #2a2f55; border-radius: 14px; padding: 24px;">
              <div style="font-weight: bold; margin-bottom: 20px; color: #e5e7eb;">📊 Progress Chart</div>
              
              <table width="100%" border="0" cellpadding="0" cellspacing="0" style="table-layout: fixed;">
                {chart_rows_html}
              </table>
              
              {'<div style="text-align: right; margin-top: 16px; color: #22c55e; font-size: 12px;">Best day: <strong>' + best_day_name + '</strong> ⭐</div>' if period == 'weekly' else ''}
            </td>
          </tr>

          <tr><td height="20"></td></tr>

          {habit_strength_html}

          <!-- Habit Breakdown -->
          <tr>
            <td style="background: #171a2f; border: 1px solid #2a2f55; border-radius: 14px; padding: 24px;">
              <div style="font-weight: bold; margin-bottom: 12px; color: #e5e7eb;">✅ Habit Breakdown</div>
              <table width="100%" border="0" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
                <thead>
                  <tr>
                    <th align="left" style="padding: 12px; border-bottom: 1px solid #2a2f55; color: #9ca3af; font-size: 11px; text-transform: uppercase;">Habit</th>
                    <th align="left" style="padding: 12px; border-bottom: 1px solid #2a2f55; color: #9ca3af; font-size: 11px; text-transform: uppercase;">Completion</th>
                    <th align="left" style="padding: 12px; border-bottom: 1px solid #2a2f55; color: #9ca3af; font-size: 11px; text-transform: uppercase;">Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {habits_html if habits_html else '<tr><td colspan="3" align="center" style="padding: 20px; color: #9ca3af;">No habits tracked yet</td></tr>'}
                </tbody>
              </table>
            </td>
          </tr>

          <tr><td height="20"></td></tr>

          {correlations_html}

          {heatmap_html}

          <!-- Motivation Footer -->
          <tr>
            <td align="center" style="background: linear-gradient(90deg, #1d4ed8, #6d28d9); border-radius: 14px; padding: 20px; color: #ffffff; font-weight: bold;">
              {"🚀 Great work this " + period + "! Keep the momentum going!" if stats['consistency'] >= 70 else "💪 Every step counts! Let's aim higher next " + period + "!"}
            </td>
          </tr>

          <!-- Footer Text -->
          <tr>
            <td align="center" style="padding-top: 24px; color: #9ca3af; font-size: 12px;">
              Generated by Altron • {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>'''
        
        return html
    
    def generate_pdf(self, user_id: int, period: str = "weekly") -> Optional[str]:
        """Generate PDF report and return file path."""
        if not WEASYPRINT_AVAILABLE:
            print("PDF generation skipped - WeasyPrint not installed")
            return None
        
        html_content = self.generate_html_report(user_id, period)
        
        user = self.get_user_data(user_id)
        username = user['username'] if user else 'unknown'
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{username}_{period}_report_{timestamp}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        try:
            HTML(string=html_content).write_pdf(filepath)
            print(f"✅ PDF generated: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            return None


# Global instance
report_generator = ReportGenerator()
