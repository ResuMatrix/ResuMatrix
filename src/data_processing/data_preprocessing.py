import pandas as pd
import os
import numpy as np
import re
import nltk
import torch
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack
from transformers import BertTokenizer, BertModel

# Ensure necessary NLTK resources are available
nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Load BERT tokenizer and model
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Ensure necessary NLTK resources are available
nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Load BERT model and tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
bert_model = BertModel.from_pretrained('bert-base-uncased')

def clean_text(text):
    """Cleans text by removing special characters, numbers, and stopwords; applies lemmatization."""
    text = re.sub('http\S+\s*', ' ', text)  # remove URLs
    text = re.sub('RT|cc', ' ', text)  # remove RT and cc
    text = re.sub('#\S+', '', text)  # remove hashtags
    text = re.sub('@\S+', '  ', text)  # remove mentions
    text = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', text)  # remove punctuations
    text = re.sub(r'[^\x00-\x7f]',r' ', text)
    text = re.sub('\s+', ' ', text)  # remove extra whitespace
    tokens = word_tokenize(text.lower())  # Tokenization and lowercasing
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]  # Lemmatization & Stopword Removal
    return " ".join(tokens)

def encode_labels(df):
    """Encodes labels and removes rows with 'potential fit' label."""
    # Directly remove rows where label is 'Potential Fit'
    df.drop(df[df['label'] == "Potential Fit"].index, inplace=True)
    # Map labels to numerical values (Good Fit: 1, No Fit: 0)
    df['label'] = df['label'].map({"Good Fit": 1, "No Fit": 0})
    return df

def load_data(data_type="train"):
    current_file_path = os.path.abspath(__file__)
    if data_type not in ["train", "test"]:
        raise ValueError("Expecting data_type to be train or test.")

    parent_dir = current_file_path[:current_file_path.index("ResuMatrix") + 10]
    src_dir = os.path.join(parent_dir, "src")

    data_file_path = os.path.join(src_dir, "model_training_data", "resume_job_description_fit", data_type + ".csv")

    df = pd.read_csv(data_file_path)
    df = encode_labels(df)
    df.drop_duplicates(inplace=True)
    df.dropna(subset=["resume_text", "job_description_text"], inplace=True)

    # Apply text cleaning to resume_text and job_description_text
    df['resume_text'] = df['resume_text'].apply(clean_text)
    df['job_description_text'] = df['job_description_text'].apply(clean_text)

    return df

def load_data(data_type="train"):
    """Loads dataset, encodes labels, and applies text preprocessing."""
    current_file_path = os.path.abspath(__file__)
    if data_type not in ["train", "test"]:
        raise ValueError("Expecting data_type to be train or test.")

    parent_dir = current_file_path[:current_file_path.index("ResuMatrix") + 10]
    src_dir = os.path.join(parent_dir, "src")

    data_file_path = os.path.join(src_dir, "model_training_data", "resume_job_description_fit", data_type + ".csv")

    df = pd.read_csv(data_file_path)
    df = encode_labels(df)
    df.drop_duplicates(inplace=True)
    df.dropna(subset=["resume_text", "job_description_text"], inplace=True)

    # Apply text cleaning
    df['resume_text'] = df['resume_text'].apply(clean_text)
    df['job_description_text'] = df['job_description_text'].apply(clean_text)

    return df

def tf_idf_vectorization(data_df):
    """Performs TF-IDF vectorization on preprocessed text."""
    all_text = pd.concat([data_df['resume_text'], data_df['job_description_text']], axis=0)

    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2))
    vectorizer.fit(all_text)

    resume_tfidf = vectorizer.transform(data_df['resume_text'])
    job_tfidf = vectorizer.transform(data_df['job_description_text'])

    # Combine resume and job description features
    X = hstack([resume_tfidf, job_tfidf])
    y = data_df['label']

    return X, y, vectorizer

def get_bert_embeddings(text):
    """Generate BERT embeddings for text."""
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors='pt', max_length=512)
    with torch.no_grad():
        outputs = bert_model(**inputs)
    return outputs.last_hidden_state[:, 0, :].numpy().flatten()

def extract_embeddings(df):
    """Generate embeddings for resumes and job descriptions."""
    df['resume_embeddings'] = df['resume_text'].apply(get_bert_embeddings)
    df['job_embeddings'] = df['job_description_text'].apply(get_bert_embeddings)
    X = np.array([np.concatenate([r, j]) for r, j in zip(df['resume_embeddings'], df['job_embeddings'])])
    y = df['label'].values
    return X, y