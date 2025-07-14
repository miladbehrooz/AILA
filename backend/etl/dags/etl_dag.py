from datetime import datetime
from airflow.decorators import dag, task
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
def etl_pipeline(sources: list, batch_id: str = "batch_003"):
    @task.short_circuit
    def check_new_extraction(is_extracted: bool) -> bool:
        if not is_extracted:
            logger.info("No new data extracted. Skipping the rest of the pipeline.")
        return is_extracted

    is_extracted = extract_sources(sources=sources, batch_id=batch_id)
    new_extraction = check_new_extraction(is_extracted)
    documents = query_data_warehouse(batch_id, new_extraction=new_extraction)
    cleaned_documents = clean_documents(documents)
    embedded_chunks = chunk_and_embed_documents(cleaned_documents)
    load_to_vector_db(embedded_chunks)


sources = [
    # "https://weaviate.io/blog/advanced-rag",
    "https://www.pinecone.io/learn/vector-database/",
    "https://python.langchain.com/docs/integrations/vectorstores/qdrant/",
    "https://en.wikipedia.org/wiki/Apache_Airflow",
    "https://datascientest.com/en/apache-airflow-what-is-it",
    # "https://www.youtube.com/watch?v=T-D1OfcDW1M&t=5s",
    # "backend/data/book.pdf",
    # "https://github.com/PacktPublishing/LLM-Engineers-Handbook.git",
]
etl_pipeline_dag = etl_pipeline(sources=sources, batch_id="batch_003")
