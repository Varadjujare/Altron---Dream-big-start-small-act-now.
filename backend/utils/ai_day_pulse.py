"""
LifeSync - Day Pulse AI Analyzer
Uses Groq API (llama-3.3-70b-versatile) to analyze 30-day habit + task patterns
and generate personalized daily insights for each user.
"""

import os
import json
from datetime import datetime, timedelta
from utils.db import execute_query


def get_user_30day_data(user_id: int) -> dict:
    """
    Fetch last 30 days of habit and task data for a user from PostgreSQL.
    Returns a structured dict ready to be passed to the AI prompt.
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    start_str = str(start_date)
    end_str = str(end_date)

    # --- Habits ---
    habits_query = """
        SELECT id, name FROM habits
        WHERE user_id = %s AND is_active = TRUE
        ORDER BY sort_order, id
    """
    habits = execute_query(habits_query, (user_id,), fetch_all=True)

    # Daily habit completions over 30 days
    habit_logs_query = """
        SELECT hl.habit_id, hl.completed_date
        FROM habit_logs hl
        JOIN habits h ON hl.habit_id = h.id
        WHERE h.user_id = %s
            AND h.is_active = TRUE
            AND hl.completed_date >= %s
            AND hl.completed_date <= %s
        ORDER BY hl.completed_date
    """
    habit_logs = execute_query(habit_logs_query, (user_id, start_str, end_str), fetch_all=True)

    # Build per-habit completion list
    habit_map = {h['id']: h['name'] for h in habits}
    habit_completions = {}
    for h in habits:
        habit_completions[h['name']] = []

    for log in habit_logs:
        name = habit_map.get(log['habit_id'])
        if name:
            habit_completions[name].append(str(log['completed_date']))

    # --- Daily task stats over 30 days ---
    task_stats_query = """
        SELECT
            due_date,
            COUNT(*) as total,
            SUM(CASE WHEN is_completed = TRUE THEN 1 ELSE 0 END) as completed
        FROM tasks
        WHERE user_id = %s
            AND due_date >= %s
            AND due_date <= %s
        GROUP BY due_date
        ORDER BY due_date
    """
    task_stats = execute_query(task_stats_query, (user_id, start_str, end_str), fetch_all=True)

    daily_task_data = []
    for row in task_stats:
        total = row['total'] or 0
        completed = row['completed'] or 0
        pct = round((completed / total * 100), 1) if total > 0 else 0
        daily_task_data.append({
            'date': str(row['due_date']),
            'total': total,
            'completed': completed,
            'completion_pct': pct
        })

    # --- Summary stats ---
    total_habits = len(habits)
    habit_summary = {}
    for name, dates in habit_completions.items():
        habit_summary[name] = {
            'completions_in_30_days': len(dates),
            'completion_rate_pct': round(len(dates) / 30 * 100, 1),
            'completed_dates': dates
        }

    avg_task_completion = 0
    if daily_task_data:
        avg_task_completion = round(
            sum(d['completion_pct'] for d in daily_task_data) / len(daily_task_data), 1
        )

    return {
        'analysis_period': f'{start_str} to {end_str}',
        'total_habits_tracked': total_habits,
        'habit_details': habit_summary,
        'daily_task_stats': daily_task_data,
        'avg_task_completion_pct': avg_task_completion
    }


def generate_day_pulse_report(user_id: int) -> str | None:
    """
    Call Groq API with the user's 30-day data and return the Day Pulse report text.
    Returns None if the API call fails or groq is not installed.
    """
    try:
        from groq import Groq
    except ImportError:
        print("❌ groq package not installed. Run: pip install groq")
        return None

    api_key = os.getenv('GROQ_API_KEY', '')
    if not api_key:
        print("❌ GROQ_API_KEY not set in .env file")
        return None

    try:
        user_data = get_user_30day_data(user_id)
    except Exception as e:
        print(f"❌ Failed to fetch user data for user {user_id}: {e}")
        return None

    # Don't run if user has no data yet
    if user_data['total_habits_tracked'] == 0 and not user_data['daily_task_stats']:
        print(f"⚠️  User {user_id} has no habit/task data — skipping Day Pulse.")
        return None

    prompt = f"""You are LifeSync's AI analyst. You analyze users' daily habit and task data to find hidden behavioral patterns.

Analyze the following 30-day data and generate a **Day Pulse Report** in EXACTLY this format — no extra text, no markdown headers, just the 4 lines:

⚡ Today's Day Pulse

💪 Your Power Combo: [Two habits or habit+task pattern that together predict the highest task completion] = [X]% task completion rate on days both are done
⚡ Your Kryptonite: [The single most impactful skipped habit] → [X]x more likely to [specific bad outcome]
🔍 Hidden Insight: [A surprising non-obvious pattern from the 30-day data, specific to this user's actual numbers]
🔮 Tomorrow's Prediction: [X]% chance of a great day if [one specific actionable recommendation based on their patterns]

Rules:
- Use REAL numbers from the data provided
- Be specific (use actual habit names from the data)
- Keep each line under 120 characters
- Make it feel personal, punchy, and motivating
- If data is limited (< 7 days), still generate insights from what's available

User's 30-Day Data:
{json.dumps(user_data, indent=2)}
"""

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.75,
            max_tokens=300
        )
        report = response.choices[0].message.content.strip()
        print(f"✅ Day Pulse generated for user {user_id}")
        return report

    except Exception as e:
        print(f"❌ Groq API error for user {user_id}: {e}")
        # Fallback to 8B model
        try:
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.75,
                max_tokens=300
            )
            report = response.choices[0].message.content.strip()
            print(f"✅ Day Pulse generated (fallback model) for user {user_id}")
            return report
        except Exception as e2:
            print(f"❌ Fallback model also failed for user {user_id}: {e2}")
            return None
