from datetime import datetime, timedelta
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def solve_full_pizza_vrptw_with_datetime(data, base_datetime=None):
    """
    Solves VRP with Time Windows using dynamic input data.
    'data' should contain: num_vehicles, starts, ends, time_matrix, pickups_deliveries, demands, vehicle_capacities, time_windows
    """
    print(f"[VRP Solver] Starting solve with {data['num_vehicles']} vehicles and {len(data['time_matrix'])} nodes...")
    
    # =========================================================================
    # 2. MODEL INITIALIZATION (Standard OR-Tools Setup)
    # =========================================================================
    print("[VRP Solver] Initializing RoutingIndexManager...")
    manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']), data['num_vehicles'], data['starts'], data['ends'])
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        return data['time_matrix'][manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        return data['demands'][manager.IndexToNode(from_index)]

    print("[VRP Solver] Adding Dimensions (Capacity & Time)...")
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(demand_callback_index, 0, data['vehicle_capacities'], True, 'Capacity')

    routing.AddDimension(transit_callback_index, 0, 1440, False, 'Time') # Increased horizon to 1440 mins
    time_dimension = routing.GetDimensionOrDie('Time')

    print("[VRP Solver] Setting Time Windows...")
    for node, (earliest, latest) in enumerate(data['time_windows']):
        index = manager.NodeToIndex(node)
        time_dimension.CumulVar(index).SetMin(earliest)
        time_dimension.SetCumulVarSoftUpperBound(index, latest, 1000)

    print("[VRP Solver] Adding global span cost coefficient to balance routes across shippers...")
    time_dimension.SetGlobalSpanCostCoefficient(5000)

    print("[VRP Solver] Adding Pickups and Deliveries constraints...")
    for request in data['pickups_deliveries']:
        p_idx, d_idx = manager.NodeToIndex(request[0]), manager.NodeToIndex(request[1])
        routing.AddPickupAndDelivery(p_idx, d_idx)
        routing.solver().Add(routing.VehicleVar(p_idx) == routing.VehicleVar(d_idx))
        routing.solver().Add(time_dimension.CumulVar(p_idx) <= time_dimension.CumulVar(d_idx))

    # =========================================================================
    # 3. SOLVE & GENERATE DATETIME SEQUENCE
    # =========================================================================
    print("[VRP Solver] Setting search parameters and solving...")
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.seconds = 25

    solution = routing.SolveWithParameters(search_params)

    results_sequence = []
    # Using provided base_datetime or 'now' as the origin of time
    if base_datetime is None:
        base_datetime = datetime.now().replace(second=0, microsecond=0)

    if solution:
        print("[VRP Solver] Solution found! Formatting results...")
        for vehicle_id in range(data['num_vehicles']):
            index = routing.Start(vehicle_id)
            previous_time_mins = 0
            
            while True:
                node_index = manager.IndexToNode(index)
                time_var = time_dimension.CumulVar(index)
                load_var = routing.GetDimensionOrDie('Capacity').CumulVar(index)
                
                arr_mins = solution.Value(time_var)
                arr_dt = base_datetime + timedelta(minutes=arr_mins)
                
                # Load logic: Current cumulative load + node action
                load_before = solution.Value(load_var)
                action_demand = data['demands'][node_index]
                load_after = load_before + action_demand
                
                # Travel time from the previous node in the sequence
                travel_time_to_node = arr_mins - previous_time_mins
                
                # Lateness calculation (Arrival vs Target Upper Bound)
                target_latest_mins = data['time_windows'][node_index][1]
                lateness_val = "0:00:00"
                if arr_mins > target_latest_mins:
                    lateness_delta = timedelta(minutes=(arr_mins - target_latest_mins))
                    lateness_val = str(lateness_delta)

                results_sequence.append({
                    "shipper_id": vehicle_id,
                    "node": node_index,
                    "arrival_datetime": arr_dt.strftime("%Y-%m-%d %H:%M"),
                    "load_after_action": str(load_after) if not routing.IsEnd(index) else "Finished",
                    "action_amount": action_demand,
                    "travel_time_minutes": int(travel_time_to_node),
                    "lateness": lateness_val
                })
                
                if routing.IsEnd(index): break
                previous_time_mins = arr_mins
                index = solution.Value(routing.NextVar(index))
                
    return results_sequence

# Default fallback data for local testing
DEFAULT_MOCK_DATA = {
    'num_vehicles': 2,
    'starts': [0, 1],
    'ends': [0, 1],
    'time_matrix': [
        [0,  12,  0,  15, 12, 22,  0,  25],
        [12,  0, 12,  20,  0, 10, 12,  18],
        [0,  12,  0,  15, 12, 22,  0,  25],
        [15, 20, 15,   0, 20, 14, 15,  30],
        [12,  0, 12,  20,  0, 10, 12,  18],
        [22, 10, 22,  14, 10,  0, 22,  15],
        [0,  12,  0,  15, 12, 22,  0,  25],
        [25, 18, 25,  30, 18, 15, 25,   0],
    ],
    'pickups_deliveries': [[2, 3], [4, 5], [6, 7]],
    'demands': [0, 0, 1, -1, 1, -1, 1, -1],
    'vehicle_capacities': [2, 2],
    'time_windows': [
        (0, 120), (0, 120), (0, 15), (10, 20),
        (0, 15), (10, 20), (0, 25), (25, 35),
    ]
}

if __name__ == "__main__":
    # Example Usage
    result_array = solve_full_pizza_vrptw_with_datetime(DEFAULT_MOCK_DATA)
    for entry in result_array:
        print(entry)
