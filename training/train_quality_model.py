import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from features.features_schema import FEATURE_COLUMNS

# ---------------- Load Dataset ----------------
DATA_PATH = "data/raw/project_dataset.csv"
df = pd.read_csv(DATA_PATH)

X = df[FEATURE_COLUMNS]
y = df["quality_score"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=8,
    random_state=42
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("Quality Model Evaluation")
print("------------------------")
print(f"MAE (avg error): {mae:.2f}")
print(f"R2 Score: {r2:.2f}")

MODEL_PATH = "models/quality_model.pkl"
joblib.dump(model, MODEL_PATH)

print(f"\nModel saved to {MODEL_PATH}")
