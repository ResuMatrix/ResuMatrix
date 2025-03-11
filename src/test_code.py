import logging

# Setup logging
logging.basicConfig(filename='test_code_exec.log', level=logging.INFO)

def main():
    logging.info("Script Started Successfully.")
    print("Hello from Docker Container!")
    logging.info("Script Finished Successfully.")

if __name__ == "__main__":
    main()
