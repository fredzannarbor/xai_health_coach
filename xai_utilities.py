import logging
import os
import sys
import urllib
import argparse

import streamlit as st
from openai import OpenAI


def display_dictionary_attributes(self, attributes_dict, default_selected=[]):
    """
    Displays a UI to select specific attributes from a dictionary.
    Args:
        attributes_dict (dict): Dictionary with label:prompt pairs for attributes.
        default_selected (list): List of default selected attributes.

    Returns:
        list: Selected attributes.
    """
    options = list(attributes_dict.keys())
    selected_attributes = st.multiselect("Select Attributes",
                                         options=options,
                                         default=default_selected,
                                         key="attributes_selector")

    logging.info(f"Selected attributes: {selected_attributes}")
    if st.button("Save Selected Attributes"):
        self.selected_attributes = selected_attributes
        self.save_selected_attributes()
        logging.info("Selected attributes saved.")

    return selected_attributes

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


class GiveMeTheLatest:

    def morph_prompts(self, prompts, morph_prompt=None, create_link=True):
        """
        Processes single or multiple prompts, applies a morph prompt, and e
        ither
        fetches the result of the morphed prompt or creates a link to the Grok website.

        Args:
            prompts (str|list): A single prompt or a list of prompts.
            morph_prompt (str): Instruction to optimize the prompt(s).
            create_link (bool): If True, create a Grok website link for the morphed prompt(s).

        Returns:
            str|list: Morphed prompt(s) or a link to the Grok website.
        """

        if isinstance(prompts, str):
            prompts = [prompts]  # Ensure prompts is a list

        if not morph_prompt:
            morph_prompt = "You are a search assistant who is fully aware of all Grok's real-time information sources including but not limited to news, fresh X content, fresh web content, Arxiv and other pdfs, financial, sports, and location-based data. As you know, not all these sources are currently available via the xai API. To remedy this shortcoming, you will be reformulating the prompts to take full advantage of real-time results.  You should prioritize real-time information from peer-reviewed or highly credible sources."

        reformulate = f"{morph_prompt}. Return the revised prompt as plain text without pleasantries or explanations."

        morphed_results = []

        print(prompts, morph_prompt, create_link)

        for prompt in prompts:
            if prompt:

                # Prepare messages for OpenAI API
                messages = [
                    dict(role="system", content=morph_prompt),
                    dict(role="user", content=prompt),
                    dict(role="assistant", content=reformulate)
                ]

                # Call OpenAI API
                response = client.chat.completions.create(
                    model="grok-2-latest", messages=messages
                )
                #print(messages)
               # print(response)

                # Get revised prompt
                ai_response = response.choices[0].message.content
                print(ai_response)
                if ai_response:
                    if create_link:
                        encoded_prompt = urllib.parse.quote(ai_response)
                        webgrok_link = f"https://grok.com/?q={encoded_prompt}"
                        morphed_results.append(webgrok_link)
                    else:
                        morphed_results.append(ai_response)
                else:
                    morphed_results.append(None)

        # Return single result if input was a single prompt
        return morphed_results[0] if len(prompts) == 1 else morphed_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process prompts using the latest data.')

    parser.add_argument('--prompts', nargs='+', help='Prompt or list of prompts to process')
    parser.add_argument('--morph_prompt', type=str, help='Instruction to optimize the prompt(s)')
    parser.add_argument('--create_link', action='store_true',
                        help='Create a Grok website link for the morphed prompt(s)')

    args = parser.parse_args()

    prompts = args.prompts
    morph_prompt = args.morph_prompt
    create_link = args.create_link

    give_me_the_latest = GiveMeTheLatest()
    print(prompts, morph_prompt, create_link)
    links = give_me_the_latest.morph_prompts(prompts=prompts, morph_prompt=morph_prompt, create_link=create_link)
    for l in links:
        print(l)


