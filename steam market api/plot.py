import math
import statistics
import os
from matplotlib import pyplot as plt
import numpy as np
import datetime as dt
import collections
import matplotlib.dates as mdates



files = {
    "buff": os.listdir("data/requests/buff/"),
    "steam": os.listdir("data/requests/steam/"),
}


def get_price_history(item:str):
    prices = {}

    for file in files["steam"]:
        with open("data/requests/"+"steam"+"/"+file, "r") as f:
            for row in list(f)[1:]:
                if(row.split(";")[1] == item or row.split(";")[1].replace('"', "") == item):
                    date = row.split(";")[0]
                    date = file.replace(".csv", "") + " " + date

                    if date not in prices:
                        prices[date] = {
                            "date": dt.datetime.strptime(date, "%Y-%m-%d %H:%M"),
                            "steam_price": float(row.split(";")[2]),
                            "steam_volume": int(row.split(";")[3]),
                            "buff_price": 0,
                            "buff_volume": 0,
                        }
                    else:
                        prices[date]["steam_price"] = float(row.split(",")[2])
                        prices[date]["steam_volume"] = float(row.split(",")[3])
    for file in files["buff"]:
        with open("data/requests/"+"buff"+"/"+file, "r") as f:
            for row in list(f)[1:]:
                if(row.split(";")[1] == item or row.split(";")[1].replace('"', "") == item):
                    date = row.split(";")[0]
                    date = file.replace(".csv", "") + " " + date

                    if date not in prices:
                        prices[date] = {
                            "date": dt.datetime.strptime(date, "%Y-%m-%d %H:%M"),
                            "steam_price": 0,
                            "steam_volume": 0,
                            "buff_price": float(row.split(";")[2]),
                            "buff_volume": int(row.split(";")[3].replace("\n", "")),
                        }
                    else:
                        prices[date]["buff_price"] = float(row.split(";")[2])
                        prices[date]["buff_volume"] = int(row.split(";")[3])

    return list(prices.values())

def plot(item:str):
    prices = get_price_history(item)

    prices = sorted(prices, key=lambda x: x["date"])

    # print(prices)


    for i in range(len(prices)):
        for key in prices[i].keys():
            if(prices[i][key] == 0):
                if i == 0:
                    for j in range(i+1, len(prices)):
                        if prices[j][key] != 0:
                            prices[i][key] = prices[j][key]
                            break
                else:
                    prices[i][key] = prices[i-1][key]

    dates, steam_price, steam_volume, buff_price, buff_volume, diff = [], [], [], [], [], []
    for i in prices:
        dates.append(i["date"])
        steam_price.append(i["steam_price"])
        steam_volume.append(i["steam_volume"])
        buff_price.append(i["buff_price"])
        buff_volume.append(i["buff_volume"])
        diff.append(i["steam_price"] - i["buff_price"])

    # print(steam_price)
    # print(dates)
    # plt.bar(dates,steam_volume, width=0.03)
    plt.plot(dates,steam_price)
    plt.scatter(dates,steam_price, s=10)
    plt.plot(dates,buff_price)
    plt.scatter(dates,buff_price, s=10)
    plt.plot(dates,diff, color="black")
    plt.scatter(dates,diff, color="black", s=10)
    plt.gcf().autofmt_xdate()
    plt.title(item)
    # plt.legend(["steam volume:" + str(steam_volume[-1]), "buff volume: " + str(buff_volume[-1]), "diff"])
    plt.show()
