"""
Embeddings Pipeline DAG

This DAG performs the following operations:
1. Fetches training data using fetch_training_data()
2. Generates embeddings using extract_embeddings()
3. Saves the embeddings locally
4. Uploads the embeddings to Google Cloud Storage
"""

from datetime import datetime, timedelta
import os
import logging
import numpy as np
import pandas as pd
import sys
import json

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.email import EmailOperator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/airflow/logs/embeddings_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add necessary paths to import project modules
sys.path.append('/opt/airflow')

# Import project modules
# Import these modules inside the task functions to avoid loading heavy models at DAG definition time
# from scripts.fetch_training_data import fetch_training_data, save_training_data
# from src.data_processing.data_preprocessing import extract_embeddings, clean_text
# from frontend.utils.gcp import upload_to_gcp

# Define default arguments for the DAG
default_args = {
    'owner': 'admin',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
    'email_on_failure': True,
    'email_on_success': True,
    'email': ['mlops.team20@gmail.com'],
}

# Define GCS bucket name
GCS_BUCKET_NAME = 'resumatrix-embeddings'  # Replace with your actual bucket name

# Define task functions
def fetch_and_save_training_data(**kwargs):
    """
    Fetch training data from the API and save it to a CSV file.
    No fallback to mock data - will fail if API is not available.

    Returns:
        str: Path to the saved CSV file
    """
    try:
        # Import here to avoid loading at DAG definition time
        from scripts.fetch_training_data import fetch_training_data, save_training_data
        import pandas as pd
        import os
        import socket
        import requests
        from datetime import datetime
        import traceback

        # Get API base URL from environment or use default
        api_base_url = os.getenv("RESUMATRIX_API_URL", "http://host.docker.internal:8000/api")
        logger.info(f"Using API base URL: {api_base_url}")

        # Check if hostname resolves
        try:
            hostname = api_base_url.split("//")[1].split(":")[0].split("/")[0]
            logger.info(f"Checking if hostname '{hostname}' resolves...")
            socket.gethostbyname(hostname)
            logger.info(f"Hostname '{hostname}' resolved successfully")
        except Exception as dns_error:
            logger.error(f"Hostname resolution failed: {str(dns_error)}")
            logger.error("This suggests the API server might not be reachable")

        # Try a basic connection to the API
        try:
            logger.info(f"Testing connection to {api_base_url}...")
            response = requests.get(f"{api_base_url}/health", timeout=5)
            logger.info(f"API health check response: Status {response.status_code}")
            if response.status_code != 200:
                logger.warning(f"API health check returned non-200 status: {response.status_code}")
                logger.warning(f"Response body: {response.text}")
        except requests.exceptions.RequestException as conn_error:
            logger.error(f"API connection test failed: {str(conn_error)}")

        # Fetch the actual training data
        logger.info("Fetching training data from API...")
        df = fetch_training_data()

        if df.empty:
            error_msg = "Empty DataFrame returned from API"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Successfully fetched training data from API with shape: {df.shape}")

        # Save the data to a CSV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_dir = '/opt/airflow/data'
        os.makedirs(data_dir, exist_ok=True)
        output_path = f"{data_dir}/training_data_{timestamp}.csv"

        df.to_csv(output_path, index=False)
        logger.info(f"Training data saved to {output_path}")

        # Push the output path to XCom for the next task
        kwargs['ti'].xcom_push(key='training_data_path', value=output_path)

        return output_path

    except Exception as e:
        logger.error(f"Error in fetch_and_save_training_data: {str(e)}")
        logger.error(f"Detailed traceback: {traceback.format_exc()}")
        raise

def generate_and_save_embeddings(**kwargs):
    """
    Generate embeddings from the training data and save them locally.

    Returns:
        dict: Paths to the saved embeddings and metadata files
    """
    try:
        # Import here to avoid loading at DAG definition time
        from src.data_processing.data_preprocessing import extract_embeddings, clean_text

        # Get the training data path from XCom
        ti = kwargs['ti']
        training_data_path = ti.xcom_pull(task_ids='fetch_training_data_task', key='training_data_path')

        logger.info(f"Loading training data from {training_data_path}")
        df = pd.read_csv(training_data_path)

        # Clean the text data if needed
        logger.info("Cleaning text data...")
        if 'resume_text' in df.columns and 'job_description_text' in df.columns:
            df['resume_text'] = df['resume_text'].apply(clean_text)
            df['job_description_text'] = df['job_description_text'].apply(clean_text)

        # Generate embeddings
        logger.info("Generating embeddings...")
        X, y = extract_embeddings(df, data_type="train")

        # Create directory for embeddings if it doesn't exist
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        embeddings_dir = '/opt/airflow/data/embeddings'
        os.makedirs(embeddings_dir, exist_ok=True)

        # Save embeddings to a local file
        embeddings_path = f"{embeddings_dir}/embeddings_{timestamp}.npz"
        np.savez(embeddings_path, X=X, y=y)

        logger.info(f"Embeddings saved to {embeddings_path}")

        # Save metadata
        metadata = {
            'timestamp': timestamp,
            'num_samples': len(df),
            'embedding_dim': X.shape[1],
            'class_distribution': {
                'fit': int(sum(y)),
                'no_fit': int(len(y) - sum(y))
            }
        }

        metadata_path = f"{embeddings_dir}/metadata_{timestamp}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        logger.info(f"Metadata saved to {metadata_path}")

        # Push the paths to XCom for the next task
        ti.xcom_push(key='embeddings_path', value=embeddings_path)
        ti.xcom_push(key='metadata_path', value=metadata_path)

        return {
            'embeddings_path': embeddings_path,
            'metadata_path': metadata_path
        }

    except Exception as e:
        logger.error(f"Error in generate_and_save_embeddings: {str(e)}")
        raise

