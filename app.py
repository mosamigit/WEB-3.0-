import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from flask import Flask, request, jsonify
from fuzzywuzzy import fuzz
from training.training import process_data_and_save
from data_collection.data_collection_2 import collect_data_and_save
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
# Call the function to process data and save it
# from training.training import process_data_and_save



app = Flask(__name__)

# Get the directory of the current script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Create a directory for logs relative to the script directory
pickle_directory = os.path.join(script_directory, 'training')
tfidf_vectorizer_pickle_directory=os.path.join(pickle_directory, 'tfidf_vectorizer.pkl')
purchase_history_pickle_directory=os.path.join(pickle_directory, 'purchase_history.pkl')


# Load tfidf_matrix from the pickle file
with open(tfidf_vectorizer_pickle_directory, 'rb') as file:
    tfidf_vectorizer = pickle.load(file)

# Load purchase_history from the pickle file
with open(purchase_history_pickle_directory, 'rb') as file:
    purchase_history = pickle.load(file)

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


purchase_history_new=purchase_history['product_name']

def find_related_customers(product_name):
    # Check if the specified product_name is in purchase_history
    if product_name not in purchase_history['product_name'].unique():
        # Find a similar product_name based on fuzzy matching
        similar_product_name = find_similar_product_name(product_name)
        # Create a pivot table with the similar_product_name
        pivot_table = purchase_history.pivot_table(index='customerEmailId', columns='product_name', values='purchase_count', fill_value=0)
        correlations = pivot_table.corrwith(pivot_table[similar_product_name])
    else:
        # Create a pivot table with the specified product_name
        pivot_table = purchase_history.pivot_table(index='customerEmailId', columns='product_name', values='purchase_count', fill_value=0)
        correlations = pivot_table.corrwith(pivot_table[product_name])

    # Drop NaN values and sort in descending order
    correlations = correlations.dropna().sort_values(ascending=False)

    return correlations

# Function to find a similar product_name using FuzzyWuzzy
def find_similar_product_name(product_name):
    # Initialize variables to keep track of the closest product and its score
    closest_product = None
    highest_score = -1  # Initialize with a value lower than any possible score

    # Iterate through unique product names in purchase_history
    unique_product_names = purchase_history['product_name'].unique()
    
    for unique_product in unique_product_names:
        # Calculate the fuzzy matching score between the specified product_name and each unique product name
        score = fuzz.ratio(product_name, unique_product)
        # Update closest_product and highest_score if a better match is found
        if score > highest_score:
            closest_product = unique_product
            highest_score = score

    return closest_product

# Define a function to extract product names from the input data
def extract_product_names(input_data):
    if "data" in input_data and "searchInfo" in input_data["data"]:
        product_list = [item["product_name"] for item in input_data["data"]["searchInfo"]]
        return product_list
    return []

# Define a function to parse the date and time string into a datetime object
def parse_datetime(datetime_str):
    return datetime.strptime(datetime_str, "%A, %B %d, %Y at %I:%M:%S %p")

# Define a function to find related products for a given customer's email
def find_related_products_for_email(customer_email,product_list,target_product_name):
    # Create an empty set to store related products
    related_products_set = set()
    # Iterate through the products purchased by the customer
    if len(product_list) > 1:
        for product_name in product_list:
            if product_name != target_product_name:  # Exclude the target product itself
                # Get the correlations for the current product
                correlations = find_related_customers(product_name)

                # Remove the customer's own product from the correlations
                correlations = correlations.drop(customer_email, errors='ignore')

                # Get the top related products for the current product (excluding the target product)
                top_related_products = correlations.head(5).index.tolist()

                # Extend the set of related products
                related_products_set.update(top_related_products)
    else:
        for product_name in product_list:
            correlations = find_related_customers(product_name)
            # Remove the customer's own product from the correlations
            correlations = correlations.drop(customer_email, errors='ignore')
            # Get the top related products for the current product (excluding the target product)
            top_related_products = correlations.head(5).index.tolist()

            # Extend the set of related products
            related_products_set.update(top_related_products)

    # Convert the set to a list and take unique products
    related_products_list = list(related_products_set)

    return related_products_list[:5]

# Define a function to find the most similar products to a given product name using cosine similarity
def find_most_similar_products(related_products_list,target_product_name, top_n=5):
    # Calculate the TF-IDF vector for the target product name
    target_product_vector = tfidf_vectorizer.transform([target_product_name])

    # Initialize an empty list to store cosine similarity scores
    similarity_scores = []

    # Iterate through the related products and calculate cosine similarity
    for product in related_products_list:
        product_vector = tfidf_vectorizer.transform([product])
        similarity_score = cosine_similarity(target_product_vector, product_vector)
        similarity_scores.append((product, similarity_score))

    # Sort the list by similarity score in descending order
    similarity_scores.sort(key=lambda x: x[1], reverse=True)

    # Get the top N most similar products (excluding the target product)
    top_similar_products = [product[0] for product in similarity_scores[:top_n]]

    return top_similar_products


# Define the API endpoint for recommendations
@app.route('/get_recommendations', methods=['GET','POST'])
def get_recommendations():
    # Parse the input JSON data from the request
    input_data = request.json
    customer_email_to_find_related_products = input_data["data"]["customerEmailId"]

    search_info = input_data["data"]["searchInfo"]
    sorted_search_info = sorted(search_info, key=lambda x: parse_datetime(x["searchDate"]), reverse=True)
    target_product_name = sorted_search_info[0]["product_name"]
    target_product_desc = sorted_search_info[0]["description"]
    target_product_log = target_product_name + target_product_desc
    target_product_clean=preprocess_text(target_product_log)
    product_list = extract_product_names(input_data)
    # related_products = find_related_products_for_email(customer_email_to_find_related_products, product_list, target_product_name)

    # Calculate the TF-IDF vectors for all products
    all_products_sku = purchase_history['sku'].unique()
    all_products = purchase_history['product_name'].unique()
    all_products_logs = purchase_history['product_name'].unique()
    all_product_vectors = tfidf_vectorizer.transform(all_products_logs)

    # Calculate cosine similarity between the target product and all products
    target_product_vector = tfidf_vectorizer.transform([target_product_clean])
    cosine_similarity_scores = cosine_similarity(target_product_vector, all_product_vectors)

    # Get the indices of the top 5 most similar products
    top_cosine_tfidf_indices = cosine_similarity_scores.argsort()[0][::-1][1:6]
    
    # Get the product names corresponding to the top indices
    top_cosine_tfidf_similar_products = [all_products[i] for i in top_cosine_tfidf_indices]
    top_cosine_tfidf_similar_sku = [all_products_sku[i] for i in top_cosine_tfidf_indices]


    # Return both sets of recommendations as JSON response
    return jsonify({
        "top_suggested_sku": top_cosine_tfidf_similar_sku,
        "top_recommended_products": top_cosine_tfidf_similar_products
    })
    # return top_cosine_tfidf_similar_products

if __name__ == '__main__':
    app.run(debug=True)