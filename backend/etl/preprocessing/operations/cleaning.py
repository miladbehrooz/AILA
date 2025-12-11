import re


def clean_text(text: str) -> str:
    """Normalize generic text for downstream chunking.
    Args:
        text (str): Raw text to clean.
    Returns:
        str: Cleaned text.
    """
    # Replace unwanted characters but keep \n
    text = re.sub(r"[^\w\s.,!?]", " ", text)

    # Normalize all whitespace except line breaks
    # Replace multiple spaces and tabs with a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Remove trailing spaces on each line (optional)
    text = re.sub(r"[ \t]+(?=\n)", "", text)

    # Strip leading/trailing global spaces
    return text.strip()


def clean_youtube_transcript(transcript: str) -> str:
    """Convert WebVTT transcripts into plain text paragraphs.
    Args:
        transcript (str): Raw YouTube transcript in WebVTT format.
    Returns:
        str: Cleaned transcript text.
    """
    # Remove the WEBVTT header block
    transcript = re.sub(r"^WEBVTT.*?\n", "", transcript, flags=re.DOTALL)

    # Remove Kind, Language metadata lines
    transcript = re.sub(r"^(Kind|Language):.*$", "", transcript, flags=re.MULTILINE)

    # Split into caption blocks
    blocks = re.split(r"\n\s*\n", transcript.strip())

    all_text = []

    for block in blocks:
        lines = block.strip().splitlines()

        for line in lines:
            line = line.strip()

            # Skip timestamp lines
            if re.match(r"^\d{2}:\d{2}:\d{2}\.\d+\s-->", line):
                continue

            # Remove inline timestamps like <00:00:01.500>
            line = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d+>", "", line)

            # Remove <c>...</c> tags
            line = re.sub(r"</?c.*?>", "", line)

            if line:
                all_text.append(line)

    # Deduplicate lines within each block
    all_text = _deduplicate_lines(all_text)

    # Combine all cleaned lines into one string
    cleaned_text = " ".join(all_text)

    return cleaned_text


def _deduplicate_lines(lines):
    """Collapse repeated adjacent lines inside a transcript block.
    Args:
        lines (list[str]): Lines within a transcript block.
    Returns:
        list[str]: Deduplicated lines.
    """
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)
    return deduped
