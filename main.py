import os
import subprocess
import time

import requests
from streamElements import main as streamElements, twitch_message_sender
from wallapopNotificator import main as wallapopNotificator
import traceback

import threading

def set_oauth_token(username):
    url = "https://id.twitch.tv/oauth2/device?client_id=kimne78kx3ncx6brgo4mv6wki5h1ko&scope=channel%3Amanage%3Apolls+channel%3Aread%3Apolls"
    response = requests.post(url)
    print(response.json()['verification_uri'])

    while True:
        url = f"https://id.twitch.tv/oauth2/token?client_id=kimne78kx3ncx6brgo4mv6wki5h1ko&scope=channel%3Amanage%3Apolls+channel%3Aread%3Apolls&device_code={response.json()['device_code']}&grant_type=urn:ietf:params:oauth:grant-type:device_code"
        new_response = requests.post(url)
        print(new_response.json())
        print(new_response.status_code)
        if new_response.status_code == 200:
            with open(username.upper() + '_OAUTH', "w") as f:
                f.write(new_response.json()["access_token"])
            return new_response.json()["access_token"]
        time.sleep(5)

def check_oauth_token(username):
    if not os.getenv(username.upper() + "_OAUTH"):

        try:
            with open(f"{username.upper() + '_OAUTH'}", "r") as f:
                oauth = f.read()
                if not oauth:
                    return set_oauth_token(username)
                else:
                    return oauth
        except FileNotFoundError:
            print(f"Set {username.upper()+'_OAUTH'}:")
            set_oauth_token(username)

if __name__ == "__main__":

    EL_PIPOW_OAUTH = check_oauth_token("El_Pipow")
    JRCOSTA_OAUTH = check_oauth_token("JRCosta")

    threading.Thread(target=twitch_message_sender.launch_viewer, args=("Runah", "JRCosta", JRCOSTA_OAUTH)).start()
    threading.Thread(target=twitch_message_sender.launch_controller, args=("El_Pipow", "JRCosta", JRCOSTA_OAUTH)).start()
    threading.Thread(target=streamElements.bettor_agent, args=("El_pipow", EL_PIPOW_OAUTH)).start()