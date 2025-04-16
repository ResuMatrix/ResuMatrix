import os
import pandas as pd
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("RESUMATRIX_API_URL", "http://host.docker.internal:8000/api")

def get_joined_resumes_from_api() -> list[dict]:
    try:
        logger.info(f"Fetching jobs from ResuMatrix API at {API_BASE_URL}...")
        jobs_response = requests.get(f"{API_BASE_URL}/jobs/", timeout=10)
        jobs_response.raise_for_status()
        jobs = jobs_response.json().get("jobs", [])
        logger.info(f"Retrieved {len(jobs)} jobs.")

        logger.info("Fetching all resumes...")
        resumes_response = requests.get(f"{API_BASE_URL}/resumes/", timeout=10)
        resumes_response.raise_for_status()
        resumes = resumes_response.json().get("resumes", [])
        logger.info(f"Retrieved {len(resumes)} resumes.")

        # Build job lookup by ID
        job_map = {job["id"]: job.get("job_text", "") for job in jobs}
        joined_data = 0
        result = []

        for resume in resumes:
            if resume.get("feedback_label") != 1:
                continue

            job_id = resume.get("job_id")
            job_text = job_map.get(job_id)
            if not job_text:
                continue  # Skip if job not found

            status = resume.get("status")
            if status == 1:
                label = "fit"
            elif status == 0:
                label = "no fit"
            else:
                continue  # Skip if status not explicitly fit/no fit

            result.append({
                "job_description_text": job_text,
                "resume_text": resume.get("resume_text", ""),
                "label": label
            })
            joined_data += 1

        logger.info(f"Joined {joined_data} resume-job pairs from API.")
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

        data = response.json()
        if not isinstance(data, list):
            logger.error("Training data response is not a list.")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        expected_columns = {"job_description_text", "resume_text", "label"}
        if not expected_columns.issubset(df.columns):
            logger.error(f"Training data missing expected columns. Found columns: {df.columns.tolist()}")
            return pd.DataFrame()

        logger.info(f"Fetched {len(df)} existing training records")
        return df

    except Exception as e:
        logger.error(f"Failed to fetch existing training data: {e}")
        return pd.DataFrame()


def fetch_training_data() -> pd.DataFrame:
    """
    Fetch and merge training data from the ResuMatrix API.
    Combines initial training data and newly joined resumes.
    """
    try:
        logger.info("Fetching initial and new training data...")
        existing_df = fetch_existing_training_data()
        new_data = get_joined_resumes_from_api()
        new_df = pd.DataFrame(new_data)

        logger.info(f"New joined resume-job data shape: {new_df.shape}")

        # Validate and filter both datasets
        def is_valid_label(label): return label in ["fit", "no fit", "potential fit"]
        all_data = pd.concat([existing_df, new_df], ignore_index=True)

        # Drop rows with missing fields or invalid labels
        valid_data = all_data.dropna(subset=["job_description_text", "resume_text", "label"])
        valid_data = valid_data[valid_data["label"].apply(is_valid_label)]

        # Remove duplicates
        deduped_data = valid_data.drop_duplicates(subset=["job_description_text", "resume_text"])
        logger.info(f"Final deduplicated training data shape: {deduped_data.shape}")

        return deduped_data

    except Exception as e:
        logger.error(f"Error merging training data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise



def save_training_data(df, output_path=None):
    """
    Save the training data to a CSV file.

    Args:
        df (pandas.DataFrame): Training data DataFrame
        output_path (str, optional): Path to save the CSV file. If None, saves to the data directory.

    Returns:
        str: Path to the saved CSV file
    """
    try:
        if output_path is None:
            # Save to the Airflow data directory with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/opt/airflow/data/training_data_{timestamp}.csv"

        # If the output_path has a directory component, ensure it exists
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
