from telegramBot import main as telegramBot

import requests
import json
import csv
import time
import datetime

first = "https://api.wallapop.com/api/v3/search?latitude=40.21083068847656&longitude=-8.405817031860352&keywords=Samsung%20s23&min_sale_price=200&max_sale_price=400&order_by=newest&is_shippable=true&country_code=PT&source=stored_filters&show_multiple_sections=false"

after = "https://api.wallapop.com/api/v3/search?next_page="


def get_json(url):
    response = requests.get(url)
    return response.json()

def run():

    try:
        while True:
            url = first
            with open("wallapopNotificator/resources/data.csv", "r") as file:
                old_data = file.readlines()
                old_ids = [i.split(",")[6] for i in old_data]
            
            with open("wallapopNotificator/resources/data.csv", "w") as file:
                pass

            
            
            for _ in range(10):



                json = get_json(url)

                url = after + json["meta"]["next_page"]
                with open("wallapopNotificator/resources/data.csv", "a") as file:
                    writer = csv.writer(file)


                    for i in json["data"]["section"]["payload"]["items"]:
                        
                        if " fe" not in i["title"].lower():

                            created_at = datetime.datetime.fromtimestamp(i["created_at"] / 1e3).strftime("%H:%M %d-%m")
                            modified_at = datetime.datetime.fromtimestamp(i["modified_at"] / 1e3).strftime("%H:%M %d-%m")

                            diff = sum ( created_at[i] != modified_at[i] for i in range(len(created_at)) )

                            item = [
                                i["reserved"]["flag"],
                                str(i["price"]["amount"]) + " " + i["price"]["currency"],
                                created_at,
                                modified_at,
                                "new" if diff < 2 else "updated",
                                "https://pt.wallapop.com/item/" + i["web_slug"] + " ",
                                i["id"],
                                i["user_id"],
                                i["title"],
                                i["description"].replace("\n", "\t"),
                            ]
                            writer.writerow(item)
                
            with open("wallapopNotificator/resources/data.csv", "r") as file:
                new_data = file.readlines()
                new_ids = [i.split(",")[6] for i in new_data]
            
            flag = False
            added_ids = []
            for i in new_ids:
                if i not in old_ids:
                    flag = True
                    added_ids.append(i)

            if flag and new_data != [] and old_data != []:
                telegram_message = "New items found:\n"
                for i in new_data:
                    if i.split(",")[6] in added_ids:
                        telegram_message += i.split(",")[8] + "\n" + i.split(",")[5] + "\n\n"
                telegramBot.sendMessage(telegram_message)
                print(telegram_message)
                pass
            else:
                print(f"{datetime.datetime.now().strftime('%H:%M')} - No new items found.")
            time.sleep(60)

    except KeyboardInterrupt:
        pass


    # print(first_json["data"]["section"]["payload"]["items"].keys())
