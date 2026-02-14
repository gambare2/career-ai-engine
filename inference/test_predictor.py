from inference.predictor import UnifiedPredictor

MODEL_PATH = "models/quality_model.pkl"

predictor = UnifiedPredictor(MODEL_PATH)

sample_features = {
    "file_count": 170,
    "folder_count": 11,
    "max_depth": 4,
    "has_services": 1,
    "has_utils": 1,
    "avg_file_lines": 115,
    "ui_score": 8.0,
    "complexity_score": 7.4
}

predicted_score = predictor.predict(sample_features)

print("Predicted Quality Score:", predicted_score)
