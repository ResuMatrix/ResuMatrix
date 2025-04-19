from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
import mlflow
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def train_xgboost_model(X_train, y_train, X_test, y_test):
    """Train XGBoost model with class balancing (SMOTE)."""
    import logging
    logger = logging.getLogger(__name__)

    smote = SMOTE()
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

    # Train the model
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train_balanced, y_train_balanced)

    # Evaluate the model
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    class_report = classification_report(y_test, y_pred)
    conf_matrix = confusion_matrix(y_test, y_pred)

    # Log to MLflow if available
    try:
        with mlflow.start_run():
            try:
                mlflow.set_experiment("XGBoost Model with Similarity")
                mlflow.log_params(model.get_params())
                mlflow.log_metric("accuracy", acc)
                mlflow.log_metrics({"classification_report": class_report})
                mlflow.log_metrics({"confusion_matrix": conf_matrix})
                mlflow.sklearn.log_model(model, "Xgboost_with_similarity_model")
                logger.info("Successfully logged model to MLflow")
            except Exception as e:
                logger.warning(f"Error logging to MLflow: {str(e)}")
    except Exception as e:
        logger.warning(f"Could not start MLflow run: {str(e)}")
        logger.warning("Continuing without MLflow tracking...")

    print(f"XGBoost Model with cosine similarity Accuracy: {acc:.4f}")
    return model

def predict_xgboost(model, data):
    """Predict using the trained XGboost model."""
    return model.predict(data)