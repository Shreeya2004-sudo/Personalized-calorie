# Personalized-calorie
🥗 Personalized Calorie Tracker with ML & Weekly Insights

A full-stack Flask web application that tracks your daily meals, predicts calories using machine learning, and provides personalized weekly insights through charts and health recommendations.

📌 Key Features

🔹 Meal Logging by Type — Log food under Breakfast, Lunch, Dinner, or Snacks  
🔹 Quantity-Based Input — Enter food items and quantity (in grams)  
🔹 Calorie Prediction with ML — ML model predicts calories for unknown dishes  
🔹 Meal-wise Weekly Graph — Visualize calories across each meal for 7 days  
🔹 Macronutrient Pie Chart — Weekly breakdown of Carbs, Proteins, and Fats  
🔹 Insightful Report Generator— Auto-generated analysis with pros/cons of your diet  
🔹 Autocomplete Suggestions — Smart search bar with dish name suggestions  
🔹 "Search in Google" Option— Instantly search unknown food items externally  


🧠 ML Model Used

- Model Type: TF-IDF Vectorizer + Linear Regression  
- Purpose: Predict calorie value for unknown dishes using food name similarity  
- Training Data: Indian food nutrition dataset (CSV)

 💻 Tech Stack

| Frontend           | Backend               | Machine Learning      | Data Handling       |
|--------------------|------------------------|------------------------|---------------------|
| HTML, CSS, JS       | Python + Flask         | Scikit-learn, Pandas   | CSV files (lightweight) |
