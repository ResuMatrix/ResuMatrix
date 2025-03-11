from src.data_processing.data_preprocessing import load_data, tf_idf_vectorization
from src.model_training.xgb_classifier import train_xgboost, predict_xgboost
from sklearn.metrics import accuracy_score


def execute_xgboost():

    train_data = load_data("train")
    X_train, y_train = tf_idf_vectorization(data_df=train_data)

    test_data = load_data("test")
    X_test, y_test = tf_idf_vectorization(data_df=test_data)

    xgboost_model = train_xgboost(X_train, y_train)

    y_pred = predict_xgboost(X_test, xgboost_model)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")


if __name__ == '__main__':
    execute_xgboost()
