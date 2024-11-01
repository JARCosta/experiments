


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
        return f"{self.date} {self.id} {self.market_hash_name} {self.buff_price} {self.steam_price} {self.buff_url} {self.steam_url} {self.type}"
    
    def csv_line(self):
        return f"{self.date};{self.id};{self.market_hash_name};{self.buff_price};{self.steam_price};{self.buff_url};{self.steam_url};{self.type}\n"

def store_item(item:Item) -> None:
    with open("History.csv", "a", encoding='utf-8') as file:
        file.write(item.csv_line())

def load_items() -> list[Item]:
    """
    Load items history, latest first
    """
    with open("History.csv", "r", encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=";")
        items = list(reader)[::-1]
    
    return [ 
        Item(
            datetime.datetime.strptime(i[0], "%Y-%m-%d %H:%M:%S"), # date,
            int(i[1]), # id,
            str(i[2]), # market_hash_name,
            float(i[3]), # buff_price,
            float(i[4]), # steam_price,
            str(i[5]), # buff_url,
            str(i[6]), # steam_url,
            str(i[7]), # type
        ) for i in items
    ]

def load_latest_items() -> list[Item]:
    """
    Load latest items, no particular order
    """
    print(load_items()[0].date)
    item_history = load_items()[::-1]
    latest_item_history = list({i.id: i for i in item_history}.values())
    return latest_item_history

def get_latest_item(id:int) -> Item:
    return {i.id: i for i in load_items()}[id]

