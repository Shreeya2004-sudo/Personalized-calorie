from flask import Flask, request, render_template, jsonify
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression
import csv
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)

# Load your CSV
food_df = pd.read_csv('Indian_Food_Nutrition_Processing.csv')

def save_prediction(username, dish_name, predicted_calories, meal_type):
    current_date = datetime.now().date()
    timestamp = datetime.now()

    # Write to user_meal_logs.csv (original detailed log)
    with open('user_meal_logs.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([username, current_date, dish_name, round(predicted_calories, 2), meal_type])

    # Also write to meal_logs.csv for graph generation
    with open('meal_logs.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([username, timestamp, dish_name, round(predicted_calories, 2), meal_type])


#graph representation

def generate_weekly_graph(username):
    try:
        df = pd.read_csv("user_meal_logs.csv")
        df.columns = df.columns.str.strip()

        # Filter by username
        df = df[df["Username"] == username]
        if df.empty:
            print("No data found for user.")
            return None

        # Normalize MealType and enforce known categories
        df["MealType"] = df["MealType"].str.strip().str.lower().str.capitalize()
        valid_meals = ["Breakfast", "Lunch", "Dinner", "Snacks"]
        df = df[df["MealType"].isin(valid_meals)]

        # Convert Date and Calories
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        df["Calories"] = pd.to_numeric(df["Calories"], errors='coerce')
        df.dropna(subset=["Date", "Calories"], inplace=True)

        # Limit to last 7 days
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        one_week_ago = today - timedelta(days=6)
        df = df[(df["Date"] >= one_week_ago) & (df["Date"] <= today)]

        if df.empty:
            print("No data for the past 7 days.")
            return None

        # Group by Date and MealType
        df["Date"] = df["Date"].dt.date
        grouped = df.groupby(["Date", "MealType"])["Calories"].sum().unstack(fill_value=0)

        # Ensure all 7 dates exist
        all_days = pd.date_range(end=today, periods=7).date
        grouped = grouped.reindex(all_days, fill_value=0)

        # Ensure all meal types are present
        for meal in valid_meals:
            if meal not in grouped.columns:
                grouped[meal] = 0
        grouped = grouped[valid_meals]

        # Plot grouped bar chart
        plt.figure(figsize=(10, 6))
        bar_width = 0.2
        dates = grouped.index.astype(str)
        x = np.arange(len(dates))

        for i, meal in enumerate(valid_meals):
            plt.bar(x + i * bar_width, grouped[meal], width=bar_width, label=meal)

        plt.title("Weekly Calorie Intake by Meal")
        plt.xlabel("Date")
        plt.ylabel("Calories")
        plt.xticks(x + bar_width * 1.5, dates, rotation=45)
        plt.legend()
        plt.tight_layout()

        # Save plot
        graph_path = f'static/weekly_graph_{username}.png'
        plt.savefig(graph_path)
        plt.close()
        return graph_path

    except Exception as e:
        print(f"Error generating weekly graph: {e}")
        return None



# Convert 'Calories (kcal)' to numeric on load
food_df['Calories (kcal)'] = pd.to_numeric(food_df['Calories (kcal)'], errors='coerce')

# Standardize 'Dish Name' column in your DataFrame
food_df['Dish Name'] = food_df['Dish Name'].str.strip().str.lower()

# Clean and train ML model
train_df = food_df.dropna(subset=['Dish Name', 'Calories (kcal)'])
train_df = train_df[train_df['Calories (kcal)'] > 0]

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(train_df['Dish Name'])
y = train_df['Calories (kcal)']

model = LinearRegression()
model.fit(X, y)

def predict_calories_with_model(dish_name):
    vector = vectorizer.transform([dish_name])
    predicted = model.predict(vector)[0]
    return round(predicted, 2)


@app.route('/')
def home():
    return render_template('index.html')  # home page

@app.route('/calorie-form')
def calorie_form():
    return render_template('calorie_form.html')  # input form page

@app.route('/predict', methods=['POST'])
def predict():
    username = request.form['username']
    age = int(request.form['age'])
    gender = request.form['gender']
    weight = float(request.form['weight'])
    height = float(request.form['height'])
    meal_type = request.form['meal_type'].lower()

    food_names = request.form.getlist('food_name')
    food_quantities = request.form.getlist('food_quantity')

    total_calories = 0
    log_lines = []

    # Step 1: Calculate recommended daily calorie intake using Mifflin-St Jeor Equation
    if gender.lower() == 'male':
      bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
      bmr = 10 * weight + 6.25 * height - 5 * age - 161
    # Assuming sedentary activity level
    recommended_cal = round(bmr * 1.2, 2)  # 1.2 for sedentary, 1.55 for moderate, 1.9 for active


    # Step 2: Recommended calorie split by meal
    recommended_split = {
        'Breakfast': round(recommended_cal * 0.25, 2),
        'Lunch': round(recommended_cal * 0.35, 2),
        'Dinner': round(recommended_cal * 0.30, 2),
        'Snacks': round(recommended_cal * 0.10, 2)
    }

    # Initialize consumed calorie split
    consumed_split = {
        "breakfast": 0,
        "lunch": 0,
        "dinner": 0
    }

    # Normalize meal_type for consistency
    meal_type_cap = meal_type.capitalize()

    for name, qty in zip(food_names, food_quantities):
        qty = float(qty)
        match = food_df[food_df['Dish Name'].str.lower() == name.strip().lower()]

        if not match.empty:
            row = match.iloc[0]
            base_cal = row['Calories (kcal)']
            predicted_cal = base_cal * (qty / 100)
            log_lines.append(f"{name} ({qty}g): {predicted_cal:.2f} kcal")
        else:
            predicted_cal = predict_calories_with_model(name)
            log_lines.append(f"{name} ({qty}g): {predicted_cal:.2f} kcal (estimated)")

        total_calories += predicted_cal
        consumed_split[meal_type] += predicted_cal  # meal_type is already lowercase

        # Save prediction
        save_prediction(username, name, predicted_cal, meal_type_cap)

    # STEP: Load previous meal data for the same user and date
    # Get today's date
    today = pd.to_datetime('today').normalize()
    # Load existing logs
    meal_logs = pd.read_csv('user_meal_logs.csv')
    # Filter for current user and today's date
    user_meals_today = meal_logs[
    (meal_logs['Username'] == username) &
    (pd.to_datetime(meal_logs['Date']).dt.normalize() == today)
    ]
    # Group and sum calories by Meal_type
    consumed_split = user_meals_today.groupby('MealType')['Calories'].sum().to_dict()
    # Ensure all keys are present
    for meal in ['Breakfast', 'Lunch', 'Dinner', 'Snacks']:
      if meal not in consumed_split:
        consumed_split[meal] = 0.0


    # Generate weekly graph
    graph_path = generate_weekly_graph(username)

    result_text = "\n".join(log_lines) + f"\n\nTotal Calories Consumed: {total_calories:.2f} kcal"

    return render_template('result.html',
                           result=result_text,
                           graph_path=graph_path,
                           recommended_cal=recommended_cal,
                           recommended_split=recommended_split,
                           consumed_split=consumed_split)


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '').lower()  # Get the typed query from URL (?q=...)
    
    # Filter dish names that contain the query (case-insensitive)
    suggestions = [
        dish for dish in food_df['Dish Name'].dropna().unique().tolist()
        if query in dish.lower()
    ]

    return jsonify(suggestions[:10])  # Return top 10 matching suggestions


if __name__ == '__main__':
    app.run(debug=True)