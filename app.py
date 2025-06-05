from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import joblib

app = Flask(__name__)

# Load trained ML model and food data
model = joblib.load('calorie_model.pkl')
food_df = pd.read_csv('Indian_Food_Nutrition_Processing.csv')

# Function to calculate calories based on food items
def calculate_food_calories(food_items):
    total = 0
    for item in food_items:
        item = item.strip().lower()
        match = food_df[food_df['Food'].str.lower() == item]
        if not match.empty:
            total += match.iloc[0]['Calories_per_100g']
    return total

@app.route('/')
def index():
    return render_template('calorie_form.html')  # 🔁 Updated filename

@app.route('/predict', methods=['POST'])
def predict():
    age = float(request.form['age'])
    weight = float(request.form['weight'])
    height = float(request.form['height'])
    foods = request.form['foods'].split(',')

    # Predict calorie need
    predicted = model.predict(np.array([[age, weight, height]]))[0]

    # Calculate consumed calories
    consumed = calculate_food_calories(foods)

    result = {
        "required": round(predicted, 2),
        "consumed": round(consumed, 2),
        "status": "You need more calories!" if consumed < predicted else "You're good!"
    }

    return render_template('calorie_form.html', result=result)  # 🔁 Updated filename

if __name__ == '__main__':
    app.run(debug=True)
