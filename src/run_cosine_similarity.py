from model_training.cosine_similarity import train_cosine_similarity_model, calculate_cosine_similarity
from data_processing.data_preprocessing import load_data, tf_idf_vectorization
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")

def execute_cosine_similarity():

    # Load and preprocess training data
    train_data = load_data("train")
    X_train, y_train, vectorizer = tf_idf_vectorization(data_df=train_data)

    # Load and preprocess test data
    test_data = load_data("test")
    X_test, y_test, _ = tf_idf_vectorization(data_df=test_data)

    # Train cosine similarity model
    model = train_cosine_similarity_model(X_train, y_train, X_test, y_test)

    # Make predictions on test data
    test_similarity = calculate_cosine_similarity(X_test[:, :X_test.shape[1]//2], X_test[:, X_test.shape[1]//2:])
    X_test_final = test_similarity.reshape(-1, 1)
    y_pred = model.predict(X_test_final)

    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("Classification report:", classification_report(y_test, y_pred))
    print("Confusion matrix:", confusion_matrix(y_test, y_pred))
    return model

if __name__ == '__main__':
    model = execute_cosine_similarity()

filename = 'cosine_similarity_model.pkl'
pickle.dump(model, open(filename, 'wb'))