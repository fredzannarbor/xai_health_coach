import json
import logging
import os
from datetime import datetime
from ftplib import all_errors
from pprint import pprint

import streamlit as st
from click import option
from dotenv import load_dotenv
from openai import OpenAI
from streamlit.elements.lib.options_selector_utils import convert_to_sequence_and_check_comparable

if "session_state" not in st.session_state:
    st.session_state.session_state = []

# Load the .env file
load_dotenv()

XAI_HEALTH_DIR = os.getenv("XAI_HEALTH_DIR")
print(XAI_HEALTH_DIR)
st.title("xAI Health Coach")
def get_user_id(dummy_user="user_1"):
    if dummy_user:
        return dummy_user
    else:
        return st.session_state.user_id




# Configuration for OpenAI API
XAI_API_KEY = os.getenv("XAI_API_KEY", "your_api_key_here")
BASE_URL = "https://api.x.ai/v1"

client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)

def dialogue_tab(user_id="user_1"):
    get_system_message(user_id=user_id)
    user_provides_health_update(user_id=user_id)
    review_your_relationship_with_user(user_id=user_id)


def user_profile_tab(user_id="user_1"):
    manage_user_profile(user_id=user_id)


# Function to save session state
def save_session_state(state, filename=f"{XAI_HEALTH_DIR}/session_state.json"):
    filepath = os.path.join(
        XAI_HEALTH_DIR, "session_state.json"
    )  # Safer path construction
    print(f"Saving session state: {state}")  # Print before saving
    with open(filepath, "w") as file:
        json.dump(state, file, indent=4)  # Use indent for readability


