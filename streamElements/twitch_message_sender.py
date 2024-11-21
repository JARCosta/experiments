import datetime
from functools import partial
import multiprocessing
import os
import re
import time
import websocket
import threading
from telegramBot import main as telegramBot
from streamElements import main
import traceback

# Event to signal that the connection is open
connection_open_event = threading.Event()

def store_log(func:callable):
    print("Storing log")
    def inner_function():
        with open("streamElements/resources/logs.txt", "a") as f:
            f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {func.__name__}() started ")
            print("Before calling func")
            func()
            f.write("and ended\n")
    return inner_function

class WebSocket:

    def connect(ws:websocket.WebSocketApp, message:str, username:str, channel:str, connection_open_event:threading.Event, creator_function:callable):
        if f":Welcome, GLHF!" in message:
            ws.send(f"JOIN #{channel}")
        
        elif f"ROOMSTATE #{channel.lower()}" in message:
            print(f"{username} connected to {channel}")
            connection_open_event.set()
        
        elif ":tmi.twitch.tv RECONNECT" in message:
            telegram_message = f"Received RECONNECT message from Twitch on a {creator_function.__name__} WebSocket\n"
            telegram_message += f"Reconnecting viewer {username} to {channel}\n"
            threading.Thread(target=creator_function, args=(channel, username, os.getenv(username.upper() + "_OAUTH"))).start()
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
        
        WebSocket.connect(ws, message, username, channel, connection_open_event, launch_bettor)

        if f"@{username}, there is no contest currently running." in message: # Bet placed too late
            print(message)
            main.increase_variable_delay()
            main.send_message()
        
        elif "a new contest has started" in message: # New bet
            timestamp = datetime.datetime.now()
            with open("streamElements/resources/player_bet.csv", "a") as f:
                f.write(f"{timestamp},New bet\n")
        
        elif "no longer accepting bets for" in message: # Bet's closed
            timestamp = datetime.datetime.now()
            with open("streamElements/resources/player_bet.csv", "a") as f:
                f.write(f"{timestamp},Bets closed\n")
        
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
            print("Bet winner: " + bet_winner)
            print("aaaaaa")
            print()
            
            timestamp = datetime.datetime.now()
            with open("streamElements/resources/player_bet.csv", "a") as f:
                # print(msg)
                # f.write(f"{timestamp},{msg}\n")
                result = re.search('"(.*)" won the contest "Aposta no resultado do próximo jogo do Runah" with (.*)% of all bets and (.*)% of the total pot!', msg)
                print(repr(result.group(1)), repr(result.group(2)), repr(result.group(3)))
                f.write(f"{timestamp},{result.group(1)},{result.group(2)},{result.group(3)}\n")


        elif ", you have bet" in message:
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split(f"PRIVMSG #{channel.lower()} :")[1]
            result = re.search('@(.*), you have bet (.*) points on (.*).\r\n', msg)
            timestamp = datetime.datetime.now()
            mentioned_user = result.group(1)
            amount_bet = result.group(2)
            option_bet = result.group(3).split(".")[0]
            with open("streamElements/resources/player_bet.csv", "a") as f:
                f.write(f"{timestamp},{mentioned_user},{amount_bet},{option_bet}\n")
            if mentioned_user.lower() == username.lower():
                telegram_message = user + ": " + msg
                telegram_message += "You have {} points\n".format(main.get_balance())
                telegramBot.sendMessage(telegram_message)
                print(telegram_message)

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
        WebSocket.connect(ws, message, username, channel, connection_open_event, launch_controller)

        allowed_users = ["el_pipow", "jrcosta"]

        for user in allowed_users:
            if f"@{username.lower()} " in message.lower() and not f":{user.lower()}" in message: # I was mentioned
                user = message.split("display-name=")[1].split(";")[0]
                msg = message.split(f"PRIVMSG #{channel.lower()} :")[1]

                telegram_message = user + ": " + msg
                
                command_idx = msg.find(" ")
                command = msg[command_idx+1:].replace("\n", "").replace("\r", "")
                print("Detected command: " + command)
                if command == "reboot":
                    telegram_message += "Rebooting..."
                    os.system('systemctl reboot -i')
                elif command == "reconnect":
                    WebSocket.connect(ws, ":tmi.twitch.tv RECONNECT", username, channel, connection_open_event, launch_controller)
                elif command == "shutdown":
                    telegram_message += "Shutting down..."
                    os.system('systemctl poweroff -i')
                telegramBot.sendMessage(telegram_message)
                print(telegram_message)

def launch_viewer(channel:str, username:str, oauth_key:str) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    ws = websocket.WebSocketApp(
        websocket_url,
        # on_message=partial(Viewer.on_message, username=username, channel=channel),
        on_message=partial(WebSocket.connect, username=username, channel=channel, connection_open_event=connection_open_event, creator_function=launch_viewer),
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
    
    








