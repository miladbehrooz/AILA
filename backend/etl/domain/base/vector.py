import uuid
from abc import ABC
from typing import Any, Callable, Dict, Generic, Type, TypeVar
from uuid import UUID

import numpy as np
from loguru import logger
from pydantic import UUID4, BaseModel, Field
from qdrant_client.http import exceptions
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    VectorParams,
)
from qdrant_client.models import CollectionInfo, PointStruct, Record

from backend.etl.domain.exceptions import ImproperlyConfigured
from backend.infrastructure.db.qdrant import connection
from backend.etl.domain.types import DataCategory
from backend.embeddings.embeddings import EmbeddingModelSingleton


T = TypeVar("T", bound="VectorBaseDocument")


class VectorBaseDocument(BaseModel, Generic[T], ABC):
    """Base Qdrant document with helpers for CRUD and grouping operations.
    Attributes:
        id (UUID): Primary key of the document.
    """

    id: UUID = Field(default_factory=uuid.uuid4)

    def __eq__(self, value: object) -> bool:
        """Compare two documents by type and identifier.

        Args:
            value (object): Object to compare against.

        Returns:
            bool: True when both objects belong to the same class and share an ID.
        """
        if not isinstance(value, self.__class__):
            return False
        return self.id == value.id

    def __hash__(self) -> int:
        """Compute a hash derived from the UUID.

        Returns:
            int: Hash value based on the document's ID.
        """
        return hash(self.id)

    @classmethod
    def from_record(cls: Type[T], point: Record) -> T:
        """Convert a Qdrant record into a document instance.

        Args:
            point (Record): Record returned by Qdrant.

        Returns:
            T: Instantiated document populated from the record payload.
        """
        _id = UUID(point.id, version=4)
        payload = point.payload or {}

        attributes = {
            "id": _id,
            **payload,
        }
        if cls._has_class_attribute("embedding"):
            attributes["embedding"] = point.vector or None

        return cls(**attributes)

    def to_point(self: T, **kwargs) -> PointStruct:
        """Translate the document into a Qdrant point payload.

        Args:
            **kwargs: Additional keyword arguments forwarded to `model_dump`.

        Returns:
            PointStruct: Payload that can be sent to Qdrant.
        """
        exclude_unset = kwargs.pop("exclude_unset", False)
        by_alias = kwargs.pop("by_alias", True)

        payload = self.model_dump(
            exclude_unset=exclude_unset, by_alias=by_alias, **kwargs
        )

        _id = str(payload.pop("id"))
        vector = payload.pop("embedding", {})
        if vector and isinstance(vector, np.ndarray):
            vector = vector.tolist()

        return PointStruct(id=_id, vector=vector, payload=payload)

    def model_dump(self: T, **kwargs) -> dict:
        """Dump the model ensuring UUIDs become strings.

        Args:
            **kwargs: Keyword arguments handed to Pydantic's `model_dump`.

        Returns:
            dict: Serialized representation safe for JSON payloads.
        """
        dict_ = super().model_dump(**kwargs)

        dict_ = self._uuid_to_str(dict_)

        return dict_

    def _uuid_to_str(self, item: Any) -> Any:
        """Recursively convert UUID instances into their string representation.

        Args:
            item (Any): Nested structure that may contain UUID values.

        Returns:
            Any: Structure with all UUID entries replaced by strings.
        """
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, UUID):
                    item[key] = str(value)
                elif isinstance(value, list):
                    item[key] = [self._uuid_to_str(v) for v in value]
                elif isinstance(value, dict):
                    item[key] = {k: self._uuid_to_str(v) for k, v in value.items()}

        return item

    @classmethod
    def bulk_insert(cls: Type[T], documents: list["VectorBaseDocument"]) -> bool:
        """Insert many documents handling collection bootstrapping.

        Args:
            documents (list[VectorBaseDocument]): Documents to persist.

        Returns:
            bool: True when every document was inserted successfully.
        """
        try:
            cls._bulk_insert(documents)
        except exceptions.UnexpectedResponse:
            logger.info(
                f"Collection '{cls.get_collection_name()}' does not exist. Trying to create the collection and reinsert the documents."
            )

            cls.create_collection()

            try:
                cls._bulk_insert(documents)
            except exceptions.UnexpectedResponse:
                logger.error(
                    f"Failed to insert documents in '{cls.get_collection_name()}'."
                )

                return False

        return True

    @classmethod
    def _bulk_insert(cls: Type[T], documents: list["VectorBaseDocument"]) -> None:
        """Low-level insertion that assumes the collection exists.

        Args:
            documents (list[VectorBaseDocument]): Documents to persist.
        """
        points = [doc.to_point() for doc in documents]

        connection.upsert(collection_name=cls.get_collection_name(), points=points)

    @classmethod
    def bulk_find(
        cls: Type[T], limit: int = 10, **kwargs
    ) -> tuple[list[T], UUID | None]:
        """Scroll through the collection and return results with the next offset.

        Args:
            limit (int, optional): Max number of records per chunk. Defaults to 10.
            **kwargs: Additional filters forwarded to Qdrant.

        Returns:
            tuple[list[T], UUID | None]: Retrieved documents plus the next offset.
        """
        try:
            documents, next_offset = cls._bulk_find(limit=limit, **kwargs)
        except exceptions.UnexpectedResponse:
            logger.error(
                f"Failed to search documents in '{cls.get_collection_name()}'."
            )

            documents, next_offset = [], None

        return documents, next_offset

    @classmethod
    def _bulk_find(
        cls: Type[T], limit: int = 10, **kwargs
    ) -> tuple[list[T], UUID | None]:
        """Execute the Qdrant scroll call for the collection.

        Args:
            limit (int, optional): Max number of records per chunk. Defaults to 10.
            **kwargs: Additional filters forwarded to the scroll API.

        Returns:
            tuple[list[T], UUID | None]: Records plus their next offset.
        """
        collection_name = cls.get_collection_name()

        offset = kwargs.pop("offset", None)
        offset = str(offset) if offset else None

        records, next_offset = connection.scroll(
            collection_name=collection_name,
            limit=limit,
            with_payload=kwargs.pop("with_payload", True),
            with_vectors=kwargs.pop("with_vectors", False),
            offset=offset,
            **kwargs,
        )
        documents = [cls.from_record(record) for record in records]
        if next_offset is not None:
            next_offset = UUID(next_offset, version=4)

        return documents, next_offset

    @classmethod
    def bulk_delete(cls: Type[T], batch_id: UUID | str, chunk_size: int = 128) -> int:
        """Delete all records that belong to the provided batch ID.

        Args:
            batch_id (UUID | str): Batch identifier attached to the records.
            chunk_size (int, optional): Number of points deleted per request.

        Returns:
            int: Number of deleted points.
        """
        try:
            deleted = cls._bulk_delete(batch_id=batch_id, chunk_size=chunk_size)
        except exceptions.UnexpectedResponse:
            logger.error(
                f"Failed to delete documents from '{cls.get_collection_name()}' for batch_id='{batch_id}'."
            )
            deleted = 0
        return deleted

    @classmethod
    def _bulk_delete(cls: Type[T], batch_id: UUID | str, chunk_size: int = 128) -> int:
        """Perform batched deletions for a batch_id filter.

        Args:
            batch_id (UUID | str): Batch identifier attached to the records.
            chunk_size (int, optional): Number of points deleted per request.

        Returns:
            int: Number of deleted points.
        """
        collection_name = cls.get_collection_name()
        filter_ = Filter(
            must=[
                FieldCondition(
                    key="batch_id",
                    match=MatchValue(value=str(batch_id)),
                )
            ]
        )
        deleted = 0
        offset: str | None = None

        while True:
            records, next_offset = connection.scroll(
                collection_name=collection_name,
                limit=chunk_size,
                offset=offset,
                with_payload=False,
                with_vectors=False,
                scroll_filter=filter_,
            )

            if not records:
                break

            point_ids: list[str] = []
            for record in records:
                record_id = getattr(record, "id", None)
                if record_id is None:
                    continue
                point_ids.append(str(record_id))
            if not point_ids:
                break

            connection.delete(
                collection_name=collection_name,
                points_selector=PointIdsList(points=point_ids),
            )
            deleted += len(point_ids)

            offset = next_offset if next_offset is None else str(next_offset)

        return deleted

    @classmethod
    def search(cls: Type[T], query_vector: list, limit: int = 10, **kwargs) -> list[T]:
        """Search the vector store for the closest matches.

        Args:
            query_vector (list): Vector representation of the query.
            limit (int, optional): Number of matches to return. Defaults to 10.
            **kwargs: Additional search constraints.

        Returns:
            list[T]: Ordered list of matching documents.
        """
        try:
            documents = cls._search(query_vector=query_vector, limit=limit, **kwargs)
        except exceptions.UnexpectedResponse:
            logger.error(
                f"Failed to search documents in '{cls.get_collection_name()}'."
            )

            documents = []

        return documents

    @classmethod
    def _search(cls: Type[T], query_vector: list, limit: int = 10, **kwargs) -> list[T]:
        """Execute the raw Qdrant search call.

        Args:
            query_vector (list): Vector representation of the query.
            limit (int, optional): Number of matches to return. Defaults to 10.
            **kwargs: Additional search constraints.

        Returns:
            list[T]: Ordered list of matching documents.
        """
        collection_name = cls.get_collection_name()
        records = connection.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=kwargs.pop("with_payload", True),
            with_vectors=kwargs.pop("with_vectors", False),
            **kwargs,
        )
        documents = [cls.from_record(record) for record in records]

        return documents

    @classmethod
    def get_or_create_collection(cls: Type[T]) -> CollectionInfo:
        """Ensure the backing collection exists and return its metadata.

        Returns:
            CollectionInfo: Metadata describing the collection.
        """
        collection_name = cls.get_collection_name()

        try:
            return connection.get_collection(collection_name=collection_name)
        except exceptions.UnexpectedResponse:
            use_vector_index = cls.get_use_vector_index()

            collection_created = cls._create_collection(
                collection_name=collection_name, use_vector_index=use_vector_index
            )
            if collection_created is False:
                raise RuntimeError(
                    f"Couldn't create collection {collection_name}"
                ) from None

            return connection.get_collection(collection_name=collection_name)

    @classmethod
    def create_collection(cls: Type[T]) -> bool:
        """Create the Qdrant collection using the class metadata.

        Returns:
            bool: True when the collection was created successfully.
        """
        collection_name = cls.get_collection_name()
        use_vector_index = cls.get_use_vector_index()

        return cls._create_collection(
            collection_name=collection_name, use_vector_index=use_vector_index
        )

    @classmethod
    def _create_collection(
        cls, collection_name: str, use_vector_index: bool = True
    ) -> bool:
        """Create a collection with or without a vector index.

        Args:
            collection_name (str): Name of the collection to create.
            use_vector_index (bool, optional): Whether to attach a vector index.

        Returns:
            bool: True when the collection creation succeeds.
        """
        if use_vector_index is True:
            vectors_config = VectorParams(
                size=EmbeddingModelSingleton().embedding_size, distance=Distance.COSINE
            )
        else:
            vectors_config = {}

        return connection.create_collection(
            collection_name=collection_name, vectors_config=vectors_config
        )

    @classmethod
    def get_category(cls: Type[T]) -> DataCategory:
        """Return the business category configured for the document.

        Returns:
            DataCategory: Category assigned via the Config inner class.
        """
        if not hasattr(cls, "Config") or not hasattr(cls.Config, "category"):
            raise ImproperlyConfigured(
                "The class should define a Config class with"
                "the 'category' property that reflects the collection's data category."
            )

        return cls.Config.category

    @classmethod
    def get_collection_name(cls: Type[T]) -> str:
        """Return the collection name declared on the Config inner class.

        Returns:
            str: Qdrant collection name.
        """
        if not hasattr(cls, "Config") or not hasattr(cls.Config, "name"):
            raise ImproperlyConfigured(
                "The class should define a Config class with"
                "the 'name' property that reflects the collection's name."
            )

        return cls.Config.name

    @classmethod
    def get_use_vector_index(cls: Type[T]) -> bool:
        """Return whether the collection should maintain a vector index.

        Returns:
            bool: True when vectors should be stored alongside payloads.
        """
        if not hasattr(cls, "Config") or not hasattr(cls.Config, "use_vector_index"):
            return True

        return cls.Config.use_vector_index

    @classmethod
    def group_by_class(
        cls: Type["VectorBaseDocument"], documents: list["VectorBaseDocument"]
    ) -> Dict["VectorBaseDocument", list["VectorBaseDocument"]]:
        """Group documents by their Python class.

        Args:
            documents (list[VectorBaseDocument]): Documents to group.

        Returns:
            dict: Mapping of class to the corresponding documents.
        """
        return cls._group_by(documents, selector=lambda doc: doc.__class__)

    @classmethod
    def group_by_category(
        cls: Type[T], documents: list[T]
    ) -> Dict[DataCategory, list[T]]:
        """Group documents by their configured data category.

        Args:
            documents (list[T]): Documents to group.

        Returns:
            dict[DataCategory, list[T]]: Mapping of categories to documents.
        """
        return cls._group_by(documents, selector=lambda doc: doc.get_category())

    @classmethod
    def _group_by(
        cls: Type[T], documents: list[T], selector: Callable[[T], Any]
    ) -> Dict[Any, list[T]]:
        """Group documents using the provided selector function.

        Args:
            documents (list[T]): Documents to group.
            selector (Callable[[T], Any]): Function returning the grouping key.

        Returns:
            dict[Any, list[T]]: Mapping of calculated keys to documents.
        """
        grouped = {}
        for doc in documents:
            key = selector(doc)

            if key not in grouped:
                grouped[key] = []
            grouped[key].append(doc)

        return grouped

    @classmethod
    def collection_name_to_class(
        cls: Type["VectorBaseDocument"], collection_name: str
    ) -> type["VectorBaseDocument"]:
        """Return the subclass that manages the provided collection.

        Args:
            collection_name (str): Registered Qdrant collection name.

        Returns:
            type[VectorBaseDocument]: Subclass associated with the name.

        Raises:
            ValueError: When no subclass matches the collection name.
        """
        for subclass in cls.__subclasses__():
            try:
                if subclass.get_collection_name() == collection_name:
                    return subclass
            except ImproperlyConfigured:
                pass

            try:
                return subclass.collection_name_to_class(collection_name)
            except ValueError:
                continue

        raise ValueError(f"No subclass found for collection name: {collection_name}")

    @classmethod
    def _has_class_attribute(cls: Type[T], attribute_name: str) -> bool:
        """Check if the class or any base defines the attribute annotation.

        Args:
            attribute_name (str): Attribute annotation to look up.

        Returns:
            bool: True if the annotation exists on the class hierarchy.
        """
        if attribute_name in cls.__annotations__:
            return True

        for base in cls.__bases__:
            if hasattr(base, "_has_class_attribute") and base._has_class_attribute(
                attribute_name
            ):
                return True

        return False
