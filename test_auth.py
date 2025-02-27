import streamlit as st
import tweepy
import logging
from dotenv import load_dotenv

# Basic page configuration
st.set_page_config(page_title="Twitter Auth Test", layout="wide")


def main():
    # Always show these elements
    st.title("Twitter Auth Test")
    st.divider()

    # Debug information at the top
    st.write("Current Query Parameters:", dict(st.query_params))
    st.write("Current Session State:", dict(st.session_state))

    # Get credentials from secrets
    consumer_key = st.secrets["twitter"]["consumer_key"]
    consumer_secret = st.secrets["twitter"]["consumer_secret"]

    # If we're not in a callback and not authenticated
    if "oauth_verifier" not in st.query_params and "authenticated" not in st.session_state:
        st.write("Starting new authentication flow...")
        try:
            auth = tweepy.OAuth1UserHandler(
                consumer_key,
                consumer_secret,
                callback="http://localhost:8501/callback/twitter"
            )
            auth_url = auth.get_authorization_url()
            # Store the request token
            st.session_state.oauth_token_secret = auth.request_token['oauth_token_secret']

            st.markdown("### Please authenticate with Twitter")
            st.link_button("Connect Twitter Account", auth_url)

        except Exception as e:
            st.error(f"Failed to start auth: {str(e)}")

    # Handle callback
    elif "oauth_verifier" in st.query_params:
        st.write("Processing callback...")
        try:
            verifier = st.query_params.get("oauth_verifier")
            oauth_token = st.query_params.get("oauth_token")

            auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret)
            auth.request_token = {
                'oauth_token': oauth_token,
                'oauth_token_secret': st.session_state.oauth_token_secret
            }

            access_token, access_token_secret = auth.get_access_token(verifier)

            # Store the access tokens
            st.session_state.access_token = access_token
            st.session_state.access_token_secret = access_token_secret
            st.session_state.authenticated = True

            # Try to get user info
            api = tweepy.API(auth)
            user = api.verify_credentials()
            st.success(f"Authenticated as @{user.screen_name}")

        except Exception as e:
            st.error(f"Callback failed: {str(e)}")

    # If we're already authenticated
    elif st.session_state.get('authenticated'):
        try:
            auth = tweepy.OAuth1UserHandler(
                consumer_key,
                consumer_secret,
                st.session_state.access_token,
                st.session_state.access_token_secret
            )
            api = tweepy.API(auth)
            user = api.verify_credentials()
            st.success(f"Already authenticated as @{user.screen_name}")

            if st.button("Logout"):
                st.session_state.clear()
                st.rerun()

        except Exception as e:
            st.error(f"Session verification failed: {str(e)}")
            st.session_state.clear()
            st.rerun()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    load_dotenv()
    main()
