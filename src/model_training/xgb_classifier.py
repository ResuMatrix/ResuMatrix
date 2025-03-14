from xgboost import XGBClassifier
from sklearn.model_selection import RandomizedSearchCV
import mlflow
import mlflow.xgboost
from sklearn.metrics import accuracy_score, classification_report

# def hyperparameter_tuning(X_train, y_train):
#     param_grid = {
#         'n_estimators': [100, 300, 500],  
#         'learning_rate': [0.01, 0.05, 0.1],  
#         'max_depth': [3, 5, 7],  
#         'subsample': [0.7, 0.8, 0.9],  
#         'colsample_bytree': [0.7, 0.8, 0.9]
#     }
    
#     xgb_model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    
#     random_search = RandomizedSearchCV(xgb_model, param_distributions=param_grid, n_iter=10, scoring='accuracy', cv=3, verbose=2, n_jobs=-1)
#     random_search.fit(X_train, y_train)

#     return random_search.best_estimator_, random_search.best_params_

def hyperparameter_tuning(X_train, y_train):
    param_grid = {
        'n_estimators': 300,  
        'learning_rate': 0.1,  
        'max_depth':  7,  
        'subsample': 0.9,  
        'colsample_bytree': 0.7
    }
    
    xgb_model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    
    random_search = RandomizedSearchCV(xgb_model, param_distributions=param_grid, n_iter=5, scoring='accuracy', cv=3, verbose=2, n_jobs=-1)
    random_search.fit(X_train, y_train)


    print(f"Best Parameters: {random_search.best_params_}")
    print(f"Best Score: {random_search.best_score_}")
    print(f"Best Estimator: {random_search.best_estimator_}")
    return random_search.best_estimator_, random_search.best_params_


def train_xgboost(X_train, y_train, X_test, y_test):
    with mlflow.start_run():

        # Perform hyperparameter tuning
        best_model, best_params = hyperparameter_tuning(X_train, y_train)

        # Log the best parameters
        mlflow.log_params(best_params)

        # Train the best model
        best_model.fit(X_train, y_train)

        # Predict on test set
        y_pred = best_model.predict(X_test)

        # Log the metrics
        accuracy = accuracy_score(y_test, y_pred)
        mlflow.log_metrics({"accuracy": accuracy})

        # Log the classification report
        classification_report = classification_report(y_test, y_pred)
        mlflow.log_text(classification_report, "classification_report.txt")

        # Log the model
        mlflow.xgboost.log_model(best_model, "xgboost_model")

        print(f"Model trained and logged with accuracy: {accuracy:.4f}")

        return best_model

def predict_xgboost(model, data):
    return model.predict(data)