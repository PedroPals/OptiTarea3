from testParser import parse_file
import gurobipy as gp
from gurobipy import Model
from gurobipy import GRB
import math




file_path = "Instances/Benchmark_1/coord20-5-1.dat"
parsed_data = parse_file(file_path)

num_customers = parsed_data["num_customers"]
num_depots = parsed_data["num_depots"]
depots = parsed_data["depots"]
customers = parsed_data["customers"]
vehicle_capacity = parsed_data["vehicle_capacity"]
depot_capacities = parsed_data["depot_capacities"]
customer_demands = parsed_data["customer_demands"]
depot_opening_costs = parsed_data["depot_opening_costs"]
route_opening_cost = parsed_data["route_opening_cost"]
distance_matrix = parsed_data["distance_matrix"]

# Crear un Modelo:
model = Model("F-MDRP")
# Definir variables:



x = model.addVars(customers, customers, vtype=GRB.BINARY, name="x")  # Variables de las rutas, si un customer se encuentra con otro, es 1. Si no, 0.

y = model.addVars(num_depots, vtype=GRB.BINARY, name="y")  # Variable de depots de inicio

c = model.addVars(distance_matrix, vtype=GRB.BINARY, name= "c") # Costo asociado a cada arco

# Objective: Minimize total cost
model.setObjective(sum(c[i, j] * x[i, j] for (i, j) in c), GRB.MINIMIZE)

# Restricciones
# Cada cliente es limitado una única vez
for j in range(num_customers):
    model.addConstr(sum(x[i, j] for i in range(num_customers) if i != j) == 1, name=f"VisitOnce_{j}")

# Each client is visited exactly once
for i in clients:
    model.addConstr(quicksum(x[i, j] for j in clients) == 1, name=f"VisitOnce_{i}")

# Each client is returned to the depot
for i in clients:
    model.addConstr(quicksum(x[j, i] for j in clients) == 1, name=f"ReturnToDepot_{i}")

# Solve the model
model.optimize()

# Verificar si la optimización fue exitosa:
if model.status == GRB.OPTIMAL:

    # Mostrar resultados:
    print("Resultados:")
    # Imprimir valores truncados
    for v in model.getVars()[:-1]:
        print(f"{v.varName}: {math.floor(v.x)}")
    print(f'F.O.: {model.objVal}')

    # Imprimir valores duales
    print("\nValores duales:")
    for constr in model.getConstrs():
        print(f"{constr.constrName}: {constr.Pi}")
    # Imprimir rangos de sensibilidad
    model.printAttr('SAObjLow')  # Rango inferior coeficiente objetivo
    model.printAttr('SAObjUp')  # Rango superior coeficiente objetivo
    model.printAttr('SARHSUp')  # Rango superior lado derecho restricción
    model.printAttr('SARHSLow')  # Rango superior lado derecho restricción

else:
    print("No se pudo encontrar una solución óptima.")
