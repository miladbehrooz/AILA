from typing import Any, Callable, Literal, Optional, TypeAlias

from langchain_cohere import CohereEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_huggingface import (
    HuggingFaceEmbeddings,
    HuggingFaceEndpointEmbeddings,
)
from langchain_openai import OpenAIEmbeddings

from backend.settings.settings import settings
from backend.utils import logger

ProviderName: TypeAlias = Literal["openai", "cohere", "huggingface", "huggingfaceapi"]
BuilderFunc: TypeAlias = Callable[..., Embeddings]


class EmbeddingFactory:
    """
    Factory class for creating embedding objects from different providers.

    This class maintains a registry of embedding providers and their builder functions.
    """

    _REGISTRY: dict[ProviderName, BuilderFunc] = {}

    @staticmethod
    def _build_openai(*, model_name: str, **kw: Any) -> OpenAIEmbeddings:
        """
        Build an OpenAIEmbeddings object.

        Args:
            model_name (str): Name of the OpenAI model.
            **kw: Additional keyword arguments for OpenAIEmbeddings.

        Returns:
            OpenAIEmbeddings: An instance of OpenAIEmbeddings.
        """
        return OpenAIEmbeddings(
            model=model_name, openai_api_key=settings.OPENAI_API_KEY, **kw
        )

    @staticmethod
    def _build_cohere(*, model_name: str, **kw: Any) -> CohereEmbeddings:
        """
        Build a CohereEmbeddings object.

        Args:
            model_name (str): Name of the Cohere model.
            **kw: Additional keyword arguments for CohereEmbeddings.

        Returns:
            CohereEmbeddings: An instance of CohereEmbeddings.
        """
        return CohereEmbeddings(model=model_name, **kw)

    @staticmethod
    def _build_hf_local(*, model_name: str, **kw: Any) -> HuggingFaceEmbeddings:
        """
        Build a HuggingFaceEmbeddings object for local models.

        Args:
            model_name (str): Name of the HuggingFace model.
            **kw: Additional keyword arguments for HuggingFaceEmbeddings.

        Returns:
            HuggingFaceEmbeddings: An instance of HuggingFaceEmbeddings.
        """
        return HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
            **kw,
        )

    @staticmethod
    def _build_hf_api(*, model_name: str, **kw: Any) -> HuggingFaceEndpointEmbeddings:
        """
        Build a HuggingFaceEndpointEmbeddings object for HuggingFace API models.

        Args:
            model_name (str): Name of the HuggingFace API model.
            **kw: Additional keyword arguments for HuggingFaceEndpointEmbeddings.

        Returns:
            HuggingFaceEndpointEmbeddings: An instance of HuggingFaceEndpointEmbeddings.
        """
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
        """
        Build an embedding object for the specified provider and model.

        Args:
            provider (ProviderName): The name of the embedding provider.
            model_name (str): The model name to use for the provider.
            config (Optional[dict[str, Any]]): Optional configuration parameters.
            **kwargs: Additional keyword arguments for the builder function.

        Returns:
            Embeddings: An embedding object for the specified provider and model.

        Raises:
            ValueError: If the provider is unknown.
            TypeError: If the builder function receives invalid arguments.
            RuntimeError: For unexpected errors during initialization.
        """
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
        """
        Register a new embedding provider and its builder function.

        Args:
            provider (ProviderName): The name of the provider to register.
            builder (BuilderFunc): The builder function for the provider.
            overwrite (bool): Whether to overwrite an existing provider. Defaults to False.

        Raises:
            ValueError: If the provider already exists and overwrite is False.
        """

        if provider in cls._REGISTRY and not overwrite:
            raise ValueError(
                f"Provider '{provider}' already exists; "
                "pass overwrite=True to replace it."
            )
        cls._REGISTRY[provider] = builder

    @classmethod
    def list_providers(cls) -> list[ProviderName]:
        """
        Return a list of registered provider names.

        Returns:
            list[ProviderName]: List of registered provider names.
        """
        return list(cls._REGISTRY.keys())
