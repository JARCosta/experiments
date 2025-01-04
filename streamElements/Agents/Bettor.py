from functools import partial
import threading
import credentials
import telegramBot
import websocket

from streamElements import main
from streamElements.twitch_message_sender import WebSocket

class Bettor:

    def on_message(ws:websocket.WebSocketApp, message:str, username:str, channel:str, counters:list, connection_open_event:threading.Event):
        WebSocket.connect(ws, message, username, channel, counters, connection_open_event, launch_bettor)
        try:
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split(f"PRIVMSG #{channel.lower()} :")[1]
            mention = message.split("@")[-1].split(" ")[0].replace(",", "")
            # print(user, ":", msg.replace("\n", "").replace("\r", ""))
            # print(user.lower(), user.lower() == "StreamElements".lower())
            # print(mention.lower(), username.lower(), mention.lower() == username.lower())
            # print()
        except IndexError:
            return
        if f", there is no contest currently running." in message: # Bet placed too late
            mention = message.split("@")[-1].split(" ")[0].replace(",", "")
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split(f"PRIVMSG #{channel.lower()} :")[1]
            print(user, ":", msg.replace("\n", "").replace("\r", ""))
            print(user.lower(), user.lower() == "StreamElements".lower())
            print(mention.lower(), username.lower(), mention.lower() == username.lower())
            print()
            if user.lower() == "StreamElements".lower():
                print("StreamElements")
            if mention.lower() == username.lower():
                print(mention.lower(), mention.lower() == username.lower())
            if mention.lower() == username.lower() and user.lower() == "StreamElements".lower():
                print("I bet too late")
                main.increase_variable_delay()
                main.send_message()

        elif f"@{username.lower()}" in message.lower() and not f":{username.lower()}" in message: # I was mentioned
            print("Got mentioned")
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split(f"PRIVMSG #{channel.lower()} :")[1]
            telegram_message = user + ": " + msg
            telegramBot.sendMessage(credentials.telegramBot_Notifications_token, telegram_message, credentials.telegramBot_User_id)
            print(telegram_message)

def launch_bettor(channel:str, username:str, oauth_key:str, counters:list, kill_thread_event:threading.Event) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    try:
        ws = websocket.WebSocketApp(
            websocket_url,
            on_message=partial(Bettor.on_message, username=username, channel=channel, counters=counters, connection_open_event=connection_open_event),
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

    # kill_thread_event.wait()
    # ws.close()
    # wst.join()

    return wst, ws