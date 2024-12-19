import requests
from telegramBot import main as telegramBot

import threading

def sendMessage(message):
    try:
        threading.Thread(target=telegramBot.sendMessage, args=(message,)).start()
    except requests.exceptions.ConnectionError:
        print("No Internet")