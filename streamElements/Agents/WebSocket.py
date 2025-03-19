import datetime
from functools import partial
import multiprocessing
import os
import re
import time
import websocket
import threading
import credentials
import telegramBot
import traceback

class WebSocket:
    def connect(ws:websocket.WebSocketApp, message:str, username:str, channel:str, oauth_key:str , counters:list, connection_open_event:threading.Event, kill_thread_event:threading.Event, creator_function:callable):
        if f":Welcome, GLHF!" in message:
            ws.send(f"JOIN #{channel}")
        
        elif f"ROOMSTATE #{channel.lower()}" in message:
            print(f"{username} connected to {channel} ({creator_function.__name__.replace('launch_', '').capitalize()})")
            connection_open_event.set()
        
        elif ":tmi.twitch.tv RECONNECT" in message:
            telegram_message = f"Received RECONNECT message from Twitch on a {creator_function.__name__} WebSocket\n"
            telegram_message += f"Reconnecting viewer {username} to {channel}\n"
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)
            threading.Thread(target=creator_function, args=(channel, username, oauth_key, counters, kill_thread_event)).start()

        elif "PING :tmi.twitch.tv" in message:
            ws.send("PONG")
            ws.send("PING")
            # telegramBot.sendMessage(f"{creator_function.__name__.replace('launch_', '').capitalize()} returned a PING")
        
        elif ":Login authentication failed":
            os.remove(username.upper() + '_OAUTH')
            telegramBot.sendMessage("Invalid OAuth key", notification=True)

    def on_error(ws:websocket.WebSocketApp, error:Exception, channel:str, username:str, oauth_key:str, counters:list, kill_thread_event:threading.Event, creator_function:callable):
        telegram_message = "Websocket error:\n"
        telegram_message += f"error,{error}, {error.__traceback__}, {type(error) == websocket._exceptions.WebSocketConnectionClosedException}\n"
        telegram_message += traceback.format_exc() + "\n"
        if type(error) == websocket._exceptions.WebSocketConnectionClosedException or error == websocket._exceptions.WebSocketConnectionClosedException:
            telegram_message += f"launching new {creator_function.__name__.replace('launch_', '').capitalize()} agent"
            ws.close()
            time.sleep(5)
            ws.run_forever()
        print(telegram_message)
        telegramBot.sendMessage(telegram_message, notification=True)

    def on_close(ws:websocket.WebSocketApp, close_status_code:int, close_msg:str):
        telegram_message = f"WebSocket connection closed with status: {close_status_code}, message: {close_msg}"
        print(telegram_message)
        telegramBot.sendMessage(telegram_message, notification=True)

    def on_open(ws:websocket.WebSocketApp, username:str, oauth_key:str, counters:list):
        print(f"Logging {username} {oauth_key}")
        ws.send("CAP REQ :twitch.tv/tags twitch.tv/commands")
        ws.send(f"PASS oauth:{oauth_key}")
        ws.send(f"NICK {username}")
        ws.send(f"USER {username} 8 * :{username}")
        counters[0] += 1

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
    
    








