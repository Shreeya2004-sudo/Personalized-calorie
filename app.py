from flask import Flask, request, render_template
import pandas as pd

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
        # Get user food input
        foods = request.form.get('foods', '').lower().split(',')
        selected_foods = [food.strip() for food in foods]

        # Get user info
        age = int(request.form.get('age', 0))
        gender = request.form.get('gender', '').lower()
        weight = float(request.form.get('weight', 0))
        height = float(request.form.get('height', 0))

        # Calculate consumed calories
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

        # Estimate required calories using Mifflin-St Jeor BMR formula
        if gender == 'male':
            required_calories = 10 * weight + 6.25 * height - 5 * age + 5
        elif gender == 'female':
            required_calories = 10 * weight + 6.25 * height - 5 * age - 161
        else:
            required_calories = 0

        # Result to display
        result_text = (
            "\n".join(found_items) +
            f"\n\nTotal Calories Consumed: {total_calories:.2f} kcal" +
            f"\nEstimated Daily Requirement: {required_calories:.2f} kcal"
        )

        return render_template('result.html', result=result_text)

    except Exception as e:
        return render_template('result.html', result=f"Error occurred: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
