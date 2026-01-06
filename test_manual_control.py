"""
Test Script for Endpoint-Based Device Control

Binary servo control - the endpoint IS the command:
- POST /activate_servo → activates servo
- POST /stop_servo → stops servo  
- POST /control/executed → marks executed
- POST /control/failed → marks failed

No control_command or status fields needed!

Usage:
    python test_manual_control.py
"""

import requests
from requests.auth import HTTPBasicAuth
import time
import json

# Configuration
BASE_URL = "http://localhost:8080/api"
DEVICE_CODE = "test"  # Change to your device code
PASSWORD = "123"      # Change to your device password

# Authentication
auth = HTTPBasicAuth(DEVICE_CODE, PASSWORD)


def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)


def test_activate_servo(message="Activating servo"):
    """Test activating servo - endpoint IS the command"""
    url = f"{BASE_URL}/device/{DEVICE_CODE}/activate_servo"
    data = {"message": message}
    
    response = requests.post(url, auth=auth, data=data)
    print_response("ACTIVATE SERVO", response)
    return response


def test_stop_servo(message="Stopping servo"):
    """Test stopping servo - endpoint IS the command"""
    url = f"{BASE_URL}/device/{DEVICE_CODE}/stop_servo"
    data = {"message": message}
    
    response = requests.post(url, auth=auth, data=data)
    print_response("STOP SERVO", response)
    return response


def test_poll_control():
    """Test polling for control command (IoT perspective)"""
    url = f"{BASE_URL}/device/{DEVICE_CODE}/control"
    
    response = requests.get(url, auth=auth)
    print_response("POLL CONTROL (IoT)", response)
    return response


def test_mark_executed(message="Command executed successfully"):
    """Test marking control as executed - endpoint IS the status"""
    url = f"{BASE_URL}/device/{DEVICE_CODE}/control/executed"
    data = {"message": message}
    
    response = requests.post(url, auth=auth, data=data)
    print_response("MARK AS EXECUTED", response)
    return response


def test_mark_failed(message="Command execution failed"):
    """Test marking control as failed - endpoint IS the status"""
    url = f"{BASE_URL}/device/{DEVICE_CODE}/control/failed"
    data = {"message": message}
    
    response = requests.post(url, auth=auth, data=data)
    print_response("MARK AS FAILED", response)
    return response


def test_get_control_status():
    """Test getting current control status"""
    url = f"{BASE_URL}/device/{DEVICE_CODE}/control/status"
    
    response = requests.get(url, auth=auth)
    print_response("GET CONTROL STATUS", response)
    return response


def simulate_iot_flow():
    """
    Simulate complete IoT flow:
    1. Admin activates servo (via endpoint)
    2. IoT polls and gets command
    3. IoT executes command
    4. IoT marks as executed (via endpoint)
    """
    print("\n" + "="*60)
    print("SIMULATING COMPLETE IoT FLOW")
    print("="*60)
    
    # Step 1: Admin activates servo - ENDPOINT IS THE COMMAND
    print("\n[ADMIN] Calling /activate_servo endpoint")
    response = test_activate_servo("Manual override from admin")
    
    if response.status_code != 200:
        print("❌ Failed to activate servo!")
        return
    
    time.sleep(1)
    
    # Step 2: IoT polls
    print("\n[IoT] Polling for control command...")
    response = test_poll_control()
    
    if response.status_code != 200:
        print("❌ Polling failed!")
        return
    
    control = response.json()
    
    # Step 3: Check mode and execute
    if control["mode"] == "MANUAL" and control["status"] == "PENDING":
        command = control["command"]
        print(f"\n[IoT] 🔧 MANUAL MODE - Executing: {command}")
        print(f"[IoT] Message: {control.get('message', 'N/A')}")
        
        # Simulate servo execution
        print(f"[IoT] Activating servo...")
        time.sleep(2)
        print(f"[IoT] ✓ Servo command executed successfully")
        
        # Step 4: Mark as executed - ENDPOINT IS THE STATUS
        print(f"\n[IoT] Calling /control/executed endpoint")
        test_mark_executed("Servo activated at " + time.strftime("%H:%M:%S"))
        
    elif control["mode"] == "AUTO":
        action = control["command"]
        print(f"\n[IoT] 🤖 AUTO MODE - Executing: {action}")
        print(f"[IoT] Running automatic control logic...")
        time.sleep(1)
        print(f"[IoT] ✓ Automatic action executed")
    
    print("\n[IoT] Flow completed!")
    
    # Check final status
    time.sleep(1)
    print("\n[VERIFY] Checking final control status...")
    test_get_control_status()


