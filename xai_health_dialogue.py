
 # TODO ensure that health profile is being incorporated in all prompts

import logging
import time
from pathlib import Path

import streamlit as st
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from openai import OpenAI
import stripe
import tweepy


logging.basicConfig(level=logging.DEBUG)

def setup_logging():
    logger = logging.getLogger('twitter_auth')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    fh = logging.FileHandler('twitter_auth.log')  # Log to a file
    fh.setLevel(logging.INFO)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger

logger = setup_logging()

# Load the .env file
load_dotenv()

XAI_HEALTH_DIR = os.getenv("XAI_HEALTH_DIR")
print(XAI_HEALTH_DIR)
st.title("xAI-powered Health Coach")

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

XAI_API_KEY = os.getenv("XAI_API_KEY", "your_api_key_here")
BASE_URL = "https://api.x.ai/v1"

if not XAI_API_KEY or not XAI_API_KEY.startswith('xai-'):
    raise ValueError("Invalid API key format")


client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)

def dialogue_tab(user_id):
    if not st.session_state.get('user_id'):
        st.session_state.user_id = user_id

    get_system_message(user_id)
    user_provides_health_update(user_id)
    st.caption(f"Authenticated user: {user_id}")
    review_your_relationship_with_user(user_id)

def user_profile_tab(user_id):
    manage_user_profile(user_id)

def ensure_user_directory(user_id):
    base_dir = Path(__file__).parent
    users_dir = base_dir / 'userdata'
    users_dir.mkdir(exist_ok=True)
    user_dir = users_dir / str(user_id)
    user_dir.mkdir(exist_ok=True)
    return user_dir

def save_session_state(session_state):
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.error("User ID not found. Please authenticate first.")
        return

    try:
        user_dir = ensure_user_directory(st.session_state.user_id)
        session_file = user_dir / 'session_state.json'

        auth_keys = ['auth_state', 'access_token', 'access_token_secret', 'request_token', 'request_token_secret', 'user_id']
        auth_data = {key: st.session_state.get(key) for key in auth_keys}

        state_data = {
            "conversation": session_state,
            "authentication": auth_data
        }

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=4)

        logging.debug(f"Session state (including auth) saved to {session_file}: {auth_data}")

    except Exception as e:
        logging.error(f"Error saving session state: {str(e)}")
        st.error(f"Error saving session state: {str(e)}")

def load_session_state(user_id):
    try:
        user_dir = ensure_user_directory(user_id)
        session_file = user_dir / 'session_state.json'

        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                conversation = state_data.get("conversation", []) if isinstance(state_data, dict) else []
                auth_data = state_data.get("authentication", {}) if isinstance(state_data, dict) else {}

                for key, value in auth_data.items():
                    if value is not None and key not in st.session_state:
                        st.session_state[key] = value
                        logging.debug(f"Restored {key}: {value}")

                if 'user_id' in auth_data and auth_data['user_id']:
                    st.session_state.user_id = auth_data['user_id']

                logging.debug(f"Loaded session state for user {user_id}")
                return conversation
        else:
            logging.debug(f"No existing session state found for user {user_id}")
            return []

    except Exception as e:
        logging.error(f"Error loading session state: {str(e)}")
        return []

def cleanup_old_sessions(max_age_days=90):
    try:
        base_dir = Path(__file__).parent
        users_dir = base_dir / 'users'
        if not users_dir.exists():
            return
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        for user_dir in users_dir.iterdir():
            if user_dir.is_dir():
                session_file = user_dir / 'session_state.json'
                if session_file.exists():
                    file_age = current_time - session_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        session_file.unlink()
                        logging.info(f"Removed old session file: {session_file}")
                if not any(user_dir.iterdir()):
                    user_dir.rmdir()
                    logging.info(f"Removed empty user directory: {user_dir}")
    except Exception as e:
        logging.error(f"Error during session cleanup: {str(e)}")

