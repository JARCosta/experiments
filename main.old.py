import os
import subprocess
import time

import requests
import credentials
import telegramBot
import buffxSteamComparison.alert
from streamElements.Agents import ChatBettor, Collector, Controller, Viewer
from wallapopNotificator import main as wallapopNotificator
import traceback
import buffxSteamComparison

import threading

from streamElements.oauth import check_oauth_token

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
    # threading.Thread(target=buffxSteamComparison.alert.alert, args=(kill_threads, 19909)).start()
    # threading.Thread(target=buffxSteamComparison.alert.alert, args=(kill_threads, 20360)).start()
    
    threads.append(threading.Thread(target=Controller.launch_controller, args=("El_Pipow", "El_Pipow", EL_PIPOW_OAUTH, counters, kill_threads)))
    
    threads.append(threading.Thread(target=Collector.launch_data_collector, args=("Runah", "JRCosta", JRCOSTA_OAUTH, counters, kill_threads)))
    threads.append(threading.Thread(target=Viewer.launch_viewer, args=("Runah", "El_Pipow", EL_PIPOW_OAUTH, counters, kill_threads)))
    threads.append(threading.Thread(target=ChatBettor.launch_bettor, args=("Runah", "JRCosta", JRCOSTA_OAUTH, counters, kill_threads)))
    
    threads.append(threading.Thread(target=Collector.launch_data_collector, args=("prcs", "JRCosta", JRCOSTA_OAUTH, counters, kill_threads)))
    threads.append(threading.Thread(target=Viewer.launch_viewer, args=("prcs", "El_Pipow", EL_PIPOW_OAUTH, counters, kill_threads)))
    threads.append(threading.Thread(target=ChatBettor.launch_bettor, args=("prcs", "JRCosta", JRCOSTA_OAUTH, counters, kill_threads)))
    
    # threads.append(threading.Thread(target=ChatBettor.launch_bettor, args=("El_Pipow", "JRCosta", JRCOSTA_OAUTH, counters, kill_threads)))
    
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
