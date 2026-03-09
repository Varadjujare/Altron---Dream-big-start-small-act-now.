"""
Altron - Reports API Routes
Endpoints for generating, previewing, and sending reports.
"""

import datetime
import traceback
from flask import Blueprint, jsonify, request, Response
from flask_login import login_required, current_user

reports_bp = Blueprint('reports', __name__)


# ─── Diagnostic Endpoint (no auth, for quick debugging) ─────────────────────

@reports_bp.route('/api/reports/email-status', methods=['GET'])
def email_status():
    """Public diagnostic endpoint — check if email service is working."""
    try:
        from utils.email_service import EmailService
        from config import Config
        import os

        svc = EmailService()
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        return jsonify({
            "success": True,
            "server_time_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "smtp_configured": svc.is_configured,
            "smtp_host": svc.smtp_host,
            "smtp_port": svc.smtp_port,
            "smtp_user_set": bool(svc.smtp_user),
            "smtp_password_set": bool(svc.smtp_password),
            "from_email": svc.from_email,
            "from_name": svc.from_name,
            "groq_key_set": bool(Config.GROQ_API_KEY),
            "python_env": os.environ.get('PYTHON_VERSION', 'unknown'),
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@reports_bp.route('/api/reports/smtp-test', methods=['GET'])
def smtp_test():
    """Bare-minimum SendGrid API test — no auth required, no DB, no heavy imports."""
    try:
        import requests as http_req
        import os

        api_key = os.environ.get('SMTP_PASSWORD', '')
        from_email = os.environ.get('SMTP_FROM_EMAIL', 'varuuu009@gmail.com')
        to_email = 'varuuu009@gmail.com'

        if not api_key:
            return jsonify({"success": False, "message": "SMTP_PASSWORD (SendGrid API key) not set"}), 500

        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": from_email, "name": "Altron Test"},
            "subject": "Altron SendGrid API Test",
            "content": [{"type": "text/html", "value": "<h1>SendGrid API Test</h1><p>If you see this, email sending works from Render!</p>"}]
        }

        resp = http_req.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=15
        )

        if resp.status_code in (200, 201, 202):
            return jsonify({"success": True, "message": f"SendGrid API test email sent to {to_email}", "status_code": resp.status_code})
        else:
            return jsonify({"success": False, "message": f"SendGrid API error", "status_code": resp.status_code, "body": resp.text}), 500

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {e}", "traceback": traceback.format_exc()}), 500


# ─── Report Preview (HTML) ──────────────────────────────────────────────────

@reports_bp.route('/api/reports/preview/<period>', methods=['GET'])
@login_required
def preview_report(period):
    """Preview a report as HTML (weekly or monthly)."""
    if period not in ['weekly', 'monthly']:
        return jsonify({"success": False, "message": "Invalid period. Use 'weekly' or 'monthly'"}), 400

    try:
        from utils.report_generator import report_generator
        user_id = current_user.id
        html_report = report_generator.generate_html_report(user_id, period)
        return Response(html_report, mimetype='text/html')
    except Exception as e:
        return jsonify({"success": False, "message": f"Report generation failed: {e}", "traceback": traceback.format_exc()}), 500


# ─── Report Download (PDF) ──────────────────────────────────────────────────

@reports_bp.route('/api/reports/download/<period>', methods=['GET'])
@login_required
def download_report(period):
    """Download a report as PDF."""
    if period not in ['weekly', 'monthly']:
        return jsonify({"success": False, "message": "Invalid period. Use 'weekly' or 'monthly'"}), 400

    try:
        from utils.report_generator import report_generator, WEASYPRINT_AVAILABLE

        if not WEASYPRINT_AVAILABLE:
            return jsonify({
                "success": False,
                "message": "PDF generation is not available. Install weasyprint: pip install weasyprint"
            }), 500

        user_id = current_user.id
        pdf_path = report_generator.generate_pdf(user_id, period)

        if pdf_path:
            import os
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()

            # Clean up the file after reading
            try:
                os.remove(pdf_path)
            except OSError:
                pass

            return Response(
                pdf_data,
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment; filename={period}_report.pdf'}
            )
        else:
            return jsonify({"success": False, "message": "Failed to generate PDF"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"PDF download failed: {e}", "traceback": traceback.format_exc()}), 500


# ─── Send Report Now ────────────────────────────────────────────────────────

@reports_bp.route('/api/reports/send-now', methods=['POST'])
@login_required
def send_report_now():
    """Manually send a report to the current user via email."""
    try:
        from utils.report_generator import report_generator
        from utils.email_service import EmailService
        from utils.db import get_db_cursor

        data = request.get_json() or {}
        period = data.get('period', 'weekly')

        if period not in ['weekly', 'monthly']:
            return jsonify({"success": False, "message": "Invalid period"}), 400

        user_id = current_user.id

        # Get user email
        with get_db_cursor(dictionary=False) as (cursor, conn):
            cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()

        if not row or not row[1]:
            return jsonify({"success": False, "message": "No email address on file"}), 400

        username, email = row[0], row[1]

        # Create fresh email service instance
        email_service = EmailService()

        if not email_service.is_configured:
            return jsonify({
                "success": False,
                "message": "Email service not configured. Check SMTP settings.",
                "debug": {
                    "smtp_host": email_service.smtp_host,
                    "smtp_user_set": bool(email_service.smtp_user),
                    "smtp_password_set": bool(email_service.smtp_password)
                }
            }), 500

        # Generate and send
        html_report = report_generator.generate_html_report(user_id, period)
        pdf_path = report_generator.generate_pdf(user_id, period)

        if period == 'weekly':
            sent = email_service.send_weekly_report(email, username, html_report, pdf_path)
        else:
            sent = email_service.send_monthly_report(email, username, html_report, pdf_path)

        if sent:
            return jsonify({
                "success": True,
                "message": f"{period.capitalize()} report sent to {email}"
            })
        else:
            return jsonify({
                "success": False,
                "message": "SMTP send_email returned False. Check server logs for SMTP errors."
            }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Send report failed: {e}",
            "traceback": traceback.format_exc()
        }), 500


