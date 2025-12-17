from datetime import datetime
from uuid import UUID

from airflow.decorators import dag, task

from backend.etl.tasks.chunk_and_embed import chunk_and_embed_documents
from backend.etl.tasks.clean import clean_documents
from backend.etl.tasks.extract import extract_sources
from backend.etl.tasks.load import load_to_vector_db
from backend.etl.tasks.query_data_warehouse import query_data_warehouse
from backend.utils import logger

# TODO: use the conf parameter to pass the sources and batch_id dynamically


@dag(
    dag_id="etl_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["etl"],
)
def etl_pipeline() -> None:
    """Define the ETL Airflow DAG that orchestrates the full pipeline."""

    @task
    def get_conf(**kwargs) -> dict:
        """Extract runtime configuration from the Airflow DAG run context.

        Args:
            **kwargs: Task context provided by Airflow.

        Returns:
            dict: Mapping with `sources` and `batch_id` extracted from the DAG
                configuration payload.
        """
        conf = kwargs["dag_run"].conf
        sources = conf.get("sources", [])
        batch_id_str = conf.get("batch_id")
        batch_id = UUID(batch_id_str) if batch_id_str else None
        logger.info(f"Fetched conf: sources={sources}, batch_id={batch_id}")
        return {"sources": sources, "batch_id": batch_id}

    conf = get_conf()
    sources = conf["sources"]
    batch_id = conf["batch_id"]

    @task.short_circuit
    def check_new_extraction(sources: list) -> bool:
        """Guard the downstream flow based on whether new sources were extracted.

        Args:
            sources (list): Extracted source identifiers.

        Returns:
            bool: True when there is at least one new source to process.
        """
        if sources:
            logger.info("No new data extracted. Skipping the rest of the pipeline.")
        return bool(sources)

    extraction_summary = extract_sources(sources=sources, batch_id=batch_id)
    new_sources = extraction_summary["new_sources"]
    new_extraction = check_new_extraction(new_sources)
    documents = query_data_warehouse(batch_id, new_extraction=new_extraction)
    cleaned_documents = clean_documents(documents)
    embedded_chunks = chunk_and_embed_documents(cleaned_documents)
    load_to_vector_db(embedded_chunks)


etl_pipeline_dag = etl_pipeline()
