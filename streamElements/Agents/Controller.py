from functools import partial
import os
import threading
import credentials
import telegramBot
import websocket

from streamElements.twitch_message_sender import WebSocket, send


class Controller:

    def on_message(ws:websocket.WebSocketApp, message:str, controller_username:str, controller_channel:str, counters:list, connection_open_event:threading.Event):
        WebSocket.connect(ws, message, controller_username, controller_channel, counters, connection_open_event, launch_controller)

        allowed_users = ["el_pipow", "jrcosta"]
        try:
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split(f"PRIVMSG #{controller_channel.lower()} :")[1]
        except IndexError:
            return
        if user.lower() in allowed_users:
            telegram_message = user + ": " + msg

            command_idx = msg.find(" ")
            command = msg[command_idx+1:].replace("\n", "").replace("\r", "")
            print("Detected command: " + command)
            if command == "reboot":
                telegram_message += "Rebooting..."
                os.system('systemctl reboot -i')
            elif command == "reconnect":
                WebSocket.connect(ws, ":tmi.twitch.tv RECONNECT", controller_username, controller_channel, connection_open_event, launch_controller)
            elif command == "shutdown":
                telegram_message += "Shutting down..."
                os.system('systemctl poweroff -i')
            elif command == "help":
                send(ws=ws, channel=controller_channel, message="Command List:\nreboot\nreconnect\nshutdown\nhelp")
            telegramBot.sendMessage(credentials.telegramBot_Notifications_token, telegram_message, credentials.telegramBot_User_id)
            print(telegram_message)

def launch_controller(channel:str, username:str, oauth_key:str, counters:list, kill_thread_event:threading.Event) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    try:
        ws = websocket.WebSocketApp(
            websocket_url,
            on_message=partial(Controller.on_message, controller_username=username, controller_channel=channel, counters=counters, connection_open_event=connection_open_event),
            on_error=WebSocket.on_error,
            on_open=partial(WebSocket.on_open, oauth_key=oauth_key, username=username, counters=counters)
            )
    except Exception as e:
        print(e)
    # Run the WebSocket connection in a separate thread to avoid blocking
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for the connection to be open before sending the message
    connection_open_event.wait()
    counters[1] += 1

    kill_thread_event.wait()
    ws.close()
    wst.join()

    return wst, ws