import requests


TOKEN = "6731395929:AAE0uPmr90EvjO1qIyVcJ6Lt6dec3F0NldA"
URL = f"https://api.telegram.org/bot{TOKEN}"
CHAT_ID = "6449165312"


############################################################
####################  GETTER FUNCTIONS  ####################
############################################################

def getUpdates():
  r = requests.get(URL + "/getUpdates")
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

def getMe():
  r = requests.get(URL + "/getMe")
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

def getChat(chat_id: str):
  params = {"chat_id": chat_id}
  r = requests.get(URL + "/getChat", params=params)
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

def getChatMembersCount(chat_id: str):
  params = {"chat_id": chat_id}
  r = requests.get(URL + "/getChatMembersCount", params=params)
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

def getChatMember(chat_id: str, user_id: str):
  params = {"chat_id": chat_id, "user_id": user_id}
  r = requests.get(URL + "/getChatMember", params=params)
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

def getMessages(chat_id: str):
  params = {"chat_id": chat_id}
  r = requests.get(URL + "/getMessages", params=params)
  return r.json()
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]

############################################################
####################  SENDER FUNCTIONS  ####################
############################################################

def sendMessage(message: str, user : str = CHAT_ID):
  params = {"chat_id": user, "text": message}
  r = requests.get(URL + "/sendMessage", params=params)
  if not r.ok:
    raise Exception(r.text)
  else:
    return r.json()["result"]



if __name__ == "__main__":
  # print(getUpdates())
  # print(getMe())
  # print(getChat(CHAT_ID))
  # print(getChatMembersCount(CHAT_ID))
  # print(getChatMember(CHAT_ID, CHAT_ID))
  # print(sendMessage("Test message"))
  print(getMessages(CHAT_ID))

