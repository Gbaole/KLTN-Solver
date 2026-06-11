from VRP_DTime import solve_full_pizza_vrptw_with_datetime

# 2 shippers, capacity 4, 10 orders
data = {
    'num_vehicles': 2,
    'starts': [0, 0],
    'ends': [0, 0],
    'time_matrix': [[0] * 21 for _ in range(21)], # 1 depot + 10 pickup + 10 delivery
    'pickups_deliveries': [[2*i+1, 2*i+2] for i in range(10)],
    'demands': [0] + [1, -1] * 10,
    'vehicle_capacities': [4, 4],
    'time_windows': [(0, 1440)] * 21
}

result = solve_full_pizza_vrptw_with_datetime(data)
print(f"Result with 10 orders, capacity 4+4=8: {len(result)} steps")

data['vehicle_capacities'] = [5, 5]
result = solve_full_pizza_vrptw_with_datetime(data)
print(f"Result with 10 orders, capacity 5+5=10: {len(result)} steps")
