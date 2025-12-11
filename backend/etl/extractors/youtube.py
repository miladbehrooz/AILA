import requests
import yt_dlp
from uuid import UUID
from .base import URLExtractor, ExtractionResult
from backend.etl.domain.documents import YoutubeDocument
from backend.utils import logger


class YoutubeVideoExtractor(URLExtractor):
    """Extractor that downloads video transcripts from YouTube.
    Attributes:
        model (type): The document model associated with YouTube videos.
    x"""

    model = YoutubeDocument

    def extract(self, link: str, **kwargs) -> bool:
        """Fetch the transcript and metadata for a YouTube video.
        Args:
            link (str): URL of the YouTube video to extract.
            **kwargs: Additional keyword arguments. Must include `batch_id`.
        Returns:
            ExtractionResult: INSERTED when a new video is stored, DUPLICATE when a
                video with the same link already exists, or FAILED if extraction fails.
        Raises:
            ValueError: If `batch_id` is missing or cannot be coerced into a UUID.
        """
        old_model = self.model.find(link=link)
        if old_model is not None:
            logger.info(f"Youtube video already exists in the database: {link}")

            return ExtractionResult.DUPLICATE

        logger.info(f"Starting scrapping Youtube video: {link}")

        try:
            logger.info("Starting loading video transcript")
            transcript, metadata = self.fetch_youtube_transcript(link)
            if transcript is None:
                logger.info(f"No transcript found for {link}")
                return ExtractionResult.FAILED
            logger.info("Video transcript loaded successfully")

            content = {
                "Content": transcript,
                "Title": metadata.get("Title"),
                "Auther": metadata.get("Auther"),
                "Description": metadata.get("Description"),
            }

            batch_id = kwargs.get("batch_id")
            if batch_id is None:
                raise ValueError("batch_id is required to extract a Youtube video.")
            if isinstance(batch_id, str):
                batch_id = UUID(batch_id)

            instance = self.model(
                link=link,
                content=content,
                platform="youtube",
                batch_id=batch_id,
            )
            instance.save()
            logger.info(f"Finished scrapping Youtube video: {link}")
            return ExtractionResult.INSERTED
        except Exception as e:
            logger.error(f"Error while extracting Youtube video {link}: {e}")
            raise

    # TODO: add support for multiple languages
    @staticmethod
    def fetch_youtube_transcript(video_url, lang="en"):
        """Load subtitles for the video and return the transcript plus metadata.
        Args:
            video_url (str): URL of the YouTube video.
            lang (str): Language code for the desired subtitles (default is "en").
        Returns:
            tuple[str | None, dict]: Transcript text (or None if not found) and
            video metadata dictionary.
        """

        ydl_opts = {
            "skip_download": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        # Build video metadata dictionary
        video_metadata = {
            "Title": info.get("title"),
            "Author": info.get("uploader"),
            "Description": info.get("description"),
        }

        transcript_text = None

        # Check manual subtitles
        subtitles = info.get("subtitles", {})

        for lang_code, tracks in subtitles.items():
            if lang_code.lower().startswith(lang.lower()):
                logger.info(f"Found manual subtitles for {lang_code} in {video_url}.")
                vtt_url = None
                for track in tracks:
                    if track["ext"] == "vtt":
                        vtt_url = track["url"]
                        break
                if vtt_url:
                    response = requests.get(vtt_url)
                    response.raise_for_status()
                    transcript_text = response.text
                    break

        # Check automatic captions if no manual found
        if transcript_text is None:
            captions = info.get("automatic_captions", {})
            for lang_code, tracks in captions.items():
                if lang_code.lower().startswith(lang.lower()):
                    logger.info(
                        f"No manual subtitles found. Using automatic captions for {lang_code} in {video_url}."
                    )
                    vtt_url = None
                    for track in tracks:
                        if track["ext"] == "vtt":
                            vtt_url = track["url"]
                            break
                    if vtt_url:
                        response = requests.get(vtt_url)
                        response.raise_for_status()
                        transcript_text = response.text
                        break

        if transcript_text is None:
            logger.info(f"No subtitles found for any {lang} dialect in {video_url}.")

        return transcript_text, video_metadata


if __name__ == "__main__":

    extractor = YoutubeVideoExtractor()
    extractor.extract("https://www.youtube.com/watch?v=L94WBLL0KjY")
