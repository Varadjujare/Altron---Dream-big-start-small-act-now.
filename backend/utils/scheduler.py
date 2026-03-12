"""
LifeSync - Report Scheduler Module
Handles automated weekly and monthly report generation and delivery.
"""

import time
import threading
import datetime
import traceback

from utils.db import get_db_cursor


def get_all_users_with_email():
    """Fetch all users who have an email address."""
    with get_db_cursor(dictionary=False) as (cursor, conn):
        cursor.execute("SELECT id, username, email FROM users WHERE email IS NOT NULL AND email != ''")
        users = [{"id": row[0], "username": row[1], "email": row[2]} for row in cursor.fetchall()]
    return users


def generate_and_send_day_pulse():
    """Generate and send Day Pulse AI reports to all users."""
    try:
        from utils.ai_day_pulse import generate_day_pulse_report
        from utils.email_service import EmailService

        # Create a FRESH email service instance (not the stale singleton)
        svc = EmailService()
        if not svc.is_configured:
            print("❌ Day Pulse aborted: Email service not configured")
            return

        print(f"\n{'='*50}")
        print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}] ⚡ DAY PULSE: Starting...")
        print(f"{'='*50}")

        users = get_all_users_with_email()
        print(f"📋 Found {len(users)} users with email addresses")

        success_count = 0
        fail_count = 0

        for user in users:
            try:
                print(f"👤 Processing Day Pulse: {user['username']} ({user['email']})")
                report = generate_day_pulse_report(user['id'])

                if report is None:
                    report = "No recent activity found. Keep tracking your habits and tasks to get personalized insights!"

                sent = svc.send_day_pulse_report(user['email'], user['username'], report)

                if sent:
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                print(f"❌ Error processing Day Pulse for {user['username']}: {e}")
                traceback.print_exc()
                fail_count += 1

        print(f"⚡ Day Pulse Complete: {success_count} sent, {fail_count} failed\n")

    except Exception as e:
        print(f"❌ Day Pulse batch CRASHED: {e}")
        traceback.print_exc()


def generate_and_send_reports(report_type: str = "weekly"):
    """Generate and send reports to all users."""
    try:
        from utils.report_generator import report_generator
        from utils.email_service import EmailService

        # Create a FRESH email service instance
        svc = EmailService()
        if not svc.is_configured:
            print(f"❌ {report_type} reports aborted: Email service not configured")
            return

        print(f"\n{'='*50}")
        print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}] 🚀 {report_type.upper()} REPORT: Starting...")
        print(f"{'='*50}")

        users = get_all_users_with_email()
        print(f"📋 Found {len(users)} users with email addresses")

        success_count = 0
        fail_count = 0

        for user in users:
            try:
                print(f"👤 Processing: {user['username']} ({user['email']})")
                html_report = report_generator.generate_html_report(user['id'], report_type)
                pdf_path = report_generator.generate_pdf(user['id'], report_type)

                if report_type == "weekly":
                    sent = svc.send_weekly_report(user['email'], user['username'], html_report, pdf_path)
                else:
                    sent = svc.send_monthly_report(user['email'], user['username'], html_report, pdf_path)

                if sent:
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                print(f"❌ Error processing {user['username']}: {e}")
                traceback.print_exc()
                fail_count += 1

        print(f"✅ {report_type.capitalize()} Batch Complete: {success_count} sent, {fail_count} failed\n")

    except Exception as e:
        print(f"❌ {report_type} batch CRASHED: {e}")
        traceback.print_exc()


class ReportScheduler:
    """Background scheduler for automated report delivery."""
    
    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = None
        self.weekly_hour = 18  # 18:00 UTC = 11:30 PM IST
        self.weekly_minute = 0
        self.weekly_day = 6   # Sunday (0=Monday, 6=Sunday)
        self.monthly_hour = 9 # 09:00 UTC = 2:30 PM IST
        self.monthly_minute = 0
        self.monthly_day = 1  # 1st of month
        # Day Pulse: 17:30 UTC = 11:00 PM IST
        self.pulse_hour = 17
        self.pulse_minute = 30

    def start(self):
        """Start the scheduler thread."""
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            print(f"🕒 Scheduler Started: (UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')})")
            print(f"   ⚡ Day Pulse:       Every night at {self.pulse_hour:02d}:{self.pulse_minute:02d} UTC")
            print(f"   📅 Weekly reports:  Every Sunday at {self.weekly_hour:02d}:{self.weekly_minute:02d} UTC")
            print(f"   📅 Monthly reports: 1st of each month at {self.monthly_hour:02d}:{self.monthly_minute:02d} UTC")

    def stop(self):
        """Stop the scheduler thread."""
        if self.thread:
            self.stop_event.set()
            self.thread.join()
            print("🛑 Scheduler stopped.")

    def _run(self):
        """Main scheduler loop — handles Render sleep/wake cycles."""
        print("🕒 Scheduler: Monitoring time for automated tasks...")
        last_weekly_run = None
        last_monthly_run = None
        last_pulse_run = None
        
        while not self.stop_event.is_set():
            try:
                now = datetime.datetime.now(datetime.timezone.utc)
                today = now.date()
                current_minutes = now.hour * 60 + now.minute

                # ── Day Pulse: every night at pulse_hour:pulse_minute UTC ──
                pulse_target = self.pulse_hour * 60 + self.pulse_minute
                if (0 <= current_minutes - pulse_target <= 30 and
                    last_pulse_run != today):
                    print(f"⚡ Day Pulse triggered at UTC {now.strftime('%H:%M')}")
                    try:
                        generate_and_send_day_pulse()
                    except Exception as e:
                        print(f"❌ Day Pulse failed: {e}")
                        traceback.print_exc()
                    last_pulse_run = today

                # ── Weekly Report: Sunday at weekly_hour:weekly_minute UTC ──
                weekly_target = self.weekly_hour * 60 + self.weekly_minute
                if (now.weekday() == self.weekly_day and
                    0 <= current_minutes - weekly_target <= 30 and
                    last_weekly_run != today):
                    print(f"📅 Weekly report triggered at UTC {now.strftime('%H:%M')}")
                    try:
                        generate_and_send_reports("weekly")
                    except Exception as e:
                        print(f"❌ Weekly report failed: {e}")
                        traceback.print_exc()
                    last_weekly_run = today
                
                # ── Monthly Report: 1st of month ──
                monthly_target = self.monthly_hour * 60 + self.monthly_minute
                if (now.day == self.monthly_day and
                    0 <= current_minutes - monthly_target <= 30 and
                    last_monthly_run != today):
                    print(f"📅 Monthly report triggered at UTC {now.strftime('%H:%M')}")
                    try:
                        generate_and_send_reports("monthly")
                    except Exception as e:
                        print(f"❌ Monthly report failed: {e}")
                        traceback.print_exc()
                    last_monthly_run = today

            except Exception as e:
                print(f"❌ Scheduler loop error: {e}")
                traceback.print_exc()

            # Sleep 30 seconds between checks
            time.sleep(30)
    
    def trigger_now(self, report_type: str = "weekly"):
        """Manually trigger a report generation (for testing)."""
        print(f"🔧 Manual trigger: {report_type} report")
        threading.Thread(
            target=generate_and_send_reports,
            args=(report_type,),
            daemon=True
        ).start()

    def trigger_day_pulse_now(self):
        """Manually trigger Day Pulse for testing."""
        print("🔧 Manual trigger: Day Pulse report")
        threading.Thread(
            target=generate_and_send_day_pulse,
            daemon=True
        ).start()


# Global instance
scheduler = ReportScheduler()
