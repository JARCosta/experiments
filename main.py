from streamElements import main as streamElements

import threading

if __name__ == "__main__":
  threading.Thread(target=streamElements.get_bets).start()
