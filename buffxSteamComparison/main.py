


import csv
import datetime
import json
import math
import operator
import random
from statistics import median
import statistics
import time
import traceback
from urllib import parse
from matplotlib import pyplot as plt
import numpy as np
import requests

import sys
sys.path.append('..')
import telegramBot
import credentials


BUFF_HEADERS = {
    'cookie': { # https://api.buff.market/account/api/bookmark/goods?game=csgo&page_num=1&page_size=80
        'session': credentials.buff_cookies
    }.__str__().replace(": ", "=").replace(", ", ";").replace("{", "").replace("}", "").replace("'", "")
}

STEAM_HEADERS = {
    'cookie': { # https://steamcommunity.com/market/pricehistory/?appid=730
        'steamLoginSecure': credentials.steam_cookies, # needs to be updated
    }.__str__().replace(": ", "=").replace(", ", ";").replace("{", "").replace("}", "").replace("'", "")
}

CSFLOAT_HEADERS = {
    # 'cookie': {
    #     'session': credentials.csfloat_cookies, # needs to be updated
    # }.__str__().replace(": ", "=").replace(", ", ";").replace("{", "").replace("}", "").replace("'", "")
    'Authorization': credentials.csfloat_api_key
}













class Item:
    def __init__(self, date:datetime, buff_id:int, market_hash_name:str, buff_price:float, steam_price:float, csfloat_price:float, buff_url:str, steam_url:str, csfloat_url:str, type:str, buff_last_update:datetime=None, steam_last_update:datetime=None, csfloat_last_update:datetime=None):
        self.date = date
        self.buff_id = buff_id
        self.market_hash_name = market_hash_name
        self.buff_price = buff_price
        self.steam_price = steam_price
        self.csfloat_price = csfloat_price
        self.buff_url = buff_url
        self.steam_url = steam_url
        self.csfloat_url = csfloat_url
        self.type = type
        self.buff_last_update = buff_last_update
        self.steam_last_update = steam_last_update
        self.csfloat_last_update = csfloat_last_update

    def __str__(self):
        return f"{self.date} {self.buff_id} {self.market_hash_name} {self.buff_price} {self.steam_price} {self.csfloat_price} {self.buff_url} {self.steam_url} {self.csfloat_url} {self.type} {self.buff_last_update} {self.steam_last_update} {self.csfloat_last_update}"
    
    def csv_line(self):
        return f"{self.date};{self.buff_id};{self.market_hash_name};{self.buff_price};{self.steam_price};{self.csfloat_price if self.csfloat_price is not None else ''};{self.buff_url};{self.steam_url};{self.csfloat_url};{self.type};{self.buff_last_update if self.buff_last_update != None else ''};{self.steam_last_update if self.steam_last_update != None else ''};{self.csfloat_last_update if self.csfloat_last_update != None else ''}\n"

def store_item(item:Item) -> None:
    with open("buffxSteamComparison/History.csv", "a", encoding='utf-8') as file:
        file.write(item.csv_line())

def load_items() -> tuple[list[Item], dict[Item]]:
    """
    Load items history, newest first

    Returns
    -------
    lst : list[Item]
        latest item info list, oldest first

    dct : dict[Item]
        latest item info list, buff_id as key
    """
    with open("buffxSteamComparison/History.csv", "r", encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=";")
        items = list(reader)
    
    dct = {}
    for i in items:
        item = Item(
            date = datetime.datetime.strptime(i[0], "%Y-%m-%d %H:%M:%S"),
            buff_id = int(i[1]),
            market_hash_name = str(i[2]),
            buff_price = float(i[3]),
            steam_price = float(i[4]),
            csfloat_price = float(i[5]) if i[5] != "" else None,
            buff_url = str(i[6]),
            steam_url = str(i[7]),
            csfloat_url = str(i[8]),
            type = str(i[9]),
            buff_last_update = datetime.datetime.strptime(i[10], "%Y-%m-%d %H:%M:%S") if i[10] != "" else None,
            steam_last_update = datetime.datetime.strptime(i[11], "%Y-%m-%d %H:%M:%S") if i[11] != "" else None,
            csfloat_last_update = datetime.datetime.strptime(i[12], "%Y-%m-%d %H:%M:%S") if i[12] != "" else None
        )
        dct[item.buff_id] = item
    
    lst = sorted(dct.values(), key=lambda x: x.date, reverse=False)

    return lst, dct














