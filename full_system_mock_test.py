import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def run_full_mock_test():
    print("🚀 Starting Full Optimization System Test (Kitchen + VRP)...\n")
    
    # --- PHASE 1: KITCHEN SCHEDULING ---
    print("--- Phase 1: Kitchen Scheduling (Assigned Chefs) ---")
    now = datetime.now()
    kitchen_payload = {
        "now_dt": now.isoformat(),
        "chef_list": ["Chef_Master", "Chef_Junior"],
        "orders": [
            {
                "id": "ORDER_001",
                "is_processing": False,
                "deadline_dt": (now + timedelta(minutes=45)).isoformat(),
                "processing_time_mins": 15
            },
            {
                "id": "ORDER_002",
                "is_processing": False,
                "deadline_dt": (now + timedelta(minutes=30)).isoformat(),
                "processing_time_mins": 10
            },
            {
                "id": "ORDER_003",
                "is_processing": False,
                "deadline_dt": (now + timedelta(minutes=60)).isoformat(),
                "processing_time_mins": 20
            }
        ]
    }

    kitchen_res = requests.post(f"{BASE_URL}/schedule", json=kitchen_payload).json()
    schedule = kitchen_res.get('schedule', [])
    
    print(f"{'Order ID':<12} | {'Assigned Chef':<15} | {'Finish Time':<20}")
    print("-" * 55)
    for item in schedule:
        print(f"{item['OrderID']:<12} | {item['PIC']:<15} | {item['FinishedTime']}")
    
    # --- PHASE 2: VRP ROUTING ---
    print("\n--- Phase 2: Delivery Routing (Shipper Routes) ---")
    
    # Mocking a time matrix for 1 Store (0) and 3 Pickups/Deliveries
    # Pickup nodes: 1, 3, 5 | Delivery nodes: 2, 4, 6
    time_matrix = [
        [0,  0, 10,  0, 15,  0, 20], # 0: Store
        [0,  0, 10,  0, 15,  0, 20], # 1: Pickup 1
        [10, 10, 0, 10, 8, 10, 25],  # 2: Delivery 1
        [0,  0, 10,  0, 15,  0, 20], # 3: Pickup 2
        [15, 15, 8, 15,  0, 15, 12], # 4: Delivery 2
        [0,  0, 10,  0, 15,  0, 20], # 5: Pickup 3
        [20, 20, 25, 20, 12, 20,  0], # 6: Delivery 3
    ]

    vrp_payload = {
        "num_vehicles": 2,
        "starts": [0, 0],
        "ends": [0, 0],
        "time_matrix": time_matrix,
        "pickups_deliveries": [[1, 2], [3, 4], [5, 6]],
        "demands": [0, 1, -1, 1, -1, 1, -1],
        "vehicle_capacities": [4, 4],
        "time_windows": [
            [0, 1440], # Store
            [0, 30], [5, 60],  # Order 1
            [0, 30], [10, 60], # Order 2
            [0, 60], [20, 90], # Order 3
        ],
        "base_datetime": now.isoformat()
    }

    vrp_res = requests.post(f"{BASE_URL}/vrp", json=vrp_payload).json()
    
    current_shipper = -1
    for entry in vrp_res:
        if entry['shipper_id'] != current_shipper:
            current_shipper = entry['shipper_id']
            print(f"\n[SHIPPER {current_shipper} ROUTE]")
            print(f"{'Step':<5} | {'Node Type':<12} | {'Time':<18} | {'Load'}")
            print("-" * 55)
            step_count = 1

        node = entry['node']
        if node == 0:
            type_str = "STORE/DEPOT"
        elif node % 2 != 0:
            type_str = f"PICKUP (O{int((node+1)/2)})"
        else:
            type_str = f"DELIVERY (O{int(node/2)})"
            
        print(f"{step_count:<5} | {type_str:<12} | {entry['arrival_datetime']} | {entry['load_after_action']}")
        step_count += 1

if __name__ == "__main__":
    try:
        run_full_mock_test()
    except Exception as e:
        print(f"\n❌ Error: Ensure the FastAPI server is running (python3 main.py).\nDetails: {e}")
