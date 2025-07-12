from datetime import datetime
from airflow.decorators import dag
from backend.etl.tasks.extract import extract_sources
from backend.etl.tasks.query_data_warehouse import query_data_warehouse
from backend.etl.tasks.clean import clean_documents
from backend.etl.tasks.chunk_and_embed import chunk_and_embed_documents
from backend.etl.tasks.load import load_to_vector_db
from backend.utils import logger


@dag(
    dag_id="etl_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["etl"],
)
def etl_pipeline(batch_id: str = "batch_002"):
    is_extracted = extract_sources(
        [
            "https://weaviate.io/blog/advanced-rag",
            # "https://www.youtube.com/watch?v=T-D1OfcDW1M&t=5s",
            # "backend/data/book.pdf",
            # "https://github.com/PacktPublishing/LLM-Engineers-Handbook.git",
        ],
        batch_id=batch_id,
    )

    documents = query_data_warehouse(batch_id, is_extracted=is_extracted)
    cleaned_documents = clean_documents(documents)
    embedded_chunks = chunk_and_embed_documents(cleaned_documents)
    load_to_vector_db(embedded_chunks)


etl_pipeline_dag = etl_pipeline()
