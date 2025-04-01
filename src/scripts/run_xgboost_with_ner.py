from data_processing.data_preprocessing import load_data, lambda_and_cosine_similarity
import pickle
from model_training.xgboost_with_ner import extract_entity_overlap, compute_entity_overlap, extract_features, train_xgboost_model, predict_xgboost_with_ner
import os


def execute_xgboost_with_ner():
    # Load and preprocess data
    train_df = load_data("train")
    test_df = load_data("test")

    train_df = lambda_and_cosine_similarity(train_df)
    test_df = lambda_and_cosine_similarity(test_df)

    # Compute entity overlap
    train_df = extract_entity_overlap(train_df)
    test_df = extract_entity_overlap(test_df)

    # Compute entity-type-specific overlaps
    train_df = compute_entity_overlap(train_df)
    test_df = compute_entity_overlap(test_df)

    X_train, y_train = extract_features(train_df)
    X_test, y_test = extract_features(test_df)
    
    # Train the model
    xgboost_model_with_ner = train_xgboost_model(X_train, y_train, X_test, y_test)

    # Make predictions on test data
    y_pred = predict_xgboost_with_ner(xgboost_model_with_ner, X_test)

    return xgboost_model_with_ner

if __name__ == "__main__":
    xgboost_model_with_ner = execute_xgboost_with_ner()

filename = os.path.join('src', 'saved_models', 'xgboost_model_with_ner.pkl')
pickle.dump(xgboost_model_with_ner, open(filename, 'wb'))