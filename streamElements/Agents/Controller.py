from functools import partial
import os
import sys
import threading
import credentials
import telegramBot
import websocket

from .WebSocket import WebSocket, send
from buffxSteamComparison.main import run
import credentials

class Controller:

    def on_message(ws:websocket.WebSocketApp, message:str, username:str, channel:str, oauth_key:str, counters:list, connection_open_event:threading.Event, kill_thread_event:threading.Event):
        WebSocket.connect(ws, message, username, channel, oauth_key, counters, connection_open_event, kill_thread_event, launch_controller)

        allowed_users = ["el_pipow", "jrcosta"]
        try:
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split(f"PRIVMSG #{channel.lower()} :")[1]
        except IndexError:
            return
        
        if f"@{username.lower()}" in msg.lower() and not f":{username.lower()}" in msg: # I was mentioned
            if user.lower() in allowed_users:
                command_idx = msg.find(" ")
                command = msg[command_idx+1:].replace("\n", "").replace("\r", "")
                print("Detected command: " + command)
                if command == "reboot" or command == "restart":
                    send(ws=ws, channel=channel, message="Rebooting")
                    os.system('systemctl reboot -i')
                elif command == "reload":
                    send(ws=ws, channel=channel, message="Reconnecting")
                    # WebSocket.connect(ws, ":tmi.twitch.tv RECONNECT", username, channel, oauth_key, counters, connection_open_event, kill_thread_event, launch_controller)
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                elif command == "shutdown":
                    send(ws=ws, channel=channel, message="Shutting down")
                    os.system('systemctl poweroff -i')
                elif command == "help":
                    send(ws=ws, channel=channel, message="Command List: reboot, restart, reload, shutdown, buff, help")
                elif command == "buff":
                    credentials.buff_cookies = "lalala"
                    run()

def launch_controller(channel:str, username:str, oauth_key:str, counters:list, kill_thread_event:threading.Event) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=partial(Controller.on_message, username=username, channel=channel, oauth_key=oauth_key, counters=counters, connection_open_event=connection_open_event, kill_thread_event=kill_thread_event),
        on_error=partial(WebSocket.on_error, channel=channel, username=username, oauth_key=oauth_key, counters=counters, kill_thread_event=kill_thread_event, creator_function=launch_controller),
        on_open=partial(WebSocket.on_open, username=username, oauth_key=oauth_key, counters=counters)
        )

    # Run the WebSocket connection in a separate thread to avoid blocking
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for the connection to be open before sending the message
    connection_open_event.wait()
    counters[1] += 1

    kill_thread_event.wait()
    ws.close()
    # wst.join()
    print(f"{launch_controller.__name__.replace('launch_', '').capitalize()} left")

    return wst, ws