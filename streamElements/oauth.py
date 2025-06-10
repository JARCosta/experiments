



import json
import time
import requests


def set_oauth_token(oauth:dict, username:str):
    url = "https://id.twitch.tv/oauth2/device?client_id=kimne78kx3ncx6brgo4mv6wki5h1ko&scope=channel%3Amanage%3Apolls+channel%3Aread%3Apolls"
    response = requests.post(url)
    print(f"{username}'s Oauth_key:", response.json()['verification_uri'])

    while True:
        url = f"https://id.twitch.tv/oauth2/token?client_id=kimne78kx3ncx6brgo4mv6wki5h1ko&scope=channel%3Amanage%3Apolls+channel%3Aread%3Apolls&device_code={response.json()['device_code']}&grant_type=urn:ietf:params:oauth:grant-type:device_code"
        new_response = requests.post(url)
        print(new_response.status_code, new_response.json())
        if new_response.status_code == 200:
            oauth[username] = new_response.json()["access_token"]
            with open("OAUTH.json", "w") as f:
                json.dump(oauth, f)
            return new_response.json()["access_token"]
        time.sleep(5)


def check_oauth_token(username):
    try:
        with open(f"OAUTH.json", "r") as f:
            oauth = json.load(f)
            if username not in oauth:
                return set_oauth_token(oauth, username)
            else:
                return oauth[username]
    except (FileNotFoundError, json.JSONDecodeError):
        oauth = {}
        print(f"Set {username.upper()}'s oauth token:")
        return set_oauth_token(oauth, username)
