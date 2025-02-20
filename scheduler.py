import schedule
import os
import time
import logging
import time
from training.training import process_data_and_save
from data_collection.data_collection_2 import collect_data_and_save

# Get the directory of the current script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Create a directory for logs relative to the script directory
log_directory = os.path.join(script_directory, 'logs')

if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Configure logging
logging.basicConfig(
    filename=os.path.join(log_directory, "script_log.txt"),
    level=logging.INFO,  # Set the logging level as needed
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def job():
    logging.info("Running data collection...")
    collect_data_and_save()
    logging.info("Running data processing...")
    process_data_and_save()

# Schedule the job to run every 5 minutes
schedule.every(1).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
