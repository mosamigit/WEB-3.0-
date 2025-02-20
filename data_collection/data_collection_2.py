import requests
import json
import logging
import os
import time

# Get the directory of the current script
script_directory = os.path.dirname(os.path.abspath(__file__))
config_directory=os.path.join(script_directory, '../config')
saved_data_directory=os.path.join(script_directory, 'collected_data.json')

# Read API endpoint URL from the configuration file
config_file_path = os.path.join(config_directory, "config_search_data.json")

# Create a directory for logs relative to the script directory
log_directory = os.path.join(script_directory, '../logs')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Configure logging
logging.basicConfig(filename=os.path.join(log_directory, "script_log.txt"), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def collect_data_and_save():

    try:
        with open(config_file_path, "r") as config_file:
            config_data = json.load(config_file)
            base_url = config_data.get("api_url")
            

        # Check if the URL was successfully read from the config file
        if base_url is None:
            raise ValueError("API URL not found in the configuration file.")
    except:
        logging.error("Unable to load the data")
        return

    page = 1
    data_list = []

    try:
        while True:
            # Construct the URL for the current page
            url = f"{base_url}?page={page}"

            # Make a GET request to the API
            response = requests.get(url)

            if response.status_code == 200:
                # Parse the JSON response
                response_data = response.json()

                # Check if there is data on the current page
                page_data = response_data.get("data", [])
                if not page_data:
                    # If no data is present, stop calling the API
                    break

                # Append the data from the current page to the list
                data_list.extend(page_data)
                print("length of datalist",len(data_list))
                logging.info(f"Data collected from page {page}")
                

                # Increment the page number for the next request
                page += 1
                # Add a 1-second delay to avoid overwhelming the server
                time.sleep(5)
            else:
                # Handle errors by raising an exception and logging the error
                response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Handle request exceptions (e.g., connection errors) and log the error
        logging.error(f"Request Exception: {e}")
    except json.JSONDecodeError as e:
        # Handle JSON decoding errors and log the error
        logging.error(f"JSON Decode Error: {e}")
    except Exception as e:
        # Handle other exceptions and log the error
        logging.error(f"An error occurred: {e}")

    # Load the existing data from collected_data.json (if it exists)
    existing_data = []
    if os.path.exists(saved_data_directory):
        with open(saved_data_directory, "r") as json_file:
            existing_data = json.load(json_file)

    # Compare the lengths of the new data and existing data
    if len(data_list) > len(existing_data):
        # Save the new data to the JSON file
        with open(saved_data_directory, "w") as json_file:
            json.dump(data_list, json_file)
        print("Data collection completed and saved to collected_data.json.")
    else:
        print("No new data collected. Existing data is up to date.")


collect_data_and_save()
