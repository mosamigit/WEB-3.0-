import pandas as pd
import json
import re
import pickle
import nltk
import logging
import os
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer

# Get the directory of the current script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Create a directory for logs relative to the script directory
log_directory = os.path.join(script_directory, '../logs')
data_collection_directory = os.path.join(script_directory, '../data_collection')
data_directory=os.path.join(data_collection_directory, 'collected_data.json')
tfidf_vectorizer_directory=os.path.join(script_directory, 'tfidf_vectorizer.pkl')
purchase_history_directory=os.path.join(script_directory, 'purchase_history.pkl')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Configure logging
logging.basicConfig(filename=os.path.join(log_directory, "script_log.txt"), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def preprocess_text(text):
    # Remove HTML tags
    text = re.sub(r'<.*?>', ' ', text)
    # Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', ' ', text).lower()
    # Tokenize the text
    tokens = nltk.word_tokenize(text)
    # Remove stopwords
    tokens = [word for word in tokens if word not in stopwords.words('english')]
    # Lemmatization
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return ' '.join(tokens)

def process_data_and_save():
    try:
        # Load the JSON data
        with open(data_directory, 'r') as file:  
            data = json.load(file)

        # Extract the relevant data part
        data_part = data
        # print(data_part)

        # Flatten the nested JSON structure using json_normalize
        data = pd.json_normalize(data_part, record_path=['searchInfo'], meta=['customerEmailId'])

        # Rename columns as needed
        data.rename(columns={'customerEmailId': 'customerEmailId'}, inplace=True)

        data['logs'] = data['product_name'] + ' ' + data['sku'] + ' ' + data['description']

        # Apply preprocessing to the 'overview' column
        data['logs'] = data['logs'].apply(preprocess_text)

        # Create a purchase history dataframe
        purchase_history = data.groupby(['customerEmailId','sku', 'product_name','logs']).size().reset_index(name='purchase_count')

        # Define a TF-IDF vectorizer for product descriptions (assuming you have product descriptions in your data)
        tfidf_vectorizer = TfidfVectorizer()

        # Fit the vectorizer on the product descriptions
        product_descriptions = data['logs'].fillna('')
        tfidf_vectorizer.fit(product_descriptions)

        # Save tfidf_vectorizer to a pickle file
        with open(tfidf_vectorizer_directory, 'wb') as file:
            pickle.dump(tfidf_vectorizer, file)

        # Save purchase_history to a pickle file
        with open(purchase_history_directory, 'wb') as file:
            pickle.dump(purchase_history, file)
        print("done______________")

        logging.info("Data processing and model retraining completed.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


process_data_and_save()