from flask import Flask, request, render_template
import os
import pandas as pd

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
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    # Save the uploaded file to the 'uploads' folder
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Process the Excel file with pandas
    try:
        # Use pandas to read the Excel file
        df = pd.read_excel(file_path)

        # Extract specific columns (adjust based on actual Excel file structure)
        order_ids = df['Order ID']  # Column for Order IDs
        addresses = df['Address']   # Column for Addresses

        # Print the extracted data to the console
        print("Order IDs:")
        print(order_ids)
        print("Addresses:")
        print(addresses)

        return "File uploaded and processed successfully!"
    except Exception as e:
        return f"Error processing file: {str(e)}", 500

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)
