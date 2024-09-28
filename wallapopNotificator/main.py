import traceback
from telegramBot import main as telegramBot

import requests
import json
import csv
import time
import datetime

first = "https://api.wallapop.com/api/v3/search?latitude=40.21083068847656&longitude=-8.405817031860352&keywords=Samsung%20s23&min_sale_price=200&max_sale_price=400&order_by=newest&is_shippable=true&country_code=PT&source=stored_filters&show_multiple_sections=false"

after = "https://api.wallapop.com/api/v3/search?next_page="

def run():
    try:
        while True:
            url = first
            new_data = []
            for _ in range(10):
                response = requests.get(url)
                while response.status_code != 200:
                    print(f"{datetime.datetime.now().strftime('%H:%M')} - Error {response.status_code}. Retrying in 1 second.")
                    time.sleep(1)
                    response = requests.get(url)
                json = response.json()
                url = after + json["meta"]["next_page"]

                # print(f"{datetime.datetime.now().strftime('%H:%M')} - Page {json['meta']['current_page']} of {json['meta']['total_pages']}")

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
                        new_data.append(item)
                
            
            with open("wallapopNotificator/resources/data.csv", "r") as file:
                old_data = file.readlines()
                old_ids = [i.split(",")[6] for i in old_data]
            with open("wallapopNotificator/resources/data.old.csv", "w") as file:
                file.writelines(old_data)

            new_listings = []
            for i in range(len(new_data)):
                if new_data[i][6] not in old_ids:
                    new_listings.append(new_data[i])

            if len(new_listings) == 0:
                print(f"{datetime.datetime.now().strftime('%H:%M')} - No new items found.")
            else:
                print(f"{datetime.datetime.now().strftime('%H:%M')} - {len(new_listings)} new items found.")
                for i in new_listings:
                    telegram_message = "New item found:\n" + i[8] + " " + i[1] + "\n" + i[5] + "\n\n"
                    telegramBot.sendMessage(telegram_message)
                    print(telegram_message)

            open("wallapopNotificator/resources/data.csv", "w").close()
            with open("wallapopNotificator/resources/data.csv", "a") as file:
                for i in new_data:
                    for j in i:
                        file.write(str(j) + ",")
                    file.write("\n")
            
            time.sleep(60)
    except Exception as e:
        telegram_message = "Error:\n"
        telegram_message += traceback.format_exc()
        telegramBot.sendMessage(telegram_message)
