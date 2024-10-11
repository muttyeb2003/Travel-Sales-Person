from flask import Flask, request, render_template
import os
import pandas as pd
from greedy import greedy  # Import the greedy function from greedy.py

# Initialize Flask app
app = Flask(__name__)

# Create a folder to store uploaded files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route for the home page (file upload form)
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle the file upload
@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the file part is present in the request
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    
    # Check if the filename is empty
    if file.filename == '':
        return "No selected file", 400

    # Save the uploaded file to the 'uploads' folder
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Process the Excel file with pandas
    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(file_path)

        # Extract the relevant columns (make sure the column names match your Excel file)
        order_ids = df['Order ID'].tolist()  # Convert to a list
        addresses = df['Address'].tolist()   # Convert to a list

        # Combine Order IDs and Addresses into an array of tuples
        combined_array = list(zip(order_ids, addresses))

        # Print the array to the console
        print("Array from the file:", combined_array)

        # Now call the greedy function directly
        API_KEY = 'API_KEY'  # Replace with your actual API key
        min_distance, route = greedy(API_KEY, addresses)  # Call the function with the API key and addresses

        # Return the result
        return f"Minimum distance: {min_distance}, Route: {route}", 200

    except Exception as e:
        return f"An error occurred while processing the file: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
