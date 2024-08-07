import websocket
import threading

# Event to signal that the connection is open
connection_open_event = threading.Event()

LOOKING_FOR = "no longer accepting bets for"

class WebSocket:

    def on_message(ws, message):
        # print(f"Received message: {message}")

        if ":tmi.twitch.tv 001 el_pipow :Welcome, GLHF!" in message:
            ws.send("JOIN #runah")
        
        if "ROOMSTATE #runah" in message:
            connection_open_event.set()
        
        if "PING :tmi.twitch.tv" in message:
            ws.send("PONG")
            ws.send("PING")
        
        if ("@el_pipow" in message or "@El_Pipow" in message) and not ":el_pipow" in message and not "@El_Pipow, you have bet " in message:
            with open("resources/twitch_chat.txt", "a") as f:
                f.write(message.split("display-name=")[1].split(";")[0] + ": " + message.split("PRIVMSG #runah :")[1] + "\n")
        
        if "@El_Pipow, you have bet " in message or "won the contest" in message:
            with open("resources/bets.txt", "a") as f:
                f.write(message.split("display-name=")[1].split(";")[0] + ": " + message.split("PRIVMSG #runah :")[1] + "\n")

    def on_error(ws, error):
        print(f"Error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print(f"WebSocket connection closed with status: {close_status_code}, message: {close_msg}")

    def on_open(ws):
        print("WebSocket connection opened")
        
        ws.send("CAP REQ :twitch.tv/tags twitch.tv/commands")
        ws.send("PASS oauth:gqboej248n02nrfeku4g5cypjdeash")
        ws.send("NICK el_pipow")
        ws.send("USER el_pipow 8 * :el_pipow")

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

def debug():
    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=WebSocket.on_message,
        on_error=WebSocket.on_error,
        on_close=WebSocket.on_close,
        on_open=WebSocket.on_open
    )
    
    # Run the WebSocket connection in a separate thread to avoid blocking
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()

    # Wait for the connection to be open before sending the message
    connection_open_event.wait()

    ws.send("PRIVMSG #{} :!bet {} {}".format("el_pipow", "win", "100"))
    ws.close()

    # Wait for the WebSocket thread to finish
    wst.join()

    

if __name__ == "__main__":
    open()
    








