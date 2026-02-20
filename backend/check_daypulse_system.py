"""
LifeSync System Health Check - ASCII safe output
Run from: e:\Program Files\LifeSync\backend\
"""

import smtplib
import os

errors = []
warnings = []
results = []

sep = "=" * 60

def ok(msg):
    results.append("[OK]  " + msg)

def fail(msg):
    errors.append("[FAIL] " + msg)

def warn(msg):
    warnings.append("[WARN] " + msg)

print()
print(sep)
print("  LIFESYNC COMPLETE SYSTEM HEALTH CHECK")
print(sep)

# ----------------------------------------------------------
# 1. FILE EXISTENCE
# ----------------------------------------------------------
print("\n[1/5] File Structure")

files_to_check = {
    "utils/ai_day_pulse.py":         "Day Pulse AI module",
    "utils/email_service.py":        "Email service",
    "utils/scheduler.py":            "Scheduler",
    "utils/db.py":                   "Database utils",
    "utils/report_generator.py":     "PDF report generator",
    "routes/analytics.py":           "Analytics routes",
    "routes/reports.py":             "Reports routes",
    "routes/auth.py":                "Auth routes",
    "models/user.py":                "User model",
    "models/habit.py":               "Habit model",
    "models/task.py":                "Task model",
    "config.py":                     "App config",
    "app.py":                        "Flask app entry",
    "requirements.txt":              "Requirements",
    ".env":                          ".env file",
    "../frontend/analytics.html":    "Analytics frontend",
}

for path, label in files_to_check.items():
    if os.path.exists(path):
        ok(label + " (" + path + ")")
    else:
        fail("MISSING: " + label + " (" + path + ")")

# ----------------------------------------------------------
# 2. CODE CONTENT CHECKS
# ----------------------------------------------------------
print("\n[2/5] Code Content Checks")

checks = [
    ("utils/ai_day_pulse.py",       "def generate_day_pulse_report",  "generate_day_pulse_report function"),
    ("utils/ai_day_pulse.py",       "def get_user_30day_data",         "get_user_30day_data function"),
    ("utils/ai_day_pulse.py",       "llama-3.3-70b-versatile",         "Primary Groq model (70B)"),
    ("utils/ai_day_pulse.py",       "llama-3.1-8b-instant",            "Fallback Groq model (8B)"),
    ("utils/email_service.py",      "def send_day_pulse_report",       "send_day_pulse_report method"),
    ("utils/email_service.py",      "def send_welcome_email",          "send_welcome_email method"),
    ("utils/email_service.py",      "def send_email",                  "send_email core method"),
    ("utils/email_service.py",      "Day Pulse Report",                "Email HTML template"),
    ("utils/email_service.py",      "Power Combo",                     "Power Combo card in email"),
    ("utils/email_service.py",      "Kryptonite",                      "Kryptonite card in email"),
    ("utils/email_service.py",      "Hidden Insight",                  "Hidden Insight card in email"),
    ("utils/email_service.py",      "Tomorrow",                        "Prediction card in email"),
    ("utils/scheduler.py",          "def generate_and_send_day_pulse", "Day Pulse batch function"),
    ("utils/scheduler.py",          "pulse_hour = 22",                 "10 PM nightly trigger"),
    ("utils/scheduler.py",          "def trigger_day_pulse_now",       "Manual test trigger"),
    ("utils/scheduler.py",          "last_pulse_run",                  "Dedup guard (no double-send)"),
    ("utils/scheduler.py",          "generate_and_send_reports",       "Weekly/Monthly reports intact"),
    ("config.py",                   "GROQ_API_KEY",                    "GROQ_API_KEY in config"),
    ("requirements.txt",            "groq",                            "groq in requirements.txt"),
    (".env",                        "GROQ_API_KEY",                    "GROQ_API_KEY in .env"),
    (".env",                        "SMTP_USER",                       "SMTP_USER in .env"),
    (".env",                        "SMTP_PASSWORD",                   "SMTP_PASSWORD in .env"),
    ("../frontend/analytics.html",  "Day Pulse",                       "Day Pulse card in frontend"),
    ("../frontend/analytics.html",  "pulseBorder",                     "Pulse animation CSS"),
    ("../frontend/analytics.html",  "AI Powered",                      "AI badge on card"),
    ("../frontend/analytics.html",  "10:00 PM",                        "Schedule text on card"),
]

