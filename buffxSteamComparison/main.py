


import csv
import datetime
import json
import math
import random
import time
import requests

class Item:
    def __init__(self, date:datetime, id:int, market_hash_name:str, buff_price:float, steam_price:float, buff_url:str, steam_url:str, type:str):
        self.date = date
        self.id = id
        self.market_hash_name = market_hash_name
        self.buff_price = buff_price
        self.steam_price = steam_price
        self.buff_url = buff_url
        self.steam_url = steam_url
        self.type = type

    def __str__(self):
        return f"{self.id} {self.market_hash_name} {self.buff_price} {self.steam_price} {self.buff_url} {self.steam_url} {self.type}"
    
    def csv_line(self):
        return f"{self.date};{self.id};{self.market_hash_name};{self.buff_price};{self.steam_price};{self.buff_url};{self.steam_url};{self.type}\n"


def store_item(item:Item):
    with open("Agents.csv", "a", encoding='utf-8') as file:
        file.write(item.csv_line())

def load_items() -> list[Item]:
    with open("Agents.csv", "r", encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=";")
        items = list(reader)
    
    item_list = []
    for i in items:
        item_list.append(Item(
            datetime.datetime.strptime(i[0], "%d-%m %H:%M:%S").replace(year=datetime.datetime.now().year), # date,
            int(i[1]), # id,
            str(i[2]), # market_hash_name,
            float(i[3]), # buff_price,
            float(i[4]), # steam_price,
            str(i[5]), # buff_url,
            str(i[6]), # steam_url,
            str(i[7]), # type
        ))
    return item_list

def get_latest_prices():
    csv_data = load_items()
    date_sorted_data = sorted(csv_data, key=lambda x: x.date, reverse=True)

    unique_items = {}
    for i in date_sorted_data:
        if i.id not in unique_items:
            unique_items[i.id] = i
    
    items = list(unique_items.values())
    return items

def import_from_manual(file_name="buff_market-manual.json"):
        with open(file_name, "r", encoding='utf-8') as file:
            json_data = json.load(file)

        for i in json_data["data"]["items"]:
                
                item = Item(
                    datetime.datetime.now().strftime('%d-%m %H:%M:%S'), # date,
                    int(i['id']), # id,
                    str(i['market_hash_name']), # market_hash_name,
                    float(i['sell_min_price']), # buff_price,
                    float(i['goods_info']['steam_price']), # steam_price,
                    str('https://buff.market/market/goods/' + str(i['id'])), # buff_url,
                    str(i['steam_market_url']), # steam_url,
                    str(i["goods_info"]["info"]["tags"]["type"]["localized_name"]), # type
                )
                print(item)
                store_item(item)

def update_prices(types=[]):
    items = get_latest_prices()[::-1]
    # print(items[0:3])
    # print(items[-1])
    # breakpoint()

    for item in items:
        # print(item)
        # print(types, types != [], item.type, item.type not in types)
        if types != [] and item.type not in types:
            continue

        threshold = datetime.datetime.now() - datetime.timedelta(seconds=len(get_latest_prices())*10)
        print("Last updated:", item.date, ">", (threshold).replace(microsecond=0))
        if item.date > threshold:
            break


        url = f"https://api.buff.market/api/market/goods/sell_order?game=csgo&page_num=1&page_size=10&goods_id={item.id}&sort_by=default"
        response = requests.get(url).json()
        try:
            new_buff_price = float(response['data']['items'][0]['price'])
        except KeyError:
            print(response)
            Exception("Buff price not found")

        url = f"https://steamcommunity.com/market/priceoverview/?appid=730&market_hash_name={item.market_hash_name}&format=json"
        response = requests.get(url).json()
        try:
            new_steam_price = float(response['lowest_price'][1:])
            new_steam_price = float(response['mean_price'][1:])
        except KeyError:
            print(response)
            Exception("Steam price not found")

        old_price_ratio = round(item.buff_price/item.steam_price,3)
        new_price_ratio = round(new_buff_price/new_steam_price,3)

        # if new_price_ratio != price_ratio:
        print(item.id, item.market_hash_name, item.type)
        print(f"\tbuff_price:\t{item.buff_price}$\t-> {new_buff_price}$")
        print(f"\tsteam_price:\t{item.steam_price}$\t-> {new_steam_price}$")
        print(f"\tprice_ratio:\t{round(old_price_ratio*100,1)}%\t-> {round(new_price_ratio*100,1)}%")

        store_item(Item(
            datetime.datetime.now().strftime('%d-%m %H:%M:%S'), # date,
            item.id, # id,
            item.market_hash_name, # market_hash_name,
            new_buff_price, # buff_price,
            new_steam_price, # steam_price,
            item.buff_url, # buff_url,
            item.steam_url, # steam_url,
            item.type, # type
            ))

        time.sleep(random.normalvariate(5, 1))

def after_steam_tax(price:float):
    return math.floor(100*price/1.15-1)/100

def get_price_ratio(item:Item, steam_to_buff=False):
    
    steam_price_after_tax = after_steam_tax(item.steam_price)
    
    if steam_to_buff:
        price_ratio = round(100*item.buff_price/item.steam_price,1)
    else:
        price_ratio = round(100*steam_price_after_tax/item.buff_price,1)
    return price_ratio

