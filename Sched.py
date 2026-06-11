import math
from datetime import datetime, timedelta
from ortools.sat.python import cp_model

def solve_pizza_scheduling(now_dt, chef_list, orders, 
                           tardiness_weight=1000, 
                           flow_time_weight=5, 
                           makespan_weight=1):
    """
    Solves pizza scheduling by optimizing three competing objectives:
      1. Minimize Tardiness (Avoid late customer promises)
      2. Minimize Completion Times (Maximize individual delivery safety buffers)
      3. Minimize Makespan (Keep kitchen cleared and balanced)
    """
    model = cp_model.CpModel()
    
    # -------------------------------------------------------------------------
    # 1. PRE-PROCESSING: Datetime to Integer Offset Conversion
    # -------------------------------------------------------------------------
    total_duration = 0
    min_deadline_offset = 0
    
    for o in orders:
        if o['is_processing'] and o.get('pic'):
            if o.get('finished_time_dt'):
                rem_seconds = (o['finished_time_dt'] - now_dt).total_seconds()
                rem_mins = math.ceil(rem_seconds / 60.0)
                o['_calculated_duration'] = max(0, rem_mins)
            else:
                # Fallback: if processing but no end time, assume it just started
                o['_calculated_duration'] = int(o['processing_time_mins'])
        else:
            o['_calculated_duration'] = int(o['processing_time_mins'])
            o['is_processing'] = False # Ensure it's treated as Pending if no PIC or not processing
            
        total_duration += o['_calculated_duration']
        
        deadline_seconds = (o['deadline_dt'] - now_dt).total_seconds()
        o['_deadline_offset'] = int(deadline_seconds / 60.0)
        if o['_deadline_offset'] < min_deadline_offset:
            min_deadline_offset = o['_deadline_offset']

    # Set variable bounds (Horizon)
    horizon = int(total_duration + 120) 
    max_tardiness_bound = int(horizon - min_deadline_offset)

    # Decision variables & tracking lists
    chef_intervals = {chef: [] for chef in chef_list}
    order_data_for_output = []
    
    # Objective component variables
    tardiness_cost_vars = []
    completion_time_vars = []
    makespan = model.NewIntVar(0, horizon, 'makespan')

    # -------------------------------------------------------------------------
    # 2. CONSTRAINTS & VARIABLE SETUP
    # -------------------------------------------------------------------------
    for o in orders:
        o_id = o['id']
        duration = o['_calculated_duration']
        deadline_offset = o['_deadline_offset']

        # --- CASE A: Already Active / Assigned ---
        if o['is_processing']:
            pic = o['pic']
            if pic not in chef_intervals:
                chef_intervals[pic] = []
            
            busy_interval = model.NewIntervalVar(0, duration, duration, f'busy_{o_id}_{pic}')
            chef_intervals[pic].append(busy_interval)
            
            # Constraints for makespan and flow time
            model.Add(makespan >= duration)
            
            order_data_for_output.append({
                'id': o_id, 'status': 'Processing', 'pic': pic,
                'start_offset': 0, 'end_offset': duration,
                'deadline_offset': deadline_offset
            })

        # --- CASE B: Unassigned / Pending ---
        else:
            start_var = model.NewIntVar(0, horizon, f'start_{o_id}')
            end_var = model.NewIntVar(0, horizon, f'end_{o_id}')
            
            # Keep track of completion time for the flow time objective
            completion_time_vars.append(end_var)
            
            # Makespan must be >= the end time of this pending job
            model.Add(makespan >= end_var)
            
            # Tardiness logic
            tardiness = model.NewIntVar(0, max_tardiness_bound, f'tardiness_{o_id}')
            model.Add(tardiness >= end_var - deadline_offset)
            model.Add(tardiness >= 0)
            
            # Calculate tardiness cost
            cost_var = model.NewIntVar(0, max_tardiness_bound * tardiness_weight, f'cost_{o_id}')
            model.Add(cost_var == tardiness * tardiness_weight)
            tardiness_cost_vars.append(cost_var)

            # Assign to an active chef
            chef_selectors = []
            for chef in chef_list:
                is_assigned = model.NewBoolVar(f'{o_id}_on_{chef}')
                chef_selectors.append((chef, is_assigned))
                
                interval = model.NewOptionalIntervalVar(
                    start_var, duration, end_var, is_assigned, f'interval_{o_id}_{chef}'
                )
                chef_intervals[chef].append(interval)

            model.AddExactlyOne([var for _, var in chef_selectors])
            
            order_data_for_output.append({
                'id': o_id, 'status': 'Pending', 'start_var': start_var,
                'end_var': end_var, 'selectors': chef_selectors,
                'deadline_offset': deadline_offset
            })

    # Constraint: No overlapping tasks for any chef
    for chef in chef_intervals:
        model.AddNoOverlap(chef_intervals[chef])

    # -------------------------------------------------------------------------
    # 3. TRIPLE-OBJECTIVE FUNCTION
    # -------------------------------------------------------------------------
    # Sum of Tardiness Costs
    total_tardiness_cost = sum(tardiness_cost_vars)
    
    # Sum of Completion Times (Flow Time) -> Minimizing this maximizes delivery slack!
    total_flow_time = model.NewIntVar(0, horizon * len(orders), 'total_flow_time')
    model.Add(total_flow_time == sum(completion_time_vars))
    weighted_flow_time = model.NewIntVar(0, horizon * len(orders) * flow_time_weight, 'weighted_flow_time')
    model.Add(weighted_flow_time == total_flow_time * flow_time_weight)
    
    # Makespan Cost
    weighted_makespan = model.NewIntVar(0, horizon * makespan_weight, 'weighted_makespan')
    model.Add(weighted_makespan == makespan * makespan_weight)
    
    # Combine all objectives
    model.Minimize(total_tardiness_cost + weighted_flow_time + weighted_makespan)

    # Solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # -------------------------------------------------------------------------
    # 4. POST-PROCESSING: Translate Solver Integers back to Datetimes & Slacks
    # -------------------------------------------------------------------------
    final_schedule = []
    solver_stats = {}
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        solver_stats['makespan_minutes'] = solver.Value(makespan)
        solver_stats['makespan_datetime'] = now_dt + timedelta(minutes=solver.Value(makespan))
        
        for item in order_data_for_output:
            if item['status'] == 'Processing':
                s_dt = now_dt
                f_dt = now_dt + timedelta(minutes=item['end_offset'])
                pic = item['pic']
                slack_mins = item['deadline_offset'] - item['end_offset']
            else:
                s_val = solver.Value(item['start_var'])
                f_val = solver.Value(item['end_var'])
                s_dt = now_dt + timedelta(minutes=s_val)
                f_dt = now_dt + timedelta(minutes=f_val)
                pic = next(chef for chef, var in item['selectors'] if solver.BooleanValue(var))
                slack_mins = item['deadline_offset'] - f_val

            final_schedule.append({
                'OrderID': item['id'],
                'PIC': pic,
                'StartedTime': s_dt,
                'FinishedTime': f_dt,
                'DeliverySlackMinutes': slack_mins
            })
            
    return final_schedule, solver_stats


