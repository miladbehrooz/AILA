import os
import shutil
import subprocess
import tempfile
from uuid import UUID

from backend.etl.domain.documents import RepositoryDocument
from backend.utils import logger

from .base import ExtractionResult, URLExtractor


class GithubExtractor(URLExtractor):
    """Extractor that clones repositories and stores their files.
    Attributes:
        model (type): The document model associated with GitHub repositories.
    """

    model = RepositoryDocument

    def __init__(self, ignore=(".git", ".toml", ".lock", ".png")) -> None:
        """Initialize the extractor with file patterns to ignore.
        Args:
            ignore (tuple[str, ...], optional): File or directory suffixes to ignore.
                Defaults to (".git", ".toml", ".lock", ".png").
        """
        super().__init__()
        self._ignore = ignore

    def extract(self, link: str, **kwargs) -> bool:
        """Clone a repository, serialize its files, and persist the metadata.
        Args:
            link (str): URL of the GitHub repository to extract.
            **kwargs: Additional keyword arguments. Must include `batch_id`.
        Returns:
            ExtractionResult: INSERTED when a new repository is stored, DUPLICATE when a
                repository with the same link already exists.
        Raises:
            ValueError: If `batch_id` is missing or cannot be coerced into a UUID.
        """
        old_model = self.model.find(link=link)
        if old_model is not None:
            logger.info(f"Github repository already exists in the database: {link}")

            return ExtractionResult.DUPLICATE

        logger.info(f"Starting scrapping Github repository: {link}")

        repo_name = link.strip("/").split("/")[-1].split(".")[0]

        local_temp = tempfile.mkdtemp()

        try:
            os.chdir(local_temp)
            subprocess.run(["git", "clone", link])

            repo_path = os.path.join(local_temp, os.listdir(local_temp)[0])

            tree = {}
            for root, _, files in os.walk(repo_path):
                dir = root.replace(repo_path, "").lstrip("/")
                if dir.startswith(self._ignore):
                    continue

                for file in files:
                    if file.endswith(self._ignore):
                        continue
                    file_path = os.path.join(dir, file)
                    with open(os.path.join(root, file), errors="ignore") as f:
                        tree[file_path] = f.read().replace(" ", "")

            batch_id = kwargs.get("batch_id")
            if batch_id is None:
                raise ValueError("batch_id is required to extract a GitHub repository.")
            if isinstance(batch_id, str):
                batch_id = UUID(batch_id)

            instance = self.model(
                content=tree,
                name=repo_name,
                link=link,
                platform="github",
                batch_id=batch_id,
            )
            instance.save()

        except Exception:
            raise
        finally:
            shutil.rmtree(local_temp)

        logger.info(f"Finished scrapping GitHub repository: {link}")
        return ExtractionResult.INSERTED
