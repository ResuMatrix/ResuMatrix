from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.email import EmailOperator
from airflow.utils.log.logging_mixin import LoggingMixin
from google.cloud import storage
import os, shutil

# Using Airflow's built-in logger
log = LoggingMixin().log

default_args = {
        'owner': 'admin',
        'start_date': datetime(2025, 4, 3),
        'retries': 1,
        'retry_delay': timedelta(minutes=3),
        'email_on_failure': True,
        'email_on_success': True,
        'email': ['mlops.team20@gmail.com'],
        }

DATA_DIR = '~/data/workspace/mlops/ResuMatrix/data'

BUCKET_NAME = "us-east1-mlops-dev-8ad13d78-bucket"

os.makedirs(DATA_DIR, exist_ok=True)


# Pipeline

def load_resumes(source_dir):
    log.info("Loading data for resume classification.")
    """
        Prerequisites:
        Python library needed: google-cloud-storage
        Download JSON key file from google cloud console.
            Go to "IAM & Admin / Service Accounts".
            Click on the "awesome-nimbus" service account.
            Click on the "Keys" tab. Click on Add key -> Create new key -> Key type: JSON.
            The JSON file of the private key will be downloaded to your local.
        Set an environment variable to point to the key file:
            export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
        Have Google Cloud CLI installed. Enter the command "gcloud init".
            Re-initialize configuration. Option 1.
            Choose your account that is associated with the GCP project.
            Pick our cloud project to use, namely, awesome-nimbus.
            Do not configure region and zone.
        Run the command "gcloud auth application-default login".
            This opens a new tab in your browser. Allow permissions for the account you had selected initially.
            Credentials will be set and this python function should run.
    """
    print("Loading dataset for resume classification.")
    storage_client = storage.Client()

    # Get the bucket
    bucket = storage_client.bucket(BUCKET_NAME)

    # Get the blob
    blobs = bucket.list_blobs(prefix=source_dir)

    current_file_path = os.path.abspath(__file__)

    parent_dir = current_file_path[:current_file_path.index("ResuMatrix") + 10]
    data_dir = os.path.join(parent_dir, "temp_data_store")

    # Cleaning temporary data store before loading in new resumes
    if os.path.isdir(data_dir):
        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    os.makedirs(data_dir, exist_ok=True)

    for blob in blobs:
        # Skip any "directory" blobs.
        if blob.name.endswith('/'):
            continue

        # Remove the prefix from the blob name to get the relative file path.
        relative_path = os.path.relpath(blob.name, source_dir)
        local_file_path = os.path.join(data_dir, relative_path)

        # Create local directories if they don't exist.
        local_dir = os.path.dirname(local_file_path)
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        # Download the blob to the local file.
        blob.download_to_filename(local_file_path)
        print(f"Downloaded {blob.name} to {local_file_path}")
    log.info("Successfully loaded resume classification dataset!")
    print("Successfully loaded resume classification dataset!")


def extract_text_from_pdf():
    log.info("Extracting text from pdf.")
    print("Extracting text from pdf.")


def data_cleaning():
    log.info("Cleaning data and removing personal information.")
    print("Cleaning data and removing personal information.")


def generate_embeddings():
    log.info("Generating Embeddings.")
    print("Generating Embeddings.")
    log.info("Embeddings generated successfully!")
    print("Embeddings generated successfully!")


def parsing_text_json_schema():
    log.info("Parsing text for LLM in JSON schema.")
    print("Parsing text for LLM in JSON schema.")
    log.info("Parsed data successfully!")
    print("Parsed data successfully!")

def data_transform():
    log.info("Transforming data into necessary format.")
    print("Transforming data into necessary format.")

    log.info("Successfully transformed data!")
    print("Successfully transformed data!")


with (DAG(
        'resumatrix_data_pipeline_dag',
        default_args=default_args,
        description="A pipeline for extracting text from resumes and creating embeddings"
        ) as dag):

    start_task = EmptyOperator(task_id='start')

    load_task = PythonOperator(
        task_id="load_resumes_task",
        python_callable=load_resumes,
        dag=dag
    )

    extract_task = PythonOperator(
        task_id="sample_extract_text_task",
        python_callable=extract_text_from_pdf,
        dag=dag
    )

    data_cleaning_task = PythonOperator(
        task_id="data_cleaning_task",
        python_callable=data_cleaning,
        dag=dag
    )

    embed_task = PythonOperator(
        task_id="embedding_generation_task",
        python_callable=generate_embeddings,
        dag=dag
    )

    parse_text_json_task = PythonOperator(
        task_id="parse_text_json_task",
        python_callable=parsing_text_json_schema,
        dag=dag
    )

    data_transformation_task = PythonOperator(
        task_id="data_transformation_task",
        python_callable=data_transform,
        dag=dag
    )

    end_task = EmptyOperator(task_id='end')

    email_success = EmailOperator(
        task_id='send_email_success',
        to='mlops.team20@gmail.com',
        subject='Airflow Task Success: {{ task_instance.task_id }}',
        html_content="""
        <h3>Task {{ task_instance.task_id }} has completed successfully.</h3>
        <p>DAG: {{ dag.dag_id }}</p>
        """,
        trigger_rule='all_success',
        dag=dag
    )

    email_failure = EmailOperator(
        task_id='send_email_failure',
        to='mlops.team20@gmail.com',
        subject='Airflow Task Failed: {{ task_instance.task_id }}',
        html_content="""
        <h3>Task {{ task_instance.task_id }} has failed.</h3>
        <p>DAG: {{ dag.dag_id }}</p>
        """,
        trigger_rule='one_failed',  # Triggers only if a task fails
        dag=dag
    )

    # set the task dependencies
    start_task >> load_task >> extract_task >> data_cleaning_task >> [embed_task, parse_text_json_task] >> data_transformation_task >> end_task >> [email_success, email_failure]

