import asyncio
import csv
from datetime import datetime
import json
import time
import visualizer

import requests
import sys

GOODS = {}
for line_str in requests.get("https://raw.githubusercontent.com/ModestSerhat/buff163-ids/main/buffids.txt").text.split("\n"):
    line_lst = line_str.split(";")
    GOODS[line_lst[1]] = line_lst[0]


def get_buff_json(url, hidden_prints:bool=False):
    headers = {
        "Accept-Language": "en-US",
        # "cookie": "session=1-KkV0mFdN6EI9S8ZGWA-Aldct4C_eK0uhmoUit1Y9KnJW2038331450", main
        "cookie": "session=1-iOHNuqGSjRWueamMaALM9ytyt7eoLLju47e2Wpb-RZ0z2029595640", # RenaGonca
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Referer": "https://buff.163.com/market/dota2",
        "X-Requested-With": "XMLHttpRequest"
      }
    request = requests.get(url, headers=headers)
    if(request.status_code == 429):
        while request.status_code != 200:
            time.sleep(10)
            if not hidden_prints: print("\033[91mError requesting again...")
            request = requests.get(url, headers=headers)
    print(request.text)
    return request

async def get_buff_data(good_name, hidden_prints:bool=False):
    sell_orders_url = "https://buff.163.com/api/market/goods/sell_order?game=csgo&page_num=1&goods_id=" + GOODS[good_name]
    buy_order_url = "https://buff.163.com/api/market/goods/buy_order?game=csgo&page_num=1&goods_id=" + GOODS[good_name]
    
    date = datetime.now().strftime("%Y-%m-%d")
    reference_time = datetime.now().strftime("%H:%M")

    sell_order_request = get_buff_json(sell_orders_url, hidden_prints)
    buy_order_request = get_buff_json(buy_order_url, hidden_prints)

    min_sell_order = round(float(sell_order_request.json()["data"]["items"][0]["price"]) * 0.13, 2)
    steam_reference_price = sell_order_request.json()["data"]["goods_infos"][GOODS[good_name]]["steam_price_cny"]
    steam_reference_price = round(float(steam_reference_price)*0.13, 2)
    try:
        max_buy_order = round(float(buy_order_request.json()["data"]["items"][0]["price"]) * 0.13, 2)
    except IndexError:
        try:
            print("\033[94mError at: ", end="")
            print(GOODS[good_name], good_name)
            print(buy_order_request.json()["data"]["items"])
            print(buy_order_request.json()["data"]["items"][0])
            print(buy_order_request.json()["data"]["items"][0]["price"])
            print("\033[0m", end="")
        except IndexError:
            max_buy_order = ""
    volume = ""

    with open("steamMarketApi/data/requests/buff/" + date + ".csv", "a", encoding="utf-8") as f:
        csv.writer(f, delimiter=";", lineterminator="\n").writerow([reference_time, good_name, min_sell_order, max_buy_order, volume, steam_reference_price])
        
    if not hidden_prints: print("\033[92m" + good_name, min_sell_order, max_buy_order, "\033[0m")


async def get_buff_data_bulk(hidden_prints:bool=False):
    for start in range(1,10):
        url = f"https://buff.163.com/api/market/goods?game=csgo&page_num={start}&page_size=80&sort_by=sell_num.desc&sort_order=desc"

        date = datetime.now().strftime("%Y-%m-%d")
        reference_time = datetime.now().strftime("%H:%M")

        request = get_buff_json(url)

        # ['appid', 'bookmarked', 'buy_max_price', 'buy_num', 'can_bargain', 'can_search_by_tournament', 'description', 'game', 'goods_info', 'has_buff_price_history', 'id', 'market_hash_name', 'market_min_price', 'name', 'quick_price', 'sell_min_price', 'sell_num', 'sell_reference_price', 'short_name', 'steam_market_url', 'transacted_num']
        # print(request.text)
        items = request.json()["data"]["items"]
        res = []
        for item in items:
            market_hash_name = item["market_hash_name"]
            good_id = item["id"]
            min_sell_order = round(float(item["sell_min_price"]) * 0.13, 2)
            sell_orders = item["sell_num"]
            buy_orders = item["buy_num"]
            max_buy_order = round(float(item["buy_max_price"]) * 0.13, 2)
            steam_reference_price = round(float(item["goods_info"]["steam_price_cny"])*0.13, 2)

            res.append([reference_time, market_hash_name, min_sell_order, sell_orders, max_buy_order, buy_orders, steam_reference_price])
            if not hidden_prints: print("\033[92m" + market_hash_name, min_sell_order, sell_orders, max_buy_order, buy_orders, steam_reference_price, "\033[0m")

        with open("steamMarketApi/data/requests/buff/" + date + ".csv", "a", encoding="utf-8") as f:
            for row in res:
                print(row)
                csv.writer(f, delimiter=";", lineterminator="\n").writerow(row)

        if not hidden_prints: print("\033[92m" + "start=", str(start), "\033[0m")


