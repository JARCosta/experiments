import datetime
from functools import partial
import re
import threading
import credentials
import telegramBot
import websocket

from .WebSocket import WebSocket
from .ChatBettor import get_balance


class DataCollector:

    def on_message(ws:websocket.WebSocketApp, message:str, username:str, channel:str, oauth_key:str, counters:list, connection_open_event:threading.Event, kill_thread_event:threading.Event):
        WebSocket.connect(ws, message, username, channel, oauth_key, counters, connection_open_event, kill_thread_event, launch_data_collector)

        if "a new contest has started" in message: # New bet
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
            telegram_message += "You have {} points\n".format(get_balance(username))
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)

            timestamp = datetime.datetime.now()
            with open("streamElements/resources/player_bet.csv", "a") as f:
                result = re.search('"(.*)" won the contest "Aposta no resultado do próximo jogo do Runah" with (.*)% of all bets and (.*)% of the total pot!', msg)
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

def launch_data_collector(channel:str, username:str, oauth_key:str, counters:list, kill_thread_event:threading.Event) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=partial(DataCollector.on_message, username=username, channel=channel, oauth_key=oauth_key, counters=counters, connection_open_event=connection_open_event, kill_thread_event=kill_thread_event),
        on_error=partial(WebSocket.on_error, channel=channel, username=username, oauth_key=oauth_key, counters=counters, kill_thread_event=kill_thread_event, creator_function=launch_data_collector),
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
    print(f"{launch_data_collector.__name__.replace('launch_', '').capitalize()} left")

    return wst, ws