from streamElements import main as streamElements
from wallapopNotificator import main as wallapopNotificator
import traceback

import threading

if __name__ == "__main__":
  threading.Thread(target=streamElements.get_bets).start()
  # threading.Thread(target=wallapopNotificator.run).start()