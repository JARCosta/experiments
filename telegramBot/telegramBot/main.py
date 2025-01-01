import requests
import credentials

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

def sendMessage(token: str, message: str, user : str):
  params = {"chat_id": user, "text": message}
  try:
    r = requests.get(f"https://api.telegram.org/bot{token}/sendMessage", params=params)
  except requests.exceptions.ConnectionError:
    print("telegramBot.sendMessage Error")
    return requests.Response()
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]
