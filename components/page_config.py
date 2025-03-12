"""Page config to be included on each page."""

import streamlit as st


class PageConfig:
    """Overridable Streamlit page config."""

    def __init__(
        self,
        page_title: str = "Xavier's options trading tracker",
        page_icon: str = ":chart:",
        layout: str = "wide",
        initial_sidebar_state: str = "expanded",
        help_link: str = "",
        report_bug_link: str = "",
        about_link: str = "",
    ) -> None:
        self.page_title = page_title
        self.page_icon = page_icon
        self.layout = layout
        self.initial_sidebar_state = initial_sidebar_state
        self.help_link = help_link
        self.report_bug_link = report_bug_link
        self.about_link = about_link

    def get_config(self) -> st.set_page_config:
        """Return consistent Page Config for Streamlit."""
        menu_items_section = {}

        if self.help_link:
            menu_items_section["Get Help"] = self.help_link
        if self.report_bug_link:
            menu_items_section["Report a bug"] = self.report_bug_link
        if self.about_link:
            menu_items_section["About"] = self.about_link

        return (
            st.set_page_config(
                self.page_title,
                self.page_icon,
                self.layout,
                self.initial_sidebar_state,
                menu_items=menu_items_section,
            ),
            # Remove watermark
            st.markdown(
                """<style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>""",
                unsafe_allow_html=True,
            ),
        )


# Attributions

# contributors/tarikvision">Anastasiia Torianyk</a> on <a href="https://iconscout.com">IconScout</a>
# <a href="https://iconscout.com/illustrations/education" target="_blank">Free Education Expenses, College Education Pricing Illustration</a> by <a href="https://iconscout.com/contributors/tarikvision">Anastasiia Torianyk</a> on <a href="https://iconscout.com">IconScout</a>


# <a href="<a href="https://iconscout.com/illustrations/education" target="_blank">Free Education Expenses, College Education Pricing Illustration</a> by <a href="https://iconscout.com/contributors/tarikvision">Anastasiia Torianyk</a> on <a href="https://iconscout.com">IconScout</a>
#
# " target="_blank">Free Pricing Innovative Product Illustration</a> by <a href="https://iconscout.com/
