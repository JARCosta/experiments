from telegramBot import main as telegramBot

import threading

def sendMessage(message):
    threading.Thread(target=telegramBot.sendMessage, args=(message,)).start()
    with open("streamElements/resources/test.txt", "a") as f:
        f.write("out: " + message.replace("\n", "\n\t")[:-1])