async def get_steam_data(market_hash_name, hidden_prints:bool=False):
    url = "https://steamcommunity.com/market/priceoverview/?appid=730&currency=1&market_hash_name=" + market_hash_name.replace("&", "%26").replace("+", "%2B")
    
    date = datetime.now().strftime("%Y-%m-%d")
    reference_time = datetime.now().strftime("%H:%M")
    # if not hidden_prints: print(url)

    request = requests.get(url, headers={"Accept-Language": "en-US"})
    if(request.status_code == 429):
        for i in range(3):
            if not hidden_prints: print("retrying in 60 seconds...")
            time.sleep(60)
            request = requests.get(url, headers={"Accept-Language": "en-US"})
            if(request.status_code == 200):
                break

    if(request.status_code == 200):
        min_sell_order = round(float(request.json()["lowest_price"][1:].replace("-", "0").replace(",", ""))*0.94, 2)
        volume = int(request.json()["volume"].replace(",", ""))
        max_buy_order = ""

        with open("steamMarketApi/data/requests/steam/" + date + ".csv", "a", encoding="utf-8") as f:
            csv.writer(f, delimiter=";", lineterminator="\n").writerow([reference_time, market_hash_name, min_sell_order, max_buy_order, volume])

        if not hidden_prints: print("\033[94m" + market_hash_name, min_sell_order, max_buy_order, "\033[0m")
    else:
        print("\033[91m" + market_hash_name, "failed", "\033[0m")

async def get_steam_data_bulk(hidden_prints:bool=False):

    for start in range(0, 20000, 100):
        url = f"https://steamcommunity.com/market/search/render/?query=&start={start}&count=100&norender=1&appid=730"
        # url = "https://steamcommunity.com/market/priceoverview/?appid=730&currency=1&market_hash_name=" + market_hash_name.replace("&", "%26").replace("+", "%2B")

        date = datetime.now().strftime("%Y-%m-%d")
        reference_time = datetime.now().strftime("%H:%M")
        # if not hidden_prints: print(url)

        request = requests.get(url, headers={"Accept-Language": "en-US"})
        if(request.status_code == 429):
            while request.status_code != 200:
                if not hidden_prints: print("\033[91mERROR: requesting again in 60 seconds... \033[0m")
                time.sleep(60)
                request = requests.get(url, headers={"Accept-Language": "en-US"})


        items = []
        if(request.status_code == 200):
            request = request.json()
            total_count = request["total_count"]
            for i in request["results"]:
                if(i["asset_description"]["appid"] == 730):
                    market_hash_name = i["hash_name"]
                    min_sell_order = float(i["sell_price"])/100
                    volume = int(i["sell_listings"])
                    max_buy_order = 0
                    items.append([reference_time, market_hash_name, min_sell_order, volume, max_buy_order, 0])
                    if not hidden_prints: print("\033[94m" + market_hash_name, min_sell_order, volume, max_buy_order, 0, "\033[0m")


            with open("steamMarketApi/data/requests/steam/" + date + ".csv", "a", encoding="utf-8") as f:
                for item in items:
                    csv.writer(f, delimiter=";", lineterminator="\n").writerow(item)
        else:
            if not hidden_prints: print("\033[91m" + "Exit caused by status code:", request.status_code, "\033[0m")
        
        if not hidden_prints: print("\033[92m" + "start=", str(start), "\033[0m")
        # time.sleep(5)


async def scrape(bypass:bool=False, source:str = "both", priority:bool=False, hidden_prints:bool=False):
    past_time = int(datetime.now().strftime("%H"))

    while True:

        current_time = int(datetime.now().strftime("%H"))
        tasks = []

        if(past_time == current_time-1 or bypass):
            if(priority):
                with open("steamMarketApi/data/requests/priorities.csv", "r", encoding="utf-8") as f:
                    csv_reader = csv.reader(f, delimiter=";")
                    if source in ["buff", "both"]:
                        for row in csv_reader:
                            tasks.append(asyncio.create_task(get_buff_data(row[0], hidden_prints)))
                    if source in ["steam", "both"]:
                        for row in csv_reader:
                            tasks.append(asyncio.create_task(get_steam_data(row[0], hidden_prints)))
            else:
                if source in ["buff", "both"]:
                    tasks.append(asyncio.create_task(get_buff_data_bulk(hidden_prints)))
                if source in ["steam", "both"]:
                    tasks.append(asyncio.create_task(get_steam_data_bulk(hidden_prints)))
        
        for task in tasks:
            await task
        
        if bypass:
            bypass = False

        past_time = current_time
        time.sleep(60)


if __name__ == '__main__':

    # print(sys.argv[1:])

    commands = sys.argv[1:]

    if len(commands) > 0:
        if "-b" in commands or "-bypass" in commands:
            position = commands.index("-bypass") if "-bypass" in commands else commands.index("-b")
            bypass = commands[position+1].upper() == "TRUE"

        if "-s" in commands or "-source" in commands:
            position = commands.index("-source") if "-source" in commands else commands.index("-s")
            source = commands[position+1].lower()
        
        if "-p" in commands or "-priority" in commands:
            position = commands.index("-priority") if "-priority" in commands else commands.index("-p")
            priority = commands[position+1].upper() == "TRUE"
        
        hidden_prints = True if "-hi" in commands or "-hidden" in commands else False
    else:
        bypass = input("Do you want to bypass the time check? (y/n): ").upper()
        bypass = bypass == "Y" or bypass == "YES"
        source = input("From where do you want to get data? (buff/steam/both): ")
        priority = input("Do you want to get priority items only? (y/n): ").upper()
        priority = priority == "Y" or priority == "YES"
        hidden_prints = False

    asyncio.run(scrape(bypass, source, priority, hidden_prints))


