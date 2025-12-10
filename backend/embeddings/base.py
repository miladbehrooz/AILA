from typing import Any, Callable, Dict, TypeAlias, Literal, Optional

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_cohere import CohereEmbeddings
from langchain_huggingface import (
    HuggingFaceEmbeddings,
    HuggingFaceEndpointEmbeddings,
)

from backend.utils import logger
from backend.settings.settings import settings

ProviderName: TypeAlias = Literal["openai", "cohere", "huggingface", "huggingfaceapi"]
BuilderFunc: TypeAlias = Callable[..., Embeddings]


class EmbeddingFactory:
    _REGISTRY: Dict[ProviderName, BuilderFunc] = {}

    @staticmethod
    def _build_openai(*, model_name: str, **kw: Any) -> OpenAIEmbeddings:
        return OpenAIEmbeddings(
            model=model_name, openai_api_key=settings.OPENAI_API_KEY, **kw
        )

    @staticmethod
    def _build_cohere(*, model_name: str, **kw: Any) -> CohereEmbeddings:
        return CohereEmbeddings(model=model_name, **kw)

    @staticmethod
    def _build_hf_local(*, model_name: str, **kw: Any) -> HuggingFaceEmbeddings:
        return HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
            **kw,
        )

    @staticmethod
    def _build_hf_api(*, model_name: str, **kw: Any) -> HuggingFaceEndpointEmbeddings:
        return HuggingFaceEndpointEmbeddings(model_name=model_name, **kw)

    _REGISTRY.update(
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
        provider: ProviderName,
        *,
        model_name: str,
        config: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Embeddings:
        if provider not in cls._REGISTRY:
            valid = ", ".join(cls._REGISTRY.keys())
            logger.error(f"Unknown provider '{provider}'. Valid providers: {valid}")
            raise ValueError(f"Unknown provider '{provider}'. Valid: {valid}")

        builder = cls._REGISTRY[provider]
        params = config.copy() if config else {}
        params.update(kwargs)
        try:
            return builder(model_name=model_name, **params)
        except TypeError as err:
            logger.error(
                f"Failed to initialize embedding for provider '{provider}' with model '{model_name}'. "
                f"TypeError: {err}. Params: {params}"
            )
            raise
        except Exception as err:
            logger.error(
                f"Unexpected error initializing embedding for provider '{provider}' with model '{model_name}': {err}"
            )
            raise RuntimeError(
                f"Could not initialize embedding for provider '{provider}' and model '{model_name}'."
            ) from err

    @classmethod
    def register(
        cls,
        provider: ProviderName,
        builder: BuilderFunc,
        *,
        overwrite: bool = False,
    ) -> None:

        if provider in cls._REGISTRY and not overwrite:
            raise ValueError(
                f"Provider '{provider}' already exists; "
                "pass overwrite=True to replace it."
            )
        cls._REGISTRY[provider] = builder

    @classmethod
    def list_providers(cls) -> list[ProviderName]:
        """Return a list of registered provider names."""
        return list(cls._REGISTRY.keys())
