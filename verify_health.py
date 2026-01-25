
import sys
import os
import importlib.util

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from config import Config

def check_dependencies():
    print("\n--- 📦 Dependency Check ---")
    
    # Check WeasyPrint (for PDF generation)
    weasy_spec = importlib.util.find_spec("weasyprint")
    if weasy_spec:
        print("✅ WeasyPrint: Installed (PDF generation available)")
    else:
        print("⚠️ WeasyPrint: Not Found (PDF generation disabled)")
        
    # Check Psycopg2 (for DB)
    psycopg_spec = importlib.util.find_spec("psycopg2")
    if psycopg_spec:
        print("✅ Psycopg2: Installed")
    else:
        print("❌ Psycopg2: Not Found (Database will fail)")

def check_db():
    print("\n--- 🗄️ Database Check ---")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=Config.PG_HOST,
            user=Config.PG_USER,
            password=Config.PG_PASSWORD,
            dbname=Config.PG_DATABASE,
            port=Config.PG_PORT,
            sslmode='require',
            connect_timeout=5
        )
        print(f"✅ Connection: Successful to {Config.PG_HOST}/{Config.PG_DATABASE}")
        
        # Check permissions/tables
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        count = cursor.fetchone()[0]
        print(f"✅ Tables Found: {count}")
        conn.close()
    except Exception as e:
        print(f"❌ Database Connection Failed: {e}")

def check_email():
    print("\n--- 📧 Email Service Check ---")
    print(f"SMTP Host: {Config.SMTP_HOST}")
    print(f"SMTP Port: {Config.SMTP_PORT}")
    print(f"SMTP User: {Config.SMTP_USER if Config.SMTP_USER else 'Not Set'}")
    
    if not Config.SMTP_USER or not Config.SMTP_PASSWORD:
        print("⚠️ Warning: SMTP credentials are missing in environment variables.")
        print("   Email features (Reports, Welcome Emails) will not work.")
    else:
        print("✅ SMTP Credentials: Present")
        # Optional: Try a dry-run connection
        try:
            import smtplib
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.quit()
            print("✅ SMTP Connection: Verified (Login Successful)")
        except Exception as e:
            print(f"❌ SMTP Connection Failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting System Health Check...")
    check_dependencies()
    check_db()
    check_email()
    print("\n✅ Health Check Complete")
