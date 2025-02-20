import requests
import json
import logging
import os

# Create a directory for logs if it doesn't exist
log_directory = "../logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Configure logging
logging.basicConfig(
    filename=os.path.join(log_directory, "script_log.txt"),
    level=logging.INFO,  # Set the logging level as needed
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Read API endpoint URL from the configuration file
config_file_path = os.path.join("../config", "config_search_data.json")

try:
    with open(config_file_path, "r") as config_file:
        config_data = json.load(config_file)
        url = config_data.get("api_url")

    # Check if the URL was successfully read from the config file
    if url is None:
        raise ValueError("API URL not found in the configuration file.")

    # Send a GET request to the API
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Define the output JSON file path
        output_file_path = "output.json"

        # Write the data to the JSON file
        with open(output_file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        print(f"Data saved to {output_file_path}")

        # Log a success message
        logging.info("Data saved successfully.")
    else:
        print(f"Request failed with status code {response.status_code}")

        # Log an error message
        logging.error(f"Request failed with status code {response.status_code}")

except FileNotFoundError:
    print(f"Configuration file not found: {config_file_path}")

    # Log an error message
    logging.error(f"Configuration file not found: {config_file_path}")

except (ValueError, json.JSONDecodeError) as e:
    print(f"Error reading the configuration file: {e}")

    # Log an error message
    logging.error(f"Error reading the configuration file: {e}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

    # Log the error message
    logging.error(f"An error occurred: {e}")
