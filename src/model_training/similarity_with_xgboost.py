from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
import mlflow
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def train_xgboost_model(X_train, y_train, X_test, y_test):
    """Train XGBoost model with class balancing (SMOTE)."""
    smote = SMOTE()
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
    
    with mlflow.start_run():

        mlflow.set_experiment("XGBoost Model with Similarity")

        model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
        mlflow.log_params(model.get_params())

        model.fit(X_train_balanced, y_train_balanced)
        
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        mlflow.log_metric("accuracy", acc)

        # Log classification report
        class_report = classification_report(y_test, y_pred)
        mlflow.log_metrics({"classification_report": class_report})

        conf_matrix = confusion_matrix(y_test, y_pred)
        mlflow.log_metrics({"confusion_matrix": conf_matrix})
        #test 3

        # Save the model
        mlflow.sklearn.log_model(model, "Xgboost_with_similarity_model")
    
        print(f"XGBoost Model with cosine similarity Accuracy: {acc:.4f}")
        return model
    
def predict_xgboost(model, data):
    """Predict using the trained XGboost model."""
    return model.predict(data)