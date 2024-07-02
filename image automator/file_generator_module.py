from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError
from elasticsearch.helpers import bulk
from sentence_transformers import SentenceTransformer
import torch
import time
import csv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Set device for model inference
device = torch.device('cpu')

# Initialize Sentence Transformer model and Elasticsearch client
model = SentenceTransformer('sentence-transformers/gtr-t5-xl')
model.to(device)
client = None

# Constants
INDEX_NAME = "cat-keywords-2"
BATCH_SIZE = 20

# Predefined query objects
query_objects = [
    {"query": "merchandise", "label": "0"},
    {"query": "careers", "label": "1"},
    {"query": "manuals/training", "label": "2"},
    {"query": "technology", "label": "3"},
    {"query": "account/finance", "label": "4"},
    {"query": "warranty", "label": "5"},
    {"query": "sis sos fluid-oil analysis", "label": "6"},
    {"query": "pornography adult", "label": "7"},
    {"query": "gibberish", "label": "11"}
]

def get_time():
    """
    Returns the current time in HH:MM:SS format.
    """
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    return current_time

def embed_text(text):
    """
    Embeds the given text using the Sentence Transformer model.
    
    Parameters:
    text (list of str): The text to embed.
    
    Returns:
    list: A list of embeddings.
    """
    vectors = model.encode(text, device=device)
    return [vector.tolist() for vector in vectors]

def index_batch(docs):
    """
    Indexes a batch of documents in Elasticsearch.
    
    Parameters:
    docs (list of dict): The documents to index.
    """
    quotes = [doc["search_keyword"] for doc in docs]
    quote_vectors = embed_text(quotes)
    requests = []
    for i, doc in enumerate(docs):
        request = doc
        request["_op_type"] = "index"
        request["_index"] = INDEX_NAME
        request["vector"] = quote_vectors[i]
        requests.append(request)
    bulk(client, requests)

def set_client(elastic_address=""):
    """
    Sets the Elasticsearch client.
    
    Parameters:
    elastic_address (str): The address of the Elasticsearch server.
    
    Returns:
    bool: True if the client was successfully set, False otherwise.
    """
    global client
    client = Elasticsearch(elastic_address, request_timeout=10, max_retries=3)
    if not client.ping():
        print(f"Elasticsearch client not found in '{elastic_address}'.")
        return False
    return True

def index_data(data_file):
    """
    Reads a CSV file and indexes its contents in Elasticsearch.
    
    Parameters:
    data_file (str): The path to the CSV file.
    """
    list_dict = []
    with open(data_file, mode='r') as csv_file:
        count = 0
        for line in csv_file:
            data_content = line.strip()
            if data_content:
                dict = {'search_keyword': data_content}
                list_dict.append(dict)
                count += 1
                if count % BATCH_SIZE == 0:
                    index_batch(list_dict)
                    list_dict = []
                    print(f"Indexed {count} documents.")
                    print("time =", get_time())
            else:
                print(f"Skipping line {count + 1}, it is empty. Data = {data_content}")
    if list_dict:
        index_batch(list_dict)
        print(f"Indexed {count} documents.")

def generate_files(output_dir="output"):
    """
    Generates CSV files with search keywords based on predefined query objects.
    
    Parameters:
    output_dir (str): The directory to save the output files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for query_object in query_objects:
        query_vector = embed_text([query_object["query"]])[0]
        added_terms = set()

        knn = {
            "field": "vector",
            "k": 1000,
            "num_candidates": 10000,
            "query_vector": query_vector
        }

        response = client.search(index=INDEX_NAME, knn=knn, source=["search_keyword"], size=1000)
        relevant_hits = [hit for hit in response["hits"]["hits"] if hit["_score"] >= 0.75]

        output_file = os.path.join(output_dir, query_object["query"].replace("\"", "").replace(" ", "_").replace("/", "_") + ".csv")
        with open(output_file, "w") as f:
            for rhit in relevant_hits:
                search_term = rhit["_source"]["search_keyword"].replace(",", " ").replace("\"", "")
                if search_term not in added_terms:
                    added_terms.add(search_term)
                    f.write(f'{query_object["label"]},{search_term}\n')

        print(f"Total for {query_object['query']} : {len(added_terms)}")
    print("done!")
