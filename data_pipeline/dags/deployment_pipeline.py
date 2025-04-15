import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/airflow/logs/deployment_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.email import EmailOperator
from airflow.utils.log.logging_mixin import LoggingMixin
from google.cloud import storage
from airflow.providers.google.cloud.hooks.gcs import GCSHook
import pandas as pd
import numpy as np
import io
from urllib.parse import urlparse

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

# DATA_DIR = '~/data/workspace/mlops/ResuMatrix/data'

BUCKET_NAME = "us-east1-mlops-dev-8ad13d78-bucket"

# os.makedirs(DATA_DIR, exist_ok=True)


# Pipeline

# def load_resumes(**kwargs):
#     log.info("Loading data for resume classification.")
#     """
#         Prerequisites:
#         Python library needed: google-cloud-storage
#         Download JSON key file from google cloud console.
#             Go to "IAM & Admin / Service Accounts".
#             Click on the "awesome-nimbus" service account.
#             Click on the "Keys" tab. Click on Add key -> Create new key -> Key type: JSON.
#             The JSON file of the private key will be downloaded to your local.
#         Set an environment variable to point to the key file:
#             export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
#         Have Google Cloud CLI installed. Enter the command "gcloud init".
#             Re-initialize configuration. Option 1.
#             Choose your account that is associated with the GCP project.
#             Pick our cloud project to use, namely, awesome-nimbus.
#             Do not configure region and zone.
#         Run the command "gcloud auth application-default login".
#             This opens a new tab in your browser. Allow permissions for the account you had selected initially.
#             Credentials will be set and this python function should run.
#     """
#     print("Loading dataset for resume classification.")
#     hook = GCSHook(gcp_conn_id='google_cloud_default')
#     storage_client = hook.get_conn()
#
#     # Get the bucket
#     bucket = storage_client.bucket(BUCKET_NAME)
#
#     dag_run_conf = kwargs.get('dag_run').conf or {}
#     source_dir = dag_run_conf.get('source_dir', 'random_resumes')
#
#     # Get the blob
#     blobs = bucket.list_blobs(prefix=source_dir)
#
#     current_file_path = os.path.abspath(__file__)
#     log.info("Current file path: ")
#     log.info(current_file_path)
#
#     parent_dir = current_file_path[:current_file_path.index("dags") + 4]
#     data_dir = os.path.join(parent_dir, "temp_data_store")
#     log.info("Data directory: ")
#     log.info(data_dir)
#
#     # Cleaning temporary data store before loading in new resumes
#     if os.path.isdir(data_dir):
#         for filename in os.listdir(data_dir):
#             file_path = os.path.join(data_dir, filename)
#             try:
#                 if os.path.isfile(file_path) or os.path.islink(file_path):
#                     os.unlink(file_path)
#                 elif os.path.isdir(file_path):
#                     shutil.rmtree(file_path)
#             except Exception as e:
#                 print('Failed to delete %s. Reason: %s' % (file_path, e))
#
#     os.makedirs(data_dir, exist_ok=True)
#
#     for blob in blobs:
#         # Skip any "directory" blobs.
#         if blob.name.endswith('/'):
#             continue
#
#         # Remove the prefix from the blob name to get the relative file path.
#         relative_path = os.path.relpath(blob.name, source_dir)
#         log.info("Relative path: ")
#         log.info(relative_path)
#         local_file_path = os.path.join(data_dir, relative_path)
#         log.info("Local File Path: ")
#         log.info(local_file_path)
#
#         # Create local directories if they don't exist.
#         local_dir = os.path.dirname(local_file_path)
#         if not os.path.exists(local_dir):
#             os.makedirs(local_dir, exist_ok=True)
#
#         # Download the blob to the local file.
#         blob.download_to_filename(local_file_path)
#         print(f"Downloaded {blob.name} to {local_file_path}")
#     log.info("Successfully loaded resume classification dataset!")
#     print("Successfully loaded resume classification dataset!")

