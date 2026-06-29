from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn

# Import solving functions from the existing files
from Sched import solve_pizza_scheduling
from TestAlloFixedData import solve_pizza_network_v2
from VRP_DTime import solve_full_pizza_vrptw_with_datetime

app = FastAPI(title="Pizza Optimization API")

# --- Pydantic Models for Sched.py ---

class OrderInput(BaseModel):
    id: str
    is_processing: bool
    pic: Optional[str] = None
    finished_time_dt: Optional[datetime] = None
    deadline_dt: datetime
    processing_time_mins: int

class SchedulingRequest(BaseModel):
    now_dt: datetime
    chef_list: List[str]
    orders: List[OrderInput]
    tardiness_weight: int = 1000
    flow_time_weight: int = 5
    makespan_weight: int = 1

class VRPRequest(BaseModel):
    num_vehicles: int
    starts: List[int]
    ends: List[int]
    time_matrix: List[List[int]]
    pickups_deliveries: List[List[int]]
    demands: List[int]
    vehicle_capacities: List[int]
    time_windows: List[List[int]]
    base_datetime: Optional[datetime] = None

# --- Endpoints ---

@app.get("/")
async def root():
    return {"message": "Welcome to the Pizza Optimization API. Available endpoints: /schedule, /network, /vrp (POST)"}

@app.post("/schedule")
async def schedule_pizza(request: SchedulingRequest):
    try:
        print(f"[API] Received /schedule request for {len(request.orders)} orders and {len(request.chef_list)} chefs.")
        # Convert Pydantic orders to list of dicts as expected by solve_pizza_scheduling
        orders_dict = [order.model_dump() for order in request.orders]
        
        schedule, stats = solve_pizza_scheduling(
            request.now_dt, 
            request.chef_list, 
            orders_dict,
            request.tardiness_weight,
            request.flow_time_weight,
            request.makespan_weight
        )
        print("[API] Kitchen Solver finished.")
        return {"schedule": schedule, "stats": stats}
    except Exception as e:
        print(f"[API] Error in /schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class OptimizationRequest(BaseModel):
    stores: dict
    orders: dict
    now_dt: datetime
    chef_lists: dict
    vrp_data_templates: dict

@app.post("/optimize-all")
async def optimize_all(request: OptimizationRequest):
    try:
        # 1. Allocation
        allocations = solve_pizza_network_v2(request.stores, request.orders)
        if allocations['status'] != 'SUCCESS':
            raise HTTPException(status_code=500, detail="Allocation failed")
            
        # 2. Scheduling per store
        all_schedules = {}
        for store_name in request.stores.keys():
            # Filter orders for this store
            store_orders = [
                {
                    'id': assn['order'],
                    'is_processing': False, # Assuming new orders for this flow
                    'pic': None,
                    'finished_time_dt': None,
                    'deadline_dt': request.orders[assn['order']].get('deadline_dt', request.now_dt + timedelta(hours=1)),
                    'processing_time_mins': assn['time_min']
                }
                for assn in allocations['assignments'] if assn['store'] == store_name
            ]
            
            if store_orders:
                schedule, stats = solve_pizza_scheduling(
                    request.now_dt,
                    request.chef_lists.get(store_name, []),
                    store_orders
                )
                all_schedules[store_name] = {"schedule": schedule, "stats": stats}
            else:
                all_schedules[store_name] = {"schedule": [], "stats": {}}
        
        # 3. Routing (This is a simplification, assumes VRP needs all deliveries)
        # We need to construct the VRP request from the scheduling results
        # This part requires mapping scheduling results to the VRP data format
        
        # NOTE: For now, return the allocation and schedules as the intermediate step
        return {"allocations": allocations, "schedules": all_schedules}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/vrp")
async def vrp_optimization(request: VRPRequest):
    try:
        data = request.model_dump()
        results = solve_full_pizza_vrptw_with_datetime(data, request.base_datetime)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vrp-demo")
async def vrp_demo():
    try:
        from VRP_DTime import DEFAULT_MOCK_DATA
        results = solve_full_pizza_vrptw_with_datetime(DEFAULT_MOCK_DATA)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
