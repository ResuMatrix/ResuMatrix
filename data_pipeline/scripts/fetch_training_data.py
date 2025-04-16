import os
import pandas as pd
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("RESUMATRIX_API_URL", "http://host.docker.internal:8000/api")

def get_joined_resumes_from_api() -> list[dict]:
    """
    Fetch resumes with feedback_label=1 from the ResuMatrix API and join with job descriptions.
    Returns a list of dictionaries containing job_description_text, resume_text, and label.
    """
    try:
        logger.info(f"Fetching jobs from ResuMatrix API at {API_BASE_URL}...")

        # Detailed logging for jobs request
        try:
            jobs_response = requests.get(f"{API_BASE_URL}/jobs/", timeout=10)
            logger.info(f"Jobs API response status code: {jobs_response.status_code}")

            # Log response headers for debugging
            logger.debug(f"Response headers: {dict(jobs_response.headers)}")

            # Check for error status codes
            jobs_response.raise_for_status()

            # Parse response
            jobs = jobs_response.json()
            logger.info(f"Successfully retrieved {len(jobs)} jobs from API")
        except requests.exceptions.Timeout:
            logger.error("Request to jobs API timed out after 10 seconds")
            raise
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Connection error to jobs API: {conn_err}")
            raise
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error from jobs API: {http_err}")
            # Log response content if available
            if hasattr(jobs_response, 'text'):
                logger.error(f"Response content: {jobs_response.text[:500]}")
            raise
        except ValueError as json_err:
            logger.error(f"Invalid JSON in jobs API response: {json_err}")
            logger.error(f"Response content: {jobs_response.text[:500]}")
            raise

        joined_data = []

        for job in jobs:
            job_id = job["id"]
            job_text = job.get("job_text", "")
            logger.info(f"Processing job ID: {job_id}")

            # Detailed logging for resumes request
            try:
                resumes_url = f"{API_BASE_URL}/jobs/{job_id}/resumes"
                logger.info(f"Fetching resumes from: {resumes_url}")
                resumes_response = requests.get(resumes_url, timeout=10)
                logger.info(f"Resumes API response status code: {resumes_response.status_code}")

                # Check for error status codes
                resumes_response.raise_for_status()

                # Parse response
                resumes = resumes_response.json()
                logger.info(f"Successfully retrieved {len(resumes)} resumes for job ID {job_id}")
            except requests.exceptions.Timeout:
                logger.error(f"Request to resumes API for job ID {job_id} timed out after 10 seconds")
                continue  # Skip this job but continue with others
            except requests.exceptions.ConnectionError as conn_err:
                logger.error(f"Connection error to resumes API for job ID {job_id}: {conn_err}")
                continue  # Skip this job but continue with others
            except requests.exceptions.HTTPError as http_err:
                logger.error(f"HTTP error from resumes API for job ID {job_id}: {http_err}")
                # Log response content if available
                if hasattr(resumes_response, 'text'):
                    logger.error(f"Response content: {resumes_response.text[:500]}")
                continue  # Skip this job but continue with others
            except ValueError as json_err:
                logger.error(f"Invalid JSON in resumes API response for job ID {job_id}: {json_err}")
                logger.error(f"Response content: {resumes_response.text[:500]}")
                continue  # Skip this job but continue with others

            # Process resumes for this job
            matched_resumes = 0
            for resume in resumes:
                if resume.get("feedback_label") != 1:
                    continue

                status = resume.get("status")
                if status == 1:
                    label = "fit"
                elif status == 0:
                    label = "no fit"
                else:
                    continue  # Skip if not explicitly fit or no fit

                joined_data.append({
                    "job_description_text": job_text,
                    "resume_text": resume.get("resume_text", ""),
                    "label": label
                })
                matched_resumes += 1

            logger.info(f"Added {matched_resumes} matching resumes for job ID {job_id}")

        logger.info(f"Fetched and joined {len(joined_data)} resume-job pairs from API.")
        if not joined_data:
            logger.warning("No matching resume-job pairs found in the API.")
        return joined_data

    except requests.RequestException as e:
        logger.error(f"API request error: {e}")
        import traceback
        logger.error(f"Detailed traceback: {traceback.format_exc()}")
        raise


def fetch_training_data() -> pd.DataFrame:
    """
    Fetch training data from the ResuMatrix API and return as a DataFrame.
    Only includes joined resumes with feedback_label=1.
    """
    try:
        logger.info("Fetching training data from ResuMatrix API...")
        joined_data = get_joined_resumes_from_api()
        training_df = pd.DataFrame(joined_data)

        if training_df.empty:
            logger.warning("No training data found from API.")
        else:
            logger.info(f"Training dataset shape: {training_df.shape}")

        return training_df

    except Exception as e:
        logger.error(f"Error fetching training data: {str(e)}")
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
