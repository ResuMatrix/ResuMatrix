from data_processing.data_preprocessing import load_data, bert_vectorization, tf_idf_vectorization
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib


def train_logistic_regression(X_train, y_train):
    model = LogisticRegression(max_iter=1000, solver='lbfgs')
    model.fit(X_train, y_train)
    return model


def predict_logistic_regression(model, X_test):
    return model.predict(X_test)


def execute_logistic_regression():
    # Load and preprocess training data
    train_data = load_data("train")
    X_train, y_train = tf_idf_vectorization(train_data)
    # X_train, y_train = bert_vectorization(data_df=train_data)

    # Load and preprocess test data
    test_data = load_data("test")
    X_test, y_test = tf_idf_vectorization(test_data)
    # X_test, y_test = bert_vectorization(data_df=test_data)

    # Train model
    logistic_model = train_logistic_regression(X_train, y_train)

    # Save the model
    joblib.dump(logistic_model, "logistic_model.pkl")

    # Make predictions on test data
    y_pred = predict_logistic_regression(logistic_model, X_test)

    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred))


if __name__ == '__main__':
    execute_logistic_regression()
