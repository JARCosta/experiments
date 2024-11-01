import datetime
from functools import partial
import multiprocessing
import os
import time
import websocket
import threading
from telegramBot import main as telegramBot
from streamElements import main
import traceback

# Event to signal that the connection is open
connection_open_event = threading.Event()

class WebSocket:

    def connect(ws:websocket.WebSocketApp, message:str, username:str, channel:str, connection_open_event:threading.Event):
        if f":Welcome, GLHF!" in message:
            ws.send(f"JOIN #{channel}")
        
        elif f"ROOMSTATE #{channel.lower()}" in message:
            print(f"{username} connected to {channel}")
            connection_open_event.set()
        
        elif ":tmi.twitch.tv RECONNECT" in message:
            telegram_message = f"Received RECONNECT message for client {username} at {channel}\n"
            telegram_message += "TODO: Reconnect\n"
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)
        
        elif "PING :tmi.twitch.tv" in message:
            ws.send("PONG")
            ws.send("PING")

    def on_error(ws:websocket.WebSocketApp, error:Exception):
        telegram_message = "Error:\n"
        telegram_message += datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
        telegram_message += str(error) + "\n"
        telegram_message += traceback.format_exc() + "\n"
        print(telegram_message)

    def on_close(ws:websocket.WebSocketApp, close_status_code:int, close_msg:str):
        print(f"WebSocket connection closed with status: {close_status_code}, message: {close_msg}")

    def on_open(ws:websocket.WebSocketApp, oauth_key:str, username:str):
        ws.send("CAP REQ :twitch.tv/tags twitch.tv/commands")
        ws.send(f"PASS oauth:{oauth_key}")
        ws.send(f"NICK {username}")
        ws.send(f"USER {username} 8 * :{username}")

        print(f"Logging {username} {oauth_key}")

class Bettor:

    def on_message(ws:websocket.WebSocketApp, message:str, username:str, channel:str, connection_open_event:threading.Event):
        
        if ":tmi.twitch.tv RECONNECT" in message:
            main.reconnect()

            telegram_message = "Received RECONNECT message from Twitch"
            telegram_message += "Reconnecting..."
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)

        WebSocket.connect(ws, message, username, channel, connection_open_event)

        if f"@{username}, there is no contest currently running." in message: # Bet placed too late
            print(message)
        
        elif "no longer accepting bets for" in message: # Bet's closed
            print(message)
        
        elif "won the contest" in message: # Result of the bet
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split(f"PRIVMSG #{channel.lower()} :")[1].split('ACTION ')[1].split("!")[0] + "!\n"
            telegram_message = user + ": " + msg + "\n"
            telegram_message += "You have {} points\n".format(main.get_balance())
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)

            bet_winner = message.split(f"PRIVMSG #{channel.lower()} :")[1].split('"')[1]
            with open("streamElements/resources/pots.txt", "a") as f:
                f.write(bet_winner + "\n")

        elif f"@{username.lower()}" in message.lower() and not f":{username.lower()}" in message: # I was mentioned
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split(f"PRIVMSG #{channel.lower()} :")[1]
            telegram_message = user + ": " + msg
            if "you have bet" in message: # Bet placed confirmation
                telegram_message += "You have {} points\n".format(main.get_balance())
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)

class Controller:

    def on_message(ws:websocket.WebSocketApp, message:str, username:str, channel:str, connection_open_event:threading.Event):
        WebSocket.connect(ws, message, username, channel, connection_open_event)

        allowed_users = ["el_pipow", "jrcosta"]

        for user in allowed_users:
            if f"@{username.lower()} " in message.lower() and not f":{user.lower()}" in message: # I was mentioned
                user = message.split("display-name=")[1].split(";")[0]
                msg = message.split(f"PRIVMSG #{channel.lower()} :")[1]

                telegram_message = user + ": " + msg
                telegramBot.sendMessage(telegram_message)
                print(telegram_message)

                if msg == "reboot":
                    os.system('systemctl reboot -i')


def launch_viewer(channel:str, username:str, oauth_key:str) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    ws = websocket.WebSocketApp(
        websocket_url,
        # on_message=partial(Viewer.on_message, username=username, channel=channel),
        on_message=partial(WebSocket.connect, username=username, channel=channel, connection_open_event=connection_open_event),
        on_error=WebSocket.on_error,
        on_open=partial(WebSocket.on_open, oauth_key=oauth_key, username=username)
        )
    
    # Run the WebSocket connection in a separate thread to avoid blocking
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for the connection to be open before sending the message
    connection_open_event.wait()

    return wst, ws

def launch_controller(channel:str, username:str, oauth_key:str) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=partial(Controller.on_message, username=username, channel=channel, connection_open_event=connection_open_event),
        on_error=WebSocket.on_error,
        on_open=partial(WebSocket.on_open, oauth_key=oauth_key, username=username)
        )
    
    # Run the WebSocket connection in a separate thread to avoid blocking
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for the connection to be open before sending the message
    connection_open_event.wait()

    return wst, ws

def launch_bettor(channel:str, username:str, oauth_key:str) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=partial(Bettor.on_message, username=username, channel=channel, connection_open_event=connection_open_event),
        on_error=WebSocket.on_error,
        on_open=partial(WebSocket.on_open, oauth_key=oauth_key, username=username)
        )
    
    # Run the WebSocket connection in a separate thread to avoid blocking
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for the connection to be open before sending the message
    connection_open_event.wait()

    return wst, ws

def send(ws:websocket.WebSocketApp, channel:str, message:str):
        print(f"PRIVMSG #{channel} :{message}")
        ws.send(f"PRIVMSG #{channel} :{message}")

def ping(ws:websocket.WebSocketApp):
    ws.send("PING")

def close(wst:threading.Thread, ws:websocket.WebSocketApp):
    if ws != None:
        ws.close()
    else:
        print("Couldn't close websocket")
    if wst != None:
        print("Closing websocket thread")
        wst.join()
        print("Websocket thread closed")
    else:
        print("Couldn't kill websocket thread")
    
    








