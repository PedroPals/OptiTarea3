from docplex.mp.model import Model as Model_cpx
from gurobipy import Model as Model_grb, GRB, quicksum
from testParser import parse_file
import time


def modelo_scf_cplex(parsed_data):
    """
    Implementación del modelo SCF (Single Commodity Flow) usando CPLEX.

    Parámetros:
        parsed_data (dict): Diccionario con los datos parseados.

    Retorna:
        Model: Modelo de CPLEX con el problema SCF formulado.
    """
    n = parsed_data["num_customers"]
    m = parsed_data["num_depots"]
    depots = parsed_data["depots"]
    customers = parsed_data["customers"]
    vehicle_capacity = parsed_data["vehicle_capacity"]
    depot_capacities = parsed_data["depot_capacities"]
    customer_demands = parsed_data["customer_demands"]
    opening_costs_depots = parsed_data["depot_opening_costs"]
    opening_cost_route = parsed_data["route_opening_cost"]
    costs = parsed_data["distance_matrix"]

    # Crear el modelo
    mdl = Model_cpx(name="SCF")

    # Nodos totales (depósitos + clientes)
    nodos = list(range(m + n))

    # Variables
    x = mdl.binary_var_matrix(nodos, nodos, name="x")  # Ruta entre nodos
    f = mdl.continuous_var_matrix(nodos, nodos, name="f")  # Flujo de producto
    y = mdl.binary_var_list(m, name="y")  # Uso de depósitos

    # Función objetivo: minimizar costos de transporte, apertura y uso de rutas
    mdl.minimize(
        mdl.sum(costs[i][j] * x[i, j] for i in nodos for j in nodos if i != j) +  # Costos de transporte
        mdl.sum(opening_costs_depots[d] * y[d] for d in range(m)) +  # Costos de apertura de depósitos
        opening_cost_route * mdl.sum(y[d] for d in range(m))  # Costos de rutas
    )

    # Restricciones
    # 1. Cada cliente es atendido exactamente una vez
    for i in range(m, m + n):
        mdl.add_constraint(mdl.sum(x[i, j] for j in nodos if j != i) == 1)  # Salen
        mdl.add_constraint(mdl.sum(x[j, i] for j in nodos if j != i) == 1)  # Entran

    # 2. Las rutas deben comenzar y terminar en depósitos abiertos
    for d in range(m):
        mdl.add_constraint(mdl.sum(x[d, j] for j in range(m, m + n)) <= y[d])
        mdl.add_constraint(mdl.sum(x[j, d] for j in range(m, m + n)) <= y[d])

    # 3. Restricciones de flujo para garantizar balance
    for i in range(m, m + n):  # Para cada cliente
        mdl.add_constraint(
            mdl.sum(f[i, j] for j in nodos if j != i) -
            mdl.sum(f[j, i] for j in nodos if j != i) == customer_demands[i - m]
        )
    for i, j in [(i, j) for i in nodos for j in nodos if i != j]:
        mdl.add_constraint(f[i, j] <= vehicle_capacity * x[i, j])  # Flujo limitado por capacidad del vehículo

    # 4. Capacidad máxima de los depósitos
    for d in range(m):
        mdl.add_constraint(
            mdl.sum(f[d, j] for j in range(m, m + n)) <= depot_capacities[d]
        )

    return mdl

def modelo_scf_gurobi(parsed_data):
    """
    Implementación del modelo SCF (Single Commodity Flow) usando Gurobi.

    Parámetros:
        parsed_data (dict): Diccionario con los datos parseados.

    Retorna:
        Model: Modelo de Gurobi con el problema SCF formulado.
    """
    n = parsed_data["num_customers"]
    m = parsed_data["num_depots"]
    depots = parsed_data["depots"]
    customers = parsed_data["customers"]
    vehicle_capacity = parsed_data["vehicle_capacity"]
    depot_capacities = parsed_data["depot_capacities"]
    customer_demands = parsed_data["customer_demands"]
    opening_costs_depots = parsed_data["depot_opening_costs"]
    opening_cost_route = parsed_data["route_opening_cost"]
    costs = parsed_data["distance_matrix"]

    # Crear el modelo
    mdl = Model_grb("SCF")

    # Nodos totales (depósitos + clientes)
    nodos = list(range(m + n))

    # Variables
    x = mdl.addVars(nodos, nodos, vtype=GRB.BINARY, name="x")  # Ruta entre nodos
    f = mdl.addVars(nodos, nodos, vtype=GRB.CONTINUOUS, name="f")  # Flujo de producto
    y = mdl.addVars(m, vtype=GRB.BINARY, name="y")  # Uso de depósitos

    # Función objetivo: minimizar costos de transporte, apertura y uso de rutas
    mdl.setObjective(
        quicksum(costs[i][j] * x[i, j] for i in nodos for j in nodos if i != j) +  # Costos de transporte
        quicksum(opening_costs_depots[d] * y[d] for d in range(m)) +  # Costos de apertura de depósitos
        opening_cost_route * quicksum(y[d] for d in range(m)),  # Costos de rutas
        GRB.MINIMIZE
    )

    # Restricciones
    # 1. Cada cliente es atendido exactamente una vez
    for i in range(m, m + n):
        mdl.addConstr(quicksum(x[i, j] for j in nodos if j != i) == 1)  # Salen
        mdl.addConstr(quicksum(x[j, i] for j in nodos if j != i) == 1)  # Entran

    # 2. Las rutas deben comenzar y terminar en depósitos abiertos
    for d in range(m):
        mdl.addConstr(quicksum(x[d, j] for j in range(m, m + n)) <= y[d])
        mdl.addConstr(quicksum(x[j, d] for j in range(m, m + n)) <= y[d])

    # 3. Restricciones de flujo para garantizar balance
    for i in range(m, m + n):  # Para cada cliente
        mdl.addConstr(
            quicksum(f[i, j] for j in nodos if j != i) -
            quicksum(f[j, i] for j in nodos if j != i) == customer_demands[i - m]
        )
    for i, j in [(i, j) for i in nodos for j in nodos if i != j]:
        mdl.addConstr(f[i, j] <= vehicle_capacity * x[i, j])  # Flujo limitado por capacidad del vehículo

    # 4. Capacidad máxima de los depósitos
    for d in range(m):
        mdl.addConstr(
            quicksum(f[d, j] for j in range(m, m + n)) <= depot_capacities[d]
        )

    return mdl

if __name__ == "__main__":

    # Load the parsed data
    file_path = "Instances/Benchmark_1/coord20-5-1.dat"
    parsed_data = parse_file(file_path)

    model = modelo_scf_cplex(parsed_data)

    # Solve the model
    start_time = time.time()
    solution = model.solve()
    end_time = time.time()

    metrics = {
        "Modelo": model.name,
        "Instancia": file_path,
        "Número de Variables": model.number_of_variables,
        "Número de Restricciones": model.number_of_constraints,
        "Valor Función Objetivo": model.objective_value if solution is not None else "N/A",
        "Tiempo de Cómputo (s)": end_time - start_time
    }

    print(metrics)
    print("\n\n------------------------------------\n")

    model = modelo_scf_gurobi(parsed_data)

    # Solve the model
    start_time = time.time()
    model.optimize()
    end_time = time.time()

    metrics = {
        "Modelo": model.getAttr("ModelName"),
        "Instancia": file_path,
        "Número de Variables": len(model.getVars()),
        "Número de Restricciones": len(model.getConstrs()),
        "Valor Función Objetivo": model.objVal,
        "Tiempo de Cómputo (s)": end_time - start_time
    }

    print(metrics)
