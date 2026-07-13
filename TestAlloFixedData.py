from ortools.linear_solver import pywraplp
import math


def solve_pizza_network_v2(stores, orders, alpha=0.35, beta=0.85):
    # Pre-calculate Distance Matrix
    dist_matrix = {}
    for o_name, o_info in orders.items():
        dist_matrix[o_name] = {}
        for s_name, s_info in stores.items():
            d = math.sqrt((o_info['pos'][0] - s_info['pos'][0])**2 +
                          (o_info['pos'][1] - s_info['pos'][1])**2)
            dist_matrix[o_name][s_name] = round(d, 2)

    # --- 2. NORMALIZATION FACTORS ---
    all_dists = [dist_matrix[o][s] for o in orders for s in stores]
    avg_dist = sum(all_dists) / len(all_dists) if all_dists else 1.0
    if avg_dist == 0:
        avg_dist = 1.0

    total_order_time = sum(orders[o]['time'] for o in orders)
    avg_w_max = (sum(stores[s]['init'] for s in stores) / len(stores) +
                 total_order_time / len(stores))

    # --- 3. SOLVER CONFIG ---
    solver = pywraplp.Solver.CreateSolver('SCIP')
    x = {}
    for o in orders:
        for s in stores:
            x[o, s] = solver.IntVar(0, 1, f'x_{o}_{s}')
    w_max = solver.NumVar(0, solver.infinity(), 'w_max')

    # --- 4. CONSTRAINTS ---
    for o in orders:
        solver.Add(solver.Sum([x[o, s] for s in stores]) == 1)

    for s in stores:
        total_time = stores[s]['init'] + \
            solver.Sum([x[o, s] * orders[o]['time'] for o in orders])
        solver.Add(total_time <= w_max)

    # --- 5. OBJECTIVE (normalized) ---
    total_network_dist = solver.Sum(
        [x[o, s] * dist_matrix[o][s] for o in orders for s in stores])
    solver.Minimize(alpha * (total_network_dist / avg_dist) +
                    beta * (w_max / avg_w_max))

    # --- 5. EXECUTION & DETAILED OUTPUT ---
    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        results = {
            "status": "SUCCESS",
            "global_objective_score": solver.Objective().Value(),
            "network_bottleneck_w_max": w_max.solution_value(),
            "assignments": [],
            "store_monitoring": []
        }

        for o in orders:
            for s in stores:
                if x[o, s].solution_value() > 0.5:
                    results["assignments"].append({
                        "order": o,
                        "store": s,
                        "distance_km": dist_matrix[o][s],
                        "time_min": orders[o]['time']
                    })

        grand_total_dist = 0
        for s in stores:
            added_load = sum(orders[o]['time']
                             for o in orders if x[o, s].solution_value() > 0.5)
            final_load = stores[s]['init'] + added_load
            store_dist = sum(dist_matrix[o][s]
                             for o in orders if x[o, s].solution_value() > 0.5)
            grand_total_dist += store_dist

            results["store_monitoring"].append({
                "store": s,
                "init_load": stores[s]['init'],
                "added_load": added_load,
                "final_load": final_load,
                "total_dist": store_dist
            })
        
        results["total_added_load"] = sum(o['time'] for o in orders.values())
        results["total_dist"] = grand_total_dist
        return results
    else:
        return {"status": "FAILED", "message": "Solver failed to find an optimal solution."}


if __name__ == "__main__":
    # --- 1. DATASET SETUP (15 Orders, 3 Stores) ---
    stores = {
        'S1': {'pos': (0, 0), 'init': 20},
        'S2': {'pos': (10, 0), 'init': 50},  # Heavy Initial Load
        'S3': {'pos': (5, 8), 'init': 15}
    }

    # Deterministic Order Placements
    # (x, y, processing_time)
    order_data = [
        (1, 1, 15), (1, 2, 20), (0, 1, 10), (2, 1, 12), (1, 0, 18),
        (9, 1, 15), (10, 2, 20), (11, 1, 25), (9, 0, 12), (10, 1, 10),
        (5, 7, 20), (6, 8, 15), (4, 8, 22), (5, 9, 10), (5, 6, 18)
    ]
    orders = {f'Order_{i+1}': {'pos': (d[0], d[1]), 'time': d[2]}
              for i, d in enumerate(order_data)}
    res = solve_pizza_network_v2(stores, orders)
    print(res)
