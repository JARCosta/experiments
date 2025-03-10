


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
import numpy as np
import requests

import sys
sys.path.append('..')
import telegramBot
import credentials

BUFF_COOKIES = { # https://api.buff.market/account/api/bookmark/goods?game=csgo&page_num=1&page_size=80
    'session': credentials.buff_cookies, # needs to be updated
}.__str__().replace(": ", "=").replace(", ", ";").replace("{", "").replace("}", "").replace("'", "")

STEAM_COOKIES = { # https://steamcommunity.com/market/pricehistory/?appid=730
    'steamLoginSecure': credentials.steam_cookies
    }.__str__().replace(": ", "=").replace(", ", ";").replace("{", "").replace("}", "").replace("'", "")


class Item:
    def __init__(self, date:datetime, id:int, market_hash_name:str, buff_price:float, steam_price:float, buff_url:str, steam_url:str, type:str, buff_last_update:datetime=None, steam_last_update:datetime=None):
        self.date = date
        self.id = id
        self.market_hash_name = market_hash_name
        self.buff_price = buff_price
        self.steam_price = steam_price
        self.buff_url = buff_url
        self.steam_url = steam_url
        self.type = type
        self.buff_last_update = buff_last_update
        self.steam_last_update = steam_last_update

    def __str__(self):
        return f"{self.date} {self.id} {self.market_hash_name} {self.buff_price} {self.steam_price} {self.buff_url} {self.steam_url} {self.type} {self.buff_last_update} {self.steam_last_update}"
    
    def csv_line(self):
        return f"{self.date};{self.id};{self.market_hash_name};{self.buff_price};{self.steam_price};{self.buff_url};{self.steam_url};{self.type};{self.buff_last_update if self.buff_last_update != None else ''};{self.steam_last_update if self.steam_last_update != None else ''}\n"

def store_item(item:Item) -> None:
    with open("buffxSteamComparison/History.csv", "a", encoding='utf-8') as file:
        file.write(item.csv_line())

def load_items() -> list[Item]:
    """
    Load items history, latest first
    """
    with open("buffxSteamComparison/History.csv", "r", encoding='utf-8') as file:
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
            datetime.datetime.strptime(i[8], "%Y-%m-%d %H:%M:%S") if i[8] != "" else None, # buff_last_update,
            datetime.datetime.strptime(i[9], "%Y-%m-%d %H:%M:%S") if i[9] != "" else None # steam_last_update
        ) for i in items
    ]

def load_latest_items_dict() -> list[Item]:
    """
    Load latest items, order of insertion in file
    """
    # print(load_items()[0].date)
    item_history = load_items()[::-1]
    latest_item_history = {i.id: i for i in item_history}
    return latest_item_history

def load_latest_items() -> list[Item]:
    """
    Load latest items, order of insertion in file
    """
    # print(load_items()[0].date)
    item_history = load_items()[::-1]
    latest_item_history = list({i.id: i for i in item_history}.values())
    return latest_item_history

def update_steam_price(item:Item):

    url = f"https://steamcommunity.com/market/pricehistory/?appid=730&market_hash_name={ parse.quote(item.market_hash_name, safe='')}"

    response = requests.get(url, headers={"cookie": STEAM_COOKIES}).json()
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
        # print(item.id, item.market_hash_name, item.type)
        print("No change in price")
        return successfull
    
    old_price_ratio = round(item.buff_price/item.steam_price,3)
    new_price_ratio = round(item.buff_price/new_steam_price,3)
    
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
        item.buff_last_update, # buff_last_update,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # steam_last_update
        ))

    return successfull

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