def update_bookmarked_prices():

    url = 'https://api.buff.market/account/api/bookmark/goods?game=csgo&page_num=1&page_size=15'
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9,pt;q=0.8,fr;q=0.7,es;q=0.6',
        'cookie': 'Locale-Supported=en; _uetvid=67f774801c1c11ef8d8e99c46aa0b808; fblo_881005522527906=y; Device-Id=cJDGYsSGk9yuvsIUw2HH; session=1-zDOYlj7g0oLtB2g_4h9IYyXO7P9-BdJGYvIznqcYj9Cn2045446835; forterToken=94905526192b40f6aa1b5cfb50e845e5_1730211347307_78_UDF9_13ck; csrf_token=Ijk4ZmZkZjA2YTFkNjI0NzQxYmJjZTFiNTk3YmZmNjIwZDk2N2VmNWYi.ZyDuFA.jOt7g-zvgW8HDYaTy8n4sC2T_lo',
        'origin': 'https://buff.market',
        'priority': 'u=1, i',
        'referer': 'https://buff.market/',
        'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'x-csrftoken': 'Ijk4ZmZkZjA2YTFkNjI0NzQxYmJjZTFiNTk3YmZmNjIwZDk2N2VmNWYi.ZyDuFA.jOt7g-zvgW8HDYaTy8n4sC2T_lo'
    }

    response = requests.get(url, headers=headers).json()
    with open("bookmarked_agents.json", "w", encoding='utf-8') as file:
        json.dump(response, file, indent=4)
    for i in response["data"]["items"]:
        i = i["goods"]
        item = Item(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date,
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

def update_steam_price(item:Item):
    url = f'https://steamcommunity.com/market/priceoverview/?appid=730&market_hash_name={item.market_hash_name}&format=json'
    response = requests.get(url).json()
    try:
        new_steam_price = float(response['lowest_price'][1:])
        new_steam_price = float(response['median_price'][1:])
    except KeyError:
        print(item)
        print(response)
        # raise Exception("Steam price not found")
        new_steam_price = -1

    old_price_ratio = round(item.buff_price/item.steam_price,3)
    new_price_ratio = round(item.buff_price/new_steam_price,3)

    if item.steam_price != new_steam_price:
        print(item.id, item.market_hash_name, item.type)
        print(f"\tbuff_price:\t{item.buff_price}$\t-> {item.buff_price}$")
        print(f"\tsteam_price:\t{item.steam_price}$\t-> {new_steam_price}$")
        print(f"\tprice_ratio:\t{round(old_price_ratio*100,1)}%\t-> {round(new_price_ratio*100,1)}%")

        store_item(Item(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date,
            item.id, # id,
            item.market_hash_name, # market_hash_name,
            item.buff_price, # buff_price,
            new_steam_price, # steam_price,
            item.buff_url, # buff_url,
            item.steam_url, # steam_url,
            item.type, # type
            ))

def update_prices(types=[]):
    for item in load_latest_items():
        if types != [] and item.type not in types:
            continue

        url = f"https://steamcommunity.com/market/priceoverview/?appid=730&market_hash_name={item.market_hash_name}&format=json"
        response = requests.get(url).json()
        try:
            new_steam_price = float(response['lowest_price'][1:])
            new_steam_price = float(response['median_price'][1:])
        except KeyError:
            print(response)
            raise Exception("Steam price not found")

        old_price_ratio = round(item.buff_price/item.steam_price,3)
        new_price_ratio = round(item.buff_price/new_steam_price,3)

        # if new_price_ratio != price_ratio:
        print(item.id, item.market_hash_name, item.type)
        print(f"\tbuff_price:\t{item.buff_price}$\t-> {item.buff_price}$")
        print(f"\tsteam_price:\t{item.steam_price}$\t-> {new_steam_price}$")
        print(f"\tprice_ratio:\t{round(old_price_ratio*100,1)}%\t-> {round(new_price_ratio*100,1)}%")

        store_item(Item(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date,
            item.id, # id,
            item.market_hash_name, # market_hash_name,
            item.buff_price, # buff_price,
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

    if item.buff_price == 0 or steam_price_after_tax == 0:
        return False
    
    if steam_to_buff:
        price_ratio = round(100*item.buff_price/item.steam_price,1)
    else:
        price_ratio = round(100*steam_price_after_tax/item.buff_price,1)
    return price_ratio

def get_best_items(types=[], steam_to_buff=False, highlights=[], verbose=False):
    items = load_latest_items()[::-1]

    items = filter(lambda x: get_price_ratio(x, steam_to_buff) != False, items)
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
        item_info += f"{price_ratio} {item.date.strftime('%Y-%m-%d %H:%M:%S')}, {item.market_hash_name}\n"
        item_info += f"\t {item.buff_price}, {item.buff_url}\n"
        item_info += f"\t {item.steam_price}, {steam_price_after_tax}, {item.steam_url}\n"

        if item.market_hash_name in highlights or item.type in highlights:
            plot_data.append((rank, price_ratio, 1))
        else:
            plot_data.append((rank, price_ratio, 0))

        print(item_info)

        with open("best_agents.txt", "a", encoding='utf-8') as file:
            file.write(item_info)
    
    if verbose:
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
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date,
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

if __name__ == "__main__":
   
    # update_prices("Agent")
    # time.sleep(random.normalvariate(5, 1))
    
    # for i in load_latest_items():
    #     print(i)
    # print(get_latest_item(17))


    # update_bookmarked_prices()
    # time.sleep(random.normalvariate(5, 1))
    # get_items("category_group=type_customplayer&") # Agents
    # time.sleep(random.normalvariate(5, 1))
    # get_items("category=csgo_tool_patch&") # Patches

    # update_steam_prices("category_730_Type%5B%5D=tag_Type_CustomPlayer&") # Agents
    # update_steam_prices("category_730_Type%5B%5D=tag_CSGO_Tool_Patch&") # Patches
    # update_steam_price("")

    to_update = get_best_items([], steam_to_buff=False, highlights=["Lieutenant Rex Krikey | SEAL Frogman", "Lt. Commander Ricksaw | NSWC SEAL", "Agent"])
    print(len(to_update))
    print(to_update[:5])
    print(to_update[-5:])
    
    temp_list = to_update[:5]
    temp_list.extend(to_update[-5:])
    for i in temp_list:
        update_steam_price(i)
    
    get_best_items([], steam_to_buff=False, highlights=["Lieutenant Rex Krikey | SEAL Frogman", "Lt. Commander Ricksaw | NSWC SEAL", "Agent"], verbose=True)
