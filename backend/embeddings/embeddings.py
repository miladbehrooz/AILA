from functools import cached_property
from typing import Any, List, Union

import numpy as np
from numpy.typing import NDArray

from backend.utils import logger
from backend.utils.singleton import SingletonMeta
from .base import EmbeddingFactory
from backend.settings.settings import settings


class EmbeddingModelSingleton(metaclass=SingletonMeta):

    def __init__(
        self,
        provider: str = settings.TEXT_EMBEDDING_PROVIDER,
        model_name: str | None = settings.TEXT_EMBEDDING_MODEL_NAME,
        **provider_kwargs: Any,
    ) -> None:
        self._provider = provider
        self._model_name = model_name

        try:
            self._model = EmbeddingFactory.build(
                provider=provider,
                model_name=model_name,
                **provider_kwargs,
            )
        except Exception as err:
            logger.error(
                f"Failed to build embedding model: provider={provider}, model_name={model_name}, error={err}"
            )
            raise RuntimeError(
                f"Could not initialize embedding model for provider '{provider}' and model '{model_name}'."
            ) from err

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider(self) -> str:
        return self._provider

    @cached_property
    def embedding_size(self) -> int:
        dummy = self._model.embed_query("")
        return len(dummy)

    @property
    def max_input_length(self) -> int | None:
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

        try:
            if isinstance(input_text, str):
                vec = self._model.embed_query(input_text)
                return vec if to_list else np.asarray(vec, dtype=np.float32)

            # list[str]
            vecs = self._model.embed_documents(list(input_text))
            return vecs if to_list else np.asarray(vecs, dtype=np.float32)

        except AttributeError as err:
            logger.error(
                f"Embedding model missing required method: provider={self._provider}, model_name={self._model_name}, error={err}"
            )
            raise
        except Exception as err:
            logger.error(
                f"Embedding error: provider={self._provider}, model_name={self._model_name}, error={err}"
            )
            return [] if to_list else np.array([], dtype=np.float32)

    def __str__(self) -> str:
        return (
            f"<EmbeddingModelSingleton provider={self._provider!r} "
            f"model={self._model_name!r} dim={self.embedding_size}>"
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
    print(f"Model: {embedding_model._model}")
    print(f"Provider: {embedding_model._provider}")