# ─── Report Stats (JSON) ────────────────────────────────────────────────────

@reports_bp.route('/api/reports/stats/<period>', methods=['GET'])
@login_required
def get_report_stats(period):
    """Get report statistics as JSON (for frontend display)."""
    if period not in ['weekly', 'monthly']:
        return jsonify({"success": False, "message": "Invalid period"}), 400

    try:
        from utils.report_generator import report_generator
        user_id = current_user.id

        if period == 'weekly':
            stats = report_generator.get_weekly_stats(user_id)
        else:
            stats = report_generator.get_monthly_stats(user_id)

        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "message": f"Stats failed: {e}", "traceback": traceback.format_exc()}), 500


# ─── Test Email ─────────────────────────────────────────────────────────────

@reports_bp.route('/api/reports/test-email', methods=['POST'])
@login_required
def test_email():
    """Send a test email to verify configuration."""
    try:
        from utils.email_service import EmailService
        from utils.db import get_db_cursor

        user_id = current_user.id

        with get_db_cursor(dictionary=False) as (cursor, conn):
            cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()

        if not row or not row[0]:
            return jsonify({"success": False, "message": "No email address on file"}), 400

        email = row[0]

        # Create fresh instance to pick up latest env vars
        svc = EmailService()

        if not svc.is_configured:
            return jsonify({
                "success": False,
                "message": "Email not configured",
                "debug": {
                    "smtp_host": svc.smtp_host,
                    "smtp_user_set": bool(svc.smtp_user),
                    "smtp_password_set": bool(svc.smtp_password)
                }
            }), 500

        sent = svc.send_test_email(email)

        if sent:
            return jsonify({"success": True, "message": f"Test email sent to {email}"})
        else:
            return jsonify({
                "success": False,
                "message": "SMTP send returned False. Check SMTP credentials and server logs."
            }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Test email failed: {e}",
            "traceback": traceback.format_exc()
        }), 500


# ─── Trigger Batch Reports ──────────────────────────────────────────────────

@reports_bp.route('/api/reports/trigger-batch', methods=['POST'])
@login_required
def trigger_batch_reports():
    """Trigger batch report generation for all users (admin only)."""
    try:
        from utils.scheduler import scheduler

        data = request.get_json() or {}
        report_type = data.get('type', 'weekly')

        if report_type not in ['weekly', 'monthly', 'pulse']:
            return jsonify({"success": False, "message": "Invalid type. Use 'weekly', 'monthly', or 'pulse'"}), 400

        scheduler.trigger_now(report_type)

        return jsonify({
            "success": True,
            "message": f"Batch {report_type} reports triggered for all users"
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Trigger failed: {e}", "traceback": traceback.format_exc()}), 500


# ─── Day Pulse Send Now ─────────────────────────────────────────────────────

@reports_bp.route('/api/daypulse/send-now', methods=['POST'])
@login_required
def send_day_pulse_now():
    """Manually send a Day Pulse report to the current user immediately (background)."""
    try:
        import threading
        from utils.email_service import EmailService
        from utils.db import get_db_cursor

        user_id = current_user.id

        # Get user email before spawning thread
        with get_db_cursor(dictionary=False) as (cursor, conn):
            cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()

        if not row or not row[1]:
            return jsonify({"success": False, "message": "No email address on file"}), 400

        username, email = row[0], row[1]

        email_service = EmailService()
        if not email_service.is_configured:
            return jsonify({"success": False, "message": "Email service not configured"}), 500

        def _send_in_background(uid, uname, uemail):
            try:
                from utils.ai_day_pulse import generate_day_pulse_report
                report = generate_day_pulse_report(uid)
                if report is None:
                    report = "Your Day Pulse is warming up! Keep tracking habits and tasks for personalized AI insights."
                svc = EmailService()
                sent = svc.send_day_pulse_report(uemail, uname, report)
                print(f"[DayPulse manual] sent={sent} to {uemail}")
            except Exception as ex:
                print(f"[DayPulse manual] ERROR: {ex}")
                traceback.print_exc()

        t = threading.Thread(target=_send_in_background, args=(user_id, username, email), daemon=True)
        t.start()

        return jsonify({
            "success": True,
            "message": f"Day Pulse is being generated and will arrive in your inbox ({email}) within 30 seconds"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Day Pulse trigger failed: {e}",
            "traceback": traceback.format_exc()
        }), 500