def update_buff_price(key_word:str, filter:str=None):

    latest_items_dict = load_items()[1]

    page = 1
    while True:
        if key_word == "Bookmarked":
            url = f"https://api.buff.market/account/api/bookmark/goods?game=csgo&page_num={page}&page_size=80"
        elif key_word == "Inventory":
            url = f"https://api.buff.market/api/market/steam_inventory?game=csgo&page_num={page}&page_size=40"
        else:
            url = f"https://api.buff.market/api/market/goods?{filter}game=csgo&page_num={page}&page_size=80"
        response = requests.get(url, headers=BUFF_HEADERS).json()
        try:
            response["data"]
        except KeyError:
            raise Exception(f"update cookies: {url}")

        if key_word == "Bookmarked":
            for i in response["data"]["items"]:
                i = i["goods"]
                item = Item(
                    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    buff_id = i["id"],
                    market_hash_name = i["market_hash_name"],
                    buff_price = float(i["sell_min_price"]),
                    steam_price = latest_items_dict[i["id"]].steam_price if i["id"] in latest_items_dict.keys() else float(i["goods_info"]["steam_price"]),
                    csfloat_price= latest_items_dict[i["id"]].csfloat_price if i["id"] in latest_items_dict.keys() else None,
                    buff_url = 'https://buff.market/market/goods/' + str(i["id"]),
                    steam_url = i["steam_market_url"],
                    csfloat_url = latest_items_dict[i["id"]].csfloat_url if i["id"] in latest_items_dict.keys() else None,
                    type = key_word, # i["goods_info"]["info"]["tags"]["type"]["localized_name"],
                    buff_last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    steam_last_update = latest_items_dict[i["id"]].steam_last_update if i["id"] in latest_items_dict.keys() else None,
                    csfloat_last_update= latest_items_dict[i["id"]].csfloat_last_update if i["id"] in latest_items_dict.keys() else None
                )
                print(item)
                store_item(item)
        elif key_word == "Inventory":
            for key, value in response["data"]["goods_infos"].items():
                item = Item(
                    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    buff_id = value["goods_id"],
                    market_hash_name = value["market_hash_name"],
                    buff_price = value["sell_min_price"],
                    steam_price = latest_items_dict[value["goods_id"]].steam_price if value["goods_id"] in latest_items_dict.keys() else value["steam_price"],
                    csfloat_price = latest_items_dict[value["goods_id"]].csfloat_price if value["goods_id"] in latest_items_dict.keys() else None,
                    buff_url = 'https://buff.market/market/goods/' + str(value["goods_id"]),
                    steam_url = "https://steamcommunity.com/market/listings/730/" + parse.quote(value["market_hash_name"], safe=''),
                    csfloat_url = latest_items_dict[value["goods_id"]].csfloat_url if value["goods_id"] in latest_items_dict.keys() else None,
                    type = "Inventory", # value["tags"]["type"]["localized_name"],
                    buff_last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    steam_last_update = latest_items_dict[value["goods_id"]].steam_last_update if value["goods_id"] in latest_items_dict.keys() else None,
                    csfloat_last_update= latest_items_dict[value["goods_id"]].csfloat_last_update if value["goods_id"] in latest_items_dict.keys() else None
                )
                print(item)
                store_item(item)
        else:
            for i in response["data"]["items"]:
                item = Item(
                    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    buff_id = i["id"],
                    market_hash_name = i["market_hash_name"],
                    buff_price = float(i["sell_min_price"]),
                    steam_price = latest_items_dict[i["id"]].steam_price if i["id"] in latest_items_dict.keys() else float(i["goods_info"]["steam_price"]),
                    csfloat_price= latest_items_dict[i["id"]].csfloat_price if i["id"] in latest_items_dict.keys() else None,
                    buff_url = 'https://buff.market/market/goods/' + str(i["id"]),
                    steam_url = i["steam_market_url"],
                    csfloat_url = latest_items_dict[i["id"]].csfloat_url if i["id"] in latest_items_dict.keys() else None,
                    type = key_word, # i["goods_info"]["info"]["tags"]["type"]["localized_name"],
                    buff_last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    steam_last_update = latest_items_dict[i["id"]].steam_last_update if i["id"] in latest_items_dict.keys() else None,
                    csfloat_last_update= latest_items_dict[i["id"]].csfloat_last_update if i["id"] in latest_items_dict.keys() else None
                )
                print(item)
                store_item(item)

        print(page, response["data"]["total_page"], response["data"]["page_num"])
        page += 1
        time.sleep(max(0, random.normalvariate(3, 1)))
        if response["data"]["total_page"] == response["data"]["page_num"]:
            break

