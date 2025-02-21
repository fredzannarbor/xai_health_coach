# xAI Health Coach

This repository contains a Python-based health coach application that leverages the xAI Grok API to provide personalized health and wellness recommendations.  The coach interacts with users via a Streamlit interface, allowing for dynamic conversations and personalized advice.

## Features

* **Personalized Recommendations:** Analyzes user input (free-text descriptions of health status, goals, and lifestyle) and provides tailored recommendations.
* **Holistic Approach:** Considers various aspects of well-being, including diet, exercise, sleep, stress management, and mental health.
* **Actionable Advice:**  Offers concrete, achievable steps for users to improve their health.
* **Conversation History:**  Maintains a log of user interactions with the coach, allowing for context and progress tracking.
* **User Profile Management:** Stores user health information in a free-text format for personalized coaching.
* **Customizable Coach Personality:**  Allows users to select attributes that influence the coach's communication style (e.g., friendly, research-oriented, direct).
* **Integration with Grok:** Utilizes the Grok API for accessing relevant health information and research.

### Roadmap & Wish List

Help me showcase the unique strengths of Grok's API!  Some key building blocks that you may be able to help with:

- _Implement X authentication_
- Implement chargeback to user xai api account
- Health-coach-powered Spaces on X, etc.
- Improve Grok's ability to find real-time peer-reviewed health knowledge
   - Give me the latest on wastewater measures of viral threats
   - Improve customization of coach
   - behind-scenes translate & export to other health formats (e.g. Apple's HealthKit)
  - Improve multimodal input & analysis -- ECGs, etc.
- Human-Thriving-Focused Dialogue
  - The end goal of AI health dialogue should be to improve the probability of species survival
  - Truth-seeking health guidance not modified by non-health/non-human-thriving priorities
  

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables:**
   Create a `.env` file in the project root and set the following variables:
   ```
   XAI_API_KEY=<your_xai_api_key>
   XAI_HEALTH_DIR=<path_to_data_directory>
   ```
   `XAI_HEALTH_DIR` is the directory where user profiles, session state, and coach attribute files will be stored.
4. **Run the application:**
   ```bash
   streamlit run xai_health_dialogue.py 
   ```



## File Structure

* `xai_health_dialogue.py`: Main application file containing the Streamlit interface and logic for interacting with the xAI API.
* `default_user_coach_personality.json`: (Example) Default coach personality attributes.
* `user_1_coach_attributes.json`: (Example) User-specific coach attributes.
* `all_available_coach_attributes.json`:  List of all available coach attributes with descriptions.
* `session_state.json`: Stores the conversation history between the user and the coach.
* `<user_id>_profile.json`: Stores the health profile for each user.


## Disclaimer

This application is intended for informational purposes only and should not be considered medical advice. Always consult with a qualified healthcare professional before making any changes to your diet, exercise routine, or health regimen.  The information provided by this application is not intended to diagnose, treat, cure, or prevent any disease.