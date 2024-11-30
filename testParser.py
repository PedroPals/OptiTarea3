import math


def parse_file(file_path):
    with open(file_path, 'r') as file:
        lines = [line.strip() for line in file if line.strip()]

    num_customers, num_depots = int(lines[0]), int(lines[1])
    depots = [tuple(map(float, lines[i].split())) for i in range(2, 2 + num_depots)]
    customers = [tuple(map(float, lines[i].split())) for i in range(2 + num_depots, 2 + num_depots + num_customers)]
    vehicle_capacity = float(lines[2 + num_depots + num_customers])
    depot_capacities = list(map(float, lines[3 + num_depots + num_customers:3 + 2 * num_depots + num_customers]))
    customer_demands = list(
        map(float, lines[3 + 2 * num_depots + num_customers:3 + 2 * num_depots + 2 * num_customers]))
    depot_opening_costs = list(
        map(float, lines[3 + 2 * num_depots + 2 * num_customers:3 + 3 * num_depots + 2 * num_customers]))
    route_opening_cost = float(lines[3 + 3 * num_depots + 2 * num_customers])

    all_points = depots + customers
    distance_matrix = [
        [math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) for x2, y2 in all_points] for x1, y1 in all_points
    ]

    return {
        "num_customers": num_customers,
        "num_depots": num_depots,
        "depots": depots,
        "customers": customers,
        "vehicle_capacity": vehicle_capacity,
        "depot_capacities": depot_capacities,
        "customer_demands": customer_demands,
        "depot_opening_costs": depot_opening_costs,
        "route_opening_cost": route_opening_cost,
        "distance_matrix": distance_matrix,
    }


# Ejemplo de uso
file_path = "Instances/Benchmark_1/coord20-5-1.dat"
parsed_data = parse_file(file_path)

# Mostrar resultados
print("Número de clientes:", parsed_data["num_customers"])
print("Número de depósitos:", parsed_data["num_depots"])
print("Depósitos:", parsed_data["depots"])
print("Clientes:", parsed_data["customers"])
print("Capacidad del vehículo:", parsed_data["vehicle_capacity"])
print("Capacidades de los depósitos:", parsed_data["depot_capacities"])
print("Demandas de los clientes:", parsed_data["customer_demands"])
print("Costos de apertura de depósitos:", parsed_data["depot_opening_costs"])
print("Costo de apertura de ruta:", parsed_data["route_opening_cost"])
print("Matriz de distancias (primera fila):", parsed_data["distance_matrix"][0])
