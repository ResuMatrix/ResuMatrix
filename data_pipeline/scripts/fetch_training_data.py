import os
import pandas as pd
from supabase import create_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_training_data():
    """
    Fetch training data from Supabase:
    1. Get existing training_data table
    2. Get joined data from resumes and jobs tables where feedback_label=1
    3. Combine both datasets with proper formatting

    Returns:
        pandas.DataFrame: Combined training dataset with job_description_text, resume_text, and label columns
    """
    try:
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")

        supabase = create_client(supabase_url, supabase_key)
        logger.info("Connected to Supabase")

        # Step 1: Fetch existing training data
        logger.info("Fetching existing training data...")
        training_data_result = supabase.table("training_data").select("job_description_text", "resume_text", "label").execute()

        if not training_data_result.data:
            logger.warning("No existing training data found")
            training_df = pd.DataFrame(columns=["job_description_text", "resume_text", "label"])
        else:
            training_df = pd.DataFrame(training_data_result.data)
            logger.info(f"Retrieved {len(training_df)} records from training_data table")

        # Step 2: Fetch resumes with feedback_label=1 joined with jobs
        logger.info("Fetching resumes with feedback_label=1 joined with jobs...")

        # First, get all resumes with feedback_label=1
        resumes_result = supabase.table("resumes").select("*").eq("feedback_label", 1).execute()

        if not resumes_result.data:
            logger.warning("No resumes found with feedback_label=1")
            joined_df = pd.DataFrame(columns=["job_description_text", "resume_text", "label"])
        else:
            # Create a DataFrame from the resumes data
            resumes_df = pd.DataFrame(resumes_result.data)
            logger.info(f"Retrieved {len(resumes_df)} resumes with feedback_label=1")

            # Get all job IDs from the resumes
            job_ids = resumes_df["job_id"].unique().tolist()

            # Fetch the corresponding jobs
            jobs_result = supabase.table("jobs").select("*").in_("id", job_ids).execute()

            if not jobs_result.data:
                logger.warning("No jobs found for the resumes")
                joined_df = pd.DataFrame(columns=["job_description_text", "resume_text", "label"])
            else:
                # Create a DataFrame from the jobs data
                jobs_df = pd.DataFrame(jobs_result.data)
                logger.info(f"Retrieved {len(jobs_df)} jobs")

                # Create a dictionary mapping job_id to job_text for faster lookups
                job_text_map = {str(row["id"]): row["job_text"] for _, row in jobs_df.iterrows()}

                # Create the joined DataFrame
                joined_data = []
                for _, resume in resumes_df.iterrows():
                    job_id = str(resume["job_id"])
                    if job_id in job_text_map:
                        # Determine the label based on the status
                        if resume["status"] == 1:
                            label = "fit"
                        elif resume["status"] == 0:
                            label = "no fit"
                        else:
                            label = "potential fit"

                        joined_data.append({
                            "job_description_text": job_text_map[job_id],
                            "resume_text": resume["resume_text"],
                            "label": label
                        })

                joined_df = pd.DataFrame(joined_data)
                logger.info(f"Created joined dataset with {len(joined_df)} records")

        # Step 3: Combine both datasets
        combined_df = pd.concat([training_df, joined_df], ignore_index=True)
        logger.info(f"Combined dataset has {len(combined_df)} records")

        # Remove duplicates if any
        combined_df = combined_df.drop_duplicates(subset=["job_description_text", "resume_text"])
        logger.info(f"After removing duplicates, dataset has {len(combined_df)} records")

        return combined_df

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
    # When run directly, fetch and save the training data
    df = fetch_training_data()
    save_training_data(df)
