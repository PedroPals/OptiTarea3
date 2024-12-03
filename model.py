from testParser import parse_file
import gurobipy as gp
from gurobipy import Model, quicksum, GRB
import math

# Load the parsed data
file_path = "Instances/Benchmark_1/coord20-5-1.dat"
parsed_data = parse_file(file_path)

# Extract parameters from parsed data
n = parsed_data["num_customers"]  # Number of customers
m = parsed_data["num_depots"]  # Number of depots
depots = parsed_data["depots"]  # List of depots (e.g., [0, 1, 2])
customers = parsed_data["customers"]  # List of customers (e.g., [3, 4, 5, ...])
vehicle_capacity = parsed_data["vehicle_capacity"]  # Capacity of a vehicle
depot_capacities = parsed_data["depot_capacities"]  # List of depot capacities
customer_demands = parsed_data["customer_demands"]  # List of customer demands
opening_costs_depots = parsed_data["depot_opening_costs"]  # List of depot opening costs
route_opening_cost = parsed_data["route_opening_cost"]  # Cost of opening a route
costs = parsed_data["distance_matrix"]  # Distance matrix

# Hacer que keys() funcione
arc_indices = [(i, j) for i in range(m + n) for j in range(m + n) if i != j]

# Create a Gurobi model
model = Model("F-MDRP_CDA")

# Variables
x = model.addVars(arc_indices, vtype=GRB.BINARY, name="x") #Variable Binaria que indica si el arco de i a j está siendo usado
v = model.addVars([(i, d) for i in customers for d in depots], vtype=GRB.CONTINUOUS, name="v") # Variable continua que indica si el cliente está asignado a un depot d
y = model.addVars(depots, vtype=GRB.BINARY, name="y") #Variable binaria que indica si el depot d está abierto


#Funcion objetivo

model.setObjective(
    gp.quicksum(costs[i, j] * x[i, j] for i, j in costs.keys()) + # Minimizar el costo de la ruta +
    gp.quicksum(opening_costs_depots[d] * y[d] for d in depots) + # El costo del inicio del depot +
    route_opening_cost * gp.quicksum(x[d, i] for d in depots for i in customers), # El inicio de la ruta.
    GRB.MINIMIZE
)

# Restricción CDA
# Asegura que cada cliente este asignado a un sólo depot
model.addConstrs((gp.quicksum(v[i, d] for d in depots) == 1 for i in customers), "client_assignment")

# Asegura que si se ocupa un arco [i,d], el cliente [d,i] o [i,d] estará ahí
model.addConstrs((x[d, i] <= v[i, d] for d in depots for i in customers), "client_inclusion_outgoing")
model.addConstrs((x[i, d] <= v[i, d] for d in depots for i in customers), "client_inclusion_incoming")

# Restriccion que elimina subtours
model.addConstrs((v[i, d] + x[i, j] <= v[j, d] + 1 for d in depots for i in customers for j in customers if i != j), "path_elimination")

# Restricciones genéricas
# Restriccion capacidad depot
model.addConstrs((gp.quicksum(customer_demands[i] * v[i, d] for i in customers) <= depot_capacities[d] * y[d] for d in depots), "depot_capacity")

# Restriccion capacidad vehiculo
model.addConstrs((gp.quicksum(customer_demands[i] * x[i, j] for i in customers for j in customers if i != j) <= vehicle_capacity for d in depots), "vehicle_capacity")

# Restriccion depot abierto
model.addConstrs((v[i, d] <= y[d] for d in depots for i in customers), "depot_open")


# Solve the model
model.optimize()

