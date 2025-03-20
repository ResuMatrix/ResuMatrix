from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import mlflow
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def calculate_cosine_similarity(resume_embeddings, job_embeddings):
    """Calculates cosine similarity between resume and job description embeddings."""
    similarity_scores = []
    for resume, job in zip(resume_embeddings, job_embeddings):
        similarity = cosine_similarity(resume.reshape(1, -1), job.reshape(1, -1))[0][0]
        similarity_scores.append(similarity)
    return np.array(similarity_scores)

def train_cosine_similarity_model(X_train, y_train, X_test, y_test):
    """Trains a model using cosine similarity scores and logs it with MLflow."""
    with mlflow.start_run():
        # Calculate cosine similarity scores
        train_similarity = calculate_cosine_similarity(X_train[:, :X_train.shape[1]//2], X_train[:, X_train.shape[1]//2:])
        test_similarity = calculate_cosine_similarity(X_test[:, :X_test.shape[1]//2], X_test[:, X_test.shape[1]//2:])

        # Use similarity scores as features
        X_train_final = train_similarity.reshape(-1, 1)
        X_test_final = test_similarity.reshape(-1, 1)

        # Train a simple logistic regression model
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression()
        model.fit(X_train_final, y_train)

        # Predict on test set
        y_pred = model.predict(X_test_final)

        # Log metrics
        accuracy = accuracy_score(y_test, y_pred)
        mlflow.log_metrics({"accuracy": accuracy})

        # Log classification report
        class_report = classification_report(y_test, y_pred)
        mlflow.log_text(class_report, "classification_report.txt")

        conf_matrix = confusion_matrix(y_test, y_pred)
        mlflow.log_text(str(conf_matrix), "confusion_matrix.txt")

        # Save the model
        mlflow.sklearn.log_model(model, "cosine_similarity_model")

        print(f"Cosine Similarity Model trained and logged with accuracy: {accuracy:.4f}")

        return model