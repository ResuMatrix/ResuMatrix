from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import sys
import os
from google.cloud import storage

# Add the scripts directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from fetch_huggingface_data import fetch_huggingface_data
from load_to_supabase import load_to_supabase

def validate_environment():
    """Validate all required environment variables and credentials"""
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GCP_PROJECT_ID'
    ]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
    
    # Validate GCP credentials
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        bucket.reload()
    except Exception as e:
        raise ValueError(f"GCP credentials validation failed: {str(e)}")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'train_data_pipeline',
    default_args=default_args,
    description='Pipeline to fetch training data from Hugging Face and load to Supabase',
    schedule_interval='0 0 */10 * *',  # Run every 10 days
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['training', 'data-pipeline'],
)

validate_env_task = PythonOperator(
    task_id='validate_environment',
    python_callable=validate_environment,
    dag=dag,
)

# Task 1: Fetch data from Hugging Face
fetch_data_task = PythonOperator(
    task_id='fetch_huggingface_data',
    python_callable=fetch_huggingface_data,
    dag=dag,
)

# Task 2: Load data to Supabase
load_data_task = PythonOperator(
    task_id='load_to_supabase',
    python_callable=load_to_supabase,
    dag=dag,
)

# Set task dependencies
validate_env_task >> fetch_data_task >> load_data_task
