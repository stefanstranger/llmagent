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

# Show title and description
st.title("🍽️ Restaurant assistant")
st.write(
    "This is a restaurant assistant that uses Azure OpenAI and Azure Maps and AutoGen to provide restaurant recommendations. "
    "You can ask for restaurant recommendations by providing your location and the type of restaurant you are looking for."
)

# Initialize session state for messages if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []


class TrackableAssistantAgent(AssistantAgent):
    def _process_received_message(self, message, sender, silent):
        # Get message content regardless of type
        if isinstance(message, str):
            message_content = message
        elif isinstance(message, dict):
            message_content = message.get("content", "")
        else:
            message_content = str(message) if message is not None else ""

        # Only process non-empty messages
        if message_content:
            # Display in Streamlit
            with st.chat_message(self.name):
                st.markdown(message_content)

            # Print to console
            print(f"\n{self.name} (to {sender.name}):")
            print(message_content)
            print(
                "--------------------------------------------------------------------------------"
            )

            # Store in session state
            st.session_state.messages.append(
                {"role": self.name, "content": message_content}
            )

        return super()._process_received_message(message, sender, silent)


class TrackableUserProxyAgent(UserProxyAgent):
    def _process_received_message(self, message, sender, silent):
        # Get message content regardless of type
        if isinstance(message, str):
            message_content = message
        elif isinstance(message, dict):
            message_content = message.get("content", "")
        else:
            message_content = str(message) if message is not None else ""

        # Only process non-empty messages
        if message_content:
            # Display in Streamlit
            with st.chat_message(sender.name):
                st.markdown(message_content)

            # Print to console
            print(f"\n{sender.name} (to {self.name}):")
            print(message_content)
            print(
                "--------------------------------------------------------------------------------"
            )

            # Store in session state
            st.session_state.messages.append(
                {"role": sender.name, "content": message_content}
            )

        return super()._process_received_message(message, sender, silent)


def is_termination_msg(x):
    """Helper function to check for termination message in a safe way"""
    if x is None:
        return False
    if isinstance(x, str):
        return x.rstrip().endswith("TERMINATE")
    if isinstance(x, dict):
        content = x.get("content", "")
        return content.rstrip().endswith("TERMINATE") if content else False
    return False


# Display chat history from session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

with st.container():
    user_input = st.chat_input("Type something...")
    if user_input:
        # Load environment configuration
        load_dotenv()
        config_list = autogen.config_list_from_json(env_or_file="OAI_CONFIG_LIST")

        llm_config = {
            "config_list": config_list,
            "timeout": 120,
        }

        # Create trackable agents
        chatbot = TrackableAssistantAgent(
            name="chatbot",
            system_message="For geo location tasks, only use the functions you have been provided with. Reply TERMINATE when the task is done.",
            llm_config=llm_config,
        )

        user_proxy = TrackableUserProxyAgent(
            name="user_proxy",
            is_termination_msg=is_termination_msg,  # Use the safer termination checker
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2,
            code_execution_config={"work_dir": "coding", "use_docker": False},
        )

        # Register the functions
        @user_proxy.register_for_execution()
        @chatbot.register_for_llm(description="Geolocation assistant.")
        def geolocation_demo(query: str) -> str:
            result = get_address(query)
            # Display function result in both console and Streamlit
            print(f"\nFunction geolocation_demo result:")
            print(result)
            print(
                "--------------------------------------------------------------------------------"
            )
            with st.chat_message("Function"):
                st.markdown(f"**Geolocation Result:**\n{result}")
            return result

        @user_proxy.register_for_execution()
        @chatbot.register_for_llm(description="Restaurant assistant.")
        def restaurant_demo(lon: float, lat: float, category_id: str) -> str:
            result = get_restaurant_info(lon, lat, category_id)
            # Display function result in both console and Streamlit
            print(f"\nFunction restaurant_demo result:")
            print(result)
            print(
                "--------------------------------------------------------------------------------"
            )
            with st.chat_message("Function"):
                st.markdown(f"**Restaurant Result:**\n{result}")
            return result

        @user_proxy.register_for_execution()
        @chatbot.register_for_llm(description="Restaurant Category Assistant.")
        def restaurant_category_demo(category: str) -> str:
            result = get_category_name(category)
            # Display function result in both console and Streamlit
            print(f"\nFunction restaurant_category_demo result:")
            print(result)
            print(
                "--------------------------------------------------------------------------------"
            )
            with st.chat_message("Function"):
                st.markdown(f"**Category Result:**\n{result}")
            return result

        @user_proxy.register_for_execution()
        @chatbot.register_for_llm(description="Distance Assistant")
        def restaurant_distance_demo(
            origin_longitude: float,
            origin_latitude: float,
            destination_longitude: float,
            destination_latitude: float,
        ) -> str:
            result = get_distance(
                origin_longitude,
                origin_latitude,
                destination_longitude,
                destination_latitude,
            )
            # Display function result in both console and Streamlit
            print(f"\nFunction restaurant_distance_demo result:")
            print(result)
            print(
                "--------------------------------------------------------------------------------"
            )
            with st.chat_message("Function"):
                st.markdown(f"**Distance Result:**\n{result}")
            return result

        # Display user input immediately
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Print user input to console
        print("\nuser: ")
        print(user_input)
        print(
            "--------------------------------------------------------------------------------"
        )

        # Define async chat function
        async def initiate_chat():
            chat_messages = user_proxy.a_initiate_chat(
                chatbot, message=user_input, max_turns=10
            )
            await chat_messages

        # Run the chat
        asyncio.run(initiate_chat())
