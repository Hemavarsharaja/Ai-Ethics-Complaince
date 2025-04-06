from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import joblib
import json
import shap
import numpy as np

from fairlearn.metrics import MetricFrame, equalized_odds_difference
from sklearn.metrics import accuracy_score

app = FastAPI()

# Enable CORS for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load dataset based on file extension
def load_dataset(file: UploadFile) -> pd.DataFrame:
    if file.filename.endswith(".csv"):
        return pd.read_csv(file.file)
    elif file.filename.endswith(".json"):
        return pd.read_json(file.file)
    raise ValueError("Unsupported dataset format.")

# Load model file
def load_model(file: UploadFile):
    if file.filename.endswith(".pkl"):
        return joblib.load(file.file)
    raise ValueError("Unsupported model format.")

@app.post("/analyze/")
async def analyze_model(
    model_name: str = Form(...),
    model_description: str = Form(...),
    model_file: UploadFile = File(...),
    dataset_file: UploadFile = File(...),
    selected_checks: str = Form(...)
):
    try:
        checks = json.loads(selected_checks)
        dataset = load_dataset(dataset_file)
        model = load_model(model_file)

        target_col = dataset.columns[-1]
        X = dataset.drop(columns=[target_col])
        y_true = dataset[target_col]

        y_pred = model.predict(X)

        score = 100
        risks = []
        suggestions = []

        # Bias Check
        if "Bias Check" in checks:
            if 'gender' in X.columns:
                mf = MetricFrame(metrics=accuracy_score, y_true=y_true, y_pred=y_pred, sensitive_features=X['gender'])
                disparity = mf.difference()
                if disparity > 0.1:
                    score -= 15
                    risks.append("Bias detected based on gender.")
                    suggestions.append("Ensure balanced data representation across genders.")
            else:
                suggestions.append("Include sensitive attributes like 'gender' for better bias analysis.")

        # Transparency Audit using SHAP
        if "Transparency Audit" in checks:
            try:
                explainer = shap.Explainer(model, X)
                shap_values = explainer(X)
                if np.mean(np.abs(shap_values.values)) < 0.01:
                    score -= 10
                    risks.append("Model features have low explainability.")
                    suggestions.append("Use SHAP or LIME to explain model predictions.")
            except Exception:
                score -= 10
                suggestions.append("Model lacks transparency. Use interpretable models or SHAP.")

        # Privacy Scan
        if "Privacy Scan" in checks:
            if any("id" in col.lower() or "name" in col.lower() for col in X.columns):
                score -= 10
                risks.append("Dataset may contain PII.")
                suggestions.append("Remove or anonymize personally identifiable data.")

        # Fairness Metrics Check
        if "Fairness Metrics Check" in checks:
            if 'gender' in X.columns:
                eo_diff = equalized_odds_difference(y_true, y_pred, sensitive_features=X['gender'])
                if eo_diff > 0.2:
                    score -= 15
                    risks.append("Unequal treatment across groups.")
                    suggestions.append("Balance accuracy across demographic subgroups.")

        # Representativeness Check
        if "Representativeness Check" in checks:
            minority_threshold = 0.1
            underrepresented = [
                col for col in X.select_dtypes(include='object').columns
                if dataset[col].value_counts(normalize=True).min() < minority_threshold
            ]
            if underrepresented:
                score -= 10
                risks.append("Underrepresentation of minority groups.")
                suggestions.append("Ensure minority groups are well represented in training data.")

        # Robustness Check
        if "Robustness Check" in checks:
            try:
                X_noisy = X.copy()
                for col in X_noisy.select_dtypes(include='number').columns:
                    X_noisy[col] += np.random.normal(0, 0.01, X_noisy.shape[0])
                y_noisy_pred = model.predict(X_noisy)
                drop = accuracy_score(y_true, y_pred) - accuracy_score(y_true, y_noisy_pred)
                if drop > 0.1:
                    score -= 10
                    risks.append("Model is not robust to small input variations.")
                    suggestions.append("Test model with adversarial or noisy input data.")
            except Exception:
                suggestions.append("Robustness testing failed. Ensure model handles noise.")

        # Clamp score between 0 and 100
        score = max(0, min(100, score))
        risk_level = (
            "High" if score < 40 else
            "Medium" if score < 70 else
            "Low"
        )

        return {
            "model_name": model_name,
            "model_description": model_description,
            "compliance_score": score,
            "risk_level": risk_level,
            "risks": risks or ["No major risks detected."],
            "suggestions": suggestions or ["Model meets the required ethical standards."]
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
