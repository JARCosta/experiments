import os
import subprocess
import time

import requests
import credentials
import telegramBot
import buffxSteamComparison.alert
from streamElements.Agents import Collector, Controller, Viewer, Bettor
from wallapopNotificator import main as wallapopNotificator
import traceback
import buffxSteamComparison

import threading

def set_oauth_token(username):
    url = "https://id.twitch.tv/oauth2/device?client_id=kimne78kx3ncx6brgo4mv6wki5h1ko&scope=channel%3Amanage%3Apolls+channel%3Aread%3Apolls"
    response = requests.post(url)
    print(f"{username}'s Oauth_key:", response.json()['verification_uri'])

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
    try:
        with open(f"{username.upper() + '_OAUTH'}", "r") as f:
            oauth = f.read()
            if not oauth:
                return set_oauth_token(username)
            else:
                return oauth
    except FileNotFoundError:
        print(f"Set {username.upper()+'_OAUTH'}:")
        return set_oauth_token(username)

if __name__ == "__main__":
    print("testing connection")
    try:
        requests.get("http://google.com")
    except requests.exceptions.ConnectionError:
        input("No wi-fi connection, continue?")
    print("connection stablished")

    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    
    telegramBot.sendMessage("Twitch bettor launched")

    EL_PIPOW_OAUTH = check_oauth_token("El_Pipow")
    JRCOSTA_OAUTH = check_oauth_token("JRCosta")
    counters = [0, 0]
    threads = []

    kill_threads = threading.Event()
    threading.Thread(target=buffxSteamComparison.alert.alert, args=(kill_threads, )).start()
    threads.append(threading.Thread(target=Collector.launch_data_collector, args=("Runah", "JRCosta", JRCOSTA_OAUTH, counters, kill_threads)))
    threads.append(threading.Thread(target=Viewer.launch_viewer, args=("Runah", "El_Pipow", EL_PIPOW_OAUTH, counters, kill_threads)))
    threads.append(threading.Thread(target=Controller.launch_controller, args=("El_Pipow", "El_Pipow", EL_PIPOW_OAUTH, counters, kill_threads)))
    threads.append(threading.Thread(target=Bettor.launch_bettor, args=("Runah", "JRCosta", JRCOSTA_OAUTH, counters, kill_threads)))
    # threads.append(threading.Thread(target=Bettor.launch_bettor, args=("El_pipow", "JRCosta", JRCOSTA_OAUTH, counters, kill_threads)))

    [i.start() for i in threads]

    while not counters[0] == len(threads) and counters[1] == 0:
        pass
    print()
    while not counters[1] == len(threads):
        pass
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("quitting")
        kill_threads.set()