def upload_to_gcs_bucket(**kwargs):
    """
    Upload embeddings and metadata files to Google Cloud Storage.
    If GCS upload fails, save files locally and log the paths.

    Returns:
        dict: GCS paths for the uploaded files or local paths if GCS upload fails
    """
    # Get the file paths from XCom
    ti = kwargs['ti']
    embeddings_path = ti.xcom_pull(task_ids='generate_embeddings_task', key='embeddings_path')
    metadata_path = ti.xcom_pull(task_ids='generate_embeddings_task', key='metadata_path')

    try:
        # Import here to avoid loading at DAG definition time
        from frontend.utils.gcp import upload_to_gcp
        from google.cloud import storage

        # Test GCS connection
        try:
            logger.info("Testing GCS connection...")
            client = storage.Client()
            # Try to access the bucket
            bucket = client.bucket(GCS_BUCKET_NAME)
            if not bucket.exists():
                logger.warning(f"Bucket {GCS_BUCKET_NAME} does not exist. Will create it.")
                bucket = client.create_bucket(GCS_BUCKET_NAME)

            # Upload embeddings file to GCS
            embeddings_blob_name = f"embeddings/{os.path.basename(embeddings_path)}"
            logger.info(f"Uploading embeddings to GCS: {embeddings_blob_name}")
            upload_to_gcp(embeddings_path, GCS_BUCKET_NAME, embeddings_blob_name)

            # Upload metadata file to GCS
            metadata_blob_name = f"metadata/{os.path.basename(metadata_path)}"
            logger.info(f"Uploading metadata to GCS: {metadata_blob_name}")
            upload_to_gcp(metadata_path, GCS_BUCKET_NAME, metadata_blob_name)

            gcs_paths = {
                'embeddings_gcs_path': f"gs://{GCS_BUCKET_NAME}/{embeddings_blob_name}",
                'metadata_gcs_path': f"gs://{GCS_BUCKET_NAME}/{metadata_blob_name}"
            }

            logger.info(f"Files successfully uploaded to GCS: {gcs_paths}")
            return gcs_paths

        except Exception as gcs_error:
            logger.warning(f"GCS upload failed: {str(gcs_error)}")
            raise

    except Exception as e:
        logger.error(f"Error in upload_to_gcs_bucket: {str(e)}")
        logger.info("Falling back to local storage only...")

        # Return local paths instead
        local_paths = {
            'embeddings_local_path': embeddings_path,
            'metadata_local_path': metadata_path
        }

        logger.info(f"Files saved locally: {local_paths}")
        return local_paths

# Define the DAG
with DAG(
    'embeddings_generation_pipeline',
    default_args=default_args,
    description='Pipeline to fetch training data, generate embeddings, and upload to GCS',
    schedule_interval=None,
    catchup=False
) as dag:

    # Define tasks
    start_task = EmptyOperator(
        task_id='start',
        dag=dag
    )

    fetch_training_data_task = PythonOperator(
        task_id='fetch_training_data_task',
        python_callable=fetch_and_save_training_data,
        provide_context=True,
        dag=dag
    )

    generate_embeddings_task = PythonOperator(
        task_id='generate_embeddings_task',
        python_callable=generate_and_save_embeddings,
        provide_context=True,
        dag=dag
    )

    upload_to_gcs_task = PythonOperator(
        task_id='upload_to_gcs_task',
        python_callable=upload_to_gcs_bucket,
        provide_context=True,
        dag=dag
    )

    end_task = EmptyOperator(
        task_id='end',
        dag=dag
    )

    # Email notifications
    email_success = EmailOperator(
        task_id='send_email_success',
        to='mlops.team20@gmail.com',
        subject='Embeddings Pipeline Success',
        html_content="""
        <h3>Embeddings Pipeline has completed successfully.</h3>
        <p>DAG: {{ dag.dag_id }}</p>
        <p>Execution Date: {{ ds }}</p>
        <p>Embeddings have been generated and uploaded to GCS.</p>
        """,
        trigger_rule='all_success',
        dag=dag
    )

    email_failure = EmailOperator(
        task_id='send_email_failure',
        to='mlops.team20@gmail.com',
        subject='Embeddings Pipeline Failed',
        html_content="""
        <h3>Embeddings Pipeline has failed.</h3>
        <p>DAG: {{ dag.dag_id }}</p>
        <p>Execution Date: {{ ds }}</p>
        <p>Failed Task: {{ task_instance.task_id }}</p>
        <p>Please check the logs for more information.</p>
        """,
        trigger_rule='one_failed',
        dag=dag
    )

    # Define task dependencies
    start_task >> fetch_training_data_task >> generate_embeddings_task >> upload_to_gcs_task >> end_task
    end_task >> [email_success, email_failure]
