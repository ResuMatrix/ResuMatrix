import pandas as pd
import os
import numpy as np
import re
import string
import torch
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import BertTokenizer, BertModel

# Load BERT tokenizer and model
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TOKENIZER = BertTokenizer.from_pretrained('bert-base-uncased')
BERT_MODEL = BertModel.from_pretrained('bert-base-uncased').to(DEVICE)

# Ensure necessary NLTK resources are available
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def clean_text(text):
    """Cleans text by removing special characters, numbers, and stopwords; applies lemmatization."""
    text = re.sub('http\S+\s*', ' ', text)  # remove URLs
    text = re.sub('RT|cc', ' ', text)  # remove RT and cc
    text = re.sub('#\S+', '', text)  # remove hashtags
    text = re.sub('@\S+', '  ', text)  # remove mentions
    text = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', text)  # remove punctuations
    text = re.sub(r'[^\x00-\x7f]',r' ', text) 
    text = re.sub('\s+', ' ', text)  # remove extra whitespace
    tokens = word_tokenize(text)  # Tokenization
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]  # Lemmatization & Stopword Removal
    return " ".join(tokens)


# def encode_labels(df):
#     le = LabelEncoder()
#     label = le.fit_transform(df['label'])
#     df.drop("label", axis=1, inplace=True)
#     df['label'] = label
#     return df

def encode_labels(df):
    """Encodes labels and maps 'potential fit' to 'no fit' (0)."""
    df['label'] = df['label'].replace("potential fit", "no fit")  # Convert 'potential fit' to 'no fit'
    le = LabelEncoder()
    df['label'] = le.fit_transform(df['label'])  # Encode labels
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

def get_bert_embedding(text):
    """Generates BERT embeddings for a given text."""
    encoded_input = TOKENIZER(text, padding='max_length', truncation=True, max_length=256, return_tensors="pt")
    
    # Move tensors to GPU/CPU
    encoded_input = {key: value.to(DEVICE) for key, value in encoded_input.items()}
    
    with torch.no_grad():
        output = BERT_MODEL(**encoded_input)
    
    # Use CLS token representation (first token in sequence)
    return output.last_hidden_state[:, 0, :].cpu().numpy()

def bert_vectorization(data_df):
    """Performs BERT-based vectorization on preprocessed text."""
    resume_embeddings = np.array([get_bert_embedding(text) for text in data_df['resume_text']])
    job_embeddings = np.array([get_bert_embedding(text) for text in data_df['job_description_text']])
    
    # Reshape (batch_size, hidden_dim)
    resume_embeddings = resume_embeddings.squeeze()
    job_embeddings = job_embeddings.squeeze()

    # Concatenate resume and job description embeddings
    X = np.hstack((resume_embeddings, job_embeddings))
    y = data_df['label']

    return X, y


# def tf_idf_vectorization(data_df):
#     """Performs TF-IDF vectorization on preprocessed text."""
#     all_text = pd.concat([data_df['resume_text'], data_df['job_description_text']], axis=0)

#     vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2))
#     vectorizer.fit(all_text)

#     resume_tfidf = vectorizer.transform(data_df['resume_text'])
#     job_tfidf = vectorizer.transform(data_df['job_description_text'])

#     X = np.hstack((resume_tfidf.toarray(), job_tfidf.toarray()))
#     y = data_df['label']

#     return X, y