import time
from streamElements import charts
from streamElements import twitch_message_sender

import threading

if __name__ == "__main__":
  # charts.scatter()
  # charts.odd()
  # charts.winrate()
  wst, ws = twitch_message_sender.launch()
  twitch_message_sender.send(ws, "el_pipow", "yo")
  time.sleep(5)
  twitch_message_sender.close(wst, ws)
  time.sleep(5)
