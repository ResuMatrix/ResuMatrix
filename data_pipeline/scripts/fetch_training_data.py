import os
import pandas as pd
import requests
import logging
import socket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("RESUMATRIX_API_URL", "http://host.docker.internal:8000/api")


def check_api_connection():
    """
    Check if the API is reachable and responding.
    Returns True if the API is reachable, False otherwise.
    """
    # Extract hostname from API_BASE_URL
    try:
        url_parts = API_BASE_URL.split('://')
        if len(url_parts) > 1:
            host_part = url_parts[1].split('/')[0]
            if ':' in host_part:
                hostname, port = host_part.split(':')
                port = int(port)
            else:
                hostname = host_part
                port = 80 if url_parts[0] == 'http' else 443
        else:
            hostname = API_BASE_URL
            port = 80

        logger.info(f"Checking connection to {hostname}:{port}...")

        # Try to resolve the hostname
        try:
            ip_address = socket.gethostbyname(hostname)
            logger.info(f"Hostname {hostname} resolved to {ip_address}")
        except socket.gaierror as e:
            logger.error(f"Failed to resolve hostname {hostname}: {e}")
            return False

        # Try to connect to the host
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((hostname, port))
            sock.close()

            if result == 0:
                logger.info(f"Successfully connected to {hostname}:{port}")
            else:
                logger.error(f"Failed to connect to {hostname}:{port} (error code: {result})")
                return False
        except socket.error as e:
            logger.error(f"Socket error connecting to {hostname}:{port}: {e}")
            return False

        # Try to make a simple HTTP request
        # First try a health endpoint if it exists
        health_endpoints = [
            f"{API_BASE_URL}/health",
            f"{API_BASE_URL.rstrip('/api')}/health",
            f"{API_BASE_URL}/jobs"
        ]

        for endpoint in health_endpoints:
            try:
                logger.info(f"Testing API endpoint: {endpoint}")
                response = requests.get(endpoint, timeout=5)
                if response.status_code < 500:  # Accept any non-server error response
                    logger.info(f"API responded with status code {response.status_code}")
                    return True
            except requests.RequestException as e:
                logger.warning(f"Failed to connect to {endpoint}: {e}")
                continue

        logger.error("All API test endpoints failed")
        return False

    except Exception as e:
        logger.error(f"Error checking API connection: {e}")
        return False


def get_joined_resumes_from_api() -> list[dict]:
    try:
        logger.info(f"Fetching jobs from ResuMatrix API at {API_BASE_URL}...")
        jobs_response = requests.get(f"{API_BASE_URL}/jobs/", timeout=10)
        jobs_response.raise_for_status()

        # Extract the jobs list from the response
        response_data = jobs_response.json()
        if isinstance(response_data, dict) and "jobs" in response_data:
            jobs = response_data["jobs"]
        else:
            jobs = response_data  # Fallback if response is already a list

        logger.info(f"Retrieved {len(jobs)} jobs.")

        joined_count = 0
        result = []

        for job in jobs:
            job_id = job.get("id")
            job_text = job.get("job_text", "")
            if not job_id or not job_text:
                logger.warning(f"Skipping job with missing id or text: {job}")
                continue

            logger.info(f"Processing job ID: {job_id}")
            resumes_url = f"{API_BASE_URL}/jobs/{job_id}/resumes"
            resumes_response = requests.get(resumes_url, timeout=10)

            if resumes_response.status_code == 200:
                response_data = resumes_response.json()

                # Extract resumes and job_text from the response
                if isinstance(response_data, dict):
                    if "resumes" in response_data:
                        resumes = response_data["resumes"]
                        # If job_text is in the response, use it (it might be more up-to-date)
                        if "job_text" in response_data:
                            job_text = response_data["job_text"]
                    else:
                        logger.warning(f"No 'resumes' key in response for job_id {job_id}")
                        continue
                else:
                    resumes = response_data  # Fallback if response is already a list

                logger.info(f"Retrieved {len(resumes)} resumes for job ID {job_id}")
            else:
                logger.warning(f"Failed to get resumes for job_id {job_id}: {resumes_response.status_code}")
                continue

            resume_count = 0
            for resume in resumes:
                # Check if this resume has feedback
                if resume.get("feedback_label") != 1:
                    continue

                status = resume.get("status")
                if status == 1:
                    label = "fit"
                elif status == 0:
                    label = "no fit"
                else:
                    continue

                result.append({
                    "job_description_text": job_text,
                    "resume_text": resume.get("resume_text", ""),
                    "label": label
                })
                joined_count += 1
                resume_count += 1

            logger.info(f"Added {resume_count} matching resumes for job ID {job_id}")

        logger.info(f"Joined {joined_count} resume-job pairs from API.")
        if not result:
            logger.warning("No matching resume-job pairs found.")
        return result

    except requests.RequestException as e:
        logger.error(f"API request error: {e}")
        import traceback
        logger.error(f"Detailed traceback: {traceback.format_exc()}")
        raise


