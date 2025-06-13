from flask import Flask, request, render_template
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# Load your CSV
food_df = pd.read_csv('Indian_Food_Nutrition_Processing.csv')

@app.route('/')
def home():
    return render_template('index.html')  # home page

@app.route('/calorie-form')
def calorie_form():
    return render_template('calorie_form.html')  # input form page

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get user input
        username = request.form.get('username', '').strip().lower()
        meal_type = request.form.get('meal_type', '').strip().lower()
        foods = request.form.get('foods', '').lower().split(',')
        selected_foods = [food.strip() for food in foods]
        age = int(request.form.get('age', 0))
        gender = request.form.get('gender', '').lower()
        weight = float(request.form.get('weight', 0))
        height = float(request.form.get('height', 0))

        # Calculate calories for current meal
        total_calories = 0
        found_items = []

        for food in selected_foods:
            match = food_df[food_df['Dish Name'].str.lower() == food]
            if not match.empty:
                calories = match['Calories (kcal)'].values[0]
                total_calories += calories
                found_items.append(f"{food.title()}: {calories} kcal")
            else:
                found_items.append(f"{food.title()}: Not found")

        # Save to meal_logs.csv
        new_data = {
            'username': username,
            'meal_type': meal_type,
            'dish_name': ", ".join(selected_foods),
            'calories': total_calories,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        new_df = pd.DataFrame([new_data])
        try:
            meal_log_df = pd.read_csv('meal_logs.csv')
            new_df.to_csv('meal_logs.csv', mode='a', header=False, index=False)
        except FileNotFoundError:
            new_df.to_csv('meal_logs.csv', mode='w', header=True, index=False)

        # Load logs and calculate today's total
        meal_log_df = pd.read_csv('meal_logs.csv')
        meal_log_df['timestamp'] = pd.to_datetime(meal_log_df['timestamp'])

        today = datetime.now().date()
        user_today_meals = meal_log_df[
            (meal_log_df['username'] == username) &
            (meal_log_df['timestamp'].dt.date == today)
        ]

        total_today_calories = user_today_meals['calories'].sum()

        # Estimate required calories
        if gender == 'male':
            required_calories = 10 * weight + 6.25 * height - 5 * age + 5
        elif gender == 'female':
            required_calories = 10 * weight + 6.25 * height - 5 * age - 161
        else:
            required_calories = 0

        # Final result
        result_text = (
            "\n".join(found_items) +
            f"\n\nTotal Calories for this Meal: {total_calories:.2f} kcal" +
            f"\nCumulative Calories Today: {total_today_calories:.2f} kcal" +
            f"\nEstimated Daily Requirement: {required_calories:.2f} kcal"
        )

        return render_template('result.html', result=result_text)

    except Exception as e:
        return render_template('result.html', result=f"Error occurred: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
