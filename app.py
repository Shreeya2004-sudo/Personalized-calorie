from flask import Flask, request, render_template
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# Load your CSV
food_df = pd.read_csv('Indian_Food_Nutrition_Processing.csv')


# Convert 'Calories (kcal)' to numeric on load
food_df['Calories (kcal)'] = pd.to_numeric(food_df['Calories (kcal)'], errors='coerce')

# --- NEW ADDITION: Standardize 'Dish Name' column in your DataFrame ---
food_df['Dish Name'] = food_df['Dish Name'].str.strip().str.lower()
# --- END NEW ADDITION ---

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
        selected_foods = [food.strip() for food in foods] # User input is already stripped and lowercased here
        
        age = int(request.form.get('age', 0))
        gender = request.form.get('gender', '').lower()
        weight = float(request.form.get('weight', 0))
        height = float(request.form.get('height', 0))

        # Calculate calories for current meal
        total_calories = 0
        found_items = []

        for food_input in selected_foods: # Rename 'food' to 'food_input' for clarity
            # --- MODIFIED LINE FOR BETTER MATCHING ---
            # Now we are matching the already stripped and lowercased user input
            # with the already stripped and lowercased 'Dish Name' column in food_df
            match = food_df[food_df['Dish Name'] == food_input]
            # --- END MODIFIED LINE ---

            if not match.empty:
                calories = match['Calories (kcal)'].values[0]
                if pd.isna(calories):
                    found_items.append(f"{food_input.title()}: Calories not available")
                else:
                    total_calories += calories
                    found_items.append(f"{food_input.title()}: {calories} kcal")
            else:
                found_items.append(f"{food_input.title()}: Not found")

        # Save to meal_logs.csv
        new_data = {
            'username': username,
            'age':age,
            'meal_type': meal_type,
            'dish_name': ", ".join(selected_foods),
            'calories': total_calories,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        new_df = pd.DataFrame([new_data])
        try:
            meal_log_df = pd.read_csv('meal_logs.csv')
            expected_columns = ['username', 'age', 'meal_type', 'dish_name', 'calories', 'timestamp']
            if list(meal_log_df.columns) != expected_columns:
                raise ValueError("meal_logs.csv has wrong columns. Delete or fix the file.")
            new_df.to_csv('meal_logs.csv', mode='a', header=False, index=False)
        except FileNotFoundError:
            new_df.to_csv('meal_logs.csv', mode='w', header=True, index=False)

        # Load logs and calculate today's total
        meal_log_df = pd.read_csv('meal_logs.csv')
        meal_log_df['timestamp'] = pd.to_datetime(meal_log_df['timestamp'])
        meal_log_df['calories'] = pd.to_numeric(meal_log_df['calories'], errors='coerce')


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

        ideal_meal_split = {
           'breakfast': 0.25,
           'lunch': 0.35,
           'dinner': 0.30,
           'snacks': 0.10
        }
        print("Form data received:", request.form)  # NEW
        print(f"[DEBUG] Meal Type Received: '{meal_type}'")  # Already added
        meal_type = request.form.get('meal_type', '').strip().lower()

        if meal_type not in ideal_meal_split:
          return render_template('result.html', result=f"⚠️ Unknown meal type received: '{meal_type}'. Please select a valid option.")
        ideal_this_meal = required_calories * ideal_meal_split[meal_type]
        
        if total_calories > ideal_this_meal:
           meal_feedback = f"⚠️ You consumed {total_calories:.2f} kcal in {meal_type.title()}, which is above the recommended {ideal_this_meal:.2f} kcal. Consider reducing intake."
        elif total_calories < ideal_this_meal * 0.8:
           meal_feedback = f"🔔 Your {meal_type.title()} calories ({total_calories:.2f} kcal) are quite low. Try including more nutrient-rich food."
        else:
           meal_feedback = f"✅ Your {meal_type.title()} calories are within the recommended range."



        # Calculate BMI
        height_m = height / 100  # convert cm to meters
        if height_m > 0:
          bmi = round(weight / (height_m ** 2), 2)
        else:
          bmi = 0

        # Classify BMI
        if bmi < 18.5:
          bmi_category = "Underweight"
        elif 18.5 <= bmi < 25:
          bmi_category = "Normal"
        elif 25 <= bmi < 30:
          bmi_category = "Overweight"
        else:
          bmi_category = "Obese"
        




        # Final result
        result_text = (
          "\n".join(found_items) +
          f"\n\nTotal Calories for this Meal: {total_calories:.2f} kcal" +
          f"\nRecommended for {meal_type.title()}: {ideal_this_meal:.2f} kcal" +
          f"\n{meal_feedback}" +
          f"\n\nTotal Calories Today: {total_today_calories:.2f} kcal" +
          f"\nEstimated Daily Requirement: {required_calories:.2f} kcal" +
          f"\n\nYour BMI: {bmi:.2f} ({bmi_category})"
        )


        return render_template('result.html', result=result_text,bmi_category=bmi_category) # Pass to HTML



    except Exception as e:
        return render_template('result.html', result=f"Error occurred: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)