def user_provides_health_update(user_id):
    if not st.session_state.get('user_id'):
        st.session_state.user_id = user_id
    if st.session_state.user_id is None:
        st.error("Please authenticate first")
        return

    with st.form("health_update_form"):
        user_input = st.text_area(
            "How's your health today? Fill me in on sleep, nutrition, exercise, stress, and anything else that's on your mind.",
            key="health_input"
        )
        submitted = st.form_submit_button("Submit")

        if submitted:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.session_state.append(
                {"role": "user", "content": user_input, "timestamp": current_time}
            )
            coach_info = get_system_message(st.session_state.user_id)
            messages = [{"role": "system", "content": coach_info}] + st.session_state.session_state

            try:
                response = client.chat.completions.create(model="grok-2-latest", messages=messages)
                ai_response = response.choices[0].message.content
                st.session_state.session_state.append(
                    {"role": "assistant", "content": ai_response, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                )
                save_session_state(st.session_state.session_state)
                st.write("Feedback from AI:")
                st.write(ai_response)
                recommendations = [line for line in ai_response.split("\n") if line.startswith("Recommendation: ")]
                if recommendations:
                    st.write("Actionable Recommendations:")
                    for rec in recommendations:
                        st.write(rec)
            except Exception as e:
                st.error(f"Error contacting AI service: {str(e)}")

def show_history(user_id):
    if st.session_state.session_state:
        with st.expander("💬 Conversation History", expanded=False):
            st.markdown("""
                <style>
                    .stChatMessage { padding: 0.5rem !important; margin-bottom: 0.5rem !important; }
                    .stMarkdown { margin-bottom: 0px !important; }
                    hr { margin: 0.2rem 0 !important; }
                </style>
            """, unsafe_allow_html=True)

            sorted_messages = sorted(
                st.session_state.session_state,
                key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"),
                reverse=True
            )

            current_date = None
            for message in sorted_messages:
                message_date = message["timestamp"].split()[0]
                if message_date != current_date:
                    current_date = message_date
                    st.markdown(f"#### {message_date}")
                message_time = message["timestamp"].split()[1]
                with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
                    st.write(f"{message_time}")
                    st.write(message["content"])
                st.markdown("<hr>", unsafe_allow_html=True)

def initialize_user(user_id):
    user_dir = ensure_user_directory(user_id)
    st.session_state.user_id = user_id
    st.session_state.session_state = load_session_state(user_id)

def initialize_default_user():
    default_user_id = "default_user"
    default_profile = {
        "profile_text": "Name: John Doe; Age: 30; Height: 180cm; Weight: 75kg; Diet: Vegetarian; Social Info: Loves hiking; Health: Hypertension"
    }
    os.makedirs(XAI_HEALTH_DIR, exist_ok=True)
    with open(f"{XAI_HEALTH_DIR}/userdata/{default_user_id}_profile.json", "w") as file:
        json.dump(default_profile, file)
    print(f"Initialized default user profile for {default_user_id}")

def manage_user_profile(user_id):
    profile_filename = f"{XAI_HEALTH_DIR}/userdata/{user_id}_profile.json"
    print(profile_filename)

    if not os.path.exists(profile_filename):
        st.warning("No profile found for this user.")
        with st.form("create_profile"):
            st.subheader("Create a New Profile")
            profile_text = st.text_area("Enter your profile information here:", height=300)
            submitted = st.form_submit_button("Create Profile")
            if submitted:
                with open(profile_filename, "w") as file:
                    json.dump({"profile_text": profile_text}, file)
                    st.success(f"Profile saved for user ID: {user_id}")
    else:
        with open(profile_filename, "r") as file:
            profile = json.load(file)
        edit_profile = st.radio("Update?", ["No", "Yes"], horizontal=True)
        if edit_profile == "Yes":
            with st.form("edit_profile"):
                profile_text = st.text_area("Update", profile.get("profile_text", ""), height=300,
                                            help="Update your health history here. Free text, any format.")
                submitted = st.form_submit_button("Update")
                if submitted:
                    with open(profile_filename, "w") as file:
                        json.dump({"profile_text": profile_text}, file)
                        st.success(f"History saved for user ID: {user_id}")
        else:
            st.write(profile.get("profile_text", "No profile found."))
    st.caption(f"User ID: {user_id}")

def get_system_message(user_id):
    base_system_message = "You are a personal health assistant providing feedback and recommendations based on user health updates. Your advice is tailored specifically for the user. In creating the advice you consider all the information in his user profile and his conversation history.\n\n"
    coach = CoachProfile(user_id)
    attributes = st.session_state.get(f"coach_attributes_{user_id}", coach.load_current_coach_attributes())
    if attributes:
        all_available_attributes = coach.load_all_available_attributes()
        coach_additional_instructions = "As you formulate your response, consider the following additional attributes of your personality.\n\n"
        for attribute in attributes:
            coach_additional_instructions += f"{all_available_attributes.get(attribute, 'Unknown attribute')}\n"
        return f"{base_system_message}\n{coach_additional_instructions}"
    else:
        logging.warning(f"No coach attributes for {user_id}")
        return base_system_message

def review_your_relationship_with_user(user_id="user_1"):
    review_prompts = {
        "work-together": "Look back over your relationship with the current user and describe its progression. Highlight any areas where you can work together to improve."
    }
    return

def check_stripe_subscription(user_id):
    stripe.api_key = st.secrets["stripe"]["api_key"]
    try:
        customer_id_file = f"{XAI_HEALTH_DIR}/{user_id}_stripe_customer.json"
        if os.path.exists(customer_id_file):
            with open(customer_id_file, "r") as f:
                customer_data = json.load(f)
                customer_id = customer_data["customer_id"]
        else:
            customer = stripe.Customer.create(email=f"{user_id}@example.com")
            customer_id = customer["id"]
            with open(customer_id_file, "w") as f:
                json.dump({"customer_id": customer_id}, f)

        subscriptions = stripe.Subscription.list(customer=customer_id)
        if subscriptions.data and subscriptions.data[0].status == "active":
            return True
        else:
            st.warning("Free during alpha test. In future, subscriptions will be required.")
            return True
    except Exception as e:
        st.error(f"Stripe error: {e}")
        return False

def give_me_the_latest_tab():
    canned_searches = {
        "Intentional health": "https://grok.com/share/72297e01-7fbb-49f8-8452-3b013d90d0ad",
        "Fitness benefits of housework": "https://grok.com/share/f7a9dca9-d1ad-4d7b-a562-2f28627897d1"
    }
    st.write("Peer-reviewed recent research results, powered by Grok")
    for search_label, search_url in canned_searches.items():
        st.markdown(f"- [{search_label}]({search_url})")

def get_research_from_before_learning_cutoff(canned_searches):
    researcher_message = "You are a health science expert who is thoroughly familiar with the scientific literature on every aspect of health."
    for search_label, search_url in canned_searches.items():
        topic_message = f"Give me the very latest research on {search_label}."
        messages = [
            dict(role="system", content=researcher_message),
            dict(role="user", content=topic_message)
        ]
        client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")
        response = client.chat.completions.create(model="grok-2-latest", messages=messages)
        topic_response = response.choices[0].message.content
        st.write(f"**{search_label}**")
        st.write(topic_response)

def twitter_auth():
    logging.debug("Starting twitter_auth")
    logging.debug("Current session state: %s", st.session_state)

    def clear_auth_session():
        auth_keys = ['auth_state', 'access_token', 'access_token_secret', 'request_token', 'request_token_secret']
        for key in auth_keys:
            if key in st.session_state:
                del st.session_state[key]
        logging.debug("Auth session cleared")

    def initialize_session_state():
        defaults = {
            'auth_state': 'not_started',
            'access_token': None,
            'access_token_secret': None,
            'request_token': None,
            'request_token_secret': None,
            'user_id': None
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def validate_tokens():
        if st.session_state.get('access_token') and st.session_state.get('access_token_secret'):
            try:
                client = tweepy.Client(
                    consumer_key=consumer_key,
                    consumer_secret=consumer_secret,
                    access_token=st.session_state.access_token,
                    access_token_secret=st.session_state.access_token_secret
                )
                me = client.get_me()
                logging.info("Tokens validated successfully: user=%s", me.data.username)
                return True
            except tweepy.TweepyException as e:
                logging.error("Token validation failed: %s", str(e))
                # Try to refresh immediately
                auth_url = refresh_twitter_auth()
                if auth_url:
                    st.markdown(f"Please re-authorize: [Click here]({auth_url})")
                return False
        return False

    def ensure_valid_auth():
        if not validate_tokens():
            logging.info("Invalid or expired tokens, initiating refresh")
            auth_url = refresh_twitter_auth()
            if auth_url:
                st.markdown(f"Please re-authorize: [Click here]({auth_url})")
                st.stop()  # Stop execution until reauthorization
            return False
        return True

    def refresh_twitter_auth():
        clear_auth_session()
        try:
            auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, callback=callback)
            auth_url = auth.get_authorization_url()
            st.session_state.request_token = auth.request_token['oauth_token']
            st.session_state.request_token_secret = auth.request_token['oauth_token_secret']
            st.session_state.auth_state = 'awaiting_callback'
            logging.info("Auth refresh successful, URL generated: %s", auth_url)
            return auth_url
        except Exception as e:
            logging.error("Auth refresh failed: %s", str(e))
            return None

    initialize_session_state()

    consumer_key = st.secrets["twitter"]["consumer_key"]
    consumer_secret = st.secrets["twitter"]["consumer_secret"]
    environment = os.getenv("ENVIRONMENT", "dev")
    callback = "http://localhost:8501" if environment == "dev" else "http://34.172.181.254:8501/"
    logging.debug("Environment: %s, Callback: %s", environment, callback)

    # Handle callback from Twitter
    if 'oauth_verifier' in st.query_params and 'oauth_token' in st.query_params:
        try:
            verifier = st.query_params['oauth_verifier']
            oauth_token = st.query_params['oauth_token']
            auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, callback=callback)
            auth.request_token = {
                'oauth_token': oauth_token,
                'oauth_token_secret': st.session_state.request_token_secret
            }
            access_token, access_token_secret = auth.get_access_token(verifier)
            st.session_state.access_token = access_token
            st.session_state.access_token_secret = access_token_secret
            st.session_state.auth_state = 'authenticated'
            client = tweepy.Client(consumer_key=consumer_key, consumer_secret=consumer_secret,
                                   access_token=access_token, access_token_secret=access_token_secret)
            me = client.get_me()
            st.session_state.user_id = me.data.username
            logging.info("Authentication successful: user=%s, access_token=%s", me.data.username, access_token[:10] + "...")
            save_session_state(st.session_state.session_state)
            # Optional: Display success in UI
            #st.success(f"Authenticated as @{me.data.username}")
            return me.data.username
        except tweepy.TweepyException as e:
            logging.error("Authentication error: %s", str(e))
            # st.error(f"Authentication Error: {str(e)}")  # Already present, just ensuring visibility
            clear_auth_session()
            return None

    # Check if already authenticated
    if st.session_state.auth_state == 'authenticated' and validate_tokens():
        if ensure_valid_auth():  # Add this line
            logging.info("Using existing authenticated session for user=%s", st.session_state.user_id)
            return st.session_state.user_id

    # Initiate authentication
    if st.button("You must connect your X account to Twitter to continue."):
        auth_url = refresh_twitter_auth()
        if auth_url:
            logging.info("Prompting user to authorize at: %s", auth_url)
            st.markdown(f"[Click here to authorize with Twitter]({auth_url})")
        else:
            logging.error("Failed to generate auth URL")
            st.error("Failed to start authentication process")
    return None

