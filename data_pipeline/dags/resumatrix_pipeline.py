from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator 
from airflow.operators.empty import EmptyOperator
from airflow.operators.email import EmailOperator
from airflow.utils.log.logging_mixin import LoggingMixin
import os

# Using Airflow's built-in logger
log = LoggingMixin().log  

default_args = {
        'owner': 'admin',
        'start_date': datetime(2025, 2, 28),
        'retries': 1,
        'retry_delay': timedelta(minutes=3),
        'email_on_failure': True,
        'email_on_success': True,
        'email': ['mlops.team20@gmail.com'],
        }

DATA_DIR = '~/data/workspace/mlops/ResuMatrix/data'

os.makedirs(DATA_DIR, exist_ok=True)


# Pipeline

def load_resumes():
    log.info("Loading dataset for resume classification.")
    print("Loading dataset for resume classification.")
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

