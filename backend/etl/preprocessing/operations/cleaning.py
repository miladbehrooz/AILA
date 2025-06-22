import re


def clean_text(text: str) -> str:
    # Replace unwanted characters but keep \n
    text = re.sub(r"[^\w\s.,!?]", " ", text)

    # Normalize all whitespace except line breaks
    # Replace multiple spaces and tabs with a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Remove trailing spaces on each line (optional)
    text = re.sub(r"[ \t]+(?=\n)", "", text)

    # Strip leading/trailing global spaces
    return text.strip()