def main():
    logging.basicConfig(level=logging.INFO)
    load_dotenv()

    if 'session_state' not in st.session_state:
        st.session_state.session_state = []
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'last_cleanup' not in st.session_state:
        st.session_state.last_cleanup = time.time()
        cleanup_old_sessions()
    elif time.time() - st.session_state.last_cleanup > 86400:
        cleanup_old_sessions()
        st.session_state.last_cleanup = time.time()

    # Load existing session state if available and no new auth
    if st.session_state.user_id and not ('oauth_verifier' in st.query_params and 'oauth_token' in st.query_params):
        st.session_state.session_state = load_session_state(st.session_state.user_id)

    user_id = twitter_auth()
    if user_id and user_id != st.session_state.user_id:
        st.session_state.user_id = user_id
        initialize_user(user_id)
        st.session_state.session_state = load_session_state(user_id)
        st.toast(f"Authenticated as @{user_id}!")

        coach = CoachProfile(user_id)
        user_coach_file = os.path.join(XAI_HEALTH_DIR, f"{user_id}_coach_attributes.json")
        default_coach_attributes = CoachProfile.initialize_default_coach_attributes()
        if not os.path.exists(user_coach_file):
            coach.save_selected_attributes(default_coach_attributes)
        if f"coach_attributes_{user_id}" not in st.session_state:
            st.session_state[f"coach_attributes_{user_id}"] = coach.load_current_coach_attributes()

    # Use existing user_id if no new authentication
    current_user_id = st.session_state.user_id

    st.image(os.path.join(XAI_HEALTH_DIR, "resources", "coach_cartoon.jpg"), width=300)
    with st.expander("Showcasing the Unique Advantages of the xAI API", expanded=False):
        st.markdown("""
        - What are the unique advantages of Grok's API? 
            - [Ask Grok](https://x.com/i/grok/share/VluBBLPMdWKSn0yeMWhOXX6xO)
            - [Roll-out blog post...](https://x.ai/blog/api)
            - [API home page](https://x.ai/api)
            - [Docs](https://docs.x.ai/docs/overview)
        - Demonstrated in Health Coach:
           - Real-time research updates, e.g. ["Intentional health"](https://grok.com/share/72297e01-7fbb-49f8-8452-3b013d90d0ad)
           - Fun, configurable personalities: "no-bs", "moar-fish", "sexy-time"
           - Persistence and self-reflection
           - Alignment with **human thriving**, not "safety"
           - Multimodal capabilities _(to come)_
           - Grok 3 Deep Search, Think _(to come)_
           - [Easy "drop-in" integration with other APIs](https://github.com/fredzannarbor/xai_health_coach/blob/main/xai_health_dialogue.py#L321-333)    
           """)

    with st.expander("Talk to Coach", expanded=True):
        if check_stripe_subscription(current_user_id):
            dialogue_tab(current_user_id)
        else:
            st.write("Subscribe to talk to Coach!")

    show_history(current_user_id)

    with st.expander("Give Me The Latest Health Science From Grok", expanded=True):
        give_me_the_latest_tab()

    with st.expander("Update My Health History"):
        user_profile_tab(current_user_id)

    with st.expander("About Coach", expanded=True):
        if current_user_id:
            #st.info(f"Authenticated as @{current_user_id}!")
            coach = CoachProfile(current_user_id)
            coach.coach_tab()
        else:
            st.warning("Please authenticate to view coach details.")

