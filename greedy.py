import googlemaps
import pandas as pd
import time
import sys
from googlemaps.exceptions import ApiError

def greedy(api_key, locations):
    # Initialize the Google Maps client with your API key
    gmaps = googlemaps.Client(key=api_key)

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
                        distance_matrix[origin_offset + i][destination_offset + j] = float('inf')  # Use infinity for unreachable routes

        return distance_matrix

    # Get the full distance matrix
    distance_matrix = extract_distances(distance_results, locations)

    def print_matrix(matrix):
        for row in matrix:
            print(" ".join(map(str, row)))  # Convert each element to string and join with spaces

    print_matrix(distance_matrix)

    INT_MAX = sys.maxsize

    # Function to find the path using greedy approach
    def greedy_alg(matrix):
        total_distance, counter = 0, 0
        i, j = 0, 0
        min_distance = INT_MAX

        # Starting from the 0th indexed location
        route = [0] * (len(matrix) + 1)

        # Traverse the adjacency matrix
        while i < len(matrix) and j < len(matrix[i]):
            # Corner of the Matrix
            if counter >= len(matrix[i]) - 1:
                break

            # If this path is unvisited then and if the distance is less then update the distance
            if j != i and (j not in route[1:len(matrix)]):
                if matrix[i][j] < min_distance:
                    min_distance = matrix[i][j]
                    route[counter + 1] = j

            j += 1

            # Check all paths from the ith indexed location
            if j == len(matrix[i]):
                total_distance += min_distance
                min_distance = INT_MAX
                j = 0
                i = route[counter + 1]
                counter += 1

        # Update the ending city in array from city which was last visited
        i = route[counter] - 1
        j = route[0]
        route[counter + 1] = route[0]
        min_distance = matrix[i][j]
        total_distance += min_distance

        # Print the route path and distance covered, from given starting city and ending at the same city.
        print("Minimum distance obtained using Greedy heuristic approach is:", total_distance)
        print("And the route is", route)

    # Finding the route
    greedy_alg(distance_matrix)

# Usage example (you can call this function in another file):
# optimize_delivery_route('YOUR_API_KEY', locations)
