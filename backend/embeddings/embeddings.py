from functools import cached_property
from typing import Any, List, Union

import numpy as np
from numpy.typing import NDArray

from backend.utils import logger
from backend.utils.singleton import SingletonMeta
from .base import EmbeddingFactory, ProviderName
from backend.settings.settings import settings


class EmbeddingModelSingleton(metaclass=SingletonMeta):
    """
    Singleton wrapper for embedding models, providing unified access and utilities.

    Attributes:
        _provider (str): The embedding provider name.
        _model_name (str): The model name used for embeddings.
        _model: The embedding model instance.
    """

    def __init__(
        self,
        provider: ProviderName = settings.TEXT_EMBEDDING_PROVIDER,
        model_name: str = settings.TEXT_EMBEDDING_MODEL_NAME,
        **provider_kwargs: Any,
    ) -> None:
        """
        Initialize the EmbeddingModelSingleton.

        Args:
            provider (str): The embedding provider name.
            model_name (str | None): The model name for embeddings.
            **provider_kwargs: Additional keyword arguments for the provider builder.

        Raises:
            RuntimeError: If the embedding model cannot be initialized.
        """
        self._provider = provider
        self._model_name = model_name

        try:
            self._model = EmbeddingFactory.build(
                provider=provider,  # type: ignore
                model_name=model_name,  # type: ignore
                **provider_kwargs,
            )
        except ValueError as err:
            logger.error(
                f"Failed to build embedding model: provider={provider}, model_name={model_name}, error={err}"
            )
            raise RuntimeError(
                f"Could not initialize embedding model for provider '{provider}' and model '{model_name}'."
            ) from err

    @property
    def model_name(self) -> str:
        """
        Get the model name.

        Returns:
            str: The model name.
        """
        return self._model_name or ""

    @property
    def provider(self) -> str:
        """
        Get the provider name.

        Returns:
            str: The provider name.
        """
        return self._provider or ""

    @cached_property
    def embedding_size(self) -> int:
        """
        Get the embedding size (vector dimension).

        Returns:
            int: The size of the embedding vector.
        """
        dummy = self._model.embed_query("")
        return len(dummy)

    @property
    def max_input_length(self) -> int | None:
        """
        Get the maximum input length supported by the embedding model, if available.

        Returns:
            int | None: The maximum input length, or None if not available.
        """
        # Try _client first
        client = getattr(self._model, "_client", None)
        if client is None:
            # Try client next
            client = getattr(self._model, "client", None)

        if client and not hasattr(client, "max_seq_length"):
            logger.warning(
                f"Model {self._model_name} from {self._provider} does not expose max_seq_length ."
            )
            return None

        return getattr(client, "max_seq_length", None)

    def __call__(
        self,
        input_text: Union[str, List[str]],
        *,
        to_list: bool = True,
    ) -> Union[NDArray[np.float32], List[float], List[List[float]]]:
        """
        Generate embeddings for input text or list of texts.

        Args:
            input_text (str | List[str]): Input text or list of texts to embed.
            to_list (bool): If True, return as list; otherwise, return as numpy array.

        Returns:
            NDArray[np.float32] | List[float] | List[List[float]]: Embedding(s) for the input.

        Raises:
            AttributeError: If the embedding model is missing required methods.
        """
        try:
            if isinstance(input_text, str):
                vec = self._model.embed_query(input_text)
                return vec if to_list else np.asarray(vec, dtype=np.float32)

            # list[str]
            vecs = self._model.embed_documents(list(input_text))
            return vecs if to_list else np.asarray(vecs, dtype=np.float32)

        except AttributeError as err:
            logger.error(
                f"Embedding model missing required method: provider={self.provider}, model_name={self.model_name}, error={err}"
            )
            raise
        except (TypeError, ValueError) as err:
            logger.error(
                f"Embedding error: provider={self.provider}, model_name={self.model_name}, error={err}"
            )
            return [] if to_list else np.array([], dtype=np.float32)

    def __str__(self) -> str:
        """
        Return a string representation of the embedding model singleton.

        Returns:
            str: String representation.
        """
        return (
            f"<EmbeddingModelSingleton provider={self.provider!r} "
            f"model={self.model_name!r} dim={self.embedding_size}>"
        )


if __name__ == "__main__":

    embedding_model = EmbeddingModelSingleton()
    print(embedding_model)
    text = "This is a test sentence."
    embedding = embedding_model(text)
    print(f"Embedding for '{text}': {embedding}")
    print(f"Embedding size: {embedding_model.embedding_size}")
    print(f"Max input length: {embedding_model.max_input_length}")
    print(f"Model name: {embedding_model.model_name}")
    print(f"Model: {getattr(embedding_model, '_model', None)}")
    print(f"Provider: {embedding_model.provider}")
