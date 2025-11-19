import streamlit as st

from frontend.views import upload_dashboard


def main() -> None:
    st.set_page_config(page_title="Upload Dashboard", layout="wide")
    upload_dashboard.render_page()


if __name__ == "__main__":
    main()