def fetch_existing_training_data() -> pd.DataFrame:
    try:
        logger.info("Fetching existing training data from /api/training/data")
        response = requests.get(f"{API_BASE_URL}/training/data", timeout=10)
        response.raise_for_status()

        # Parse the response
        response_data = response.json()

        # Handle different response formats
        if isinstance(response_data, dict):
            # If response is a dict, look for data in common keys
            if "data" in response_data:
                data = response_data["data"]
            elif "training_data" in response_data:
                data = response_data["training_data"]
            else:
                # If no recognized keys, use the whole dict
                data = [response_data]
        elif isinstance(response_data, list):
            # If response is already a list, use it directly
            data = response_data
        else:
            logger.error(f"Unexpected training data response type: {type(response_data)}")
            return pd.DataFrame()

        if not data:
            logger.warning("Training data response is empty.")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        expected_columns = {"job_description_text", "resume_text", "label"}
        if not expected_columns.issubset(df.columns):
            logger.error(f"Training data missing expected columns. Found columns: {df.columns.tolist()}")
            return pd.DataFrame()

        logger.info(f"Fetched {len(df)} existing training records")
        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch existing training data: {e}")
        logger.error(f"Request URL: {API_BASE_URL}/training/data")
        import traceback
        logger.error(f"Detailed traceback: {traceback.format_exc()}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error fetching training data: {e}")
        import traceback
        logger.error(f"Detailed traceback: {traceback.format_exc()}")
        return pd.DataFrame()


def fetch_training_data() -> pd.DataFrame:
    try:
        logger.info("Starting training data fetch process...")

        # First check if the API is reachable
        if not check_api_connection():
            logger.error("API connection check failed. Cannot proceed with fetching training data.")
            raise ConnectionError("Cannot connect to the API. Please check if the backend API is running and accessible.")

        logger.info("API connection check passed. Proceeding with data fetch...")
        logger.info("Fetching initial and new training data...")

        # Fetch existing training data
        existing_df = fetch_existing_training_data()
        logger.info(f"Existing training data shape: {existing_df.shape}")

        # Fetch new training data
        new_data = get_joined_resumes_from_api()
        new_df = pd.DataFrame(new_data)
        logger.info(f"New joined resume-job data shape: {new_df.shape}")

        # Define valid labels
        def is_valid_label(label): return label in ["fit", "no fit", "potential fit"]

        # Combine datasets
        all_data = pd.concat([existing_df, new_df], ignore_index=True)
        logger.info(f"Combined data shape: {all_data.shape}")

        # Clean and validate data
        valid_data = all_data.dropna(subset=["job_description_text", "resume_text", "label"])
        logger.info(f"Data after dropping NAs: {valid_data.shape}")

        valid_data = valid_data[valid_data["label"].apply(is_valid_label)]
        logger.info(f"Data after filtering valid labels: {valid_data.shape}")

        # Remove duplicates
        deduped_data = valid_data.drop_duplicates(subset=["job_description_text", "resume_text"])
        logger.info(f"Final deduplicated training data shape: {deduped_data.shape}")

        if deduped_data.empty:
            logger.warning("No valid training data found after processing.")

        return deduped_data

    except ConnectionError as e:
        # Re-raise connection errors for visibility
        logger.error(f"Connection error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error merging training data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def save_training_data(df, output_path=None):
    try:
        if output_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/opt/airflow/data/training_data_{timestamp}.csv"

        dirname = os.path.dirname(output_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        df.to_csv(output_path, index=False)
        logger.info(f"Training data saved to {output_path}")

        return output_path
    except Exception as e:
        logger.error(f"Error saving training data: {str(e)}")
        raise


if __name__ == "__main__":
    df = fetch_training_data()
    save_training_data(df)
