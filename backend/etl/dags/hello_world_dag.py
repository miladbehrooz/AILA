from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


# This is a simple Python function that will be our task
def say_hello():
    print("Hello, Airflow!")


# Define the DAG
with DAG(
    dag_id="hello_world",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,  # don't backfill old runs
) as dag:
    # Define the task
    hello_task = PythonOperator(
        task_id="say_hello_task",
        python_callable=say_hello,
    )
