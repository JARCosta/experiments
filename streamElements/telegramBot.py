from telegramBot import main as telegramBot

import threading

def send_message(message):
    threading.Thread(target=telegramBot.sendMessage, args=(message,)).start()
    with open("resources/test.txt", "a") as f:
        f.write("out: " + message.replace("\n", "\n\t")[:-1])