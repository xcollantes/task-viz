"""Home page."""

import logging
import os
import streamlit as st
from st_pages import Page, show_pages
from components.page_config import PageConfig


PageConfig().get_config()
show_pages(
    [
        Page("Home.py", "Getting started", ":house:"),
        Page("pages/other.py", "Other page", ":mag:"),
    ]
)


def main() -> None:
    with open("assets/icon.svg", "r") as svg_file:
        st.header("Title")
        st.subheader("Template for Streamlit by Xavier Collantes")
        st.write(svg_file.read(), unsafe_allow_html=True)


if __name__ == "__main__":
    logging.info("%s running", os.path.basename(__file__))
    main()
