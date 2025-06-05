import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# Load real dataset
data = pd.read_csv('Indian_Food_Nutrition_Processing.csv')  # Make sure this file exists

# Features and target
X = data[['Age', 'Weight', 'Height']]
y = data['Calories_Needed']

# Train model
model = LinearRegression()
model.fit(X, y)

# Save the model
joblib.dump(model, 'calorie_model.pkl')
print("✅ Model trained and saved using real data!")