def update_csfloat_price(item:Item):
    url = f"https://csfloat.com/api/v1/listings?type=buy_now&sort_by=lowest_price&market_hash_name={parse.quote(item.market_hash_name, safe='')}"
    response = requests.get(url, headers=CSFLOAT_HEADERS).json()
    with open("buffxSteamComparison/csfloat.json", "w", encoding='utf-8') as file:
        json.dump(response, file, indent=4, ensure_ascii=False)
    if "data" not in response.keys():
        print(url)
        raise Exception(f"Got banned from csfloat") # 200 requests 
    if len(response["data"]) == 0:
        print("No data")
        item.date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        item.csfloat_price = None
        item.csfloat_last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        store_item(item)
        return False
    paint_index = response["data"][0]["item"]["paint_index"] if "paint_index" in response["data"][0]["item"].keys() else None
    def_index = response["data"][0]["item"]["def_index"] if "def_index" in response["data"][0]["item"].keys() else None
    
    # is_commodity = response["data"][0]["item"]["is_commodity"] if "is_commodity" in response["data"][0]["item"].keys() else False
    is_stattrak = response["data"][0]["item"]["is_stattrak"] if "is_stattrak" in response["data"][0]["item"].keys() else None
    is_souvenir = response["data"][0]["item"]["is_souvenir"] if "is_souvenir" in response["data"][0]["item"].keys() else None
    category = None if is_stattrak is None else 1 if is_stattrak else 2 if is_souvenir else 0

    item.date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item.csfloat_price = response["data"][0]["price"]/100
    item.csfloat_url = f"https://csfloat.com/search?" +\
        (f"paint_index={paint_index}" if paint_index is not None else "") +\
        (f"&def_index={def_index}" if def_index is not None else "") +\
        (f"&category={category}" if category is not None else "")
    item.csfloat_last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    store_item(item)

    return True

def update_steam_price(item:Item):

    url = f"https://steamcommunity.com/market/pricehistory/?appid=730&market_hash_name={ parse.quote(item.market_hash_name, safe='')}"

    response = requests.get(url, headers=STEAM_HEADERS).json()
    try:
        _ = response["prices"]
    except (KeyError, TypeError):
        raise Exception(f"update cookies: {url}")

    window_size = 21
    dates = [i[0].split(":")[0] for i in response["prices"][-window_size:]]
    dates = [datetime.datetime.strptime(i, "%b %d %Y %H") for i in dates][::-1]
    date_diff = (datetime.datetime.now() - dates[-1]).total_seconds()/3600

    mean_prices = median([i[1] for i in response["prices"][-window_size:]])
    mean_prices = round(mean_prices, 2)
    
    new_steam_price = mean_prices
    print(round(date_diff, 1))
    if date_diff < 720:
        successfull = True
    else:
        successfull = False

    if item.steam_price == new_steam_price:
        # print(item.buff_id, item.market_hash_name, item.type)
        print("No change in price")
        return successfull
    
    old_price_ratio = round(item.steam_price/item.buff_price,3)
    new_price_ratio = round(new_steam_price/item.buff_price,3)
    
    print(item.buff_id, item.market_hash_name, item.type)
    print(f"\tbuff_price:\t{item.buff_price}$")
    print(f"\tsteam_price:\t{item.steam_price}$\t-> {new_steam_price}€")
    print(f"\tprice_ratio:\t{round(old_price_ratio*100,1)}%\t-> {round(new_price_ratio*100,1)}%")

    item.date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item.steam_price = new_steam_price
    item.steam_url = f"https://steamcommunity.com/market/listings/730/{parse.quote(item.market_hash_name, safe='')}"
    item.steam_last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    store_item(item)

    return successfull













