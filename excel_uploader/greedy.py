

import googlemaps
import pandas as pd
import time
import folium  # Import folium for mapping
import sys
from googlemaps.exceptions import ApiError
from typing import DefaultDict
from collections import defaultdict

# Initialize the Google Maps client with your API key
API_KEY = 'Api key'  # Do not share this apikey
gmaps = googlemaps.Client(key=API_KEY)


# Example list of addresses (Depot + Delivery Locations)
locations = [
    '2618 Clifton St, Halifax, NS B3K 4V1',  # Depot
    '6299 South St, Halifax, NS B3H 4R2',    # Delivery Location 1
    '3647 Leaman St, Halifax NS B3K 4A2',    # Delivery Location 2
    '1333 South Park St, Halifax NS B3J 2K9', # Delivery Location 3
    '7001 Mumford Rd, Halifax, NS B3L 4R3',
    '1065 Purcells Cove Rd, Halifax, NS B3N 1R2',
    '127 Harlington Crescent, Halifax, NS B3M 3M9 ',
    '1991 Brunswick St, Halifax, NS B3J 3J8',
    '5214 Gerrish St, Halifax, NS B3K 5K3',
    '1583 Hollis St, Halifax, NS B3J 0E4',
    '923 Robie St, Halifax, NS B3H 3C3',
    '5633 Fenwick St, Halifax, NS B3H 1R2',
    '3003 Olivet St, Halifax, NS B3L 4A1',
    '5651 Ogilvie St, Halifax, NS B3H 1B8',
    '166 Bedford Hwy, Halifax, NS B3M 2J6',
    '26 Thomas Raddall Dr, Halifax, NS B3S 0E2',
    '21 Micmac Blvd, Dartmouth, NS B3A 4N3',
    '110 Wyse Rd, Dartmouth, NS B3A 1M2',
    '3248 Isleville St #5, Halifax, NS B3K 3Y5',
    '697 Windmill Rd, Dartmouth, NS B3B 1B7',
    '149 Albro Lake Rd, Dartmouth, NS B3A 3Y8',
    '155 Chain Lake Dr, Halifax, NS B3S 1B3',
    '6055 Almon St, Halifax, NS B3K 1T9',
    '5657 Spring Garden Rd, Halifax, NS B3J 3R4',
    '1899 Albemarle St, Halifax, NS B3J 4A9'
]

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

def print_matrix(matrix):
    for row in matrix:
        print(" ".join(map(str, row))) # Convert each element to string and join with spaces
        
print_matrix(distance_matrix)


INT_MAX = sys.maxsize
 
# Function to find the path using greedy approach
def greedy_alg(matrix):
    sum, counter = 0,0 
    i, j = 0, 0
    min = INT_MAX
 
    # Starting from the 0th indexed location i.e., the first location
    route = [0] * (len(matrix) + 1)
 
    # Traverse the adjacency matrix tsp[][]
    while i < len(matrix) and j < len(matrix[i]):
 
        # Corner of the Matrix
        if counter >= len(matrix[i]) - 1:
            break
 
        # If this path is unvisited then and if the distance is less then update the distance
        if j != i and (j not in route[1:len(matrix)]):
            if matrix[i][j] < min:
                min = matrix[i][j]
                route[counter + 1] = j
 
        j += 1
 
        # Check all paths from the ith indexed location
        if j == len(matrix[i]):
            sum += min
            min = INT_MAX
            j = 0
            i = route[counter +1]
            counter += 1
 
    # Update the ending city in array from city which was last visited
    i = route[counter] - 1
    j = route[0]
    route[counter +1] = route[0]
    min = matrix[i][j]
    sum += min

 
    # Started from the node where we finished as well.
    print("Minimum distance  obtained using Greedy heuristic approach is :", sum)
    print("And the route is " ,route )
 
 
# Driver Code
if __name__ == "__main__":
 
   
 
    # Finding the route
    greedy_alg(distance_matrix)

 
