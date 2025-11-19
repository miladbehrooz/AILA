import streamlit as st


def main() -> None:
    st.set_page_config(page_title="LAIA", layout="wide")
    st.title("LAIA Console")
    st.write(
        "Select a page from the Streamlit sidebar to access the Source Upload form "
        "or the Upload Dashboard."
    )


if __name__ == "__main__":
    main()
