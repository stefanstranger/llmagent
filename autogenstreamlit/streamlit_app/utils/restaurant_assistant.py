"""Module for LLM Agent restaurant assistant."""

import http.client
import requests
import urllib.parse
import autogen
import os
import json
import logging
import re
from dotenv import load_dotenv

from autogen.cache import Cache

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# variable with a list of Azure Maps Restaurant categories.
# The category ID 7315 corresponds to the "restaurant" category
# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the JSON file
json_file_name = "restaurant_categories.json"
json_file_path = os.path.join(script_dir, json_file_name)
# Open and load the JSON file
with open(json_file_path, "r") as file:
    restaurant_categories = json.load(file)


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
        raise ValueError(
            "Subscription key not found in environment variables. Please set 'AZURE_SUBSCRIPTION_KEY'."
        )

    conn = http.client.HTTPSConnection("atlas.microsoft.com")
    # Encode the query parameter to ensure it's URL-safe
    encoded_query = urllib.parse.quote(query)
    # Use the encoded query and subscription key in the URL
    conn.request(
        "GET",
        f"/search/address/json?api-version=1.0&query={encoded_query}&subscription-key={subscription_key}",
    )
    res = conn.getresponse()
    data = res.read()

    # Decode the response and load it as a JSON object
    json_data = json.loads(data.decode("utf-8"))

    # Pretty-print the JSON data
    return json.dumps(json_data, indent=4)

# Define function that retrieves restaurant information from Azure Maps REST API
# using lon and lat coordinates as parameters
# add the categorySet parameter to the URL to filter the search results by the restaurant category
def get_restaurant_info(lon: float, lat: float, category_id) -> str:
    subscription_key = os.getenv("AZURE_SUBSCRIPTION_KEY")

    if not subscription_key:
        raise ValueError(
            "Subscription key not found in environment variables. Please set 'AZURE_SUBSCRIPTION_KEY'."
        )

    conn = http.client.HTTPSConnection("atlas.microsoft.com")
    conn.request(
        "GET",
        f"/search/nearby/json?api-version=1.0&lat={lat}&lon={lon}&limit=10&radius=8046&subscription-key={subscription_key}&categorySet={category_id}",
    )
    res = conn.getresponse()
    data = res.read()

    # Decode the response and load it as a JSON object
    json_data = json.loads(data.decode("utf-8"))

    # Pretty-print the JSON data
    return json.dumps(json_data, indent=4)


# Define function to calculate distance between two geocoordinates.
def get_distance(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> str:
    subscription_key = subscription_key = os.getenv("AZURE_SUBSCRIPTION_KEY")

    if not subscription_key:
        raise ValueError(
            "Subscription key not found in environment variables. Please set 'AZURE_SUBSCRIPTION_KEY'."
        )

    headers = {"Content-Type": "application/json"}

    body = json.dumps(
        {
            "origins": {
                "type": "MultiPoint",
                "coordinates": [[origin_latitude, origin_longitude]],
            },
            "destinations": {
                "type": "MultiPoint",
                "coordinates": [[destination_latitude, destination_longitude]],
            },
        }
    )

    url = f"https://atlas.microsoft.com/route/matrix/json?api-version=1.0&routeType=shortest&subscription-key={subscription_key}"

    print(f"Calling Azure Maps API with URL: {url}")
    print(f"Request Body: {body}")

    response = requests.post(url, headers=headers, data=body)

    if response.status_code != 202:
        raise Exception(
            f"Failed to get response from Azure Maps API: {response.status_code} - {response.text}"
        )

    location_header = response.headers.get("Location")
    print(f"Location Header: {location_header}")

    if not location_header:
        raise Exception("Location header not found in the response.")

    result_response = requests.get(location_header)

    if result_response.status_code != 200:
        raise Exception(
            f"Failed to get result from Location URL: {result_response.status_code} - {result_response.text}"
        )

    return json.dumps(result_response.json(), indent=4)
