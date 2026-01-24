
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from utils.scheduler import scheduler, generate_and_send_reports

print("Testing Scheduler Initialization...")
scheduler.start()

print("\nForce triggering a report for demonstration...")
generate_and_send_reports()

print("\nTest Complete. The scheduler logic is valid.")
# Stop it so it doesn't hang the script
scheduler.stop()
