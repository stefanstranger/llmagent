# Frontend for the restaurant recommandation autogen LLM Agent code using Streamlit

import streamlit as st
import autogen
from autogen import AssistantAgent, UserProxyAgent
from utils.restaurant_assistant import (
    get_category_name,
    get_address,
    get_restaurant_info,
    get_distance,
)
from dotenv import load_dotenv
import asyncio

# Show title and description.
st.title("🍽️ Restaurant assistant")
st.write(
    "This is a restaurant assistant that uses Azure OpenAI and Azure Maps and AutoGen to provide restaurant recommendations. "
    "You can ask for restaurant recommendations by providing your location and the type of restaurant you are looking for."
)


# The TrackableAssistantAgent and TrackableUserProxyAgent classes override the _process_received_message method to display chat messages in a Streamlit app with the sender's name and message content in the order received.
class TrackableAssistantAgent(AssistantAgent):
    def _process_received_message(self, message, sender, silent):
        with st.chat_message(sender.name):
            st.markdown(message)
        return super()._process_received_message(message, sender, silent)


class TrackableUserProxyAgent(UserProxyAgent):
    def _process_received_message(self, message, sender, silent):
        with st.chat_message(sender.name):
            st.markdown(message)
        return super()._process_received_message(message, sender, silent)


with st.container():
    user_input = st.chat_input("Type something...")
    if user_input:
        # Load LLM inference endpoints from an env variable or a file
        # Load the .env file
        load_dotenv()
        config_list = autogen.config_list_from_json(env_or_file="OAI_CONFIG_LIST")

        llm_config = {
            "config_list": config_list,
            "timeout": 120,
        }

        # Define the AssistantAgent instance named "chatbot"
        chatbot = autogen.AssistantAgent(
            name="chatbot",
            system_message="For geo location tasks, only use the functions you have been provided with. Reply TERMINATE when the task is done.",
            llm_config=llm_config,
        )

        # create a UserProxyAgent instance named "user_proxy"
        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            is_termination_msg=lambda x: x.get("content", "")
            and x.get("content", "").rstrip().endswith("TERMINATE"),
            human_input_mode="ALWAYS",
            max_consecutive_auto_reply=2,
            code_execution_config={"work_dir": "coding", "use_docker": False},
        )

        # Register the function Geolocation for execution
        @user_proxy.register_for_execution()
        @chatbot.register_for_llm(description="Geolocation assistant.")
        def geolocation_demo(
            query: str,
        ) -> str:
            return get_address(query)  # convert the result to a string and return it

        # Register the function Restaurant for execution
        @user_proxy.register_for_execution()
        @chatbot.register_for_llm(description="Restaurant assistant.")
        def restaurant_demo(lon: float, lat: float, category_id: str) -> str:
            return get_restaurant_info(lon, lat, category_id)

        # Register the function Restaurant for execution
        @user_proxy.register_for_execution()
        @chatbot.register_for_llm(description="Restaurant Category Assistant.")
        def restaurant_category_demo(category: str) -> str:
            return get_category_name(category)

        # Register the function for the distance execution
        @user_proxy.register_for_execution()
        @chatbot.register_for_llm(description="Distance Assistant")
        def restaurant_distance_demo(
            origin_longitude: float,
            origin_latitude: float,
            destination_longitude: float,
            destination_latitude: float,
        ) -> str:
            return get_distance(
                origin_longitude,
                origin_latitude,
                destination_longitude,
                destination_latitude,
            )

        assert user_proxy.function_map["geolocation_demo"]._origin == geolocation_demo

        if user_input:
            # Define aynchronous function
            async def initiate_chat():
                chat_messages = user_proxy.a_initiate_chat(
                    chatbot, message=user_input, max_turns=10
                )
                await chat_messages
                print("Console Log" + chat_messages)
                messages = []
                for message in chat_messages.messages:
                    if message not in messages:
                        messages.append(message["name"] + ": " + message["content"])
                        st.session_state.messages = messages
                        st.write(message["name"] + ": " + message["content"])
                    # return chat_messages

            # Run the asynchronous function
            asyncio.run(initiate_chat())
