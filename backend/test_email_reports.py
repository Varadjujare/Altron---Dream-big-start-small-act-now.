"""
Email Report Verification Test Script
Tests all new email report features including visualizations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.report_generator import report_generator
from utils.email_service import email_service
import datetime

def test_data_methods(user_id=1):
    """Test all new data fetching methods."""
    print("\n" + "="*60)
    print("TESTING DATA FETCHING METHODS")
    print("="*60)
    
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)
    month_ago = today - datetime.timedelta(days=30)
    
    # Test 1: Productivity Scores
    print("\n📈 Testing get_productivity_scores()...")
    try:
        productivity = report_generator.get_productivity_scores(user_id, week_ago, today)
        print(f"✅ SUCCESS: Average score = {productivity.get('average_score', 0)}%")
        print(f"   Scores count: {len(productivity.get('scores', []))}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # Test 2: Habit Strength
    print("\n💪 Testing get_habit_strength()...")
    try:
        strength = report_generator.get_habit_strength(user_id)
        habits_count = len(strength.get('habits', []))
        print(f"✅ SUCCESS: Found {habits_count} habits")
        if habits_count > 0:
            top_habit = strength['habits'][0]
            print(f"   Top habit: {top_habit['habit_name']} (score: {top_habit['consistency_score']})")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # Test 3: Correlations
    print("\n🔗 Testing get_correlations()...")
    try:
        correlations = report_generator.get_correlations(user_id, days=7)
        corr_count = len(correlations.get('correlations', []))
        print(f"✅ SUCCESS: Found {corr_count} correlations")
        if corr_count > 0:
            top_corr = correlations['correlations'][0]
            print(f"   Top: {top_corr['habit1']} ↔ {top_corr['habit2']} ({round(top_corr['correlation']*100)}%)")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # Test 4: Heatmap Data
    print("\n📅 Testing get_heatmap_data()...")
    try:
        heatmap = report_generator.get_heatmap_data(user_id, days=30)
        data_count = len(heatmap.get('data', []))
        print(f"✅ SUCCESS: Generated {data_count} days of heatmap data")
        if data_count > 0:
            sample = heatmap['data'][0]
            print(f"   Sample: {sample['date']} - Level {sample['level']} ({sample['percentage']}%)")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # Test 5: Comparison Stats
    print("\n📊 Testing get_comparison_stats()...")
    try:
        comparison = report_generator.get_comparison_stats(user_id, period="weekly")
        changes = comparison.get('changes', {})
        print(f"✅ SUCCESS: Habits change = {changes.get('habits', 0)}%, Tasks change = {changes.get('tasks', 0)}%")
    except Exception as e:
        print(f"❌ FAILED: {e}")

def test_html_generation(user_id=1):
    """Test HTML report generation."""
    print("\n" + "="*60)
    print("TESTING HTML REPORT GENERATION")
    print("="*60)
    
    # Test Weekly Report
    print("\n📧 Generating Weekly Report HTML...")
    try:
        weekly_html = report_generator.generate_html_report(user_id, "weekly")
        
        # Check for required sections
        checks = {
            "Period Comparison": "📊 Period Comparison" in weekly_html,
            "Productivity Score": "📈 Productivity Score" in weekly_html,
            "Habit Strength": "💪 Habit Strength Analysis" in weekly_html,
            "Progress Chart": "📊 Progress Chart" in weekly_html,
            "Habit Breakdown": "✅ Habit Breakdown" in weekly_html,
            "Correlations": "🔗 Habit Correlations" in weekly_html,
            "Heatmap (should NOT appear)": "📅 30-Day Activity Heatmap" not in weekly_html,
        }
        
        print("\nSection Checks:")
        for section, present in checks.items():
            status = "✅" if present else "❌"
            print(f"  {status} {section}")
        
        all_passed = all(checks.values())
        if all_passed:
            print("\n✅ Weekly Report: ALL CHECKS PASSED")
        else:
            print("\n⚠️ Weekly Report: SOME CHECKS FAILED")
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Monthly Report
    print("\n📧 Generating Monthly Report HTML...")
    try:
        monthly_html = report_generator.generate_html_report(user_id, "monthly")
        
        # Check for required sections
        checks = {
            "Period Comparison": "📊 Period Comparison" in monthly_html,
            "Productivity Score": "📈 Productivity Score" in monthly_html,
            "Habit Strength": "💪 Habit Strength Analysis" in monthly_html,
            "Progress Chart": "📊 Progress Chart" in monthly_html,
            "Habit Breakdown": "✅ Habit Breakdown" in monthly_html,
            "Correlations": "🔗 Habit Correlations" in monthly_html,
            "Heatmap (SHOULD appear)": "📅 30-Day Activity Heatmap" in monthly_html,
        }
        
        print("\nSection Checks:")
        for section, present in checks.items():
            status = "✅" if present else "❌"
            print(f"  {status} {section}")
        
        all_passed = all(checks.values())
        if all_passed:
            print("\n✅ Monthly Report: ALL CHECKS PASSED")
        else:
            print("\n⚠️ Monthly Report: SOME CHECKS FAILED")
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

def test_email_service():
    """Test email service configuration."""
    print("\n" + "="*60)
    print("TESTING EMAIL SERVICE CONFIGURATION")
    print("="*60)
    
    print(f"\n📧 Email Service Configured: {email_service.is_configured}")
    if email_service.is_configured:
        print(f"   SMTP Host: {email_service.smtp_host}")
        print(f"   SMTP Port: {email_service.smtp_port}")
        print(f"   From Email: {email_service.from_email}")
        print("   ✅ Email service is ready")
    else:
        print("   ⚠️ Email service NOT configured - emails will not send")

def main():
    """Run all verification tests."""
    print("\n" + "="*60)
    print("EMAIL REPORT VERIFICATION TEST SUITE")
    print("="*60)
    print(f"Run Time: {datetime.datetime.now()}")
    
    # Get user ID to test (default to first user)
    from utils.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print("\n❌ NO USERS FOUND IN DATABASE")
        print("   Create at least one user to run tests")
        return
    
    user_id = result[0]
    print(f"\nTesting with User ID: {user_id}")
    
    # Run all tests
    test_email_service()
    test_data_methods(user_id)
    test_html_generation(user_id)
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    print("\nNext Steps:")
    print("1. Review test results above")
    print("2. If all tests pass, the email reports are ready")
    print("3. Test actual email delivery if SMTP is configured")
    print("\nTo send a test email, use:")
    print("  python -c \"from backend.utils.scheduler import generate_and_send_reports; generate_and_send_reports('weekly')\"")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
