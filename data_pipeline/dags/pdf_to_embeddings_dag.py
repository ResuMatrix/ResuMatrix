from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator 
from airflow.operators.empty import EmptyOperator
import os

default_args = {
        'owner': 'admin',
        'start_date': datetime(2025, 2, 28),
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
        }

DATA_DIR = '~/data/workspace/mlops/ResuMatrix/data'

os.makedirs(DATA_DIR, exist_ok=True)


# Pipeline

def extract_text_from_pdf():
    print("Extracting text from pdf")


def preprocess():
    print("Processing text")


def generate_embeddings():
    print("Generating Embeddings")
    print("Embeddings generated successfuly!")


with DAG(
        'pdf_to_embeddings_pipeline',
        default_args=default_args,
        description="A pipeline for extracting text from resumes and creating embeddings"
        ) as dag:

    start_task = EmptyOperator(task_id='start')

    extract_task = PythonOperator(
        task_id= 'sample_extract_text_task',
        python_callable=extract_text_from_pdf,
        dag=dag
        )

    preprocess_task = PythonOperator(
        task_id = 'sample_preprocess_text_task',
        python_callable= preprocess,
        dag=dag
        )

    embed_task = PythonOperator(
        task_id = 'sample_embed_text_task',
        python_callable=generate_embeddings,
        dag=dag
        )
    end_task = EmptyOperator(task_id='end')

    # set the task dependencies
    start_task >> extract_task >> preprocess_task >> embed_task >> end_task

