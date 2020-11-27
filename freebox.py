# 30/04/2016
# Mikail BASER

import requests
import json
import os
import time
from zeroconf import ServiceBrowser, Zeroconf

app_id = "fr.freebox.test_app"
app_version = "0.0.2"
app_name= "Test"
device_name = "PC"

# Listener class for zeroconf
class MyListener:
    def __init__(self):
        self.api_info = None

    def remove_service(self, zeroconf, type, name):
        print(f"Service removed : {name}")

    def add_service(self, zeroconf, type, name):
        # Get service info
        service_info = zeroconf.get_service_info(type, name)

        # Extract API information from mDNS query (decode bytes to utf-8)
        self.api_info = {k.decode(): v.decode() for k,v in service_info.properties.items()}

        # Close listener, as we don't need it anymore
        zeroconf.close()

# Function that parses response errors and returns the response JSON if the request was successful
def parse_errors(response):
    try:
        # Parse response
        response_dict = response.json()

        # If the request failed, determine and print error
        if not response_dict["success"]:
            print("Error : Request has failed !")
            print(response_dict["msg"])
            print(f"Error code : {response_dict['error_code']}")

        # No errors, return response JSON as a dict
        return response_dict
    except ValueError:
        print(f"Error : Response string is not json-encoded : {response.text}")
        exit()
    except KeyError:
        print(f"Error : Response doesn't have all required fields : {response.text}")
        exit()

# Get API info with mDNS
zeroconf = Zeroconf()
listener = MyListener()
browser = ServiceBrowser(zeroconf, "_fbx-api._tcp.local.", listener)

# Wait for API information, with a timeout of ~5 seconds
timeout_counter = 50
while listener.api_info is None and timeout_counter > 0:
    time.sleep(0.1)
    timeout_counter -= 1
if timeout_counter <= 0:
    print("Error : mDNS query timed out.")
    print("Please verify that a Freebox is connected to your network.")

print("Obtained API info.")

# Building API URL
api_domain = listener.api_info["api_domain"]
freebox_port = listener.api_info["https_port"]
api_base_url = listener.api_info["api_base_url"]
major_api_version = listener.api_info["api_version"].split(".")[0] # Get major version only

api_url = f"https://{api_domain}:{freebox_port}{api_base_url}v{major_api_version}"

# Create data.json file if it doesn't exist
if not os.path.isfile("data.json"):
    print("Data file doesn't exist, creating...")
    with open("data.json", "w"):
        pass

# If the data.json file is empty, fill it with app_token and track_id from the Freebox
if os.stat("data.json").st_size == 0:
    print("Getting app_token...")

    with open("data.json", "w") as data_file:
        payload = {
            "app_id": app_id,
            "app_name": app_name,
            "app_version": app_version,
            "device_name": device_name
        }

        # Request app_token and track_id from the Freebox
        response_dict = parse_errors(requests.post(f"{api_url}/login/authorize/", json=payload, verify="freebox_ecc_root_ca.pem"))

        data = {
            "app_token": response_dict["result"]["app_token"],
            "track_id": response_dict["result"]["track_id"]
        }

        # Store data to config file
        data_file.write(json.dumps(data, indent=4))
else:
    print("Found an existing app_token and track_id in 'data.json'.")

# Load existing data from data.json file
with open("data.json", "r") as f:
    data_dict = json.loads(f.read())

    try:
        app_token = data_dict["app_token"]
        track_id = data_dict["track_id"]
    except KeyError:
        print("Error : 'data.json' doesn't have app_token or track_id !")
        print("Please remove 'data.json' to request other tokens.")
        exit()

print(f"app_token = {app_token}")
print(f"track_id = {track_id}")

print("\nChecking app_token validity...")
response_dict = parse_errors(requests.get(f"{api_url}/login/authorize/{track_id}", verify="freebox_ecc_root_ca.pem"))

if response_dict["result"]["status"] == "pending":
    print("\nPlease authorize the app on the LCD screen of your Freebox.")
    print("Veuillez autoriser l'application sur l'interface LCD de votre Freebox.")

    # Continue polling the Freebox about the auth status
    while response_dict["result"]["status"] == "pending":
        response_dict = parse_errors(requests.get(f"{api_url}/login/authorize/{track_id}", verify="freebox_ecc_root_ca.pem"))
        time.sleep(0.5)

if response_dict["result"]["status"] == "granted":
    print("Authorization acquired.")
else:
    print("Error : Could not get authorization.")
    print(f"Status : {response_dict['result']['status']}")
    exit()