# =============================================================================
# NUMERICAL SIMULATION RUN
# =============================================================================
if __name__ == "__main__":
    current_time = datetime(2026, 5, 10, 13, 5)
    active_chefs = ["Chef_A", "Chef_B"]

    orders_db = [
        {
            'id': 'Order_1_Margherita',
            'is_processing': True,
            'pic': 'Chef_A',
            'finished_time_dt': datetime(2026, 5, 10, 13, 10), # Busy until 13:10
            'deadline_dt': datetime(2026, 5, 10, 13, 20),
            'processing_time_mins': 10
        },
        {
            'id': 'Order_2_Pepperoni',
            'is_processing': True,
            'pic': 'Chef_B',
            'finished_time_dt': datetime(2026, 5, 10, 13, 15), # Busy until 13:15
            'deadline_dt': datetime(2026, 5, 10, 13, 25),
            'processing_time_mins': 15
        },
        {
            'id': 'Order_3_Veggie',
            'is_processing': False,
            'pic': None,
            'finished_time_dt': None,
            'deadline_dt': datetime(2026, 5, 10, 13, 45),      # Deadline far away
            'processing_time_mins': 10
        },
        {
            'id': 'Order_4_Four_Cheese',
            'is_processing': False,
            'pic': None,
            'finished_time_dt': None,
            'deadline_dt': datetime(2026, 5, 10, 13, 35),      # Deadline closer
            'processing_time_mins': 12
        }
    ]

    # Run Solver
    schedule, stats = solve_pizza_scheduling(current_time, active_chefs, orders_db)

    print(f"--- Optimized Schedule Snapshot (Current Time: {current_time.strftime('%H:%M')}) ---")
    print(f"{'Order ID':<25} | {'PIC':<10} | {'StartedTime':<12} | {'FinishedTime':<12} | {'Delivery Slack':<15}")
    print("-" * 88)
    for task in schedule:
        slack_str = f"{task['DeliverySlackMinutes']} mins" if task['DeliverySlackMinutes'] >= 0 else "LATE"
        print(f"{task['OrderID']:<25} | "
              f"{task['PIC']:<10} | "
              f"{task['StartedTime'].strftime('%H:%M'):<12} | "
              f"{task['FinishedTime'].strftime('%H:%M'):<12} | "
              f"{slack_str:<15}")
              
    print("\n" + "="*40)
    print(f"Overall Kitchen Makespan: {stats['makespan_minutes']} minutes")
    print(f"All current work cleared by: {stats['makespan_datetime'].strftime('%H:%M')}")
    print("="*40)