from enum import StrEnum


class DataCategory(StrEnum):
    """Canonical identifiers for each supported data source."""

    ARTICLES = "articles"
    YOUTUBEVIDEOS = "youtube_videos"
    REPOSITORIES = "repositories"
    PDFS = "pdfs"
