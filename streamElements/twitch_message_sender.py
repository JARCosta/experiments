import websocket
import threading
import telegramBot
import streamelements

# Event to signal that the connection is open
connection_open_event = threading.Event()
repeat_runah = True

class WebSocket:

    def on_message(ws, message):
        # print(f"Received message: {message}")
        global repeat_runah
        if ":tmi.twitch.tv 001 el_pipow :Welcome, GLHF!" in message:
            ws.send("JOIN #runah")
            with open("resources/test.txt", "a") as f:
                f.write("out: JOIN #runah\n")
        
        elif "ROOMSTATE #runah" in message:
            connection_open_event.set()
        
        elif ":tmi.twitch.tv RECONNECT" in message:
            streamelements.reconnect()

            telegram_message = "Received RECONNECT message from Twitch"
            telegram_message += "Reconnecting..."
            telegramBot.sendMessage(telegram_message)
            print(telegram_message)
        
        elif "PING :tmi.twitch.tv" in message: # Respond to PING messages
            ws.send("PONG")
            ws.send("PING")
            with open("resources/test.txt", "a") as f:
                f.write("out: PONG\n")
                f.write("out: PING\n")
        
        elif "@El_Pipow, there is no contest currently running." in message: # Bet placed too late
            streamelements.increase_variable_delay()
        
        elif "no longer accepting bets for" in message: # Bet's closed
            pass

        elif "@El_Pipow, you have bet " in message or "won the contest" in message: # I placed a bet or contest ended
            with open("resources/bets.txt", "a") as f:
                f.write(message.split("display-name=")[1].split(";")[0] + ": " + str(message.split("PRIVMSG #runah :")[1]))
            msg = message.split("PRIVMSG #runah :")[1]
            print(msg)
            msg = str(msg).replace("\x01", "") if "won the contest" in message else msg
            
            telegram_message = message.split("display-name=")[1].split(";")[0] + ": " + msg + "\n"
            telegram_message += "You have {} points\n".format(streamelements.get_balance())
            telegramBot.sendMessage(telegram_message)

        elif "@El_Pipow" in message and not ":el_pipow" in message: # I was mentioned
            with open("resources/twitch_chat.txt", "a") as f:
                f.write(message.split("display-name=")[1].split(";")[0] + ": " + message.split("PRIVMSG #runah :")[1])
            
        elif repeat_runah and (";display-name=Runah" in message or ";display-name=runah" in message): # and not message.split("PRIVMSG #runah :")[1].contains(" "): # Runah sent the word of the day message
            with open("resources/twitch_chat.txt", "a") as f:
                f.write(message.split("display-name=")[1].split(";")[0] + ": " + message.split("PRIVMSG #runah :")[1])
                        
            telegramBot.sendMessage(message.split("display-name=")[1].split(";")[0] + ": " + message.split("PRIVMSG #runah :")[1])
            # repeat_runah = False

        with open("resources/test.txt", "a") as f:
            f.write("in: " + message.replace("\n", "\n\t")[:-1])

    def on_error(ws, error):
        print(f"Error: {error}")
        telegramBot.sendMessage(f"Error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print(f"WebSocket connection closed with status: {close_status_code}, message: {close_msg}")

    def on_open(ws):
        print("WebSocket connection opened")
        
        ws.send("CAP REQ :twitch.tv/tags twitch.tv/commands")
        ws.send("PASS oauth:gqboej248n02nrfeku4g5cypjdeash")
        ws.send("NICK el_pipow")
        ws.send("USER el_pipow 8 * :el_pipow")

        with open("resources/test.txt", "a") as f:
            f.write("out: CAP REQ :twitch.tv/tags twitch.tv/commands\n")
            f.write("out: PASS oauth:AUTH_KEY\n")
            f.write("out: NICK el_pipow\n")
            f.write("out: USER el_piow 8 * :el_pipow\n")

        print("Sent login information")

        # Signal that the connection is open
        # connection_open_event.set()

def launch():
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

def bet(ws, option, amount):
        ws.send("PRIVMSG #{} :!bet {} {}".format("runah", option, amount))

def close(wst, ws):
    ws.close()
    wst.join()
    

if __name__ == "__main__":
    open()
    








