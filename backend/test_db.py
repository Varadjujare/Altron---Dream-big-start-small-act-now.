
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from pathlib import Path
import sys

env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

host = os.getenv('MYSQL_HOST', '').strip()
user = os.getenv('MYSQL_USER', '').strip()
pwd = os.getenv('MYSQL_PASSWORD', '').strip()
port_str = os.getenv('MYSQL_PORT', '').strip()
database = os.getenv('MYSQL_DATABASE', '').strip()

print(f"DEBUG: Host='{host}'")
print(f"DEBUG: Port='{port_str}'")
print(f"DEBUG: User='{user}'")
# print(f"DEBUG: Pwd='{pwd}'") # don't print pwd

try:
    port = int(port_str)
except ValueError:
    print(f"❌ Invalid port: '{port_str}'")
    sys.exit(1)

print("-" * 20)
print("TEST 1: Standard Connection")
try:
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=pwd,
        port=port,
        database=database,
        connection_timeout=5
    )
    if connection.is_connected():
        print("✅ TEST 1 Successful!")
        connection.close()
except Error as e:
    print(f"❌ TEST 1 Failed: {e}")
    # print(f"Error Code: {e.errno}")
except Exception as e:
    print(f"❌ TEST 1 Exception: {type(e).__name__}: {e}")

print("-" * 20)
print("TEST 2: Connection with ssl_disabled=True (Expect Failure if SSL Required)")
try:
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=pwd,
        port=port,
        database=database,
        connection_timeout=5,
        ssl_disabled=True
    )
    if connection.is_connected():
        print("✅ TEST 2 Successful!")
        connection.close()
except Error as e:
    print(f"❌ TEST 2 Failed: {e}")
except Exception as e:
    print(f"❌ TEST 2 Exception: {type(e).__name__}: {e}")
