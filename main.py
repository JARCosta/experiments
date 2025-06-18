import time
import threading

import signal
import sys

from streamElements.Agent import Agent
from streamElements import oauth

def signal_handler(sig, frame):
    print("\nReceived interrupt signal, shutting down...")
    kill_event.set()
    sys.exit(0)

if __name__ == "__main__":
    print("Starting agent")
    kill_event = threading.Event()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    EL_PIPOW_OAUTH = oauth.check_oauth_token("El_Pipow")
    JRCOSTA_OAUTH = oauth.check_oauth_token("JRCosta")

    OAUTH = {
        "el_pipow": EL_PIPOW_OAUTH,
        "jrcosta": JRCOSTA_OAUTH,
    }


    thread_list = []
    # thread_list.append(threading.Thread(target=lambda: Agent("el_pipow", "JRCosta", "bfrjqg8xuc6vuz7m6d36uyq5qmren3", kill_event), daemon=True))
    thread_list.append(threading.Thread(target=lambda: Agent("runah", "JRCosta", OAUTH["jrcosta"], kill_event), daemon=True))
    thread_list.append(threading.Thread(target=lambda: Agent("prcs", "JRCosta", OAUTH["jrcosta"], kill_event), daemon=True))
    thread_list.append(threading.Thread(target=lambda: Agent("nopeej", "JRCosta", OAUTH["jrcosta"], kill_event), daemon=True))
    
    [thread.start() for thread in thread_list]


    try:
        # Keep the main thread alive
        while not kill_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, shutting down...")
        kill_event.set()
    
    print("Waiting for agent to finish...")
    [thread.join(timeout=3) for thread in thread_list]
    print("Agent stopped.")
