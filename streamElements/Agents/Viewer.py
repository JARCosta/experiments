from functools import partial
import threading
import websocket

from .WebSocket import WebSocket


def launch_viewer(channel:str, username:str, oauth_key:str, counters:list, kill_thread_event:threading.Event) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    try:
        ws = websocket.WebSocketApp(
            websocket_url,
            # on_message=partial(Viewer.on_message, username=username, channel=channel),
            on_message=partial(WebSocket.connect, username=username, channel=channel, counters=counters, connection_open_event=connection_open_event, creator_function=launch_viewer),
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