def load_data_for_fit_pred(ti, **kwargs):
    """
    Assumptions:
        - There is a CSV loaded into "temp_data_store" with all the resumes that need fit classification.
        - There is a TXT loaded into "temp_data_store" with the corresponding JD that those resumes need to be fit 
        against.
        - CSV format: 2 columns, resume_id and resume.
        - Only one CSV file and one TXT file is present in the directory.
    """
    hook = GCSHook(gcp_conn_id='google_cloud_default')
    client = hook.get_conn()
    bucket = client.get_bucket(BUCKET_NAME)
    dag_run_conf = kwargs.get('dag_run').conf or {}
    source_dir = dag_run_conf.get('source_dir', 'random_resumes')
    blobs = bucket.list_blobs(prefix=source_dir)
    resume_df = pd.DataFrame()
    jd_text = ""
    for blob in blobs:
        if blob.name.endswith('.csv'):
            csv_data = blob.download_as_text(encoding='utf-8')
            resume_df = pd.read_csv(io.StringIO(csv_data))
        if blob.name.endswith('.txt'):
            jd_text = blob.download_as_text(encoding='utf-8')
    if len(resume_df.index) == 0:
        raise ValueError("No resume CSV file found in given source directory.")
    if len(jd_text) == 0:
        raise ValueError("No text file found for Job Description or the file is empty.")

    resume_df['job_description_text'] = jd_text
    resume_df.rename({"resume": "resume_text"})

    csv_data = resume_df.to_csv(index=False)

    # Define your GCS bucket and blob name
    destination_blob_name = "temp_airflow_storage/resume_jd_data.csv"  # Replace with desired blob path

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(csv_data, content_type='text/csv')

    # Construct a GCS path that can be used by downstream tasks
    gcs_path = f"gs://{BUCKET_NAME}/{destination_blob_name}"

    ti.xcom_push(key="data_path", value=gcs_path)

def gen_embeddings(ti, **kwargs):
    from data_processing.data_preprocessing import extract_embeddings
    gcs_path = ti.xcom_pull(key="data_path", task_ids="load_data_for_fit_pred_task")
    if not gcs_path:
        raise ValueError("No GCS path found in XCom. Check upstream task.")

    # Parse the GCS path to extract bucket and blob names
    parsed = urlparse(gcs_path)
    blob_name = parsed.path.lstrip('/')

    # Initialize GCS client and download the CSV file as string
    hook = GCSHook(gcp_conn_id='google_cloud_default')
    client = hook.get_conn()
    bucket = client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    csv_data = blob.download_as_string().decode('utf-8')

    # Load the CSV data into a pandas DataFrame
    resume_df = pd.read_csv(io.StringIO(csv_data))
    blob.delete()

    X_test = extract_embeddings(resume_df, data_type="deployment")
    buffer = io.BytesIO()
    np.save(buffer, X_test)
    buffer.seek(0)

    destination_blob_name = "temp_airflow_storage/embeddings_np_array.npy"  # Replace with desired blob path

    # Initialize GCS client and upload the file from the buffer
    client = storage.Client()
    bucket = client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)

    # Upload the NumPy binary data to GCS
    blob.upload_from_file(buffer, content_type="application/octet-stream")

    # Construct the GCS path (URI) to be passed via XCom
    gcs_path = f"gs://{BUCKET_NAME}/{destination_blob_name}"
    ti.xcom_push(key="numpy_path", value=gcs_path)


# def extract_text_from_pdf():
#     log.info("Extracting text from pdf.")
#     print("Extracting text from pdf.")
#
#
# def data_cleaning():
#     log.info("Cleaning data and removing personal information.")
#     print("Cleaning data and removing personal information.")
#
#
# def generate_embeddings():
#     log.info("Generating Embeddings.")
#     print("Generating Embeddings.")
#     log.info("Embeddings generated successfully!")
#     print("Embeddings generated successfully!")
#
#
# def parsing_text_json_schema():
#     log.info("Parsing text for LLM in JSON schema.")
#     print("Parsing text for LLM in JSON schema.")
#     log.info("Parsed data successfully!")
#     print("Parsed data successfully!")
#
# def data_transform():
#     log.info("Transforming data into necessary format.")
#     print("Transforming data into necessary format.")
#
#     log.info("Successfully transformed data!")
#     print("Successfully transformed data!")


with (DAG(
        'resumatrix_deployment_data_pipeline_dag',
        default_args=default_args,
        description="A pipeline for extracting text from resumes and creating embeddings"
        ) as dag):

    start_task = EmptyOperator(task_id='start')

    # load_resumes_task = PythonOperator(
    #     task_id="load_resumes_task",
    #     python_callable=load_resumes,
    #     dag=dag,
    #     provide_context=True
    # )

    load_data_for_fit_pred_task = PythonOperator(
        task_id="load_data_for_fit_pred_task",
        python_callable=load_data_for_fit_pred,
        dag=dag,
        provide_context=True
    )

    gen_embeddings_task = PythonOperator(
        task_id="gen_embeddings_task",
        python_callable=gen_embeddings,
        dag=dag,
        provide_context=True
    )

    # embed_task = PythonOperator(
    #     task_id="embedding_generation_task",
    #     python_callable=generate_embeddings,
    #     dag=dag
    # )
    #
    # parse_text_json_task = PythonOperator(
    #     task_id="parse_text_json_task",
    #     python_callable=parsing_text_json_schema,
    #     dag=dag
    # )
    #
    # data_transformation_task = PythonOperator(
    #     task_id="data_transformation_task",
    #     python_callable=data_transform,
    #     dag=dag
    # )

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
    start_task >> load_data_for_fit_pred_task >> gen_embeddings_task >> end_task >> [email_success, email_failure]

