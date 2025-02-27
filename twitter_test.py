import streamlit as st
import tweepy
from dotenv import load_dotenv
import base64
import json

st.set_page_config(page_title="Twitter Auth Test", layout="wide")


def encode_state(data):
    """Encode dictionary to base64 string"""
    json_str = json.dumps(data)
    return base64.b64encode(json_str.encode()).decode()


def decode_state(state_str):
    """Decode base64 string to dictionary"""
    try:
        json_str = base64.b64decode(state_str.encode()).decode()
        return json.loads(json_str)
    except:
        return None


def init_session_state():
    """Initialize session state variables"""
    if 'auth_state' not in st.session_state:
        st.session_state.auth_state = 'not_started'
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'access_token_secret' not in st.session_state:
        st.session_state.access_token_secret = None
    if 'request_token' not in st.session_state:
        st.session_state.request_token = None
    if 'request_token_secret' not in st.session_state:
        st.session_state.request_token_secret = None


def main():
    init_session_state()

    st.title("Twitter Auth Test")
    st.divider()

    # Debug section
    with st.expander("Debug Information", expanded=True):
        st.write("Auth State:", st.session_state.auth_state)
        st.write("Query Parameters:", dict(st.query_params))
        st.write("Session State:", dict(st.session_state))

    # First, handle callback if present
    if 'oauth_verifier' in st.query_params and 'oauth_token' in st.query_params:
        try:
            st.write("Processing callback from Twitter...")
            verifier = st.query_params['oauth_verifier']
            oauth_token = st.query_params['oauth_token']

            # Create new handler
            consumer_key = st.secrets["twitter"]["consumer_key"]
            consumer_secret = st.secrets["twitter"]["consumer_secret"]
            auth = tweepy.OAuth1UserHandler(
                consumer_key,
                consumer_secret,
                callback="http://127.0.0.1:8501"
            )

            # Set the request token from stored session state
            auth.request_token = {
                'oauth_token': oauth_token,
                'oauth_token_secret': st.session_state.request_token_secret
            }

            # Get the access token
            access_token, access_token_secret = auth.get_access_token(verifier)

            # Store in session state
            st.session_state.access_token = access_token
            st.session_state.access_token_secret = access_token_secret
            st.session_state.auth_state = 'authenticated'

            st.success("Successfully authenticated!")

            # Test the credentials
            client = tweepy.Client(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )

            # Try to get user info
            me = client.get_me()
            st.write("Successfully connected as:", me.data.username)

        except Exception as e:
            st.error(f"Callback Error: {str(e)}")
            st.code(str(e), language="text")
            st.session_state.auth_state = 'error'

    # Handle initial authentication
    elif st.button("Start Authentication") or st.session_state.auth_state == 'not_started':
        try:
            consumer_key = st.secrets["twitter"]["consumer_key"]
            consumer_secret = st.secrets["twitter"]["consumer_secret"]

            # Create OAuth handler
            auth = tweepy.OAuth1UserHandler(
                consumer_key,
                consumer_secret,
                callback="http://127.0.0.1:8501"
            )

            # Get authorization URL
            auth_url = auth.get_authorization_url()

            # Store the request tokens in session state
            st.session_state.request_token = auth.request_token['oauth_token']
            st.session_state.request_token_secret = auth.request_token['oauth_token_secret']
            st.session_state.auth_state = 'awaiting_callback'

            # Show debug info
            st.write("Debug - Generated tokens:")
            st.json({
                'request_token': st.session_state.request_token,
                'request_token_secret': st.session_state.request_token_secret
            })

            # Show the authentication link
            st.markdown("### Please authenticate with Twitter")
            st.markdown(f"[Click here to authenticate with Twitter]({auth_url})")
            st.info("After authenticating, you'll be redirected back to this app.")

        except Exception as e:
            st.error(f"Authentication Error: {str(e)}")
            st.code(str(e), language="text")
            st.session_state.auth_state = 'error'

    # Show current authentication state
    st.write("Current authentication state:", st.session_state.auth_state)

    # Reset button
    if st.button("Reset Authentication"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_set_query_params()  # Clear URL parameters
        st.rerun()


if __name__ == "__main__":
    load_dotenv()
    main()