def no_tax(price:float):
    return price

def steam_tax(price:float):
    return math.floor(100*price/1.15-1)/100

def csfloat_tax(price:float):
    return round(price*0.95, 2)

def get_price_ratio(buy_price:float, sell_price:float, sell_tax_function:callable=no_tax):
    if buy_price in [0, None] or sell_price in [0, None]:
        return False
    return round(100*sell_tax_function(sell_price)/buy_price,1)

def get_items_to_update(and_filters:list=[], or_filters:list=[], highlights:list=[], graph:bool=False, max_from_var:str="buff_price", max_to_var:str="steam_price") -> list[Item]:
    items = load_items()[0]

    nulls = [item for item in items if getattr(item, max_from_var) is None or getattr(item, max_to_var) is None]
    items = sorted(items, key=lambda x: get_price_ratio(getattr(x, max_from_var), getattr(x, max_to_var), no_tax), reverse=True) # TODO: make selling site independent
    items = nulls + items

    ranking:list[Item] = []
    for rank in range(len(items)):
        item = items[rank]

        good = True
        for variable,operator,value in and_filters:
            if not type(getattr(item, variable)) == type(None) and  not operator(getattr(item, variable), value):
                good = False
                break
        if not good:
            continue

        good = False if len(or_filters) > 0 else True
        for variable,operator,value in or_filters:
            if operator(getattr(item, variable), value):
                good = True
                break
        if not good:
            continue
        ranking.append(item)
    
    return ranking

