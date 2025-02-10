from flask import Flask, request, render_template
import pickle
import pandas as pd
import numpy as np


# Create a Flask application
app = Flask(__name__)

# Load the pickled models
preprocessing = pickle.load(open('preprocessing_pipeline.pkl', 'rb'))
model = pickle.load(open('rfmodel.pkl', 'rb'))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/predict',methods=['POST'])
def predict():
    # Retrieve input from the form
    streetNumber = request.form['streetNumber']
    street = request.form['street']
    suburb = request.form['suburb']
    postcode = int(request.form['postcode'])
    bathrooms = int(request.form['bathrooms'])
    bedrooms = int(request.form['bedrooms'])
    parking = int(request.form['parking'])
    landArea = float(request.form['landArea'])
    propertyType = request.form['propertyType']
    # Retrieve selected features as a list
    features = request.form.getlist('features')  # Gets all selected checkboxes

    # Construct a dictionary for the DataFrame
    data = {
        'streetNumber': [streetNumber],
        'street': [street],
        'suburb': [suburb],
        'postcode': [postcode],
        'bathrooms': [bathrooms],
        'bedrooms': [bedrooms],
        'parking': [parking],
        'landArea': [landArea],
        'propertyType': [propertyType],
        'features': [features]  # Features remain as a list
    }

    # Create the DataFrame
    df = pd.DataFrame(data)
    print(df)

    # Preprocessing pipeline
    final_input = preprocessing.transform(df)
    print(final_input)

    # Model prediction
    output = model.predict(final_input).item()
    output = np.round(10**output, -3)    # price output is in log10

    return render_template("home.html",prediction_text="Estimated Price: ${}".format(output))

# Start the Flask app if this file is run directly
if __name__ == '__main__':
    app.run(debug=True)
