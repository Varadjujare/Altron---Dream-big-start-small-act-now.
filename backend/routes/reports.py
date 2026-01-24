"""
LifeSync - Reports API Routes
Endpoints for generating, previewing, and sending reports.
"""

from flask import Blueprint, jsonify, request, Response
from flask_login import login_required, current_user

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/api/reports/preview/<period>', methods=['GET'])
@login_required
def preview_report(period):
    """Preview a report as HTML (weekly or monthly)."""
    if period not in ['weekly', 'monthly']:
        return jsonify({"success": False, "message": "Invalid period. Use 'weekly' or 'monthly'"}), 400
    
    from utils.report_generator import report_generator
    
    user_id = current_user.id
    html_report = report_generator.generate_html_report(user_id, period)
    
    return Response(html_report, mimetype='text/html')


@reports_bp.route('/api/reports/download/<period>', methods=['GET'])
@login_required
def download_report(period):
    """Download a report as PDF."""
    if period not in ['weekly', 'monthly']:
        return jsonify({"success": False, "message": "Invalid period. Use 'weekly' or 'monthly'"}), 400
    
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
        os.remove(pdf_path)
        
        return Response(
            pdf_data,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=lifesync_{period}_report.pdf'
            }
        )
    else:
        return jsonify({"success": False, "message": "Failed to generate PDF"}), 500


@reports_bp.route('/api/reports/send-now', methods=['POST'])
@login_required
def send_report_now():
    """Manually send a report to the current user via email."""
    from utils.report_generator import report_generator
    from utils.email_service import EmailService
    from utils.db import get_db_connection
    
    data = request.get_json() or {}
    period = data.get('period', 'weekly')
    
    if period not in ['weekly', 'monthly']:
        return jsonify({"success": False, "message": "Invalid period"}), 400
    
    user_id = current_user.id
    
    # Get user email
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row[1]:
        return jsonify({"success": False, "message": "No email address on file"}), 400
    
    username, email = row[0], row[1]
    
    # Create fresh email service instance
    email_service = EmailService()
    
    if not email_service.is_configured:
        return jsonify({"success": False, "message": "Email service not configured. Check SMTP settings."}), 500
    
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
            "message": "Failed to send email. Check server logs and SMTP configuration."
        }), 500


@reports_bp.route('/api/reports/stats/<period>', methods=['GET'])
@login_required
def get_report_stats(period):
    """Get report statistics as JSON (for frontend display)."""
    if period not in ['weekly', 'monthly']:
        return jsonify({"success": False, "message": "Invalid period"}), 400
    
    from utils.report_generator import report_generator
    
    user_id = current_user.id
    
    if period == 'weekly':
        stats = report_generator.get_weekly_stats(user_id)
    else:
        stats = report_generator.get_monthly_stats(user_id)
    
    return jsonify({"success": True, "stats": stats})


@reports_bp.route('/api/reports/test-email', methods=['POST'])
@login_required
def test_email():
    """Send a test email to verify configuration."""
    from utils.email_service import email_service
    from utils.db import get_db_connection
    
    user_id = current_user.id
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row[0]:
        return jsonify({"success": False, "message": "No email address on file"}), 400
    
    email = row[0]
    sent = email_service.send_test_email(email)
    
    if sent:
        return jsonify({"success": True, "message": f"Test email sent to {email}"})
    else:
        return jsonify({
            "success": False, 
            "message": "Failed to send test email. Check SMTP configuration."
        }), 500


@reports_bp.route('/api/reports/trigger-batch', methods=['POST'])
@login_required
def trigger_batch_reports():
    """Trigger batch report generation for all users (admin only)."""
    # In a real app, you'd check for admin privileges here
    from utils.scheduler import scheduler
    
    data = request.get_json() or {}
    period = data.get('period', 'weekly')
    
    if period not in ['weekly', 'monthly']:
        return jsonify({"success": False, "message": "Invalid period"}), 400
    
    scheduler.trigger_now(period)
    
    return jsonify({
        "success": True, 
        "message": f"Batch {period} report generation triggered. Check server logs."
    })