def get_best_items(value_filters:list=[], steam_to_buff:bool=False, highlights:list=[], graph:bool=False):
    items = load_latest_items()

    items = sorted(items, key=lambda x: get_price_ratio(x, steam_to_buff), reverse=True)

    open("best_items.txt", "w").close()
    rank, plot_data, item_info_storage = 1, [], ""
    for item in items:

        continuer = False
        for variable,operator,value in value_filters:
            if not type(getattr(item, variable)) == type(None) and  not operator(getattr(item, variable), value):
                continuer = True
                break
        if continuer:
            continue
    
        price_ratio = get_price_ratio(item, steam_to_buff)
        steam_price_after_tax = after_steam_tax(item.steam_price)

        item_info = f"{rank}\n"
        item_info += f"{price_ratio} {item.date.strftime('%Y-%m-%d %H:%M:%S')}, {item.market_hash_name}, {item.type}\n"
        item_info += f"\t {item.buff_price}, {item.buff_url}\n"
        item_info += f"\t {item.steam_price}, {steam_price_after_tax}, {item.steam_url}\n"

        plot_data.append((rank, price_ratio, item.market_hash_name, item.type))

        item_info_storage += item_info
        
        rank += 1
    with open("best_items.txt", "a", encoding='utf-8') as file:
        file.write(item_info_storage)
    
    if graph:

        ratios = [i[1] for i in plot_data]
        quantile = np.quantile(ratios, 0.5)
        # print(quantile)
        plot_data = [i for i in plot_data if i[1] > quantile]
        
        import matplotlib.pyplot as plt

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

    return items

def get_items(key_word:str, filter:str=None):

    latest_items_dict = load_latest_items_dict()

    page = 1
    while True:
        if key_word == "Bookmarked":
            url = f"https://api.buff.market/account/api/bookmark/goods?game=csgo&page_num={page}&page_size=80"
        elif key_word == "Inventory":
            url = f"https://api.buff.market/api/market/steam_inventory?game=csgo&page_num={page}&page_size=40"
        else:
            url = f"https://api.buff.market/api/market/goods?{filter}game=csgo&page_num={page}&page_size=80"
        headers = {
            "cookie": BUFF_COOKIES,
        }
        response = requests.get(url, headers=headers).json()
        try:
            response["data"]
        except KeyError:
            raise Exception(f"update cookies: {url}")

        if key_word == "Bookmarked":
            for i in response["data"]["items"]:
                i = i["goods"]
                item = Item(
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date,
                    i["id"], # id,
                    i["market_hash_name"], # market_hash_name,
                    float(i["sell_min_price"]), # buff_price,
                    latest_items_dict[i["id"]].steam_price if i["id"] in latest_items_dict.keys() else float(i["goods_info"]["steam_price"]), # steam_price,
                    'https://buff.market/market/goods/' + str(i["id"]), # buff_url,
                    i["steam_market_url"], # steam_url,
                    # i["goods_info"]["info"]["tags"]["type"]["localized_name"], # type
                    key_word, # type
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # buff_last_update,
                    latest_items_dict[i["id"]].steam_last_update if i["id"] in latest_items_dict.keys() else None # steam_last_update
                )
                print(item)
                store_item(item)

        elif key_word == "Inventory":
            for key, value in response["data"]["goods_infos"].items():
                item = Item(
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date,
                    value["goods_id"], # id,
                    value["market_hash_name"], # market_hash_name,
                    value["sell_min_price"], # buff_price,
                    latest_items_dict[value["goods_id"]].steam_price if value["goods_id"] in latest_items_dict.keys() else value["steam_price"], # steam_price,
                    'https://buff.market/market/goods/' + str(value["goods_id"]), # buff_url,
                    "https://steamcommunity.com/market/listings/730/" + parse.quote(value["market_hash_name"], safe=''), # steam_url,
                    # value["tags"]["type"]["localized_name"], # type
                    "Inventory", # type
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # buff_last_update,
                    latest_items_dict[value["goods_id"]].steam_last_update if value["goods_id"] in latest_items_dict.keys() else None # steam_last_update
                )
                print(item)
                store_item(item)
        else:
            for i in response["data"]["items"]:
                if 30551 == i["id"] or "30551" == i["id"]:
                    breakpoint()
                item = Item(
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date,
                    i["id"], # id,
                    i["market_hash_name"], # market_hash_name,
                    float(i["sell_min_price"]), # buff_price,
                    latest_items_dict[i["id"]].steam_price if i["id"] in latest_items_dict.keys() else float(i["goods_info"]["steam_price"]), # steam_price,
                    'https://buff.market/market/goods/' + str(i["id"]), # buff_url,
                    i["steam_market_url"], # steam_url,
                    # i["goods_info"]["info"]["tags"]["type"]["localized_name"], # type
                    key_word, # type
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # buff_last_update,
                    latest_items_dict[i["id"]].steam_last_update if i["id"] in latest_items_dict.keys() else None # steam_last_update
                )
                print(item)
                store_item(item)

        print(page, response["data"]["total_page"], response["data"]["page_num"])
        page += 1
        time.sleep(random.normalvariate(5, 1))
        if response["data"]["total_page"] == response["data"]["page_num"]:
            break


