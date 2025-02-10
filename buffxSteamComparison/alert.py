


import threading
import time
import requests
import telegramBot


def alert(kill_thread:threading.Event):
    print("Alert Agent initialized")
    
    last_price = None
    while True:
        id = 19909
        r = requests.get(f"https://api.buff.market/api/market/goods/sell_order?game=csgo&page_num=1&page_size=10&goods_id={id}&sort_by=default").json()
        print(r["data"]["items"][0]["price"])
        if last_price != r["data"]["items"][0]["price"]:
            last_price = r["data"]["items"][0]["price"]
            print("new price")
            telegramBot.sendMessage(str(last_price), notification=True)
        print(kill_thread.is_set())
        for _ in range(int(60)//5):
            time.sleep(5)
            if kill_thread.is_set():
                return

if __name__ == "__main__":
    alert()