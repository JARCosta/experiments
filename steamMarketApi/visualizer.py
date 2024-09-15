import asyncio
import csv
from datetime import datetime
import os
import scrape
import plot


STEAM_TAX = 0.130434783
BUFF_TAX = 0.02


async def get_file_csv(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        csv_reader = csv.reader(f, delimiter=";")
        return list(csv_reader)


async def main():
    os.chdir("steamMarketApi/data/requests/buff/")
    lst = [int(i.replace(".csv", "").replace("-", "")) for i in os.listdir()]
    temp_file = str(sorted(lst)[-1])
    buff_file = temp_file[:4] + "-" + temp_file[4:6] + "-" + temp_file[6:8]
    os.chdir("../steam")
    lst = [int(i.replace(".csv", "").replace("-", "")) for i in os.listdir()]
    temp_file = str(sorted(lst)[-1])
    steam_file = temp_file[:4] + "-" + temp_file[4:6] + "-" + temp_file[6:8]
    os.chdir("../../../")
    
    # print(buff_files)
    # print(steam_files)

    tasks = []
    tasks.append(asyncio.create_task(get_file_csv("steamMarketApi/data/requests/buff/"+buff_file + ".csv")))
    tasks.append(asyncio.create_task(get_file_csv("steamMarketApi/data/requests/steam/"+steam_file + ".csv")))
    
    [await task for task in tasks]

    items = {}
    for task in range(len(tasks)):
        for row in list(tasks[task].result())[1:]:
            if(items.get(row[1]) == None):
                items[row[1]] = {}
                
            element = {
                "date": buff_file + " " + row[0] if task == 0 else steam_file + " " + row[0],
                "sell_order_price": float(row[2]),
                "sell_order_volume": int(row[3]),
                "buy_order_price": float(row[4]),
                "buy_order_volume": int(row[5]),
                }
            items[row[1]]["buff" if task == 0 else "steam"] = element


    res = {}
    for i in items:
        try:
            buff_buy_price = items[i]["buff"]["sell_order_price"]
            buff_sell_price = round(buff_buy_price * (1-BUFF_TAX), 2) # for now using slow sell
            buff_sell_price = round(items[i]["buff"]["buy_order_price"] * (1-BUFF_TAX), 2)
            
            steam_buy_price = items[i]["steam"]["sell_order_price"]
            steam_sell_price = round(items[i]["steam"]["buy_order_price"] * (1 - STEAM_TAX), 2)
            steam_sell_price = round(steam_buy_price * (1 - STEAM_TAX), 2) # for now using slow sell

            res[i] = {
                "item": i,

                "buff date": items[i]["buff"]["date"],
                "buy on buff for": buff_buy_price,
                "buff sell orders": items[i]["buff"]["sell_order_volume"],
                "sell on buff for": buff_sell_price,
                "buff buy orders": items[i]["buff"]["buy_order_volume"],

                "steam date": items[i]["steam"]["date"],
                "buy on steam for": steam_buy_price,
                "steam sell orders": items[i]["steam"]["sell_order_volume"],
                "sell on steam for": steam_sell_price,
                "steam buy orders": items[i]["steam"]["buy_order_volume"],

                "buff->steam": round(steam_sell_price/buff_buy_price, 2) if buff_buy_price != 0 else 0,
                "steam->buff": round(buff_sell_price/steam_buy_price, 2) if steam_buy_price != 0 else 0,
            }
        except KeyError as e:
            if( e.args[0] != "steam" and e.args[0] != "buff"):
                print(e.args[0])
            continue
    
    
    # print(list(res.keys())[0:10])

    with open("steamMarketApi/data/requests/visualizer.csv", "w", encoding="utf-8") as f:
        f.write("item,buff_date,buff_buy_price,buff_sell_orders,buff_sell_price,buff_buy_orders,steam_date,steam_buy_price,steam_sell_orders,steam_sell_price,steam_buy_orders,buff->steam,steam->buff\n")

    max_buff_to_steam = ["", 0]
    max_steam_to_buff = ["", 0]
    
    # filter res where buy on steam for > 0.1
    res = {k: v for k, v in res.items() if v["buy on buff for"] < 2 and  "Graffiti" not in v["item"] and "Sticker" not in v["item"] and "Field-Tested" not in v["item"] and "Battle-Scarred" not in v["item"] and "Well-Worn" not in v["item"] and "Minimal Wear" not in v["item"] and "Factory New" not in v["item"]}
    
    # sort res by steam sell order value
    res = {k: v for k, v in sorted(res.items(), key=lambda item: item[1]["steam sell orders"], reverse=True)}
    
    for item in res:
        if(res[item]["buff->steam"] > max_buff_to_steam[1]):
            max_buff_to_steam = [res[item], res[item]["buff->steam"], item, "BUY ON BUFF, SELL ON STEAM"]
        if(res[item]["steam->buff"] > max_steam_to_buff[1]):
            max_steam_to_buff = [res[item], res[item]["steam->buff"], item, "BUY ON STEAM, SELL ON BUFF"]
        
        with open("steamMarketApi/data/requests/visualizer.csv", "a", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")

            lst = list(res[item].values())
            for i in list(res[item].keys()):
                if i == "buff->steam" or i == "steam->buff":
                    lst[list(res[item].keys()).index(i)] = round(lst[list(res[item].keys()).index(i)]*100, 2)
            
            writer.writerow(lst)
    
    for element in [max_buff_to_steam, max_steam_to_buff]:
        if [max_buff_to_steam, max_steam_to_buff].index(element) == 0:
            print("\033[95m")
        else:
            print("\033[94m")
        print(element[3])
        for i in list(element[0].keys()):
            if "item" in i:
                print(element[0][i])
            elif "date" in i:
                print("\t" + i, element[0][i])
            elif "orders" in i:
                print("\t\t\t" + i, element[0][i])
            else:
                print("\t\t" + i, element[0][i])
        plot.plot(element[0]["item"])

if __name__ == '__main__':
    # asyncio.run(scrape.main(True))
    asyncio.run(main())
    