def run_full_test():
    """Run complete test suite"""
    print("\n" + "="*60)
    print("ENDPOINT-BASED CONTROL - FULL TEST")
    print("="*60)
    
    # Test 1: Check current status
    print("\n\nTest 1: Check initial control status")
    print("-" * 60)
    test_get_control_status()
    
    # Test 2: Poll without control (AUTO mode expected)
    print("\n\nTest 2: Poll without control set (AUTO mode)")
    print("-" * 60)
    test_poll_control()
    
    time.sleep(1)
    
    # Test 3: Activate servo via endpoint
    print("\n\nTest 3: Call /activate_servo endpoint")
    print("-" * 60)
    response = test_activate_servo("Testing endpoint-based control")
    
    if response.status_code == 200:
        time.sleep(1)
        
        # Test 4: Poll with control set (MANUAL mode expected)
        print("\n\nTest 4: Poll with servo activated")
        print("-" * 60)
        test_poll_control()
        
        time.sleep(1)
        
        # Test 5: Mark as executed via endpoint
        print("\n\nTest 5: Call /control/executed endpoint")
        print("-" * 60)
        test_mark_executed("Servo activated successfully")
        
        time.sleep(1)
        
        # Test 6: Check status after execution
        print("\n\nTest 6: Check status after execution")
        print("-" * 60)
        test_get_control_status()
        
        time.sleep(1)
        
        # Test 7: Poll again (should be AUTO mode now)
        print("\n\nTest 7: Poll after execution")
        print("-" * 60)
        test_poll_control()
    
    # Test 8: Test FAILED status
    print("\n\nTest 8: Stop servo and report failure")
    print("-" * 60)
    test_stop_servo("Testing stop command")
    time.sleep(1)
    test_mark_failed("Servo timeout error")
    time.sleep(1)
    test_get_control_status()
    
    print("\n\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)


def interactive_menu():
    """Interactive test menu"""
    while True:
        print("\n" + "="*60)
        print("ENDPOINT-BASED CONTROL - TEST MENU")
        print("="*60)
        print("1. POST /activate_servo - Activate servo")
        print("2. POST /stop_servo - Stop servo")
        print("3. GET /control - Poll for control (IoT)")
        print("4. POST /control/executed - Mark as executed")
        print("5. POST /control/failed - Mark as failed")
        print("6. GET /control/status - Get status")
        print("7. Simulate complete IoT flow")
        print("8. Run full test suite")
        print("q. Exit")
        print("="*60)
        
        choice = input("\nSelect option: ").strip().lower()
        
        if choice == "1":
            msg = input("Message (optional): ").strip()
            test_activate_servo(msg if msg else "Activating servo")
        elif choice == "2":
            msg = input("Message (optional): ").strip()
            test_stop_servo(msg if msg else "Stopping servo")
        elif choice == "3":
            test_poll_control()
        elif choice == "4":
            msg = input("Success message: ").strip()
            test_mark_executed(msg if msg else "Command executed successfully")
        elif choice == "5":
            msg = input("Error message: ").strip()
            test_mark_failed(msg if msg else "Command failed")
        elif choice == "6":
            test_get_control_status()
        elif choice == "7":
            simulate_iot_flow()
        elif choice == "8":
            run_full_test()
        elif choice == "q":
            print("\nExiting...")
            break
        else:
            print("\n❌ Invalid option!")


if __name__ == "__main__":
    import sys
    
    print("""
╔════════════════════════════════════════════════════════════╗
║      ENDPOINT-BASED CONTROL - TEST SCRIPT                 ║
║                                                            ║
║  Binary servo control - endpoint IS the command:          ║
║  - POST /activate_servo → activates servo                 ║
║  - POST /stop_servo → stops servo                         ║
║  - POST /control/executed → marks executed                ║
║  - POST /control/failed → marks failed                    ║
║                                                            ║
║  No control_command or status fields required!            ║
║  The endpoint itself IS the action.                       ║
║                                                            ║
║  CREDENTIALS:                                              ║
║  - Device Code: test                                       ║
║  - Password: 123                                           ║
║  - Auth: HTTP Basic Authentication                         ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print(f"✓ Server is running at {BASE_URL}")
        else:
            print(f"❌ Server responded with status {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print(f"   Make sure server is running at {BASE_URL}")
        sys.exit(1)
    
    # Run interactive menu
    interactive_menu()
