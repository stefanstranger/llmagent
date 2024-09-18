import http.client
import requests
import urllib.parse
import autogen
import os
import json
import logging
import re

from autogen.cache import Cache

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Load LLM inference endpoints from an env variable or a file  
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
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    #human_input_mode="NEVER",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=2,
    #code_execution_config={"work_dir": "coding", "use_docker": True}
)

# variable with a list of Azure Maps Restaurant categories.
# The category ID 7315 corresponds to the "restaurant" category
# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the JSON file
json_file_name = "restaurant_categories.json"
json_file_path = os.path.join(script_dir, json_file_name)
# Open and load the JSON file
with open(json_file_path, 'r') as file:
    restaurant_categories  = json.load(file)
    
# define a function that retrieves the category name from the json file using the type of restaurant as a parameter
# The parameter category string is used to search in the "Category Name" property of the json using a regular expression to find the category name
def get_category_name(category: str) -> str:
    # Search for the category name in the JSON file
    for item in restaurant_categories:
        if re.search(category, item["category_name"], re.IGNORECASE):
            return item
    # If the category is not found, return an error message
    return "Category not found"

# define geolocation_demo function
def get_address(query: str) -> str:
    # Retrieve the subscription key from environment variables
    subscription_key = os.getenv("AZURE_SUBSCRIPTION_KEY")
    
    if not subscription_key:
        raise ValueError("Subscription key not found in environment variables. Please set 'AZURE_SUBSCRIPTION_KEY'.")

    conn = http.client.HTTPSConnection("atlas.microsoft.com")
    # Encode the query parameter to ensure it's URL-safe
    encoded_query = urllib.parse.quote(query)
    # Use the encoded query and subscription key in the URL
    conn.request("GET", f"/search/address/json?api-version=1.0&query={encoded_query}&subscription-key={subscription_key}")
    res = conn.getresponse()
    data = res.read()
    
    # Decode the response and load it as a JSON object
    json_data = json.loads(data.decode("utf-8"))

    # Pretty-print the JSON data
    return (json.dumps(json_data, indent=4))

# Define function that retrieves restaurant information from Azure Maps REST API
# using lon and lat coordinates as parameters
# add the categorySet parameter to the URL to filter the search results by the restaurant category
def get_restaurant_info(lon: float, lat: float, category_id) -> str:
    subscription_key = os.getenv("AZURE_SUBSCRIPTION_KEY")
    
    if not subscription_key:
        raise ValueError("Subscription key not found in environment variables. Please set 'AZURE_SUBSCRIPTION_KEY'.")

    conn = http.client.HTTPSConnection("atlas.microsoft.com")
    conn.request("GET", f"/search/nearby/json?api-version=1.0&lat={lat}&lon={lon}&limit=10&radius=8046&subscription-key={subscription_key}&categorySet={category_id}")
    res = conn.getresponse()
    data = res.read()
    
    # Decode the response and load it as a JSON object
    json_data = json.loads(data.decode("utf-8"))

    # Pretty-print the JSON data
    return (json.dumps(json_data, indent=4))

# Define function to calculate distance between two geocoordinates.
def get_distance(origin_latitude: float, origin_longitude: float, destination_latitude: float, destination_longitude: float) -> str:
    subscription_key = subscription_key = os.getenv("AZURE_SUBSCRIPTION_KEY")
    
    if not subscription_key:
        raise ValueError("Subscription key not found in environment variables. Please set 'AZURE_SUBSCRIPTION_KEY'.")

    headers = {
        "Content-Type": "application/json"
    }

    body = json.dumps({
        "origins": {
            "type": "MultiPoint",
            "coordinates": [
                [origin_latitude, origin_longitude]
            ]
        },
        "destinations": {
            "type": "MultiPoint",
            "coordinates": [
                [destination_latitude, destination_longitude]
            ]
        }
    })

    url = f"https://atlas.microsoft.com/route/matrix/json?api-version=1.0&routeType=shortest&subscription-key={subscription_key}"
    
    print(f"Calling Azure Maps API with URL: {url}")
    print(f"Request Body: {body}")

    response = requests.post(url, headers=headers, data=body)
    
    if response.status_code != 202:
        raise Exception(f"Failed to get response from Azure Maps API: {response.status_code} - {response.text}")

    location_header = response.headers.get('Location')
    print(f"Location Header: {location_header}")

    if not location_header:
        raise Exception("Location header not found in the response.")

    result_response = requests.get(location_header)
    
    if result_response.status_code != 200:
        raise Exception(f"Failed to get result from Location URL: {result_response.status_code} - {result_response.text}")

    return json.dumps(result_response.json(), indent=4)

# Register the function Geolocation for execution
@user_proxy.register_for_execution()
@chatbot.register_for_llm(description="Geolocation assistant.")
def geolocation_demo(
    query: str,
) -> str:
    return get_address(query) # convert the result to a string and return it

# Register the function Restaurant for execution
@user_proxy.register_for_execution()
@chatbot.register_for_llm(description="Restaurant assistant.")
def restaurant_demo(
    lon: float, lat: float, category_id: str
) -> str:
    return get_restaurant_info(lon, lat, category_id)

# Register the function Restaurant for execution
@user_proxy.register_for_execution()
@chatbot.register_for_llm(description="Restaurant Category Assistant.")
def restaurant_category_demo(
    category: str
) -> str:
    return get_category_name(category)

# Register the function for the distance execution
@user_proxy.register_for_execution()
@chatbot.register_for_llm(description="Distance Assistant")
def restaurant_distance_demo(
    origin_longitude: float, origin_latitude: float, destination_longitude: float, destination_latitude: float 
) -> str:
    return get_distance(origin_longitude, origin_latitude, destination_longitude, destination_latitude)

# What does below code does?
assert user_proxy.function_map["geolocation_demo"]._origin == geolocation_demo

# Start the conversation
with Cache.disk() as cache:
    # start the conversation
    res = user_proxy.initiate_chat(
        chatbot, message="Where is Haarlem in the Netherlands located?", summary_method="reflection_with_llm", cache=cache
    )