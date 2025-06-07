from typing import Any, Callable, Dict
from numpy.typing import NDArray

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_cohere import CohereEmbeddings
from langchain_huggingface import (
    HuggingFaceEmbeddings,
    HuggingFaceEndpointEmbeddings,
)

from backend.settings.settings import settings


# TODO: refactor the EmbeddingFactory used best practices and make it more flexible
class EmbeddingFactory:
    _REGISTRY_PROVIDERS: Dict[str, Callable[..., Embeddings]] = {}

    @staticmethod
    def _build_openai(*, model_name: str, **kw) -> OpenAIEmbeddings:
        return OpenAIEmbeddings(
            model=model_name, openai_api_key=settings.OPENAI_API_KEY, **kw
        )

    @staticmethod
    # TODO: pass the api_key as an argument from the settings and enviroment variables
    def _build_cohere(*, model_name: str, **kw) -> CohereEmbeddings:
        return CohereEmbeddings(model=model_name, **kw)

    @staticmethod
    def _build_hf_local(
        *,
        model_name: str,
        **kw,
    ) -> HuggingFaceEmbeddings:
        return HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
            **kw,
        )

    @staticmethod
    # TODO: pass the api_key as an argument from the seetings and enviroment variables
    def _build_hf_api(*, model_name: str, **kw) -> HuggingFaceEndpointEmbeddings:
        return HuggingFaceEndpointEmbeddings(model_name=model_name, **kw)

    _REGISTRY_PROVIDERS.update(
        {
            "openai": _build_openai.__func__,
            "cohere": _build_cohere.__func__,
            "huggingface": _build_hf_local.__func__,
            "huggingfaceapi": _build_hf_api.__func__,
        }
    )

    @classmethod
    def build(
        cls,
        provider: str,
        *,
        model_name: str | None = None,
        **kwargs: Any,
    ) -> Embeddings:

        if provider not in cls._REGISTRY_PROVIDERS:
            valid = ", ".join(cls._REGISTRY_PROVIDERS.keys())
            raise ValueError(f"Unknown provider '{provider}'. Valid: {valid}")

        try:
            builder = cls._REGISTRY_PROVIDERS[provider]
        except KeyError as err:
            valid = ", ".join(cls._REGISTRY_PROVIDERS.keys())
            raise ValueError(
                f"Provider '{provider}' not registered. Valid: {valid}"
            ) from err

        return builder(model_name=model_name, **kwargs)

    @classmethod
    def register(
        cls,
        provider: str,
        builder: Callable[..., Embeddings],
        *,
        overwrite: bool = False,
    ) -> None:

        if provider in cls._REGISTRY_PROVIDERS and not overwrite:
            raise ValueError(
                f"Provider '{provider}' already exists; "
                "pass overwrite=True to replace it."
            )
        cls._REGISTRY_PROVIDERS[provider] = builder
