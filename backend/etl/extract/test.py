import io
import os
from abc import ABC, abstractmethod
from loguru import logger
from docling.datamodel.document import DocumentStream
from docling.document_converter import DocumentConverter


class ContentExtractor(ABC):
    """Base class for content extraction strategies."""

    @abstractmethod
    def extract(self, file: io.BytesIO) -> str:
        pass


class DoclingContentExtractor(ContentExtractor):
    """Extract content using Docling."""

    def extract(self, file: io.BytesIO) -> str:
        try:
            doc_stream = DocumentStream(name="file_stream", stream=file)
            converter = DocumentConverter()
            result = converter.convert(doc_stream)
            markdown_result = result.document.export_to_markdown()
            return markdown_result
        except Exception as e:
            error_message = f"Error extracting content from file: {str(e)}"
            logger.error(error_message)
            raise ValueError(error_message) from e


class FileExtractor(ABC):
    """Base class for file extraction strategies."""

    @abstractmethod
    def extract(self, file_path: str) -> io.BytesIO:
        pass


class LocalFileExtractor(FileExtractor):
    """Extract file from local path."""

    def extract(self, file_path: str) -> io.BytesIO:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found.")

        try:
            # read the file content and store it in a variable
            with open(file_path, "rb") as file:
                file_content = file.read()

            # create a file stream from the file content
            file_stream = io.BytesIO(file_content)

            # reset the file stream to the beginning of the file
            file_stream.seek(0)

            return file_stream
        except OSError as e:
            logger.error(f"Error in reading file: {str(e)}")
            raise OSError(f"Error in reading file: {str(e)}") from e


if __name__ == "__main__":
    file_path = "backend/data/test.pdf"
    logger.info(f"Extracting content from {file_path}")
    file_extractor = LocalFileExtractor()
    file_stream = file_extractor.extract(file_path)
    logger.info(f"Extracted file from {file_path}")

    logger.info("Extracting content from file")
    content_extractor = DoclingContentExtractor()
    content = content_extractor.extract(file_stream)
    logger.info("Extracted content from file")

    print(content)
    with open("backend/data/test.md", "w") as f:
        f.write(content)
