import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from sklearn.preprocessing import LabelEncoder


def encode_labels(df):
    le = LabelEncoder()
    label = le.fit_transform(df['label'])
    df.drop("label", axis=1, inplace=True)
    df['label'] = label
    return df


def load_data(data_type="train"):
    current_file_path = os.path.abspath(__file__)
    if data_type not in ["train", "test"]:
        raise ValueError("Expecting data_type to be train or test.")

    parent_dir = current_file_path[:current_file_path.index("ResuMatrix") + 10]
    src_dir = os.path.join(parent_dir, "src")

    data_file_path = os.path.join(src_dir, "model_training_data", "resume_job_description_fit", data_type + ".csv")
    return encode_labels(pd.read_csv(data_file_path))


def tf_idf_vectorization(data_df):
    all_text = pd.concat([data_df['resume_text'], data_df['job_description_text']], axis=0)

    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    vectorizer.fit(all_text)

    resume_tfidf = vectorizer.transform(data_df['resume_text'])
    job_tfidf = vectorizer.transform(data_df['job_description_text'])

    X = np.hstack((resume_tfidf.toarray(), job_tfidf.toarray()))
    y = data_df['label']

    return X, y

