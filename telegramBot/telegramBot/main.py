import time
import traceback
import credentials
import requests
import threading

############################################################
####################  GETTER FUNCTIONS  ####################
############################################################

def getUpdates(token: str):
  r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

def getMe(token: str):
  r = requests.get(f"https://api.telegram.org/bot{token}/getMe")
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

def getChat(token: str, chat_id: str):
  params = {"chat_id": chat_id}
  r = requests.get(f"https://api.telegram.org/bot{token}/getChat", params=params)
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

def getChatMembersCount(token: str, chat_id: str):
  params = {"chat_id": chat_id}
  r = requests.get(f"https://api.telegram.org/bot{token}/getChatMembersCount", params=params)
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

def getChatMember(token: str, chat_id: str, user_id: str):
  params = {"chat_id": chat_id, "user_id": user_id}
  r = requests.get(f"https://api.telegram.org/bot{token}/getChatMember", params=params)
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

def getMessages(token: str, chat_id: str):
  params = {"chat_id": chat_id}
  r = requests.get(f"https://api.telegram.org/bot{token}/getMessages", params=params)
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

############################################################
####################  SENDER FUNCTIONS  ####################
############################################################

def _send_request(token, params):
  while True:
    try:
      r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data=params)
      # print(r.json())
      return r
    except requests.exceptions.ConnectionError as e:
      print(e)
      # print(traceback.format_exc())
      time.sleep(2)
      # print("Retrying to send:", message)
      continue
      break

def sendMessage(message: str, log:bool = True, notification:bool = False):
  user = credentials.telegramBot_User_id
  params = {"chat_id": user, "text": message}
  if log:
    r = _send_request(credentials.telegramBot_Logs_token, params)
  if notification:
    r = _send_request(credentials.telegramBot_Notifications_token, params)
  
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]
  
def sendMessage_threaded(message: str, log:bool = True, notification:bool = False):
  threading.Thread(target=sendMessage, args=(message, notification)).start()