def run(UPDATE_BUFF:bool=True, UPDATE_STEAM:bool=True, STEAM_TO_BUFF:bool=False, graph:bool=False):

    if UPDATE_BUFF:
        get_items("Bookmarked")
        get_items("Inventory")
        get_items("Agent", "category_group=type_customplayer&")
        get_items("Patch", "category=csgo_tool_patch&")
        get_items("Gallery", "quality=normal&itemset=set_community_34,set_realism_camo,set_graphic_design,set_overpass_2024&")
        get_items("Charm", "category=csgo_tool_keychain&")
        get_items("Riptide", "quality=normal&itemset=set_community_29,set_vertigo_2021,set_mirage_2021,set_dust_2_2021,set_train_2021&")
        get_items("Broken Fang", "quality=normal&itemset=set_community_27,set_op10_ancient,set_op10_ct,set_op10_t&")
        get_items("Shattered Web", "quality=normal&itemset=set_community_23,set_norse,set_stmarc,set_canals&")
        get_items("Music Kit", "category=csgo_type_musickit&quality=normal&")

    if UPDATE_STEAM:
        filters = [
            ["buff_price", operator.le, 100],
            ["buff_price",operator.ge, 0.1],
            # ["date", operator.ge, (datetime.datetime.now() - datetime.timedelta(weeks=1)),
            ["type", operator.eq, "Gallery"],
            ["type", operator.eq, "Agent"],
            ["type", operator.eq, "Charm"],
            ["type", operator.eq, "Patch"],
            ["type", operator.eq, "Inventory"],
        ]

        to_update, has_median_counter, counter = get_best_items(filters, steam_to_buff=STEAM_TO_BUFF), 0, 0
        while has_median_counter < 30:
            print(to_update[counter])
            if update_steam_price(to_update[counter]):
                has_median_counter += 1
            counter += 1
            print(counter, has_median_counter)
            time.sleep(max(0, random.normalvariate(3, 1)))

    
    filters = [
        ["buff_last_update", operator.ge, (datetime.datetime.now() - datetime.timedelta(weeks=1))],
        ["steam_last_update", operator.ge, (datetime.datetime.now() - datetime.timedelta(weeks=1))],
        ["id", operator.ne, 20004]
    ]
    
    
    top10 = get_best_items(value_filters=filters)[:10]
    telegram_message = "Top10:\n"
    for i in top10:
        telegram_message += f"{i.market_hash_name} {get_price_ratio(i)} {i.buff_price} {after_steam_tax(i.steam_price)}\n"


    highlights =["Bookmarked", "Inventory", "Agent", "Charm", "Patch", "Music Kit"]
    # highlights += ["Lieutenant Rex Krikey | SEAL Frogman", "Lt. Commander Ricksaw | NSWC SEAL", "'Medium Rare' Crasswater | Guerrilla Warfare", "Sir Bloody Silent Darryl | The Professionals", "Antwerp 2022 Viewer Pass"]
    ranking = get_best_items(value_filters=filters,highlights=highlights, steam_to_buff=STEAM_TO_BUFF, graph=graph)
    
    telegram_message += "\n Filtered:\n"
    for i in ranking[:10]:
        telegram_message += f"{i.market_hash_name} {get_price_ratio(i)} {i.buff_price} {after_steam_tax(i.steam_price)}\n"
    telegramBot.sendMessage(telegram_message, notification=True)
    print(telegram_message)

if __name__ == "__main__":
    run()
