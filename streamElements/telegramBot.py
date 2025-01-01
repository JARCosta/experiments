import requests
import telegramBot
import credentials
import threading

def sendMessage(message, notification=True):
    try:
        threading.Thread(target=telegramBot.sendMessage, args=(credentials.telegramBot_Logs_token, message, credentials.telegramBot_User_id)).start()
        if notification:
            threading.Thread(target=telegramBot.sendMessage, args=(credentials.telegramBot_Notifications_token, message, credentials.telegramBot_User_id)).start()
    except requests.exceptions.ConnectionError:
        print("No Internet")