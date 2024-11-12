import os
from streamElements import main as streamElements, twitch_message_sender
from wallapopNotificator import main as wallapopNotificator
import traceback

import threading

if __name__ == "__main__":
  threading.Thread(target=twitch_message_sender.launch_viewer, args=("Runah", "JRCosta", os.getenv("JRCOSTA_OAUTH"))).start()
  threading.Thread(target=twitch_message_sender.launch_controller, args=("El_Pipow", "JRCosta", os.getenv("JRCOSTA_OAUTH"))).start()
  threading.Thread(target=streamElements.bettor_agent, args=("El_pipow", os.getenv("EL_PIPOW_OAUTH"))).start()