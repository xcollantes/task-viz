"""Utils for checking passphrase."""

import streamlit as st


def is_auth(main, url_args):
    """Checks for URL args to match passphrase.

    Usage:
        ```
        url_args = st.experimental_get_query_params()
        is_auth(show_feature(), url_args)
        ```

    Args:
        main: Function to run once authenticated.

    Returns:
        Renders either the given next authenticated function or an access denied
       visual.
    """
    try:
        if url_args["p"][0] in st.secrets.passphrases.p:
            return main()
        return access_denied()
    except KeyError:
        return access_denied()


def access_denied():
    """Visual for access denied."""
    st.header("Access is denied")
