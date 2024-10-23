from streamElements import main as streamElements
from wallapopNotificator import main as wallapopNotificator
from streamElements.twitch_message_sender import launch
import traceback

import threading

if __name__ == "__main__":
  launch("runah", "JRCosta", "AUTH_KEY")
  threading.Thread(target=streamElements.get_bets).start()
  # threading.Thread(target=wallapopNotificator.run).start()