import logging
from datetime import datetime

# Setup logging
log_file = f"logs/log-{datetime.now().strftime('%Y%m%d%H%M%S')}.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Test script logic
def main():
    logging.info("====== Starting Test Code ======")
    print("Running the test script...")
    for i in range(5):
        logging.info(f"Processing step {i+1}")
        print(f"Step {i+1} complete.")
    logging.info("====== Test Code Finished ======")

if __name__ == "__main__":
    main()