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
    fd = mdl.continuous_var_matrix(range(m), range(n), name="fd")  # Flujo de depósitos
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

    for i, j in [(i, j) for i in range(m, m + n) for j in range(m, m + n) if i != j]:
        mdl.add_constraint(x[i, j] == 0, f"no_subtour_clientes_{i}_{j}")

    for d in range(m):
        mdl.add_constraint(
            mdl.sum(x[d, j] for j in range(m, m + n)) >= y[d], f"depot_serve_customer_{d}"
        )

    for d in range(m):
        mdl.add_constraint(
            mdl.sum(f[d, j] for j in range(m, m + n)) <= depot_capacities[d], f"capacidad_deposito_{d}"
        )

    for d in range(m):
        mdl.add_constraint(
            mdl.sum(fd[d, j] for j in range(n)) == n,
            f"flujo_total_deposito_{d}"
        )

    return mdl


def solver_scf_gurobi(data):
    """
    Implementación del modelo Single Commodity Flow (SCF) usando Gurobi.

    Parámetros:
        data (dict): Diccionario con los datos necesarios para el modelo.

    Retorna:
        dict: Resultados del modelo con métricas clave.
    """
    # Crear el modelo
    mdl = Model("SCF")

    # Variables
    x = mdl.addVars(data['distancias'], vtype=GRB.BINARY, name="x")  # Ruta entre nodos
    f = mdl.addVars(data['distancias'], lb=0, vtype=GRB.CONTINUOUS, name="f")  # Flujo continuo
    fd = mdl.addVars(
        [(d, j) for d in range(data['num_depositos']) for j in range(data['num_clientes'])],
        lb=0, vtype=GRB.CONTINUOUS, name="fd"
    )  # Flujo desde depósitos a clientes
    y = mdl.addVars(data['num_depositos'], vtype=GRB.BINARY, name="y")  # Uso de depósitos

    # Función objetivo
    mdl.setObjective(
        quicksum(data['distancias'][(i, j)] * x[i, j] for (i, j) in data['distancias']) +
        quicksum(data['costo_apertura_deposito'][d] * y[d] for d in range(data['num_depositos'])),
        GRB.MINIMIZE
    )

    # Restricciones
    # 1. Capacidad de los depósitos
    for deposito in range(data['num_depositos']):
        mdl.addConstr(
            quicksum(
                data['demanda'][j] * x[deposito, j]
                for j in range(data['num_clientes']) if (deposito, j) in data['distancias']
            ) <= data['cap_deposito'][deposito] * y[deposito]
        )

    # 2. Capacidad de los vehículos
    for deposito in range(data['num_depositos']):
        mdl.addConstr(
            quicksum(
                data['demanda'][j] * x[deposito, j]
                for j in range(data['num_clientes']) if (deposito, j) in data['distancias']
            ) <= data['cap_vehiculo'] * y[deposito]
        )

    # 3. Circuitos que comienzan y terminan en el mismo depósito
    for deposito in range(data['num_depositos']):
        mdl.addConstr(
            quicksum(x[deposito, cliente] for cliente in range(data['num_clientes'])
                     if (deposito, cliente) in data['distancias']) ==
            quicksum(x[cliente, deposito] for cliente in range(data['num_clientes'])
                     if (cliente, deposito) in data['distancias'])
        )

    # 4. No debe haber circuitos con más de un depósito
    for i in range(data['num_depositos']):
        for j in range(data['num_depositos']):
            if i != j:
                mdl.addConstr(x[i, j] == 0)

    # 5. No debe haber circuitos entre clientes sin pasar por un depósito
    for i, j in data['distancias']:
        if i >= data['num_depositos'] and j >= data['num_depositos']:
            mdl.addConstr(x[i, j] == 0)

    # 6. Conservación de flujo: Un cliente debe recibir exactamente una unidad de flujo
    for cliente in range(data['num_clientes']):
        mdl.addConstr(
            quicksum(f[i, cliente] for i in range(data['num_depositos'] + data['num_clientes'])
                     if (i, cliente) in data['distancias']) == 1
        )

    # 7. Cada depósito debe servir al menos a un cliente
    for deposito in range(data['num_depositos']):
        mdl.addConstr(
            quicksum(x[deposito, j] for j in range(data['num_clientes'])
                     if (deposito, j) in data['distancias']) >= y[deposito]
        )

    # 8. Flujo total desde todos los depósitos hacia los clientes debe ser igual al número de clientes
    for d in range(data['num_depositos']):
        mdl.addConstr(
            quicksum(fd[d, j] for j in range(data['num_clientes'])) ==
            quicksum(x[d, j] for j in range(data['num_clientes']) if (d, j) in data['distancias'])
        )

    # 9. Restricción de flujo en los arcos (d, j): El flujo debe estar acotado
    for d in range(data['num_depositos']):
        for j in range(data['num_clientes']):
            mdl.addConstr(fd[d, j] <= data['cap_deposito'][d] * y[d])

    # 10. Restricción de flujo entre clientes y depósitos
    for i, j in data['distancias']:
        if i >= data['num_depositos']:  # Es un cliente
            mdl.addConstr(f[i, j] <= (data['num_clientes'] - 1) * x[i, j])
        if j >= data['num_depositos']:  # Es un cliente
            mdl.addConstr(f[i, j] <= (data['num_clientes'] - 1) * x[i, j])

    return mdl


if __name__ == "__main__":
    # Load the parsed data
    file_path = "Instances/Benchmark_1/coord100-10-3b.dat"
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
        "Valor Función Objetivo": model.objVal if model.status == GRB.OPTIMAL else "N/A",
        "Tiempo de Cómputo (s)": end_time - start_time
    }

    print(metrics)
