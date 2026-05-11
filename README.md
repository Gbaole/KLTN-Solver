# Pizza Optimization API (KLTN-Solver)

A FastAPI-based optimization engine for pizza shop operations, featuring three core modules: Kitchen Scheduling, Network Assignment (Order-to-Store), and VRP (Vehicle Routing Problem) for deliveries.

## Features
- **Kitchen Scheduling:** Optimizes pizza preparation sequences to minimize tardiness and makespan using OR-Tools CP-SAT.
- **Network Optimization:** Assigns orders to stores based on distance and current workload balance.
- **VRP & Delivery:** Generates optimal delivery routes with time windows and capacity constraints.

---

## Installation

### Prerequisites
- Python 3.10+
- [OR-Tools](https://developers.google.com/optimization)

### Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Gbaole/KLTN-Solver.git
   cd KLTN-Solver
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   *Note: Specific versions are used to ensure compatibility between NumPy 1.x and OR-Tools.*
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### Running the Server
Start the FastAPI server using Uvicorn:
```bash
python3 main.py
```
The API will be available at `http://localhost:8000`. You can access the interactive documentation (Swagger UI) at `http://localhost:8000/docs`.

### Testing the API
A test script is provided to verify all endpoints:
```bash
python3 test_api.py
```

---

## API Documentation

### 1. Kitchen Scheduling (`/schedule`)
Optimizes the preparation order for pizzas in the kitchen.

- **Method:** `POST`
- **Input (JSON):**
    | Field | Type | Description |
    | :--- | :--- | :--- |
    | `now_dt` | `string` | Current time (ISO 8601). |
    | `chef_list` | `array[string]` | List of available chefs. |
    | `orders` | `array[object]` | List of orders to schedule (see below). |
    | `tardiness_weight`| `int` | (Optional) Weight for late orders. Default: 1000. |

- **Order Object:**
    | Field | Type | Description |
    | :--- | :--- | :--- |
    | `id` | `string` | Unique Order ID. |
    | `is_processing` | `bool` | `true` if already started, `false` if pending. |
    | `pic` | `string` | Person In Charge (Chef name) if processing. |
    | `deadline_dt` | `string` | Customer's promised delivery/finish time. |
    | `processing_time_mins`| `int` | Preparation time in minutes. |

- **Output:**
    - `schedule`: List of tasks with assigned PIC, start/end times, and delivery slack.
    - `stats`: Overall kitchen metrics (makespan, clear time).

---

### 2. Network Optimization (`/network`)
Assigns incoming orders to the best store location.

- **Method:** `GET`
- **Input:** None (Currently uses internal dataset).
- **Output:**
    - `assignments`: List of orders mapped to stores with distances.
    - `store_monitoring`: Workload distribution across stores.
    - `global_objective_score`: Optimization quality metric.

---

### 3. VRP Optimization (`/vrp`)
Calculates optimal delivery routes for drivers.

- **Method:** `GET`
- **Input:** None (Currently uses internal dataset).
- **Output:**
    - A sequence of delivery nodes per driver including:
        - `arrival_datetime`: Predicted time at stop.
        - `load_after_action`: Number of pizzas on board.
        - `lateness`: Calculated delay relative to target window.

---

## Contributing
Feel free to open issues or submit pull requests for improvements.

## License
MIT
