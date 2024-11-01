import os
from streamElements import main as streamElements, twitch_message_sender
from wallapopNotificator import main as wallapopNotificator
import traceback

import threading

if __name__ == "__main__":
  twitch_message_sender.launch_viewer("Runah", "JRCosta", os.getenv("JRCOSTA_OAUTH"))
  twitch_message_sender.launch_controller("El_Pipow", "JRCosta", os.getenv("JRCOSTA_OAUTH"))
  threading.Thread(target=streamElements.bettor_agent, args=("El_pipow", os.getenv("EL_PIPOW_OAUTH"))).start()