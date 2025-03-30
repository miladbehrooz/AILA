from langchain_community.document_loaders import YoutubeLoader

from loguru import logger
from mongoengine import disconnect
from pydantic import validate_email
from .base import BaseCrawler
from backend.etl.domain.documents import YoutubeDocument


class YoutubeVideoCrawler(BaseCrawler):
    model = YoutubeDocument

    def __init__(self) -> None:
        super().__init__()

    def extract(self, link: str, **kwargs) -> None:
        old_model = self.model.find(link=link)
        if old_model is not None:
            logger.info(f"Youtube video already exists in the database: {link}")

            return

        logger.info(f"Starting scrapping Youtube video: {link}")

        try:
            logger.info("Starting loading video transcript")
            # TODO: change add_video_info to True leads to 404 bad request error due to pytube
            loader = YoutubeLoader.from_youtube_url(link, add_video_info=False)
            docs = loader.load()

            if docs and docs[0].page_content.strip():
                logger.info("Video transcript loaded successfully")

            content = {"Content": docs[0].page_content}

        except Exception as e:
            logger.error(f"Failed to load video transcript: {e}")
            return None

        instance = self.model(
            link=link,
            content=content,
            platform="youtube",
        )
        instance.save()

        logger.info(f"Finished scrapping Youtube video: {link}")


# TODO: This is a fix for the pytube issue but needs adding autentucation
def _modified_get_video_info(self) -> dict:
    """Get important video information.

    Components include:
        - title
        - description
        - thumbnail URL,
        - publish_date
        - channel author
        - and more.
    """
    try:
        from pytube import YouTube

    except ImportError:
        raise ImportError(
            'Could not import "pytube" Python package. '
            "Please install it with `pip install pytube`."
        )
        yt = YouTube(
            f"https://www.youtube.com/watch?v={self.video_id}",
            use_oauth=True,
            allow_oauth_cache=True,
        )

        video_info = {
            "title": yt.title or "Unknown",
            "description": yt.description or "Unknown",
            "view_count": yt.views or 0,
            "thumbnail_url": yt.thumbnail_url or "Unknown",
            "publish_date": (
                yt.publish_date.strftime("%Y-%m-%d %H:%M:%S")
                if yt.publish_date
                else "Unknown"
            ),
            "length": yt.length or 0,
            "author": yt.author or "Unknown",
        }
        return video_info


# Monkey patch the method
YoutubeLoader._get_video_info = _modified_get_video_info

if __name__ == "__main__":
    crawler = YoutubeVideoCrawler()
    crawler.extract("https://www.youtube.com/watch?v=RoR4XJw8wIc")
