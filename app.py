from flask import Flask, request, render_template
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

# Load your CSV
food_df = pd.read_csv('Indian_Food_Nutrition_Processing.csv')


# Convert 'Calories (kcal)' to numeric on load
food_df['Calories (kcal)'] = pd.to_numeric(food_df['Calories (kcal)'], errors='coerce')

# Standardize 'Dish Name' column in your DataFrame
food_df['Dish Name'] = food_df['Dish Name'].str.strip().str.lower()

@app.route('/')
def home():
    return render_template('index.html')  # home page

@app.route('/calorie-form')
def calorie_form():
    return render_template('calorie_form.html')  # input form page

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get user input for personal details
        username = request.form.get('username', '').strip().lower()
        meal_type = request.form.get('meal_type', '').strip().lower()
        age = int(request.form.get('age', 0))
        gender = request.form.get('gender', '').lower()
        weight = float(request.form.get('weight', 0))
        height = float(request.form.get('height', 0))

        # --- MODIFICATION START: Get lists of food names and quantities ---
        # Use getlist() to retrieve all values for inputs with the same name
        food_names_list = request.form.getlist('food_name')
        food_quantities_list = request.form.getlist('food_quantity')
        
        total_calories = 0
        found_items_display = [] # For display on the result page
        logged_food_entries = [] # For saving to meal_logs.csv

        # Iterate through the lists of food names and quantities
        # We iterate up to the length of the shorter list to avoid index errors
        for i in range(min(len(food_names_list), len(food_quantities_list))):
            food_name_input = food_names_list[i].strip()
            quantity_str_input = food_quantities_list[i].strip()
            
            # Skip empty food names, but still process if quantity is missing
            if not food_name_input:
                continue

            # Standardize food name for lookup
            food_name_lookup = food_name_input.lower()
            
            # Try converting quantity to float
            quantity_grams = None
            try:
                if quantity_str_input: # Check if string is not empty
                    quantity_grams = float(quantity_str_input)
            except ValueError:
                # quantity_grams remains None if conversion fails
                pass 

            # Prepare for logging (original case for display, quantity as provided)
            logged_food_entries.append(f"{food_name_input} ({quantity_str_input}g)")

            # Lookup food in DataFrame
            match = food_df[food_df['Dish Name'] == food_name_lookup]
            
            if not match.empty:
                calories_per_100g = match['Calories (kcal)'].values[0]
                
                if pd.isna(calories_per_100g):
                    found_items_display.append(f"{food_name_input} ({quantity_str_input}g): Calories not available in database.")
                elif quantity_grams is not None and quantity_grams > 0:
                    calculated_calories = (calories_per_100g / 100) * quantity_grams
                    total_calories += calculated_calories
                    found_items_display.append(f"{food_name_input} ({quantity_grams:.0f}g): {calculated_calories:.2f} kcal")
                else:
                    # Case: Food found, but quantity is invalid or 0
                    found_items_display.append(f"{food_name_input}: Invalid quantity '{quantity_str_input}'. Calories not calculated for this item.")
            else:
                found_items_display.append(f"{food_name_input}: Not found in database.")
        # --- MODIFICATION END ---

        # Save to meal_logs.csv
        new_data = {
            'username': username,
            'age': age,
            'meal_type': meal_type,
            'dish_name': ", ".join(logged_food_entries), # Use the prepared list for logging
            'calories': total_calories,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        new_df = pd.DataFrame([new_data])
        try:
            meal_log_df = pd.read_csv('meal_logs.csv')
            expected_columns = ['username', 'age', 'meal_type', 'dish_name', 'calories', 'timestamp']
            if list(meal_log_df.columns) != expected_columns:
                return render_template('result.html', result="Error: meal_logs.csv has unexpected columns. Please delete or fix the file to continue.")
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

        # Estimate required calories (BMR - Mifflin-St Jeor Equation)
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
        
        # print("Form data received:", request.form) # Commented out for cleaner console, uncomment if needed
        # print(f"[DEBUG] Meal Type Received: '{meal_type}'") # Commented out

        if meal_type not in ideal_meal_split:
            return render_template('result.html', result=f"Unknown meal type received: '{meal_type}'. Please select a valid option.")
        
        ideal_this_meal = required_calories * ideal_meal_split[meal_type]
        
        # Feedback on meal
        if total_calories > ideal_this_meal:
           meal_feedback = f" You consumed {total_calories:.2f} kcal in {meal_type.title()}, which is above the recommended {ideal_this_meal:.2f} kcal for this meal. Consider reducing intake."
        elif total_calories < ideal_this_meal * 0.8:
           meal_feedback = f" Your {meal_type.title()} calories ({total_calories:.2f} kcal) are quite low compared to the recommended {ideal_this_meal:.2f} kcal. Try including more nutrient-rich food."
        else:
           meal_feedback = f" Your {meal_type.title()} calories ({total_calories:.2f} kcal) are within the recommended range ({ideal_this_meal:.2f} kcal)."

        # Calculate BMI
        height_m = height / 100
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
        
        # Final result text construction
        result_text = (
            "\n".join(found_items_display) + # Use the list for display
            f"\n\nTotal Calories for this Meal: {total_calories:.2f} kcal" +
            f"\nRecommended for {meal_type.title()}: {ideal_this_meal:.2f} kcal" +
            f"\n{meal_feedback}" +
            f"\n\nTotal Calories Today: {total_today_calories:.2f} kcal" +
            f"\nEstimated Daily Requirement: {required_calories:.2f} kcal" +
            f"\n\nYour BMI: {bmi:.2f} ({bmi_category})"
        )

        return render_template('result.html', result=result_text, bmi_category=bmi_category)

    except Exception as e:
        print(f"An error occurred during prediction: {e}")
        return render_template('result.html', result=f"An unexpected error occurred: {str(e)}. Please try again or contact support.")

if __name__ == '__main__':
    app.run(debug=True)