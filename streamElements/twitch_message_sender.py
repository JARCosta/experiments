import datetime
import multiprocessing
import time
import websocket
import threading
from telegramBot import main as telegramBot
from streamElements import main
import traceback

# Event to signal that the connection is open
connection_open_event = threading.Event()

class WebSocket:

    def on_message(ws, message):
        if ":tmi.twitch.tv 001 el_pipow :Welcome, GLHF!" in message:
            ws.send("JOIN #runah")
            with open("streamElements/resources/test.txt", "a") as f:
                f.write("out: JOIN #runah\n")
        
        elif "ROOMSTATE #runah" in message:
            connection_open_event.set()
        
        elif ":tmi.twitch.tv RECONNECT" in message:
            main.reconnect()

            telegram_message = "Received RECONNECT message from Twitch"
            telegram_message += "Reconnecting..."
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)
            print(threading.get_ident())
        
        elif "PING :tmi.twitch.tv" in message: # Respond to PING messages
            ws.send("PONG")
            ws.send("PING")
            with open("streamElements/resources/test.txt", "a") as f:
                f.write("out: PONG\n")
                f.write("out: PING\n")
        
        elif "@El_Pipow, there is no contest currently running." in message: # Bet placed too late
            main.increase_variable_delay()
            main.send_message()
        
        elif "no longer accepting bets for" in message: # Bet's closed
            pass
        
        elif "won the contest" in message: # Result of the bet
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split("PRIVMSG #runah :")[1].split('ACTION ')[1].split("!")[0] + "!\n"
            with open("streamElements/resources/bets.txt", "a") as f:
                f.write(user + ": " + msg)
            
            telegram_message = user + ": " + msg + "\n"
            telegram_message += "You have {} points\n".format(main.get_balance())
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)
            print(threading.get_ident())

            bet_winner = message.split("PRIVMSG #runah :")[1]
            bet_winner = bet_winner.split('"')[1]
            with open("streamElements/resources/pots.txt", "a") as f:
                f.write(bet_winner + "\n")

        elif "@el_pipow" in message.lower() and not ":el_pipow" in message: # I was mentioned
            user = message.split("display-name=")[1].split(";")[0]
            msg = message.split("PRIVMSG #runah :")[1]
            with open("streamElements/resources/twitch_chat.txt", "a") as f:
                f.write(user + ": " + msg)
            telegram_message = user + ": " + msg
            if "you have bet" in message: # Bet placed confirmation
                with open("streamElements/resources/bets.txt", "a") as f:
                    f.write(user + ": " + msg)
                telegram_message += "You have {} points\n".format(main.get_balance())
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)
            print(threading.get_ident())

        with open("streamElements/resources/test.txt", "a") as f:
            f.write("in: " + message.replace("\n", "\n\t")[:-1])

    def on_error(ws, error):
        telegram_message = "Error:\n"
        telegram_message += datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
        telegram_message += str(error) + "\n"
        telegram_message += traceback.format_exc() + "\n"
        # telegramBot.sendMessage(telegram_message)
        print(telegram_message)

    def on_close(ws, close_status_code, close_msg):
        print(f"WebSocket connection closed with status: {close_status_code}, message: {close_msg}")

    def on_open(ws):
        print("WebSocket connection opened")
        
        ws.send("CAP REQ :twitch.tv/tags twitch.tv/commands")
        ws.send("PASS oauth:gqboej248n02nrfeku4g5cypjdeash")
        ws.send("NICK el_pipow")
        ws.send("USER el_pipow 8 * :el_pipow")

        with open("streamElements/resources/test.txt", "a") as f:
            f.write("out: CAP REQ :twitch.tv/tags twitch.tv/commands\n")
            f.write("out: PASS oauth:AUTH_KEY\n")
            f.write("out: NICK el_pipow\n")
            f.write("out: USER el_piow 8 * :el_pipow\n")

        print("Sent login information")

def launch():
    global READY
    READY = False
    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=WebSocket.on_message,
        on_error=WebSocket.on_error,
        on_open=WebSocket.on_open
        )
    
    # Run the WebSocket connection in a separate thread to avoid blocking
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for the connection to be open before sending the message
    connection_open_event.wait()

    return wst, ws

def send(ws, channel, message):
        ws.send(f"PRIVMSG #{channel} :{message}")

def ping(ws):
    ws.send("PING")

def close(wst, ws):
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
    
    








