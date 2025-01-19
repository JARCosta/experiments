from functools import partial
import threading
import websocket

from .WebSocket import WebSocket


def launch_viewer(channel:str, username:str, oauth_key:str, counters:list, kill_thread_event:threading.Event) -> tuple[threading.Thread, websocket.WebSocketApp]:
    connection_open_event = threading.Event()

    websocket_url = "wss://irc-ws.chat.twitch.tv/"
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=partial(WebSocket.connect, username=username, channel=channel, oauth_key=oauth_key, counters=counters, connection_open_event=connection_open_event, kill_thread_event=kill_thread_event, creator_function=launch_viewer),
        on_error=partial(WebSocket.on_error, channel=channel, username=username, oauth_key=oauth_key, counters=counters, kill_thread_event=kill_thread_event, creator_function=launch_viewer),
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
    print(f"{launch_viewer.__name__.replace('launch_', '').capitalize()} left")

    return wst, ws