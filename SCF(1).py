from docplex.mp.model import Model
from testParser import parse_file


# 3.1. Single commodity flow formulations (pag 2 del paper).
def Solver_SCF1(data):
    # -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Crear modelo +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-

    modelo = Model(name="SCF")

    # -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Variables: +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-

    # x[i, j]: Binaria, indica si se utiliza el arco entre el nodo i y el nodo j
    x = modelo.binary_var_dict(data['distancias'], name="x")
    # f[i, j]: Flujo continuo asociado al arco (i, j)
    f = modelo.continuous_var_dict(data['distancias'], lb=0, name="f")
    # f[d, j]: Flujo de los depósitos hacia los clientes
    fd = modelo.continuous_var_dict([(d, j) for d in range(data['num_depositos']) for j in range(data['num_clientes'])],
                                    lb=0, name="fd")
    # y[d]: Binaria, indica si el depósito d está abierto
    y = modelo.binary_var_list(data['num_depositos'], name="y")
    # -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Funcion objetivo: +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-

    modelo.minimize(
        modelo.sum(data['distancias'][(i, j)] * x[i, j] for (i, j) in data['distancias']) +
        modelo.sum(data['costo_apertura_deposito'][d] * y[d] for d in range(data['num_depositos']))
    )

    # -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Restricciones: +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-

    # 1. El flujo total desde todos los depósitos hacia los clientes debe ser igual al número de clientes
    for d in range(data['num_depositos']):
        modelo.add_constraint(
            modelo.sum(fd[d, j] for j in range(data['num_clientes'])) == data['num_clientes'],
            f"flujo_total_deposito_{d}"
        )

    # 2. Restricción de flujo en los arcos (d, j): El flujo debe estar acotado
    for d in range(data['num_depositos']):
        for j in range(data['num_clientes']):
            modelo.add_constraint(
                fd[d, j] <= data['cap_deposito'][d] * y[d],
                f"flujo_deposito_cliente_{d}_{j}"
            )

    # 3. Restricción de flujo entre clientes y depósitos
    for i, j in data['distancias']:
        if i >= data['num_depositos']:  # Es un cliente
            modelo.add_constraint(
                f[i, j] <= (data['num_clientes'] - 1) * x[i, j],
                f"flujo_cliente_{i}_{j}"
            )
        if j >= data['num_depositos']:  # Es un cliente
            modelo.add_constraint(
                f[i, j] <= (data['num_clientes'] - 1) * x[i, j],
                f"flujo_cliente_{i}_{j}"
            )

    # 4. Restricción de conservación de flujo: Un cliente debe recibir exactamente una unidad de flujo
    for cliente in range(data['num_clientes']):
        modelo.add_constraint(
            modelo.sum(f[i, cliente] for i in range(data['num_depositos'] + data['num_clientes']) if
                       (i, cliente) in data['distancias']) == 1,
            f"conservacion_flujo_cliente_{cliente}"
        )

    # 5. Restricciones para que cada depósito sirva al menos un cliente
    for deposito in range(data['num_depositos']):
        modelo.add_constraint(
            modelo.sum(x[deposito, j] for j in range(data['num_clientes']) if (deposito, j) in data['distancias']) >= y[
                deposito],
            f"deposito_servir_cliente_{deposito}"
        )

    # 6. No debe haber circuitos entre clientes sin pasar por un depósito
    for i, j in data['distancias']:
        if i >= data['num_depositos'] and j >= data['num_depositos']:
            modelo.add_constraint(
                x[i, j] == 0,
                f"no_circuito_sin_deposito_{i}_{j}"
            )

    # 7. No debe haber circuitos con más de un depósito
    for i in range(data['num_depositos']):
        for j in range(data['num_depositos']):
            if i != j:
                modelo.add_constraint(
                    x[i, j] == 0,
                    f"no_circuito_multiples_depositos_{i}_{j}"
                )

    # -+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ Resolver el modelo +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-

    solucion = modelo.solve(log_output=True)
    if solucion:
        print("Costo total:", solucion.objective_value)
        return {
            "n_variables": modelo.number_of_variables,
            "n_restricciones": modelo.number_of_constraints,
            "valor_FO": solucion.objective_value,
            "tiempo_ejecucion": solucion.solve_details.time
        }
    else:
        print("No se encontro solucion.")
        return {
            "n_variables": modelo.number_of_variables,
            "n_restricciones": modelo.number_of_constraints,
            "valor_FO": 0,
            "tiempo_ejecucion": 0
        }


from gurobipy import Model, GRB, quicksum


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

    # Resolver el modelo
    mdl.optimize()

    if mdl.status == GRB.OPTIMAL:
        return {
            "n_variables": mdl.NumVars,
            "n_restricciones": mdl.NumConstrs,
            "valor_FO": mdl.objVal,
            "tiempo_ejecucion": mdl.Runtime
        }
    else:
        print("No se encontró solución.")
        return {
            "n_variables": mdl.NumVars,
            "n_restricciones": mdl.NumConstrs,
            "valor_FO": 0,
            "tiempo_ejecucion": 0
        }


if __name__ == "__main__":
    # Ejecutar el modelo
    parsed_data = parse_file("Instances/Benchmark_1/coord100-10-3b.dat")

    n = parsed_data["num_customers"]
    m = parsed_data["num_depots"]

    arc_indices = [(i, j) for i in range(m + n) for j in range(m + n) if i != j]

    data = {
        "num_clientes": parsed_data["num_customers"],
        "num_depositos": parsed_data["num_depots"],
        "distancias": {(i, j): parsed_data["distance_matrix"][i][j] for i, j in arc_indices},
        "cap_deposito": parsed_data["depot_capacities"],
        "costo_apertura_deposito": parsed_data["depot_opening_costs"],
        'demanda': parsed_data["customer_demands"],
        'cap_vehiculo': parsed_data["vehicle_capacity"]
    }

    metrics = solver_scf_gurobi(data)
    print(metrics)
