"""Other page."""

from components.page_config import PageConfig
import streamlit as st

PageConfig().get_config()


def main() -> None:
    st.header("This is other page")


if __name__ == "__main__":
    main()
