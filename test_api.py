import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_root():
    print("Testing Root Endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_network():
    print("Testing Network Optimization Endpoint...")
    response = requests.get(f"{BASE_URL}/network")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success: Received network optimization results.\n")
    else:
        print(f"Error: {response.text}\n")

def test_vrp():
    print("Testing VRP Optimization Endpoint...")
    response = requests.get(f"{BASE_URL}/vrp")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Success: Received {len(response.json())} route entries.\n")
    else:
        print(f"Error: {response.text}\n")

def test_schedule():
    print("Testing Scheduling Endpoint...")
    payload = {
        "now_dt": "2026-05-10T13:05:00",
        "chef_list": ["Chef_A", "Chef_B"],
        "orders": [
            {
                "id": "Order_1_Margherita",
                "is_processing": True,
                "pic": "Chef_A",
                "finished_time_dt": "2026-05-10T13:10:00",
                "deadline_dt": "2026-05-10T13:20:00",
                "processing_time_mins": 10
            },
            {
                "id": "Order_3_Veggie",
                "is_processing": False,
                "deadline_dt": "2026-05-10T13:45:00",
                "processing_time_mins": 10
            }
        ]
    }
    response = requests.post(f"{BASE_URL}/schedule", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success: Received schedule results.\n")
    else:
        print(f"Error: {response.text}\n")

if __name__ == "__main__":
    print("Note: Ensure the FastAPI server is running (python3 main.py) before running this test.\n")
    # Uncomment to run if server is active
    test_root()
    test_network()
    test_vrp()
    test_schedule()