def get_best_items(and_filters:list=[], or_filters:list=[], highlights:list=[], graph:bool=False, max_from_var:str="buff_price", max_to_var:str="steam_price") -> list[Item]:
    items = load_items()[0]

    items = sorted(items, key=lambda x: get_price_ratio(getattr(x, max_from_var), getattr(x, max_to_var), no_tax), reverse=True) # TODO: make selling site independent

    ranking:list[Item] = []
    for rank in range(len(items)):
        item = items[rank]
        buy_price = getattr(item, max_from_var)
        sell_price = getattr(item, max_to_var)

        if buy_price in [0, None] or sell_price in [0, None]:
            continue

        good = True
        for variable,operator,value in and_filters:
            if not type(getattr(item, variable)) == type(None) and  not operator(getattr(item, variable), value):
                good = False
                break
        if not good:
            continue

        good = False if len(or_filters) > 0 else True
        for variable,operator,value in or_filters:
            if operator(getattr(item, variable), value):
                good = True
                break
        if not good:
            continue
        ranking.append(item)

    item_info_storage, plot_data = "", []
    for rank in range(len(ranking)):
        item = ranking[rank]
        buy_price = getattr(item, max_from_var)
        sell_price = getattr(item, max_to_var)
        price_ratio = get_price_ratio(buy_price, sell_price, no_tax)
        
        item_info_storage += f"{rank},{item.type},{item.market_hash_name},{price_ratio},{buy_price},{sell_price}\n"

        plot_data.append((rank, price_ratio, item.market_hash_name, item.type))
    with open("buffxSteamComparison/best_items.txt", "w", encoding='utf-8') as file:
        file.write(item_info_storage)
    
    if graph:
        print(max_from_var, max_to_var)

        ratios = [i[1] for i in plot_data]
        quantile = np.quantile(ratios, 0.5)
        plot_data = [i for i in plot_data if i[1] > quantile]
        
        fig, ax = plt.subplots()
        x = [i[0] for i in plot_data]
        y = [i[1] for i in plot_data]
        plt.bar(x, y, width=1, color="lightgray")

        highlighted_data = []
        for i in range(len(highlights)):
            for j in plot_data:
                if j[2] == highlights[i]:
                    # print(i, len(highlights)-1)
                    highlighted_data.append((j[0], j[1], (i)/(len(highlights)-1), j[2]))
                elif j[3] == highlights[i]:
                    # print(i, len(highlights)-1)
                    highlighted_data.append((j[0], j[1], (i)/(len(highlights)-1), j[2]))
        x = [i[0] for i in highlighted_data]
        y = [i[1] for i in highlighted_data]
        c = [i[2] for i in highlighted_data]
        hash_names = [i[3] for i in highlighted_data]
        plt.bar(x, y, width=1, color=plt.cm.turbo(c))
        scatter = plt.scatter(x, y, c=plt.cm.turbo(c), s = 15)


        annotation = ax.annotate(
            text='',
            xy=(0, 0),
            xytext=(15, 15), # distance from x, y
            textcoords='offset points',
            bbox={'boxstyle': 'round', 'fc': 'w'},
            arrowprops={'arrowstyle': '->'}
        )
        annotation.set_visible(False)


        # Step 3. Implement the hover event to display annotations
        def motion_hover(event):
            annotation_visbility = annotation.get_visible()
            if event.inaxes == ax:
                is_contained, annotation_index = scatter.contains(event)
                if is_contained:
                    data_point_hash_name = hash_names[annotation_index['ind'][0]]
                    data_point_location = scatter.get_offsets()[annotation_index['ind'][0]]
                    annotation.xy = data_point_location

                    # text_label = '({0:.2f}, {0:.2f})'.format(data_point_location[0], data_point_location[1])
                    text_label = f"{data_point_hash_name}"
                    annotation.set_text(text_label)

                    annotation.get_bbox_patch().set_facecolor(plt.cm.turbo(c[annotation_index['ind'][0]]))
                    annotation.get_bbox_patch().set_alpha(0.4)
                    annotation.set_alpha(0.4)

                    annotation.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if annotation_visbility:
                        annotation.set_visible(False)
                        fig.canvas.draw_idle()

        fig.canvas.mpl_connect('motion_notify_event', motion_hover)


        ticks = [(i)/(len(highlights)-1) for i in range(len(highlights))]
        print(ticks)
        # print(ticks)
        # print(highlights)
        plt.set_cmap("turbo")
        plt.colorbar().set_ticks(ticks=ticks, labels=highlights)
        plt.show()

    return ranking






