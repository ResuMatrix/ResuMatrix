import logging
import os
from datetime import datetime

# Ensure logs directory exists
log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)

# Setup logging
log_file = os.path.join(log_dir, f"log-{datetime.now().strftime('%Y%m%d%H%M%S')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Test script logic
def main():
    logging.info("====== Starting Automatio Test Code ======")
    print("Running the test script...")
    for i in range(5):
        logging.info(f"Processing step {i+1}")
        print(f"Step {i+1} complete.")
    logging.info("====== Automatio Test Code Finished ======")

if __name__ == "__main__":
    main()