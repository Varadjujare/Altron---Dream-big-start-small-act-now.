"""
Altron - Email Service Module
Sends reports and notifications via SendGrid HTTP API.
(Render blocks outbound SMTP on port 587, so we use the REST API instead.)
"""

import os
import base64
import json
from typing import Optional

try:
    import requests as http_requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ 'requests' library not installed. Email sending disabled.")

from config import Config


class EmailService:
    """Handles sending emails via SendGrid HTTP API."""
    
    SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
    
    def __init__(self):
        # Load configuration from Config class
        self.smtp_host = Config.SMTP_HOST
        self.smtp_port = Config.SMTP_PORT
        self.smtp_user = Config.SMTP_USER
        self.smtp_password = Config.SMTP_PASSWORD  # This is the SendGrid API key (SG.xxx)
        self.from_name = Config.SMTP_FROM_NAME
        self.from_email = Config.SMTP_FROM_EMAIL or self.smtp_user
        
        # The SendGrid API key is stored in SMTP_PASSWORD (starts with SG.)
        self.api_key = self.smtp_password
        
        # Check if configured
        self.is_configured = bool(self.api_key and REQUESTS_AVAILABLE)
        
        if not self.is_configured:
            if not REQUESTS_AVAILABLE:
                print("⚠️ Email service disabled: 'requests' library not installed")
            elif not self.api_key:
                print("⚠️ Email service not configured. Set SMTP_PASSWORD to your SendGrid API key.")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        pdf_attachment: Optional[str] = None
    ) -> bool:
        """
        Send an email via SendGrid HTTP API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML body content
            text_content: Plain text fallback
            pdf_attachment: Path to PDF file to attach
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured:
            print(f"❌ Cannot send email - SendGrid API not configured")
            return False
        
        try:
            # Build the SendGrid API payload
            payload = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": self.from_email, "name": self.from_name},
                "subject": subject,
                "content": []
            }
            
            # Add text content
            if text_content:
                payload["content"].append({"type": "text/plain", "value": text_content})
            else:
                payload["content"].append({"type": "text/plain", "value": "Please view this email in an HTML-capable email client."})
            
            # Add HTML content
            payload["content"].append({"type": "text/html", "value": html_content})
            
            # Add PDF attachment if provided
            if pdf_attachment and os.path.exists(pdf_attachment):
                with open(pdf_attachment, 'rb') as f:
                    pdf_data = base64.b64encode(f.read()).decode('utf-8')
                payload["attachments"] = [{
                    "content": pdf_data,
                    "filename": os.path.basename(pdf_attachment),
                    "type": "application/pdf",
                    "disposition": "attachment"
                }]
                print(f"📎 Attached PDF: {os.path.basename(pdf_attachment)}")
            
            # Send via SendGrid HTTP API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = http_requests.post(
                self.SENDGRID_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in (200, 201, 202):
                print(f"✅ Email sent to {to_email}: {subject}")
                return True
            else:
                print(f"❌ SendGrid API error {response.status_code}: {response.text}")
                return False
            
        except Exception as e:
            print(f"❌ Failed to send email via SendGrid API: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_weekly_report(self, to_email: str, username: str, html_report: str, pdf_path: Optional[str] = None) -> bool:
        """Send weekly progress report."""
        subject = f"🎯 Altron Weekly Report - {username}"
        return self.send_email(to_email, subject, html_report, pdf_attachment=pdf_path)
    
    def send_monthly_report(self, to_email: str, username: str, html_report: str, pdf_path: Optional[str] = None) -> bool:
        """Send monthly progress report."""
        subject = f"📊 Altron Monthly Report - {username}"
        return self.send_email(to_email, subject, html_report, pdf_attachment=pdf_path)
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send a welcome email to newly registered users."""
        subject = "🎉 Welcome to Altron!"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%); color: #fff;">
            <div style="max-width: 600px; margin: 0 auto; background: rgba(30, 30, 45, 0.95); border-radius: 16px; padding: 40px; border: 1px solid rgba(0, 255, 136, 0.3);">
                <h1 style="color: #00ff88; margin-bottom: 20px;">Welcome to Altron, {username}! 🚀</h1>
                <p style="font-size: 16px; line-height: 1.6; color: #e0e0e0;">
                    Thank you for joining Altron! You're now part of a community focused on 
                    productivity and personal growth.
                </p>
                <p style="font-size: 16px; line-height: 1.6; color: #e0e0e0;">
                    Here's what you can do with Altron:
                </p>
                <ul style="color: #e0e0e0; line-height: 1.8;">
                    <li>📋 <strong>Track Tasks</strong> - Organize your daily to-dos</li>
                    <li>🎯 <strong>Build Habits</strong> - Create and maintain positive habits</li>
                    <li>📊 <strong>View Analytics</strong> - Monitor your progress over time</li>
                    <li>📅 <strong>Calendar View</strong> - See your schedule at a glance</li>
                    <li>📧 <strong>Weekly Reports</strong> - Get automated progress updates</li>
                </ul>
                <div style="margin-top: 30px; padding: 20px; background: rgba(0, 255, 136, 0.1); border-radius: 8px; border-left: 4px solid #00ff88;">
                    <p style="margin: 0; color: #00ff88;">
                        💡 <strong>Pro Tip:</strong> Start by adding your first habit or task to get going!
                    </p>
                </div>
                <hr style="border: 1px solid rgba(255,255,255,0.1); margin: 30px 0;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Sent from Altron Dashboard<br>
                    You're receiving this because you signed up at altron.app
                </p>
            </div>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, html)
    
    def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify configuration."""
        subject = "🧪 Altron Email Test"
        html = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #4CAF50;">✅ Email Configuration Working!</h1>
            <p>Your Altron email notifications are set up correctly.</p>
            <p style="color: #666; font-size: 14px;">You will receive weekly and monthly progress reports at this address.</p>
            <hr style="border: 1px solid #eee;">
            <p style="color: #999; font-size: 12px;">Sent from Altron Dashboard</p>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, html)

    def send_day_pulse_report(self, to_email: str, username: str, pulse_report: str) -> bool:
        """Send the nightly Day Pulse AI report to a user."""
        from datetime import datetime
        today_str = datetime.now().strftime('%A, %b %d, %Y')

        # Parse the 4 lines from the AI report
        lines = [l.strip() for l in pulse_report.strip().splitlines() if l.strip()]
        power_combo   = next((l for l in lines if 'Power Combo'   in l), '💪 Your Power Combo: Keep completing your habits together!')
        kryptonite    = next((l for l in lines if 'Kryptonite'    in l), '⚡ Your Kryptonite: Skipping morning habits hurts your day.')
        hidden_insight= next((l for l in lines if 'Hidden Insight' in l), '🔍 Hidden Insight: Consistency is your superpower.')
        prediction    = next((l for l in lines if "Prediction"    in l), '🔮 Tomorrow\'s Prediction: Start strong for a great day!')

        # Strip leading emoji+label — keep the value part only
        def extract_value(line: str, label: str) -> str:
            if label in line:
                parts = line.split(':', 1)
                return parts[1].strip() if len(parts) > 1 else line
            return line

        power_val   = extract_value(power_combo,    'Power Combo')
        krypto_val  = extract_value(kryptonite,     'Kryptonite')
        insight_val = extract_value(hidden_insight, 'Hidden Insight')
        predict_val = extract_value(prediction,     "Prediction")

        subject = f"⚡ Your Day Pulse Report — {today_str}"

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Day Pulse Report</title>
</head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0f;padding:30px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 100%);
                      border-radius:20px;overflow:hidden;
                      border:1px solid rgba(0,255,136,0.25);
                      box-shadow:0 0 40px rgba(0,255,136,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#00ff88 0%,#00cc6a 100%);
                       padding:32px 40px;text-align:center;">
              <div style="font-size:36px;margin-bottom:6px;">⚡</div>
              <h1 style="margin:0;color:#0a0a0f;font-size:26px;font-weight:800;letter-spacing:-0.5px;">
                Day Pulse Report
              </h1>
              <p style="margin:6px 0 0;color:rgba(0,0,0,0.65);font-size:14px;">
                {today_str}
              </p>
            </td>
          </tr>

          <!-- Greeting -->
          <tr>
            <td style="padding:28px 40px 8px;">
              <p style="margin:0;color:#c0c0d0;font-size:16px;line-height:1.6;">
                Hey <strong style="color:#fff;">{username}</strong> 👋 — here's what your AI analyst
                found hiding in your last 30 days of data:
              </p>
            </td>
          </tr>

          <!-- Power Combo Card -->
          <tr>
            <td style="padding:12px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:rgba(0,255,136,0.07);border-radius:14px;
                            border:1px solid rgba(0,255,136,0.25);overflow:hidden;">
                <tr>
                  <td style="padding:20px 24px;">
                    <div style="display:flex;align-items:center;margin-bottom:8px;">
                      <span style="font-size:22px;margin-right:10px;">💪</span>
                      <span style="color:#00ff88;font-size:11px;font-weight:700;
                                   text-transform:uppercase;letter-spacing:1.5px;">
                        Power Combo
                      </span>
                    </div>
                    <p style="margin:0;color:#e8ffe8;font-size:16px;line-height:1.5;
                               font-weight:600;">
                      {power_val}
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Kryptonite Card -->
          <tr>
            <td style="padding:4px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:rgba(255,80,80,0.07);border-radius:14px;
                            border:1px solid rgba(255,80,80,0.25);overflow:hidden;">
                <tr>
                  <td style="padding:20px 24px;">
                    <div style="margin-bottom:8px;">
                      <span style="font-size:22px;margin-right:10px;">⚡</span>
                      <span style="color:#ff6b6b;font-size:11px;font-weight:700;
                                   text-transform:uppercase;letter-spacing:1.5px;">
                        Your Kryptonite
                      </span>
                    </div>
                    <p style="margin:0;color:#ffe8e8;font-size:16px;line-height:1.5;
                               font-weight:600;">
                      {krypto_val}
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Hidden Insight Card -->
          <tr>
            <td style="padding:4px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:rgba(147,51,234,0.1);border-radius:14px;
                            border:1px solid rgba(147,51,234,0.3);overflow:hidden;">
                <tr>
                  <td style="padding:20px 24px;">
                    <div style="margin-bottom:8px;">
                      <span style="font-size:22px;margin-right:10px;">🔍</span>
                      <span style="color:#c084fc;font-size:11px;font-weight:700;
                                   text-transform:uppercase;letter-spacing:1.5px;">
                        Hidden Insight
                      </span>
                    </div>
                    <p style="margin:0;color:#f3e8ff;font-size:16px;line-height:1.5;
                               font-weight:600;">
                      {insight_val}
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Tomorrow's Prediction Card -->
          <tr>
            <td style="padding:4px 40px 24px;">
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:rgba(59,130,246,0.1);border-radius:14px;
                            border:1px solid rgba(59,130,246,0.3);overflow:hidden;">
                <tr>
                  <td style="padding:20px 24px;">
                    <div style="margin-bottom:8px;">
                      <span style="font-size:22px;margin-right:10px;">🔮</span>
                      <span style="color:#60a5fa;font-size:11px;font-weight:700;
                                   text-transform:uppercase;letter-spacing:1.5px;">
                        Tomorrow's Prediction
                      </span>
                    </div>
                    <p style="margin:0;color:#e8f4ff;font-size:16px;line-height:1.5;
                               font-weight:600;">
                      {predict_val}
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 40px;">
              <div style="border-top:1px solid rgba(255,255,255,0.07);"></div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 40px;text-align:center;">
              <p style="margin:0 0 6px;color:#666;font-size:12px;">
                Generated by LifeSync Day Pulse AI · Every night at 10 PM
              </p>
              <p style="margin:0;color:#444;font-size:11px;">
                You're receiving this because you have an active LifeSync account.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
        text_fallback = f"""
Day Pulse Report — {today_str}
Hi {username},

⚡ TODAY'S DAY PULSE

{power_combo}
{kryptonite}
{hidden_insight}
{prediction}

Generated by LifeSync Day Pulse AI
"""
        return self.send_email(to_email, subject, html, text_content=text_fallback)


# Global instance
email_service = EmailService()
