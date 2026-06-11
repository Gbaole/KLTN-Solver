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
        # Convert Pydantic orders to list of dicts as expected by solve_pizza_scheduling
        orders_dict = [order.dict() for order in request.orders]
        
        schedule, stats = solve_pizza_scheduling(
            request.now_dt, 
            request.chef_list, 
            orders_dict,
            request.tardiness_weight,
            request.flow_time_weight,
            request.makespan_weight
        )
        return {"schedule": schedule, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/network")
async def network_optimization():
    try:
        results = solve_pizza_network_v2()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vrp")
async def vrp_optimization(request: VRPRequest):
    try:
        data = request.dict()
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
