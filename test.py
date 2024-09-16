from streamElements import charts, main as streamElements
import wallapopNotificator.main as wallapopNotificator

import threading

if __name__ == "__main__":
  # charts.scatter()
  # charts.odd()
  # charts.winrate()
  threading.Thread(target=wallapopNotificator.run).start()
