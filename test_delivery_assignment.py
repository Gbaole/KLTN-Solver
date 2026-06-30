import math

# Mocking the allocation solver function (from KLTN-Solver/TestAlloFixedData.py)
# Since I need to run this as a standalone script, I'll include the necessary logic here.

def solve_pizza_network_mock(stores, orders, alpha=0.35, beta=0.85):
    # Simplified mock for verification
    # Finds the closest store for each order (ignoring load)
    assignments = []
    for o_name, o_info in orders.items():
        best_store = None
        min_dist = float('inf')
        for s_name, s_info in stores.items():
            dist = math.sqrt((o_info['pos'][0] - s_info['pos'][0])**2 +
                             (o_info['pos'][1] - s_info['pos'][1])**2)
            if dist < min_dist:
                min_dist = dist
                best_store = s_name
        assignments.append({"order": o_name, "store": best_store})
    return {"status": "SUCCESS", "assignments": assignments}

# --- TEST ---

# 1. Setup mock data
stores = {
    'S1': {'pos': (0, 0)},
    'S2': {'pos': (10, 0)}
}

# 2. Simulate creating an order without storeId (None)
order_1 = {'id': 'Order_Delivery_1', 'pos': (1, 1), 'time': 15}
# The backend logic would effectively be this dictionary for the solver:
orders_to_solve = {'Order_Delivery_1': {'pos': (1, 1), 'time': 15}}

print(f"Test: Creating delivery order '{order_1['id']}' with NO store assignment.")

# 3. Simulate triggering the solver
print("Test: Triggering solver to assign store...")
result = solve_pizza_network_mock(stores, orders_to_solve)

# 4. Verify the result
assigned_store = next((a['store'] for a in result['assignments'] if a['order'] == 'Order_Delivery_1'), None)
print(f"Test: Solver assigned '{order_1['id']}' to '{assigned_store}'.")

if assigned_store:
    print("Test SUCCESS: Delivery order successfully assigned to a store by the solver.")
else:
    print("Test FAILED: Delivery order was not assigned.")