class CoachProfile:
    def __init__(self, user_id, selected_attributes=None,
                 available_attributes_file_path=f"{XAI_HEALTH_DIR}/all_available_coach_attributes.json"):
        self.user_id = user_id
        self.available_attributes_file_path = available_attributes_file_path
        self.coach_attributes_file_path = f"{XAI_HEALTH_DIR}/{self.user_id}_coach_attributes.json"
        self.selected_attributes = selected_attributes or st.session_state.get(f"coach_attributes_{user_id}", [])

    def coach_tab(self):
        self.load_all_available_attributes()
        self.display_current_coach_personality()
        self.modify_current_coach_attributes()

    def load_current_coach_attributes(self):
        if os.path.exists(self.coach_attributes_file_path):
            try:
                with open(self.coach_attributes_file_path, "r") as file:
                    data = json.load(file)
                    attributes = data.get(self.user_id, [])
                    st.session_state[f"coach_attributes_{self.user_id}"] = attributes
                    logging.info(f"Loaded coach attributes for user {self.user_id}: {attributes}")
                    return attributes
            except json.JSONDecodeError:
                logging.error(f"Corrupted JSON in {self.coach_attributes_file_path}, resetting")
                attributes = self.initialize_default_coach_attributes()
                self.save_selected_attributes(attributes)
                return attributes
        else:
            logging.warning(f"No coach attributes file found at {self.coach_attributes_file_path}")
            attributes = self.initialize_default_coach_attributes()
            self.save_selected_attributes(attributes)
            return attributes

    def save_selected_attributes(self, attributes=None):
        attributes = attributes if attributes is not None else self.selected_attributes
        try:
            data = {self.user_id: attributes}
            with open(self.coach_attributes_file_path, "w") as file:
                json.dump(data, file, indent=4)
            st.session_state[f"coach_attributes_{self.user_id}"] = attributes
            self.selected_attributes = attributes
            logging.info(f"Saved coach attributes: {data}")
        except Exception as e:
            logging.error(f"Error saving coach attributes: {e}")
            st.error(f"Error saving coach attributes: {e}")

    def load_all_available_attributes(self):
        if self.available_attributes_file_path and os.path.exists(self.available_attributes_file_path):
            with open(self.available_attributes_file_path, "r") as file:
                self.all_available_attributes = json.load(file)
                logging.info(f"Available attributes loaded from {self.available_attributes_file_path}")
        else:
            self.all_available_attributes = {}
        return self.all_available_attributes

    def modify_current_coach_attributes(self):
        options = list(self.load_all_available_attributes().keys())
        current_attributes = st.session_state.get(f"coach_attributes_{self.user_id}", self.load_current_coach_attributes())
        selected_attributes = st.multiselect(
            "Available Coach Attributes",
            options=options,
            default=current_attributes,
            key=f"coach_attributes_selector_{self.user_id}"
        )
        if st.button("Save Selected Attributes"):
            self.save_selected_attributes(selected_attributes)
            logging.info(f"Selected attributes saved: {selected_attributes}")
            st.success("Coach attributes updated!")

    @staticmethod
    def initialize_default_coach_attributes():
        default_attributes = {
            "default": ["loves-citations", "no-bs", "hard-core"]
        }
        default_file_path = f"{XAI_HEALTH_DIR}/default_coach_attributes.json"
        if not os.path.exists(default_file_path):
            with open(default_file_path, "w") as f:
                json.dump(default_attributes, f, indent=4)
        return default_attributes["default"]

    def display_current_coach_personality(self):
        attributes = st.session_state.get(f"coach_attributes_{self.user_id}", self.load_current_coach_attributes())
        if attributes:
            st.subheader("Current Personality")
            for attribute in attributes:
                st.markdown(f"- {self.all_available_attributes.get(attribute, 'Unknown attribute')}")
        else:
            st.warning("No attributes selected or saved!")

if __name__ == "__main__":
    main()