for filepath, needle, label in checks:
    if not os.path.exists(filepath):
        warn("Skipped (file missing): " + label)
        continue
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    if needle in content:
        ok(label)
    else:
        fail("NOT FOUND in " + filepath + ": " + label + " (searched: '" + needle + "')")

# ----------------------------------------------------------
# 3. ENV KEY VALUES
# ----------------------------------------------------------
print("\n[3/5] Environment Variables")

with open(".env", "r") as f:
    env_lines = f.read()

smtp_user = smtp_pass = groq_key = ""
for line in env_lines.splitlines():
    if line.startswith("SMTP_USER="):
        smtp_user = line.split("=", 1)[1].strip()
    elif line.startswith("SMTP_PASSWORD="):
        smtp_pass = line.split("=", 1)[1].strip()
    elif line.startswith("GROQ_API_KEY="):
        groq_key = line.split("=", 1)[1].strip()

if smtp_user and "@" in smtp_user:
    ok("SMTP_USER configured: " + smtp_user)
else:
    fail("SMTP_USER missing or invalid: '" + smtp_user + "'")

if smtp_pass and len(smtp_pass) > 8:
    ok("SMTP_PASSWORD configured: ********")
else:
    fail("SMTP_PASSWORD missing or too short")

if groq_key and groq_key != "your_groq_api_key_here":
    ok("GROQ_API_KEY configured: " + groq_key[:8] + "...")
else:
    warn("GROQ_API_KEY is still placeholder! Day Pulse reports won't send.")
    warn("Get your FREE key at: https://console.groq.com then update .env + Render env vars")

# ----------------------------------------------------------
# 4. SMTP LIVE CONNECTION TEST
# ----------------------------------------------------------
print("\n[4/5] SMTP Email Connection Test")

try:
    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(smtp_user, smtp_pass)
    server.quit()
    ok("SMTP Gmail connection SUCCESSFUL (TLS, port 587) - Email service is LIVE")
except smtplib.SMTPAuthenticationError:
    fail("SMTP auth failed - check SMTP_USER and SMTP_PASSWORD in .env")
except Exception as e:
    fail("SMTP test failed: " + type(e).__name__ + ": " + str(e))

# ----------------------------------------------------------
# 5. GROQ PACKAGE
# ----------------------------------------------------------
print("\n[5/5] Groq AI Package")

try:
    import groq as groq_pkg
    ok("groq package installed: v" + groq_pkg.__version__)
    from groq import Groq
    ok("Groq client class importable - ready to use")
except ImportError as e:
    fail("groq not installed: " + str(e) + " -- run: pip install groq==0.9.0")
except Exception as e:
    fail("groq import error: " + str(e))

# ----------------------------------------------------------
# SUMMARY
# ----------------------------------------------------------
print()
print(sep)
print("  RESULTS SUMMARY")
print(sep)
for r in results:
    print(r)

if warnings:
    print()
    for w in warnings:
        print(w)

if errors:
    print()
    print("  ISSUES FOUND (" + str(len(errors)) + "):")
    for e in errors:
        print(e)
    print()
    print("  Some checks failed. See details above.")
else:
    print()
    if warnings:
        print("  All checks PASSED with " + str(len(warnings)) + " warning(s).")
        print("  Action required: Set GROQ_API_KEY to activate Day Pulse.")
    else:
        print("  ALL CHECKS PASSED - System is fully healthy!")

print(sep)
print()
