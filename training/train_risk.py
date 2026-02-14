import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

from features.features_schema import FEATURE_COLUMNS


# ---------------- Load Dataset ----------------

DATA_PATH = "data/raw/project_dataset.csv"
df = pd.read_csv(DATA_PATH)

FEATURES = [
    "file_count",
    "folder_count",
    "max_depth",
    "has_services",
    "has_utils",
    "avg_file_lines",
    "ui_score",
    "complexity_score",
    "quality_score"  
]

X = df[FEATURES]
y = df["risk"]



# ---------------- Encode Risk Labels ----------------

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)


# ---------------- Train / Test Split ----------------
# No stratify to avoid small-dataset edge cases

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.2,
    random_state=42
)


# ---------------- Train Model ----------------

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    class_weight="balanced",
    random_state=42
)

model.fit(X_train, y_train)


# ---------------- Evaluate ----------------

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print("\nRisk Detection Model Evaluation")
print("--------------------------------")
print(f"Accuracy: {accuracy:.2f}\n")

# Safe classification report (handles missing classes in test set)
unique_labels = sorted(set(y_test))

print(
    classification_report(
        y_test,
        y_pred,
        labels=unique_labels,
        target_names=label_encoder.inverse_transform(unique_labels)
    )
)


# ---------------- Save Model ----------------

joblib.dump(model, "models/risk_model.pkl")
joblib.dump(label_encoder, "models/risk_label_encoder.pkl")

print("\nSaved:")
print(" - models/risk_model.pkl")
print(" - models/risk_label_encoder.pkl")