def get_best_items(types=[], steam_to_buff=False, highlights=[]):
    items = get_latest_prices()

    items = sorted(items, key=lambda x: get_price_ratio(x, steam_to_buff))
    
    open("best_agents.txt", "w").close()
    rank = 1
    plot_data = []
    for item in items:

        if types != [] and item.type not in types:
            continue

        if "★" in item.market_hash_name or ("StatTrak™" in item.market_hash_name and not "Music Kit" in item.market_hash_name):
            continue
    
        price_ratio = get_price_ratio(item, steam_to_buff)
        steam_price_after_tax = after_steam_tax(item.steam_price)

        item_info = f"{rank}\n"
        rank += 1
        item_info += f"{price_ratio} {item.date.strftime('%d-%m %H:%M:%S')}, {item.market_hash_name}\n"
        item_info += f"\t {item.buff_price}, {item.buff_url}\n"
        item_info += f"\t {item.steam_price}, {steam_price_after_tax}, {item.steam_url}\n"

        if item.market_hash_name in highlights or item.type in highlights:
            plot_data.append((rank, price_ratio, 1))
        else:
            plot_data.append((rank, price_ratio, 0))

        print(item_info)

        with open("best_agents.txt", "a", encoding='utf-8') as file:
            file.write(item_info)
    
    import matplotlib.pyplot as plt

    x = [i[0] for i in plot_data]
    y = [i[1] for i in plot_data]
    c = [i[2] for i in plot_data]

    plt.scatter(x, y, c=c, cmap='coolwarm')
    plt.show()


    return items



def get_items(filter:str):
    page = 1
    while True:
        url = f"https://api.buff.market/api/market/goods?{filter}game=csgo&page_num={page}&page_size=80"
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,pt;q=0.8,fr;q=0.7,es;q=0.6",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "x-csrftoken": "Ijk4ZmZkZjA2YTFkNjI0NzQxYmJjZTFiNTk3YmZmNjIwZDk2N2VmNWYi.Zx1fvQ.mYuvD3iJyafQYruJWoNddUVo-_c",
            "cookie": "Locale-Supported=en; _uetvid=67f774801c1c11ef8d8e99c46aa0b808; fblo_881005522527906=y; Device-Id=cJDGYsSGk9yuvsIUw2HH; session=1-zDOYlj7g0oLtB2g_4h9IYyXO7P9-BdJGYvIznqcYj9Cn2045446835; forterToken=94905526192b40f6aa1b5cfb50e845e5_1729978299755_35_UDF9_13ck; csrf_token=Ijk4ZmZkZjA2YTFkNjI0NzQxYmJjZTFiNTk3YmZmNjIwZDk2N2VmNWYi.Zx1fvQ.mYuvD3iJyafQYruJWoNddUVo-_c",
            "Referer": "https://buff.market/",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        response = requests.get(url, headers=headers).json()
        try:
            _ = response["data"]
        except KeyError:
            print(response)
        
        for i in response["data"]["items"]:
            item = Item(
                datetime.datetime.now().strftime('%d-%m %H:%M:%S'), # date,
                i["id"], # id,
                i["market_hash_name"], # market_hash_name,
                float(i["sell_min_price"]), # buff_price,
                float(i["goods_info"]["steam_price"]), # steam_price,
                'https://buff.market/market/goods/' + str(i["id"]), # buff_url,
                i["steam_market_url"], # steam_url,
                i["goods_info"]["info"]["tags"]["type"]["localized_name"], # type 
            )

            print(item)
            store_item(item)
        print(page, response["data"]["total_page"], response["data"]["page_num"])
        page += 1
        if response["data"]["total_page"] == response["data"]["page_num"]:
            break
        time.sleep(random.normalvariate(5, 1))

def get_main_page():
    url = f"https://api.buff.market/api/market/goods?game=csgo&page_num=1&page_size=80"
    response = requests.get(url).json()
    for i in response["data"]["items"]:
        item = Item(
            datetime.datetime.now().strftime('%d-%m %H:%M:%S'), # date,
            i["id"], # id,
            i["market_hash_name"], # market_hash_name,
            float(i["sell_min_price"]), # buff_price,
            float(i["goods_info"]["steam_price"]), # steam_price,
            'https://buff.market/market/goods/' + str(i["id"]), # buff_url,
            i["steam_market_url"], # steam_url,
            i["goods_info"]["info"]["tags"]["type"]["localized_name"], # type 
        )

        print(item)
        store_item(item)

if __name__ == "__main__":
   
    
    # url = "https://api.buff.market/api/market/goods?category_group=type_customplayer&game=csgo&page_num=1&page_size=80"
    # url = "https://api.buff.market/api/market/goods?category=sticker_community2021&game=csgo&page_num=1&page_size=80"
    # import_from_manual()

    # update_prices("Agent")

    # get_best_items("Agent", steam_to_buff=False, highlights=["Lieutenant Rex Krikey | SEAL Frogman", "Lt. Commander Ricksaw | NSWC SEAL", "Agent"])

    get_items("category_group=type_customplayer&") # Agents
    time.sleep(random.normalvariate(5, 1))
    get_items("category=csgo_tool_patch&") # Patches
    # get_main_page()
