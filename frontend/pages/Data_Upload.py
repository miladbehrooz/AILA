import streamlit as st

from frontend.views import source_upload


def main() -> None:
    st.set_page_config(page_title="Source Upload", layout="wide")
    source_upload.render_page()


if __name__ == "__main__":
    main()
