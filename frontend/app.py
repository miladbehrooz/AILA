import streamlit as st

# from frontend.utils.logging import logger
from loguru import logger


def main() -> None:
    """Render the landing page layout for the Streamlit app."""
    st.set_page_config(page_title="AI Learning Assistant", layout="wide")
    logger.info("AILA landing page rendered")
    st.title("AI Learning Assistant")
    st.write(
        "Select a page from sidebar to access the Source Upload form "
        "or the Upload Dashboard."
    )


if __name__ == "__main__":
    main()
