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
        """Generate HTML content for the report."""
        user = self.get_user_data(user_id)
        if not user:
            return "<p>User not found</p>"
        
        if period == "weekly":
            stats = self.get_weekly_stats(user_id)
            title = "Weekly Progress Report"
            chart_data = stats.get("daily_stats", [])
        else:
            stats = self.get_monthly_stats(user_id)
            title = "Monthly Progress Report"
            chart_data = stats.get("weekly_stats", [])
        
        # Chart Data Preparation
        # Using a table for the chart to ensure bars stay side-by-side in emails
        chart_rows_html = ""
        
        # 1. Bars row
        chart_rows_html += '<tr>'
        for d in chart_data:
            pct_value = d["percentage"]
            # Color logic
            if pct_value >= 80:
                color = "#22c55e" # accent
            elif pct_value >= 50:
                color = "#00d9ff" # blue
            else:
                color = "#f59e0b" # orange
                
            chart_rows_html += f'''
            <td valign="bottom" style="padding: 0 4px; height: 160px;">
                <div style="background: {color}; width: 100%; height: {max(pct_value, 2)}%; border-radius: 6px 6px 0 0; min-height: 4px; position: relative;" title="{pct_value}%">
                    <div style="position: absolute; top: -20px; width: 100%; text-align: center; color: #e5e7eb; font-size: 10px; font-weight: bold;">{pct_value}%</div>
                </div>
            </td>'''
        chart_rows_html += '</tr>'
        
        # 2. Labels row
        chart_rows_html += '<tr>'
        for d in chart_data:
            label = d.get("date") or d.get("week", "")
            chart_rows_html += f'<td align="center" style="padding-top: 8px; color: #9ca3af; font-size: 11px;">{label}</td>'
        chart_rows_html += '</tr>'

        best_day_name = stats.get('best_day', 'N/A')
        
        # Habit Breakdown Preparation
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
            
        # Overall HTML Template (Email Safe: No CSS Grid, No Variables, Inline Styles)
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

          <!-- Overview Cards (Table Layout) -->
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

          <!-- Spacer -->
          <tr><td height="20"></td></tr>

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

          <!-- Spacer -->
          <tr><td height="20"></td></tr>

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

          <!-- Spacer -->
          <tr><td height="20"></td></tr>

          <!-- Motivation Footer -->
          <tr>
            <td align="center" style="background: linear-gradient(90deg, #1d4ed8, #6d28d9); border-radius: 14px; padding: 20px; color: #ffffff; font-weight: bold;">
              {"🚀 Great work this week! Keep the momentum going!" if stats['consistency'] >= 70 else "💪 Every step counts! Let's aim higher next week!"}
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
