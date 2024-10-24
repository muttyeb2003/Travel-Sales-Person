import googlemaps
import pandas as pd
import time
import folium  # Import folium for mapping
from googlemaps.exceptions import ApiError

# Initialize the Google Maps client with your API key
API_KEY = 'API_KEY'  # Replace with your actual API key
gmaps = googlemaps.Client(key=API_KEY)


# Function to geocode addresses and get their latitude and longitude
def geocode_addresses(addresses):
    latitudes = []
    longitudes = []
    for address in addresses:
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            latitudes.append(location['lat'])
            longitudes.append(location['lng'])
        else:
            latitudes.append(None)
            longitudes.append(None)
        time.sleep(0.1)  # Small delay to respect API rate limits
    return latitudes, longitudes

# Get latitudes and longitudes of all locations
latitudes, longitudes = geocode_addresses(locations)

# Create a DataFrame for easy handling
locations_df = pd.DataFrame({
    'Address': locations,
    'Latitude': latitudes,
    'Longitude': longitudes
})

# Function to split the locations into batches with offsets
def split_into_batches_with_offset(locations, batch_size):
    for i in range(0, len(locations), batch_size):
        yield locations[i:i + batch_size], i

# Function to get the distance matrix in batches with offsets
def get_distance_matrix_in_batches(locations, batch_size=10):
    all_results = []
    
    origin_batches = list(split_into_batches_with_offset(locations, batch_size))
    destination_batches = list(split_into_batches_with_offset(locations, batch_size))
    
    for origins, origin_offset in origin_batches:
        for destinations, destination_offset in destination_batches:
            try:
                result = gmaps.distance_matrix(origins=origins, destinations=destinations, mode='driving')
            except ApiError as e:
                print(f"Error fetching distance matrix: {e}")
                continue
            all_results.append((origin_offset, destination_offset, result))
            
            # To avoid hitting rate limits, add a delay between requests
            time.sleep(1)  # Delay of 1 second
            
    return all_results

# Fetch the distance matrix in batches
distance_results = get_distance_matrix_in_batches(locations, batch_size=10)

# Function to extract and organize distance values from the batch results
def extract_distances(results, locations):
    distance_matrix = [[0 for _ in range(len(locations))] for _ in range(len(locations))]

    for origin_offset, destination_offset, result in results:
        for i, row in enumerate(result['rows']):
            for j, element in enumerate(row['elements']):
                if element['status'] == 'OK' and 'distance' in element:
                    distance_matrix[origin_offset + i][destination_offset + j] = element['distance']['value']
                else:
                    distance_matrix[origin_offset + i][destination_offset + j] = float('inf')  # Use infinity or a large number for unreachable routes

    return distance_matrix

# Get the full distance matrix
distance_matrix = extract_distances(distance_results, locations)

# Convert to a pandas DataFrame for easy viewing
distance_df = pd.DataFrame(distance_matrix, index=locations, columns=locations)
print(distance_df)

# Now use the distance matrix with the OR-Tools TSP solver
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2  # Import the enums

def create_data_model():
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = distance_matrix  # Use your actual distance matrix
    data['num_vehicles'] = 1  # One vehicle for TSP
    data['depot'] = 0  # Start and end at the depot (index 0)
    return data

def tsp_solver():
    data = create_data_model()

    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']), data['num_vehicles'], data['depot'])

    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(data['distance_matrix'][from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    # Optionally, you can set a time limit for the solver
    # search_parameters.time_limit.FromSeconds(30)

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        route = get_solution_route(manager, routing, solution)
        print_solution(manager, routing, solution)
        plot_route(route, data)  # Pass data to plot_route
    else:
        print("No solution found!")

def get_solution_route(manager, routing, solution):
    """Extracts the route from the solution."""
    index = routing.Start(0)
    route = []
    while not routing.IsEnd(index):
        node_index = manager.IndexToNode(index)
        route.append(node_index)
        index = solution.Value(routing.NextVar(index))
    node_index = manager.IndexToNode(index)
    route.append(node_index)
    return route

def print_solution(manager, routing, solution):
    """Prints the solution on console."""
    print('Objective: {} meters'.format(solution.ObjectiveValue()))
    index = routing.Start(0)
    plan_output = 'Route:\n'
    while not routing.IsEnd(index):
        node_index = manager.IndexToNode(index)
        plan_output += f' {locations[node_index]} ->'
        index = solution.Value(routing.NextVar(index))
    node_index = manager.IndexToNode(index)
    plan_output += f' {locations[node_index]}'
    print(plan_output)

def plot_route(route, data):
    """Plots the route on a map using folium."""
    # Center of the map (we'll use the depot's coordinates)
    depot_lat = locations_df.iloc[route[0]]['Latitude']
    depot_lon = locations_df.iloc[route[0]]['Longitude']
    map_center = (depot_lat, depot_lon)

    # Create a folium map
    m = folium.Map(location=map_center, zoom_start=12)

    # For numbering the stops
    stop_number = 1

    # Add markers for each location
    for idx, node in enumerate(route[:-1]):  # Exclude the last point as it's the same as the first
        lat = locations_df.iloc[node]['Latitude']
        lon = locations_df.iloc[node]['Longitude']

        if node == data['depot']:
            # Depot marker with home icon
            folium.Marker(
                location=(lat, lon),
                popup=f"Depot: {locations[node]}",
                icon=folium.Icon(color='green', icon='home')
            ).add_to(m)
        else:
            # Other stops with numbered icons
            folium.Marker(
                location=(lat, lon),
                popup=f"Stop {stop_number}: {locations[node]}",
                icon=folium.DivIcon(
                    icon_size=(20, 20),
                    icon_anchor=(10, 10),
                    html=f'''
                        <div style="font-size: 12pt; color : black; text-align: center;">
                            {stop_number}
                        </div>
                    '''
                )
            ).add_to(m)
            stop_number += 1

    # For each leg of the route, get the polyline from the Directions API
    for i in range(len(route) - 1):
        origin_index = route[i]
        dest_index = route[i + 1]

        origin = (locations_df.iloc[origin_index]['Latitude'], locations_df.iloc[origin_index]['Longitude'])
        destination = (locations_df.iloc[dest_index]['Latitude'], locations_df.iloc[dest_index]['Longitude'])

        # Get directions between origin and destination
        try:
            directions_result = gmaps.directions(
                origin=origin,
                destination=destination,
                mode='driving'
            )
        except ApiError as e:
            print(f"Error fetching directions between {locations[origin_index]} and {locations[dest_index]}: {e}")
            continue

        # Extract the polyline from the directions result
        if directions_result:
            steps = directions_result[0]['legs'][0]['steps']
            path = []
            for step in steps:
                polyline = step['polyline']['points']
                decoded_points = googlemaps.convert.decode_polyline(polyline)
                lat_lngs = [(point['lat'], point['lng']) for point in decoded_points]
                path.extend(lat_lngs)
            folium.PolyLine(locations=path, color='blue', weight=5, opacity=0.8).add_to(m)
        else:
            # If no directions are found, draw a straight line
            folium.PolyLine(locations=[origin, destination], color='red', weight=2, opacity=0.8).add_to(m)

        # Sleep to respect rate limits
        time.sleep(1)  # Adjust as needed based on your API usage and limits

    # Save the map to an HTML file
    m.save('tsp_route_map.html')
    print("Route map saved to 'tsp_route_map.html'.")

# Call the solver
tsp_solver()
