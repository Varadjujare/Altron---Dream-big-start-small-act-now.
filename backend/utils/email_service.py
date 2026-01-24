"""
Altron - Email Service Module
Sends reports and notifications via email using SMTP.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional
from backend.config import Config


class EmailService:
    """Handles sending emails via SMTP."""
    
    def __init__(self):
        # Load configuration from Config class
        self.smtp_host = Config.SMTP_HOST
        self.smtp_port = Config.SMTP_PORT
        self.smtp_user = Config.SMTP_USER
        self.smtp_password = Config.SMTP_PASSWORD
        self.from_name = Config.SMTP_FROM_NAME
        self.from_email = Config.SMTP_FROM_EMAIL or self.smtp_user
        
        # Check if configured
        self.is_configured = bool(self.smtp_user and self.smtp_password)
        
        if not self.is_configured:
            print("⚠️ Email service not configured. Add SMTP credentials to .env file:")
            print("   SMTP_USER=your.email@gmail.com")
            print("   SMTP_PASSWORD=your-app-password")
            print("   For Gmail: Create an App Password at https://myaccount.google.com/apppasswords")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        pdf_attachment: Optional[str] = None
    ) -> bool:
        """
        Send an email with optional PDF attachment.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML body content
            text_content: Plain text fallback (auto-generated if not provided)
            pdf_attachment: Path to PDF file to attach
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured:
            print(f"❌ Cannot send email - SMTP not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Plain text version (fallback)
            if not text_content:
                text_content = "Please view this email in an HTML-capable email client."
            msg.attach(MIMEText(text_content, 'plain'))
            
            # HTML version
            msg.attach(MIMEText(html_content, 'html'))
            
            # PDF attachment if provided
            if pdf_attachment and os.path.exists(pdf_attachment):
                with open(pdf_attachment, 'rb') as f:
                    pdf = MIMEApplication(f.read(), _subtype='pdf')
                    pdf.add_header(
                        'Content-Disposition', 
                        'attachment', 
                        filename=os.path.basename(pdf_attachment)
                    )
                    msg.attach(pdf)
                    print(f"📎 Attached PDF: {os.path.basename(pdf_attachment)}")
            
            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent to {to_email}: {subject}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print(f"❌ SMTP Authentication failed. Check credentials.")
            print("   For Gmail: Use an App Password, not your regular password.")
            return False
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
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


# Global instance
email_service = EmailService()