def run(UPDATE_BUFF:bool=True, UPDATE_STEAM:bool=True, UPDATE_CSFLOAT:bool=True, graph:bool=False):


    or_filters = [
        ["type", operator.eq, "Agent"],
        ["type", operator.eq, "Bookmarked"],
        ["type", operator.eq, "Charm"],
        ["type", operator.eq, "Gallery"],
        ["type", operator.eq, "Inventory"],
        ["type", operator.eq, "Music Kit"],
        ["type", operator.eq, "Patch"],
        ["type", operator.eq, "Train"],
    ]

    highlights =["Bookmarked", "Charm", "Train"]
    # highlights += ["Lieutenant Rex Krikey | SEAL Frogman", "Lt. Commander Ricksaw | NSWC SEAL", "'Medium Rare' Crasswater | Guerrilla Warfare", "Sir Bloody Silent Darryl | The Professionals", "Antwerp 2022 Viewer Pass"]


    if UPDATE_BUFF:
        update_buff_price("Bookmarked")
        update_buff_price("Inventory")
        update_buff_price("Agent", "category_group=type_customplayer&")
        update_buff_price("Patch", "category=csgo_tool_patch&")
        update_buff_price("Gallery", "quality=normal&itemset=set_community_34,set_community_35,set_realism_camo,set_graphic_design,set_overpass_2024&")
        update_buff_price("Charm", "category=csgo_tool_keychain&")
        update_buff_price("Riptide", "quality=normal&itemset=set_community_29,set_vertigo_2021,set_mirage_2021,set_dust_2_2021,set_train_2021&")
        update_buff_price("Broken Fang", "quality=normal&itemset=set_community_27,set_op10_ancient,set_op10_ct,set_op10_t&")
        update_buff_price("Shattered Web", "quality=normal&itemset=set_community_23,set_norse,set_stmarc,set_canals&")
        update_buff_price("Music Kit", "category=csgo_type_musickit&quality=normal&")
        update_buff_price("Train", "quality=normal&itemset=set_train_2021&")

    if UPDATE_STEAM:
        and_filters = [
            ["buff_price", operator.le, 100],
            ["buff_price",operator.ge, 0.1],
            ["steam_last_update", operator.le, (datetime.datetime.now() - datetime.timedelta(minutes=30))],
        ]

        to_update = get_best_items(and_filters, or_filters, max_from_var="buff_price", max_to_var="steam_price")
        counter, has_data_counter = 0, 0

        while has_data_counter < 30 and counter < len(to_update):
            print(to_update[counter])
            has_data_counter += 1 if update_steam_price(to_update[counter]) else 0
            counter += 1
            print(counter, has_data_counter)
            time.sleep(max(0, random.normalvariate(3, 1)))

    if UPDATE_CSFLOAT:
        and_filters = [
            ["buff_price", operator.le, 100],
            ["buff_price",operator.ge, 0.1],
            ["csfloat_last_update", operator.le, (datetime.datetime.now() - datetime.timedelta(minutes=30))],
            ["type", operator.ne, "Music Kit"],
        ]

        to_update = get_items_to_update(and_filters, or_filters, max_from_var="buff_price", max_to_var="csfloat_price")
        # to_update = get_best_items(and_filters, or_filters + [["csfloat_price", operator.eq, None]], max_from_var="buff_price", max_to_var="csfloat_price")
        counter, has_data_counter = 0, 0
        
        # while has_data_counter < 30 and counter < len(to_update):
        print(f"Updating {len(to_update)} items...")
        while counter < len(to_update):
            print(to_update[counter])
            has_data_counter += 1 if update_csfloat_price(to_update[counter]) else 0
            counter += 1
            print(counter, has_data_counter)
            time.sleep(max(0, random.normalvariate(5, 1)))
    
    
    
    



    and_filters = [
        ["buff_last_update", operator.ge, (datetime.datetime.now() - datetime.timedelta(weeks=1))],
        # ["steam_last_update", operator.ge, (datetime.datetime.now() - datetime.timedelta(weeks=1))],
    ]
    telegram_message = "Filtered:\n"
    if UPDATE_STEAM:
        ranking:list[Item] = get_best_items(and_filters, or_filters,highlights=highlights, graph=graph, max_from_var="buff_price", max_to_var="steam_price")
        
        telegram_message += "\n Steam:\n"
        for i in ranking[:20]:
            telegram_message += f"{i.market_hash_name}\n\t{get_price_ratio(i.buff_price, i.steam_price, steam_tax)}\t {i.buff_price}$ -> {i.steam_price}$({steam_tax(i.steam_price)}$)\n"
    
    if UPDATE_CSFLOAT or True:
        ranking:list[Item] = get_best_items(and_filters, or_filters,highlights=highlights, graph=graph, max_from_var="buff_price", max_to_var="csfloat_price")
        
        telegram_message += "\n CSFloat:\n"
        for i in ranking[:20]:
            if i.csfloat_price is None:
                continue
            telegram_message += f"  - {i.market_hash_name}\n\t{get_price_ratio(i.buff_price, i.csfloat_price, csfloat_tax)}\t {i.buff_price}$ -> {i.csfloat_price}$({csfloat_tax(i.csfloat_price)}$)\n"

    telegramBot.sendMessage(telegram_message, notification=True)
    print(telegram_message)

