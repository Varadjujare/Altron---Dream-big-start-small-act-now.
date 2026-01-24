"""
LifeSync - Report Scheduler Module
Handles automated weekly and monthly report generation and delivery.
"""

import time
import threading
import datetime

from utils.db import get_db_connection


def get_all_users_with_email():
    """Fetch all users who have an email address."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE email IS NOT NULL AND email != ''")
    users = [{"id": row[0], "username": row[1], "email": row[2]} for row in cursor.fetchall()]
    conn.close()
    return users


def generate_and_send_reports(report_type: str = "weekly"):
    """Generate and send reports to all users."""
    from utils.report_generator import report_generator
    from utils.email_service import email_service
    
    print(f"\n{'='*50}")
    print(f"[{datetime.datetime.now()}] 🚀 AUTOMATION: Starting {report_type.capitalize()} Report Generation...")
    print(f"{'='*50}")
    
    users = get_all_users_with_email()
    print(f"📋 Found {len(users)} users with email addresses")
    
    success_count = 0
    fail_count = 0
    
    for user in users:
        try:
            print(f"\n👤 Processing: {user['username']} ({user['email']})")
            
            # Generate HTML report
            html_report = report_generator.generate_html_report(user['id'], report_type)
            
            # Optionally generate PDF
            pdf_path = report_generator.generate_pdf(user['id'], report_type)
            
            # Send email
            if report_type == "weekly":
                sent = email_service.send_weekly_report(
                    user['email'], 
                    user['username'], 
                    html_report, 
                    pdf_path
                )
            else:
                sent = email_service.send_monthly_report(
                    user['email'], 
                    user['username'], 
                    html_report, 
                    pdf_path
                )
            
            if sent:
                success_count += 1
            else:
                fail_count += 1
                
        except Exception as e:
            print(f"❌ Error processing {user['username']}: {e}")
            fail_count += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Batch Complete: {success_count} sent, {fail_count} failed")
    print(f"{'='*50}\n")


class ReportScheduler:
    """Background scheduler for automated report delivery."""
    
    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = None
        self.weekly_hour = 9  # 9 AM
        self.weekly_day = 6   # Sunday (0=Monday, 6=Sunday)
        self.monthly_hour = 9 # 9 AM
        self.monthly_day = 1  # 1st of month

    def start(self):
        """Start the scheduler thread."""
        if self.thread is None:
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print("🕒 Scheduler Started: Automated Reporting System is ONLINE.")
            print(f"   📅 Weekly reports: Every Sunday at {self.weekly_hour}:00 AM")
            print(f"   📅 Monthly reports: 1st of each month at {self.monthly_hour}:00 AM")

    def stop(self):
        """Stop the scheduler thread."""
        if self.thread:
            self.stop_event.set()
            self.thread.join()
            print("🛑 Scheduler stopped.")

    def _run(self):
        """Main scheduler loop."""
        print("🕒 Scheduler: Monitoring time for automated tasks...")
        last_weekly_run = None
        last_monthly_run = None
        
        while not self.stop_event.is_set():
            now = datetime.datetime.now()
            today = now.date()
            
            # Weekly Report: Sunday at specified hour
            if (now.weekday() == self.weekly_day and 
                now.hour == self.weekly_hour and 
                last_weekly_run != today):
                generate_and_send_reports("weekly")
                last_weekly_run = today
            
            # Monthly Report: 1st of month at specified hour
            if (now.day == self.monthly_day and 
                now.hour == self.monthly_hour and 
                last_monthly_run != today):
                generate_and_send_reports("monthly")
                last_monthly_run = today

            # Sleep for 30 seconds between checks
            time.sleep(30)
    
    def trigger_now(self, report_type: str = "weekly"):
        """Manually trigger a report generation (for testing)."""
        print(f"🔧 Manual trigger: {report_type} report")
        threading.Thread(
            target=generate_and_send_reports, 
            args=(report_type,), 
            daemon=True
        ).start()


# Global instance
scheduler = ReportScheduler()

