import gurobipy as gp
from gurobipy import Model
from gurobipy import GRB
import math

# Crear un Modelo:
model = Model("F-MDRP")
# Definir variables:

x = model.addVars(costs, vtype=GRB.BINARY, name="x") #1 = Usado en circuito, 0 = No

y = model.addVars(depots, vtype=GRB.BINARY,name = "y") #1 = Depot usado en circuito, 0 = No

c = model.addVars(distances, vtype=GRB.BINARY, name= "c") # Costo asociado a cada arco

# Objective: Minimize total cost
model.setObjective(sum(c_ij * x_ij for (i, j)),  GRB.MINIMIZE)

# Restricciones
# Cada cliente es limitado por un unico depot
for d in depots:
    model.addConstr(sum(x[d, j] for j in clients) == y[d], name=f"UsoDepot_{d}")

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
