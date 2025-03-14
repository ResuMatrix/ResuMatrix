from data_processing.data_preprocessing import load_data, bert_vectorization
from model_training.xgb_classifier import train_xgboost, predict_xgboost
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report


def execute_xgboost():
    # Load and preprocess training data
    train_data = load_data("train")
    X_train, y_train = bert_vectorization(data_df=train_data)
    # Load and preprocess test data
    test_data = load_data("test")
    X_test, y_test = bert_vectorization(data_df=test_data)
    # Train model
    xgboost_model = train_xgboost(X_train, y_train)
    # Make predictions on test data
    y_pred = predict_xgboost(xgboost_model, X_test)

    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))


if __name__ == '__main__':
    execute_xgboost()