def load_session_state(filename=f"{XAI_HEALTH_DIR}/session_state.json"):
    filepath = os.path.join(
        XAI_HEALTH_DIR, "session_state.json"
    )  # Safer path construction
    if os.path.exists(filepath):
        print(f"Loading session state from {filepath}")  # Print full path!
        try:
            with open(filepath, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:  # Catch JSON errors!
            print(f"Error decoding JSON: {e}")
            return []  # return empty list on decode error
    else:
        print(f"Session state file {filepath} not found.")  # Print full path!
    return []


def user_provides_health_update(user_id="user_1"):
    # User input for health update
    with st.form("health_update_form"):
        user_input = st.text_area(
            "How's your health today? Fill me in on sleep, nutrition, exercise, stress, and anything else that's on your mind.",
            key="health_input",
        )
        submitted = st.form_submit_button("Submit")

        if submitted:
            # Get current datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Append user input to session state
            st.session_state.session_state.append(
                {"role": "user", "content": user_input, "timestamp": current_time}
            )

            # Prepare messages for OpenAI, including conversation history
            messages = [
                dict(role="system", content=get_system_message())
            ] + st.session_state.session_state

            # Call OpenAI API
            response = client.chat.completions.create(
                model="grok-2-latest", messages=messages
            )

            # Get AI's response
            ai_response = response.choices[0].message.content

            # Append AI response to session state with timestamp
            st.session_state.session_state.append(
                {
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            # Save session state to file
            save_session_state(st.session_state.session_state)

            # Display AI response
            st.write("Feedback from AI:")
            st.write(ai_response)

            recommendations = [
                line
                for line in ai_response.split("\n")
                if line.startswith("Recommendation: ")
            ]
            if recommendations:
                st.write("Actionable Recommendations:")
                for rec in recommendations:
                    st.write(rec)






# Display conversation history in reverse chronological order
def show_history(user_id="user_1"):
    if st.session_state.session_state:
        with st.expander("Show Conversation History", expanded=False):
            # Group messages by date
            daily_messages = {}
            for message in st.session_state.session_state:
                date = message["timestamp"].split(" ")[0]  # Extract date from timestamp
                if date not in daily_messages:
                    daily_messages[date] = []
                daily_messages[date].append(message)

            # Display messages grouped by day in expanders
            for date, messages in sorted(daily_messages.items(), reverse=True):
                for message in messages:
                    with st.chat_message(message["role"]):
                        st.markdown(f"**{message['timestamp']}**")
                        st.json(message, expanded=False)


def initialize_default_user():
    """
    Initializes a dummy default user profile for testing purposes.
    This function creates a basic profile with placeholder data and saves it.
    """
    default_user_id = "default_user"
    default_profile = {
        "profile_text": "Name: John Doe; Age: 30; Height: 180cm; Weight: 75kg; Diet: Vegetarian; Social Info: Loves hiking; Health: Hypertension"
    }

    # Create the directory if it doesn't exist
    os.makedirs(XAI_HEALTH_DIR, exist_ok=True)

    # Save the default profile
    with open(f"{XAI_HEALTH_DIR}/{default_user_id}_profile.json", "w") as file:
        json.dump(default_profile, file)

    print(f"Initialized default user profile for {default_user_id}")


def manage_user_profile(user_id="user_1"):
    """
    Manages user's personal profile where all info is entered in one free text field.
    - Checks if we have a profile for the user.
    - If not, prompts to create one.
    - If we do, allows the profile to be displayed and edited in a single text area.
    """
    # Use a default user ID when there's no authentication
    user_id = "user_1"  # This is now hardcoded for the dummy implementation
    profile_filename = f"{XAI_HEALTH_DIR}/{user_id}_profile.json"
    print(profile_filename)

    if not os.path.exists(profile_filename):
        st.warning("No profile found for this user.")
        with st.form("create_profile"):
            st.subheader("Create a New Profile")
            profile_text = st.text_area(
                "Enter your profile information here:",
                height=300,
            )
            submitted = st.form_submit_button("Create Profile")
            if submitted:

                with open(profile_filename, "w") as file:
                    json.dump({"profile_text": profile_text}, file)
                    st.success(f"Profile saved for user ID:{user_id}")

    else:
        # Load existing profile
        with open(profile_filename, "r") as file:
            profile = json.load(file)
        # display profile

       # col1, col2, col3 = st.columns(1, 5, 1)
        edit_profile = st.radio("Update?", ["No", "Yes"], horizontal=True)
        if edit_profile == "Yes":
            with st.form("edit_profile"):
                profile_text = st.text_area("Update", profile.get("profile_text", ""), height=300, help="Update your health history here.  Free text, any format, anything you think is important: just tell Coach.")

                submitted = st.form_submit_button("Update")
                if submitted:
                    with open(profile_filename, "w") as file:
                        json.dump({"profile_text": profile_text}, file)
                        st.success(f"History saved for user ID:{user_id}")
        else:
            st.write(profile.get("profile_text", "No profile found."))

    st.caption(f"User ID: {user_id}")

def get_system_message(user_id="user_1"):
    base_system_message = "You are a personal health assistant providing feedback and recommendations based on user health updates. Your advice is tailored specifically for the user.  In creating the advice you consider all the information in his user profile and his conversation history.\n\n"
    #personality_attributes = load_coach_personality(user_id)
    coach_attributes_file = f"{XAI_HEALTH_DIR}/{user_id}_coach_attributes.json"
    coach = CoachProfile(user_id=user_id)
    if os.path.exists(coach_attributes_file):
        with open(coach_attributes_file, "r") as f:
            coach_attributes = json.load(f)

        coach_additional_instructions = "As you formulate your response, consider the following additional attributes of your personality.\n\n"
        for attribute in coach_attributes[user_id] if coach_attributes.get(user_id) else []:
            all_available_attributes = coach.load_all_available_attributes()
            coach_additional_instructions += f"{all_available_attributes[attribute]}\n"
            #st.write(f"added additional instructions: {additional_instructions}")
        return f"{base_system_message}\n{coach_additional_instructions}"
    else:
        st.error(f"No coach attributes file found at {coach_attributes_file}")
        return base_system_message


def review_your_relationship_with_user(user_id="user_1"):
    """
    You will be given a prompt to review your relationship with the user.

    """
    review_prompts = {
        "work-together": "Look back over your relationship with the current user and describe its progression. Highlight any areas where you can work together to improve."
    }
    return


# Main app function
def give_me_the_latest_tab():
    # dict of canned searches
    canned_searches = {"Intentional health": "https://grok.com/share/72297e01-7fbb-49f8-8452-3b013d90d0ad", "Fitness benefits of housework": "https://grok.com/share/f7a9dca9-d1ad-4d7b-a562-2f28627897d1"}
    # show a go button for each canned search
    st.write("Peer-reviewed recent research results, powered by Grok")
    for search_label, search_url in canned_searches.items():
        st.markdown(f"- [{search_label}]({search_url})")  # Display the hyperlinked text



def main():

   # initialize_default_user()
    user_id = "user_1"
    st.session_state.session_state = load_session_state()

    #col1, col2 = st.columns([6,4])


    with st.expander("Showcasing the Unique Advantages of the xAI API", expanded=True):
        st.markdown("""
           - Grok [explains](https://x.com/i/grok/share/8Ki9YkE5JiUUN5Gyg5d8XDuKo)
           - Real-Time Data Access
           - Personality and Interaction Style
           - Multimodal Capabilities
           - Integration with X Platform
           - API Flexibility
           - Human-Thriving-Focused AI Development
           """)
    st.image(f"{XAI_HEALTH_DIR}/resources/coach_cartoon.jpg", width=300)

    with st.expander("About Coach", expanded=False):
            coach = CoachProfile()
            coach.coach_tab()

    with st.expander("Give Me The Latest Health Science From Grok"):
        give_me_the_latest_tab()


    with st.expander("Talk to Coach", expanded=True):
        dialogue_tab()
    with st.expander("Update My Health History"):
        user_profile_tab()

    show_history(user_id=user_id)




class CoachProfile:

    def __init__(self, user_id="user_1", selected_attributes=[], available_attributes_file_path=f"{XAI_HEALTH_DIR}/all_available_coach_attributes.json") -> None:

        self.user_id = user_id
        self.selected_attributes = selected_attributes
        self.available_attributes_file_path = available_attributes_file_path
        self.coach_attributes = []
        self.coach_attributes_file_path = f"{XAI_HEALTH_DIR}/{self.user_id}_coach_attributes.json"

    def coach_tab(self):
        self.load_all_available_attributes()
        self.load_current_coach_attributes()
        self.display_current_coach_personality()
        self.modify_current_coach_attributes()



    def load_current_coach_attributes(self):
        """
        Loads the specified personality attributes for the current user.
        """
        coach_attributes_file_path = f"{XAI_HEALTH_DIR}/{self.user_id}_coach_attributes.json"

        if os.path.exists(self.coach_attributes_file_path):
            with open(coach_attributes_file_path, "r") as file:
                self.coach_attributes = json.load(file)
                logging.info(f"Coach attributes loaded for user {self.user_id}: {self.coach_attributes}")
                return self.coach_attributes.get(self.user_id, [])
        else:
            st.warning(f"No coach attributes file found at {coach_attributes_file_path}, creating empty list")
            self.coach_attributes = []

        return []

    def load_all_available_attributes(self):
        if self.available_attributes_file_path and os.path.exists(self.available_attributes_file_path):
            # st.toast(f"Loading available attributes from {self.available_attributes_file_path}")
            with open(self.available_attributes_file_path
                    , "r") as file:
                self.all_available_attributes = json.load(file)
                logging.info(f"Available attributes loaded from {self.available_attributes_file_path}")
        else:
            self.all_available_attributes = {}
        return self.all_available_attributes


    def modify_current_coach_attributes(self):
        """
        Displays a Streamlit multiselect UI to select specific attributes for the user.
        """
        options = list(self.all_available_attributes.keys())
        current_coach_options = self.coach_attributes[self.user_id] if self.coach_attributes else []
        selected_attributes = st.multiselect("Available Coach Attributes",
                                             options=options,
                                             default=current_coach_options,
                                             key="coach_attributes_selector")

        logging.info(f"Selected attributes: {selected_attributes}")
        if st.button("Save Selected Attributes"):
            self.selected_attributes = selected_attributes
            self.save_selected_attributes()
            logging.info("Selected attributes saved.")




    def display_current_coach_personality(self):
        """
        Displays the current coach personality settings for the user.
        """
        attributes = self.load_current_coach_attributes()
        #st.write(f"Current coach attributes: {attributes}")
        if attributes:
            st.subheader("Current Personality")
            for attribute in attributes:
                st.markdown(f"- {self.all_available_attributes[attribute]}")
        else:
            st.warning("No attributes selected or saved!")

    def save_selected_attributes(self):
        """
        Saves the selected coach attributes into the `coach_attributes.json` for the user.
        """
        coach_attributes_file = f"{XAI_HEALTH_DIR}/{self.user_id}_coach_attributes.json"

        try:
            if os.path.exists(self.coach_attributes_file_path):
                with open(self.coach_attributes_file_path, "r") as file:
                    existing_data = json.load(file)
            else:
                existing_data = {}

            # Update attributes for the user
            existing_data[self.user_id] = self.selected_attributes
            #st.write(existing_data)
            with open(self.coach_attributes_file_path, "w") as file:
                json.dump(existing_data, file, indent=4)

            logging.info("Selected coach attributes saved.")
        except Exception as e:
            print(f"Error saving coach attributes: {e}")
            st.error(f"Error saving coach attributes: {e}")



if __name__ == "__main__":
    main()
