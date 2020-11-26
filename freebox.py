# 30/04/2016
# Mikail BASER

import requests
import json
import os
import hmac
from hashlib import sha1

version = "0.0.1"

if not os.path.isfile("data"):
    print("Data file doesn't exist, creating...")
    data_file = open("data", "w")
    data_file.close()

if os.stat("data").st_size == 0:  # If data file is empty
    print("App_token not found.\nGetting app_token...")

    data_file = open("data", "w")

    payload_list = {
        "app_id": "fr.freebox.test_app",
        "app_name": "Test",
        "app_version": version,
        "device_name": "PC"
    }

    payload = json.dumps(payload_list, ensure_ascii=False)  # Convert list to json to send it

    r = requests.post("http://mafreebox.freebox.fr/api/v3/login/authorize/", data=payload)  # Request for app_token and track_id

    app_token = r.json()["result"]["app_token"]  # Extracting data
    track_id = r.json()["result"]["track_id"]

    data_file.write(str(app_token) + "\n" + str(track_id))  # Storing data
    data_file.close()

else:
    print("Already got an app_token.")

data_file = open("data", "r")
data_file_content = data_file.read().splitlines()
data_file.close()

app_token = data_file_content[0]  # Extracting data
track_id = data_file_content[1]

print("App_token =", app_token)
print("Track_id =", track_id)


print("Checking app_token validity...")
r = requests.get("http://mafreebox.freebox.fr/api/v3/login/authorize/" + str(track_id))
status = r.json()["result"]["status"]
challenge = r.json()["result"]["challenge"]
print("Status :", status)
if status == "granted":
    print("The app_token is valid.")
else:
    pass

h = hmac.new(app_token.encode("utf-8"), challenge.encode("utf-8"), sha1)
password = h.hexdigest()
print("Password = ", password)
print("Requesting session_token...")
payload_list = {
    "app_name": "Test Mikail",
    "password": password
}
payload = json.dumps(payload_list, ensure_ascii=False)
r = requests.post("http://mafreebox.freebox.fr/api/v3/login/session/", data=payload)
print(r.json())

os.system("pause")
