import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_dynamic_vrp():
    print("Testing Dynamic VRP Optimization Endpoint...")
    
    # Simulation: 1 Store (node 0), 2 Shippers, 3 Orders
    # Nodes:
    # 0: Store
    # 1: Order A Pickup (at Store)
    # 2: Order A Delivery (Customer A)
    # 3: Order B Pickup (at Store)
    # 4: Order B Delivery (Customer B)
    # 5: Order C Pickup (at Store)
    # 6: Order C Delivery (Customer C)
    
    # Realistic time matrix (minutes)
    # Distances from store (0) to deliveries: A=15, B=10, C=25
    time_matrix = [
        [0,  0, 15,  0, 10,  0, 25], # 0: Store
        [0,  0, 15,  0, 10,  0, 25], # 1: Pickup A (same as store)
        [15, 15, 0, 15, 12, 15, 30], # 2: Delivery A
        [0,  0, 15,  0, 10,  0, 25], # 3: Pickup B (same as store)
        [10, 10, 12, 10,  0, 10, 20], # 4: Delivery B
        [0,  0, 15,  0, 10,  0, 25], # 5: Pickup C (same as store)
        [25, 25, 30, 25, 20, 25,  0], # 6: Delivery C
    ]

    payload = {
        "num_vehicles": 2,
        "starts": [0, 0],
        "ends": [0, 0],
        "time_matrix": time_matrix,
        "pickups_deliveries": [[1, 2], [3, 4], [5, 6]],
        "demands": [0, 1, -1, 1, -1, 1, -1],
        "vehicle_capacities": [4, 4],
        "time_windows": [
            [0, 1440], # Depot
            [0, 30],   # Pickup A window
            [10, 60],  # Delivery A window
            [0, 30],   # Pickup B window
            [5, 45],   # Delivery B window
            [0, 60],   # Pickup C window
            [20, 90],  # Delivery C window
        ],
        "base_datetime": datetime.now().isoformat()
    }

    try:
        response = requests.post(f"{BASE_URL}/vrp", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"Success: Received {len(results)} route entries.\n")
            
            # Format and print the results
            current_shipper = -1
            for entry in results:
                if entry['shipper_id'] != current_shipper:
                    current_shipper = entry['shipper_id']
                    print(f"\n--- Shipper {current_shipper} Route ---")
                
                node_type = "Depot/Store" if entry['node'] == 0 else ("Pickup" if entry['node'] % 2 != 0 else "Delivery")
                print(f"Node {entry['node']} ({node_type}): Arrive at {entry['arrival_datetime']}, Load: {entry['load_after_action']}, Travel: {entry['travel_time_minutes']} min")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    print("Starting Mockup VRP Test...")
    test_dynamic_vrp()
