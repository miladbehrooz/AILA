import streamlit as st

# from frontend.utils.logging import logger
from loguru import logger


def main() -> None:
    st.set_page_config(page_title="LAIA", layout="wide")
    logger.info("LAIA console landing page rendered")
    st.title("LAIA Console")
    st.write(
        "Select a page from the Streamlit sidebar to access the Source Upload form "
        "or the Upload Dashboard."
    )


if __name__ == "__main__":
    main()
