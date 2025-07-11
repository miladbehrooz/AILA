from datetime import datetime
from loguru import logger
from airflow import DAG
from backend.etl.tasks.extract import extract_sources
from backend.etl.tasks.query_data_warehouse import query_data_warehouse
from backend.etl.tasks.clean import clean_documents
from backend.etl.tasks.chunk_and_embed import chunk_and_embed_documents
from backend.etl.tasks.load import load_to_vector_db


with DAG(
    dag_id="etl_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    documents = extract_sources(
        [
            "https://weaviate.io/blog/advanced-rag",
            "https://www.youtube.com/watch?v=T-D1OfcDW1M&t=5s",
            "backend/data/book.pdf",
            "https://github.com/PacktPublishing/LLM-Engineers-Handbook.git",
        ]
    )
    batch_id = "batch_001"
    documents = query_data_warehouse(batch_id)
    cleaned_documents = clean_documents(documents)
    embedded_chunks = chunk_and_embed_documents(cleaned_documents)
    successful = load_to_vector_db(embedded_chunks)
